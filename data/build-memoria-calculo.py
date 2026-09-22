#!/usr/bin/env python3
"""
Insumos da memória de cálculo do painel, por UF.

A aba Coeficientes mostra como cada coeficiente do ente foi obtido, passo a
passo, de modo que a pessoa consiga repetir a conta. Quase tudo de que ela
precisa já está publicado: a série histórica por ano está em
painel-estados.json e em painel-municipios/<UF>.json, e as médias e os
coeficientes também. O que falta é de dois tipos.

O primeiro são as referências de denominador: o total nacional da receita de
referência, a soma nacional do produto POF × domicílios e, dentro da UF, a
população somada, a contagem de municípios e a soma de renda × população.
Sem esses números a pessoa vê o resultado mas não consegue refazer a divisão.

O segundo é o Seguro-Receita. O arquivo seguro-receita-repasses.json tem
5.596 entes em cinco anos e ocupa 8,3 MB, grande demais para o navegador
carregar só para mostrar cinco linhas de um município. Esta rotina fatia por
UF, como já é feito com os municípios.

Nada aqui recalcula o modelo: a rotina só lê os resultados já publicados e os
reorganiza. Os coeficientes continuam vindo de build-resultados-consolidados.py.

Uso:
  python3 build-memoria-calculo.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
OUT_DIR = HERE / "memoria-calculo"

ANOS_HIST = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def carrega(nome):
    with open(HERE / nome, encoding="utf-8") as f:
        return json.load(f)


def grava(caminho, obj):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def arredonda(v, casas=2):
    return None if v is None else round(v, casas)


def nivel_de_nivelamento(entidades):
    """Razão até a qual o fundo eleva os entes contemplados naquele ano.

    O repasse é sequencial: quem tem a menor razão entre o IBS-destino
    recebido e a receita de referência ajustada é elevado primeiro, e o fundo
    se esgota num patamar comum. Conferir que esse patamar é o mesmo para
    todos os contemplados é o que valida a leitura; se não for, a premissa
    mudou e a memória estaria contando outra história.
    """
    niveis = [
        (e["numerador"] + e["repasse"]) / e["denom_capado"]
        for e in entidades
        if e["repasse"] > 0 and e["denom_capado"]
    ]
    if not niveis:
        return None
    if max(niveis) - min(niveis) > 1e-6:
        raise SystemExit(
            f"nivelamento não é uniforme: {min(niveis):.8f} a {max(niveis):.8f}"
        )
    return sum(niveis) / len(niveis)


def main():
    coef_uf = carrega("coeficientes-uf.json")
    phi = carrega("phi-dest-pof-censo.json")
    rateio = carrega("rateio-destino-municipios.json")
    estados = carrega("painel-estados.json")["estados"]
    seguro = carrega("seguro-receita-repasses.json")

    total_br = coef_uf["total_br_2025"]
    anos_seguro = sorted(seguro["anos"].keys())

    # Denominador do coeficiente de destino: a soma nacional do produto entre a
    # despesa familiar da POF e os domicílios do Censo.
    soma_produto_br = sum(
        v["despesa_pof_familiar"] * v["domicilios_censo_2022"]
        for v in phi["por_uf"].values()
    )

    nacional = {
        "fonte": "Reorganização dos resultados já publicados; nenhum valor é recalculado aqui.",
        "anos_historicos": ANOS_HIST,
        "total_br_2025": total_br,
        "soma_produto_pof_censo_br": soma_produto_br,
        "frac_estado_pct": phi["frac_estado_pct"],
        "frac_muni_pct": phi["frac_muni_pct"],
        "seguro_por_ano": {},
    }
    for ano in anos_seguro:
        a = seguro["anos"][ano]
        nacional["seguro_por_ano"][ano] = {
            "pool": arredonda(a["pool"]),
            "n_entes": len(a["entidades"]),
            "n_beneficiarios": a["n_beneficiarios"],
            "nivel": nivel_de_nivelamento(a["entidades"]),
        }

    # Fatia do Seguro-Receita por ente, indexada por UF.
    seguro_estado = {}   # uf -> ano -> registro
    seguro_muni = {}     # uf -> cod -> ano -> registro
    for ano in anos_seguro:
        for e in seguro["anos"][ano]["entidades"]:
            reg = {
                "num": arredonda(e["numerador"]),
                "den": arredonda(e["denom_capado"]),
                "raz": round(e["razao"], 8),
                "rep": arredonda(e["repasse"]),
            }
            if e["esfera"] == "estado":
                seguro_estado.setdefault(e["uf"], {})[ano] = reg
            else:
                cod = e["id"].replace("MUN-", "")
                seguro_muni.setdefault(e["uf"], {}).setdefault(cod, {})[ano] = reg

    # Referências intra-UF do rateio de destino municipal.
    por_uf_munis = {}
    for cod, m in rateio["municipios"].items():
        por_uf_munis.setdefault(m["uf"], {})[cod] = m

    OUT_DIR.mkdir(exist_ok=True)
    escritos = []
    for uf, edata in estados.items():
        munis = por_uf_munis.get(uf, {})
        pop_uf = sum(m["pop_media"] for m in munis.values())
        soma_renda_pop = sum(
            (m.get("renda_domiciliar_per_capita_2022") or 0) * m["pop_media"]
            for m in munis.values()
        )
        p = phi["por_uf"][uf]
        saida = {
            "uf": uf,
            "refs": {
                "despesa_pof_familiar": p["despesa_pof_familiar"],
                "domicilios_censo_2022": p["domicilios_censo_2022"],
                "produto_uf": p["despesa_pof_familiar"] * p["domicilios_censo_2022"],
                "phi_dest_uf_pct": p["pof_censo_bruto_pct"],
                "coef_estado_pct": edata["coef_pleno_estado_pct"],
                "coef_municipios_pct": edata["coef_pleno_municipio_pct"],
                "cota_parte_municipios_pct": sum(m["cota_parte_pct"] for m in munis.values()),
                "propria_municipios_pct": sum(m["propria_pct"] for m in munis.values()),
                "pop_uf": pop_uf,
                "n_municipios": len(munis),
                "soma_renda_pop_uf": soma_renda_pop,
            },
            "seguro_estado": seguro_estado.get(uf, {}),
            "seguro_municipios": seguro_muni.get(uf, {}),
        }
        caminho = OUT_DIR / f"{uf}.json"
        grava(caminho, saida)
        escritos.append((uf, caminho.stat().st_size))

    grava(OUT_DIR / "nacional.json", nacional)

    # Conferência: as cadeias que a página vai exibir precisam fechar aqui,
    # antes de virarem texto na tela.
    es = estados["ES"]
    media_es = sum(es["historico_por_ano"][str(a)]["estado_reais_2025"] for a in ANOS_HIST) / len(ANOS_HIST)
    cpt_es = media_es / total_br * 100
    assert abs(cpt_es - es["coef_cpt_estado_pct"]) < 1e-9, "φCPT estadual não fecha"
    p_es = phi["por_uf"]["ES"]
    dest_es = p_es["despesa_pof_familiar"] * p_es["domicilios_censo_2022"] / soma_produto_br * 100
    assert abs(dest_es - p_es["pof_censo_bruto_pct"]) < 1e-9, "φdest da UF não fecha"
    assert abs(dest_es * phi["frac_estado_pct"] / 100 - es["coef_pleno_estado_pct"]) < 1e-9, \
        "fração estadual do destino não fecha"

    maior = max(escritos, key=lambda x: x[1])
    total = sum(s for _, s in escritos)
    print(f"Escritos {len(escritos)} arquivos em {OUT_DIR}")
    print(f"Maior: {maior[0]}.json com {maior[1]/1e3:.0f} kB | soma {total/1e6:.2f} MB")
    print(f"Anos do Seguro-Receita: {', '.join(anos_seguro)}")
    print("Conferências de fechamento: φCPT, φdest e fração estadual, todas exatas.")


if __name__ == "__main__":
    main()
