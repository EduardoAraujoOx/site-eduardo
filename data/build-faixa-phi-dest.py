#!/usr/bin/env python3
"""
Faixa de incerteza do coeficiente de destino do governo estadual, entre os
quatro métodos de estimativa da proxy de consumo já calculados em
build-phi-dest-pof-censo.py: POF/Censo bruto (o método publicado nas
demais abas do painel), POF/Censo ponderado por tributabilidade, a tabela
de Gobetti e Monteiro (2023, IPEA) e um modelo interno anterior.

Por que só o governo estadual, não os municípios: a incerteza tratada aqui
é sobre o tamanho do "balde" de destino de cada UF, isto é, qual fração do
consumo nacional aquela UF representa. Não é sobre como esse balde é
repartido dentro da UF entre o estado e seus municípios (art. 361 da LC
214/2025, fração fixa) nem entre os municípios entre si (peso por renda
per capita do Censo, que não tem hoje uma alternativa externa publicada
equivalente ao Gobetti para servir de segundo ponto de comparação). Migrar
esta faixa para municípios exigiria inventar um estimador sem essa mesma
base empírica, e essa é uma decisão deliberadamente adiada para outra
rodada. Por isso os municípios continuam usando, nos quatro cenários,
exatamente o coeficiente já publicado em rateio-destino-municipios.json
(POF/Censo bruto) -- o "balde" de cada UF muda de tamanho, mas a régua
que reparte a fatia municipal dentro dele não.

Por que refazer o nivelamento do Seguro-Receita inteiro, e não só a conta
do coeficiente: trocar o método de uma UF muda o numerador dela na
disputa pelo fundo (art. 117 LC 227/2026), o que desloca a régua de
nivelamento sequencial para TODO MUNDO -- inclusive entes que não
mudaram de método. Ignorar esse efeito de segunda ordem faria a faixa
subestimar a diferença entre os métodos nos entes que recebem repasse.

Uso:
  python3 build-faixa-phi-dest.py
"""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "faixa-phi-dest-estados.json"

METODOS = {
    "pof_censo_bruto": {
        "chave": "pof_censo_bruto_pct",
        "rotulo": "POF/Censo, consumo bruto",
        "nota": "Método publicado nas demais abas do painel: despesa de consumo média mensal (POF 2017–2018) × domicílios (Censo 2022), sem ajuste por tributabilidade.",
    },
    "pof_censo_ponderado": {
        "chave": "pof_censo_ponderado_pct",
        "rotulo": "POF/Censo, ponderado por tributabilidade",
        "nota": "Mesma base do método publicado, substituindo a despesa total pela despesa ponderada pela tributabilidade de cada categoria (alimentação, por exemplo, pesa menos por ter alíquota reduzida).",
    },
    "gobetti_2023": {
        "chave": "gobetti_tabela1_2023_pct",
        "rotulo": "Gobetti e Monteiro (2023)",
        "nota": "Tabela 1 de Gobetti e Monteiro, IPEA TD 2022 (2023): estimativa publicada de forma independente, não recalculada pelo painel.",
    },
    "modelo_anterior": {
        "chave": "modelo_anterior_pct",
        "rotulo": "Modelo interno anterior",
        "nota": "Versão anterior da estimativa própria do painel, mantida aqui só para comparação histórica.",
    },
}
ANOS = [2029, 2030, 2031, 2032, 2033]


def load(nome):
    with open(HERE / nome, encoding="utf-8") as f:
        return json.load(f)


