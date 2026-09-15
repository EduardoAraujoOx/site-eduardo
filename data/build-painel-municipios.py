#!/usr/bin/env python3
"""
Exportação complementar ao Estudo 15 (build-resultados-consolidados.py),
para o Painel de Indicadores da Reforma Tributária.

Reaplica exatamente as mesmas funções já publicadas e citadas em
resultados-consolidados-ibs.json (project_municipio, compute_params_uf,
compute_neutro_municipal_2025) -- nenhuma lógica de projeção é reescrita ou
alterada aqui. A única diferença é o que é exportado: o Estudo 15 mantém só
os 20 maiores ganhos e as 20 maiores perdas de 2033 (destaques_municipios_2033);
este script exporta o resultado 2029-2033 completo, já computado
internamente por main() mas descartado antes de chegar ao JSON, para todos
os municípios com coeficiente de participação (coeficientes-municipios.json)
e coeficiente de destino (rateio-destino-municipios.json) disponíveis.

As mesmas sinalizações de qualidade do Estudo 15 (neutro_aproximado,
neutro_suspeito, cobertura_anos) são preservadas no output, para que o
front-end trate a incerteza dos dados exatamente como o próprio Estudo 15
já trata -- não como uma tabela "limpa" escondendo os casos frágeis.

Uso:
  python3 build-painel-municipios.py
"""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "painel-municipios-2033.json"

spec = importlib.util.spec_from_file_location(
    "build_resultados_consolidados", HERE / "build-resultados-consolidados.py"
)
brc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brc)


def main():
    ref_data = brc.load("reforma-tributaria.json")
    coef_uf = brc.load("coeficientes-uf.json")
    phi_dest = brc.load("phi-dest-pof-censo.json")
    nac_data = brc.load("ibs-projecao-nacional.json")
    seguro_data = brc.load("seguro-receita-repasses.json")
    coef_muni = brc.load("coeficientes-municipios.json")["municipios"]
    rateio_muni = brc.load("rateio-destino-municipios.json")["municipios"]
    pop_muni = brc.load("populacao-municipios-media-2019-2026.json")["municipios"]

    nacional_by_year = {r["ano"]: r for r in nac_data["projecao"]}
    params_uf, total_br_2025 = brc.compute_params_uf(ref_data, coef_uf, phi_dest)
    r0_neutro_muni = brc.compute_neutro_municipal_2025(ref_data)

    repasse_muni_idx = {}
    for a in brc.ANOS:
        ano_data = (seguro_data.get("anos") or {}).get(str(a))
        if not ano_data:
            continue
        for e in ano_data.get("entidades", []):
            if e.get("esfera") != "municipio":
                continue
            repasse_muni_idx.setdefault(e["id"], {})[a] = e.get("repasse") or 0

    municipios = {}
    for cod, cm in coef_muni.items():
        rd = rateio_muni.get(cod)
        if rd is None:
            continue
        coef_cpt = (cm.get("coeficiente_pct") or 0) / 100
        coef_pleno = (rd.get("phi_dest_pct") or 0) / 100
        uf = cm["uf"]

        r0 = r0_neutro_muni.get(cod)
        neutro_aproximado = r0 is None
        if neutro_aproximado:
            r0 = coef_cpt * total_br_2025

        implied_pelo_cpt = coef_cpt * total_br_2025
        neutro_suspeito = (
            not neutro_aproximado and implied_pelo_cpt > 0
            and not (0.2 <= r0 / implied_pelo_cpt <= 5)
        )

        res = brc.project_municipio(
            cod, r0, coef_cpt, coef_pleno, uf, total_br_2025,
            nacional_by_year, repasse_muni_idx, brc.ANOS,
        )
        pop = (pop_muni.get(cod) or {}).get("pop_media")

        municipios[cod] = {
            "nome": cm["nome"],
            "uf": uf,
            "cobertura_anos": cm.get("cobertura_anos", 0),
            "neutro_aproximado": neutro_aproximado,
            "neutro_suspeito": neutro_suspeito,
            "pop_media": pop,
            "pre_2025": r0,
            "receita_media_referencia_7anos": cm.get("receita_media_referencia"),
            "coef_cpt_pct": coef_cpt * 100,
            "coef_pleno_pct": coef_pleno * 100,
            "cota_parte_pct": rd.get("cota_parte_pct"),
            "propria_pct": rd.get("propria_pct"),
            "renda_domiciliar_per_capita_2022": rd.get("renda_domiciliar_per_capita_2022"),
            "pos_por_ano": {a: res[a]["total"] for a in brc.ANOS},
            "contrafactual_por_ano": {a: res[a]["contrafactual"] for a in brc.ANOS},
            "variacao_por_ano": {a: res[a]["dpct"] for a in brc.ANOS},
        }

    output = {
        "_meta": {
            "descricao": (
                "Projeção de receita municipal 2029-2033, cenário de destino pleno "
                "(mesma metodologia do Estudo 15 -- resultados-consolidados-ibs.json "
                "-- aqui exportada para todos os municípios computados, não só os "
                "20 maiores ganhos/perdas), com os insumos do coeficiente de "
                "participação (coeficientes-municipios.json) e do rateio de destino "
                "(rateio-destino-municipios.json) reunidos no mesmo registro."
            ),
            "fonte": "Estudos 02, 06, 09, 10, 11, 12, 13, 15 deste site; ver nota-metodologica-ibs.html",
            "cobertura_anos_min_recomendada": brc.COBERTURA_MIN,
            "populacao_min_recomendada": brc.POP_MIN,
            "aviso_qualidade": (
                "Municípios com neutro_aproximado=true ou neutro_suspeito=true têm "
                "participação neutra (2025) estimada de forma menos direta; o "
                "Estudo 15 os exclui do ranking de destaques por esse motivo. Exibir "
                "com indicação de incerteza, não como valor definitivo."
            ),
            "anos": brc.ANOS,
        },
        "n_municipios": len(municipios),
        "municipios": municipios,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=1)

    n_ok = sum(1 for m in municipios.values() if not m["neutro_aproximado"] and not m["neutro_suspeito"])
    print(f"Salvo em {OUT}")
    print(f"Municípios: {len(municipios)} | sem ressalva de qualidade: {n_ok}")


if __name__ == "__main__":
    main()