def load_module(nome):
    spec = importlib.util.spec_from_file_location(nome, HERE / f"{nome}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    seguro_mod = load_module("build-seguro-receita-repasses")
    UFS = seguro_mod.UFS

    ref = load("reforma-tributaria.json")
    coeficientes_uf = load("coeficientes-uf.json")
    coeficientes_municipios = load("coeficientes-municipios.json")
    phi_dest_data = load("phi-dest-pof-censo.json")
    rateio_muni = load("rateio-destino-municipios.json")
    nacional = load("ibs-projecao-nacional.json")
    pop_uf = load("populacao-uf-media-2019-2026.json")
    pop_muni = load("populacao-municipios-media-2019-2026.json")
    painel_estados = load("painel-estados.json")["estados"]
    resultados_pub = load("resultados-consolidados-ibs.json")["por_uf_estado"]

    nac_by_year = {r["ano"]: r for r in nacional["projecao"]}

    dca_icms_2025 = ref.get("dca_icms_por_uf", {}).get("2025", {})
    dca_iss_2025 = ref.get("dca_iss_por_uf", {}).get("2025", {})
    dca_fecop_2025 = ref.get("dca_fecop_por_uf", {}).get("2025", {})
    dca_cota_2025 = ref.get("dca_transf_munis_por_uf", {}).get("2025", {})
    dca_outras_2025 = ref.get("dca_icms_outras_deducoes_por_uf", {}).get("2025", {})
    total_br_2025 = sum(
        (dca_icms_2025.get(uf, 0) or 0) - (dca_outras_2025.get(uf, 0) or 0)
        + (dca_iss_2025.get(uf, 0) or 0) + (dca_fecop_2025.get(uf, 0) or 0)
        for uf in UFS
    )

    frac_estado = phi_dest_data["frac_estado_pct"] / 100
    pop_by_uf = {uf: v["pop_media"] for uf, v in pop_uf["ufs"].items()}

    # coef_cpt (histórico) e coef_neutro não dependem do método de destino,
    # então são calculados uma única vez e reaproveitados nos quatro
    # cenários. r_estado replica exatamente build-resultados-consolidados.py
    # (não a versão simplificada de build-seguro-receita-repasses.py, que
    # não subtrai "outras deduções" do ICMS e esquece o ISS do DF no
    # numerador -- ali sem efeito prático porque esse r_estado local nunca é
    # devolvido pela função, mas replicá-lo aqui divergiria do coefNeutro
    # publicado em todo o resto do painel).
    coefs_fixos = {}
    for uf in UFS:
        icms = dca_icms_2025.get(uf, 0) or 0
        iss = dca_iss_2025.get(uf, 0) or 0
        fecop = dca_fecop_2025.get(uf, 0) or 0
        outras = dca_outras_2025.get(uf, 0) or 0
        cuf = coeficientes_uf["por_uf"].get(uf, {})
        is_df = bool(cuf.get("is_df"))
        cota_declarada = dca_cota_2025.get(uf)
        cota = 0 if is_df else (cota_declarada if cota_declarada is not None else icms * 0.25)
        r_estado = (icms - outras + iss + fecop) if is_df else (icms - outras - cota + fecop)
        coefs_fixos[uf] = {
            "is_df": is_df,
            "coef_neutro": r_estado / total_br_2025 if total_br_2025 else 0,
            "coef_cpt_estado": ((cuf.get("coeficiente_total_pct") if is_df else cuf.get("coeficiente_estado_pct")) or 0) / 100,
            "coef_cpt_total": (cuf.get("coeficiente_total_pct") or 0) / 100,
            "iss_2025": iss,
        }

    # Municípios: sempre o coeficiente já publicado (POF/Censo bruto), fixo
    # nos quatro cenários -- ver docstring do módulo.
    municipios_entidades = []
    for cod, r in coeficientes_municipios["municipios"].items():
        rd = rateio_muni["municipios"].get(cod)
        pm = pop_muni["municipios"].get(cod)
        if rd is None or pm is None:
            continue
        municipios_entidades.append({
            "id": f"MUN-{cod}", "uf": r["uf"], "esfera": "municipio",
            "denom": r["receita_media_referencia"], "phi_dest": rd["phi_dest_pct"] / 100,
            "pop": pm["pop_media"],
        })

    def roda_metodo(chave_metodo):
        """Reproduz compute_params_estado()/main() de
        build-seguro-receita-repasses.py, trocando só a coluna de φdest
        usada para os estados. Municípios ficam como estão."""
        entidades = []
        for uf in UFS:
            cf = coefs_fixos[uf]
            denom = (cf["coef_cpt_total"] if cf["is_df"] else cf["coef_cpt_estado"]) * total_br_2025
            phi_uf = (phi_dest_data["por_uf"].get(uf, {}).get(chave_metodo) or 0) / 100
            phi_dest_estado = phi_uf if cf["is_df"] else phi_uf * frac_estado
            entidades.append({
                "id": f"UF-{uf}", "uf": uf, "esfera": "estado", "is_df": cf["is_df"],
                "denom": denom, "phi_dest": phi_dest_estado, "pop": pop_by_uf.get(uf, 0),
            })
        entidades += municipios_entidades

        # Teto de 3x a média nacional per capita da esfera (art. 117, §§3º-6º):
        # não depende do método de destino, mas precisa ser recalculado porque
        # a lista de entidades acima é nova a cada chamada.
        grupo_estado = [e for e in entidades if e["esfera"] == "estado"]
        denom_df_icms = next(coefs_fixos[uf]["coef_cpt_estado"] * total_br_2025 for uf in UFS if coefs_fixos[uf]["is_df"])
        soma_denom_estado = sum((denom_df_icms if e.get("is_df") else e["denom"]) for e in grupo_estado)
        soma_pop_estado = sum(e["pop"] for e in grupo_estado)
        media_pc_estado = soma_denom_estado / soma_pop_estado if soma_pop_estado else 0

        grupo_muni = [e for e in entidades if e["esfera"] == "municipio"]
        uf_df = next(uf for uf in UFS if coefs_fixos[uf]["is_df"])
        denom_df_iss = coefs_fixos[uf_df]["iss_2025"]
        pop_df = pop_by_uf.get(uf_df, 0)
        soma_denom_muni = sum(e["denom"] for e in grupo_muni) + denom_df_iss
        soma_pop_muni = sum(e["pop"] for e in grupo_muni) + pop_df
        media_pc_muni = soma_denom_muni / soma_pop_muni if soma_pop_muni else 0

        for e in entidades:
            if e["esfera"] == "estado" and e.get("is_df"):
                teto = 3 * (media_pc_estado + media_pc_muni) * e["pop"]
            elif e["esfera"] == "estado":
                teto = 3 * media_pc_estado * e["pop"]
            else:
                teto = 3 * media_pc_muni * e["pop"]
            e["denom_capado"] = min(e["denom"], teto) if e["pop"] > 0 else e["denom"]

        repasse_estado_por_ano = {uf: {} for uf in UFS}
        for a in ANOS:
            nac = nac_by_year[a]
            ibsd = nac["ibs_destino_liquido"]
            for e in entidades:
                e["numerador"] = ibsd * e["phi_dest"]
            pares = [(e["numerador"], e["denom_capado"]) for e in entidades]
            repasses = seguro_mod.water_fill(pares, nac["ibs_seguro_receita"])
            for e, rep in zip(entidades, repasses):
                if e["esfera"] == "estado":
                    repasse_estado_por_ano[e["uf"]][a] = rep

        phi_dest_estado_uf = {e["uf"]: e["phi_dest"] for e in entidades if e["esfera"] == "estado"}
        return phi_dest_estado_uf, repasse_estado_por_ano

    por_uf = {uf: {"metodos": {}} for uf in UFS}
    for chave, meta in METODOS.items():
        phi_dest_estado_uf, repasse_por_ano = roda_metodo(meta["chave"])
        for uf in UFS:
            cf = coefs_fixos[uf]
            coef_pleno = phi_dest_estado_uf[uf]
            variacao_por_ano = {}
            for a in ANOS:
                nac = nac_by_year[a]
                ca = nac["ca"]
                repasse = repasse_por_ano[uf][a]
                total = (nac["icms_iss_residual"] * cf["coef_neutro"]
                         + (1 - ca) * nac["ibs_historico"] * cf["coef_cpt_estado"]
                         + nac["ibs_destino_liquido"] * coef_pleno
                         + (1 - ca) * repasse)
                contra = (nac["icms_iss_residual"] + nac["ibs_bruto"]) * cf["coef_neutro"]
                variacao_por_ano[str(a)] = (total - contra) / contra * 100 if contra else None
            por_uf[uf]["metodos"][chave] = {
                "coef_pleno_estado_pct": coef_pleno * 100,
                "variacao_por_ano": variacao_por_ano,
            }

    # ── Conferência: o método publicado precisa reproduzir exatamente o
    # coeficiente e a variação já publicados nas demais abas, senão a faixa
    # nova estaria contando outra história além da que o resto do painel conta. ──
    max_diff_coef = 0.0
    max_diff_var = 0.0
    for uf in UFS:
        m = por_uf[uf]["metodos"]["pof_censo_bruto"]
        max_diff_coef = max(max_diff_coef, abs(m["coef_pleno_estado_pct"] - painel_estados[uf]["coef_pleno_estado_pct"]))
        pub_var = resultados_pub[uf]["variacao_por_ano"]
        for a in ANOS:
            max_diff_var = max(max_diff_var, abs(m["variacao_por_ano"][str(a)] - pub_var[str(a)] * 100))
    if max_diff_coef > 1e-6:
        raise SystemExit(f"φdest do método publicado não reproduz o coeficiente já publicado: desvio {max_diff_coef:.2e} p.p.")
    if max_diff_var > 1e-6:
        raise SystemExit(f"variação do método publicado não reproduz a variação já publicada: desvio {max_diff_var:.2e} p.p.")

    for uf in UFS:
        for chave in METODOS:
            m = por_uf[uf]["metodos"][chave]
            m["variacao_por_ano"] = {a: (round(v, 6) if v is not None else None) for a, v in m["variacao_por_ano"].items()}
            m["coef_pleno_estado_pct"] = round(m["coef_pleno_estado_pct"], 6)
        vals_2033 = {chave: por_uf[uf]["metodos"][chave]["variacao_por_ano"]["2033"] for chave in METODOS}
        chave_min = min(vals_2033, key=vals_2033.get)
        chave_max = max(vals_2033, key=vals_2033.get)
        por_uf[uf]["min_2033"] = {"metodo": chave_min, "variacao": vals_2033[chave_min]}
        por_uf[uf]["max_2033"] = {"metodo": chave_max, "variacao": vals_2033[chave_max]}
        por_uf[uf]["amplitude_2033_pp"] = round(vals_2033[chave_max] - vals_2033[chave_min], 6)

    saida = {
        "fonte": "data/phi-dest-pof-censo.json (quatro métodos) + o mesmo nivelamento do Seguro-Receita de build-seguro-receita-repasses.py, refeito para cada método.",
        "descricao": "Faixa de variação do governo estadual em cada ano da transição, conforme o método usado para estimar o coeficiente de destino (φdest). O método 'pof_censo_bruto' é o publicado nas demais abas; os outros três servem de comparação. Municípios não estão aqui: ver docstring de build-faixa-phi-dest.py.",
        "metodo_publicado": "pof_censo_bruto",
        "anos": ANOS,
        "metodos": METODOS,
        "por_uf": por_uf,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Salvo em {OUT} ({OUT.stat().st_size/1e3:.0f} kB)")
    print("Conferência: o método publicado reproduz o coeficiente já publicado, "
          f"desvio máximo {max_diff_coef:.2e} p.p.; variação, desvio máximo {max_diff_var:.2e} p.p.")
    amps = sorted(((por_uf[uf]["amplitude_2033_pp"], uf) for uf in UFS), reverse=True)
    print("Maiores amplitudes entre métodos em 2033 (p.p.):")
    for amp, uf in amps[:5]:
        print(f"  {uf}: {amp:.3f}")


if __name__ == "__main__":
    main()
