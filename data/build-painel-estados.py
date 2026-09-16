#!/usr/bin/env python3
"""
Exportação complementar ao Estudo 15 (build-resultados-consolidados.py),
para o Painel de Indicadores da Reforma Tributária -- equivalente, para as
27 UFs, ao que build-painel-municipios.py já faz para municípios.

Reaplica as mesmas funções já publicadas em build-resultados-consolidados.py
(compute_params_uf, build_repasse_index) -- nenhuma lógica de projeção é
reescrita. resultados-consolidados-ibs.json já publica pos/contrafactual/
variação por UF (por_uf, por_uf_estado) e os três coeficientes (anexo_a);
este script acrescenta o que falta para a "ficha do ente": a decomposição
em 4 categorias por ano, o repasse do Seguro-Receita por ano (direto de
seguro-receita-repasses-longo-prazo.json, sem recomputar), e a série
histórica 2019-2025 (mesma proporcionalização de build-coeficientes-uf.py).

Uso:
  python3 build-painel-estados.py
"""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "painel-estados.json"

spec = importlib.util.spec_from_file_location(
    "build_resultados_consolidados", HERE / "build-resultados-consolidados.py"
)
brc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brc)

HIST_ANOS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def main():
    ref_data = brc.load("reforma-tributaria.json")
    coef_uf = brc.load("coeficientes-uf.json")
    phi_dest = brc.load("phi-dest-pof-censo.json")
    nac_data = brc.load("ibs-projecao-nacional.json")
    seguro_lp = brc.load("seguro-receita-repasses-longo-prazo.json")

    nacional_by_year = {r["ano"]: r for r in nac_data["projecao"]}
    params_uf, total_br_2025 = brc.compute_params_uf(ref_data, coef_uf, phi_dest)
    repasse_por_uf_lp = seguro_lp.get("anos", {})

    # ── Série histórica por UF, 2019-2025 (mesmos insumos e mesmo deflator
    # de build-coeficientes-uf.py, expostos ano a ano) ──
    dca_icms_br = ref_data.get("dca_icms_br", {})
    dca_iss_br = ref_data.get("dca_iss_br", {})
    dca_fecop_br = ref_data.get("dca_fecop_br", {})
    dca_outras_uf = ref_data.get("dca_icms_outras_deducoes_por_uf", {})
    dca_icms_uf = ref_data.get("dca_icms_por_uf", {})
    dca_fecop_uf = ref_data.get("dca_fecop_por_uf", {})
    dca_transf_uf = ref_data.get("dca_transf_munis_por_uf", {})
    dca_iss_uf = ref_data.get("dca_iss_por_uf", {})

    total_br_hist = {}
    for ano in HIST_ANOS:
        s = str(ano)
        icms, iss = dca_icms_br.get(s), dca_iss_br.get(s)
        fecop = dca_fecop_br.get(s, 0) or 0
        outras = sum((dca_outras_uf.get(s, {}) or {}).values())
        total_br_hist[ano] = (icms - outras + iss + fecop) if (icms is not None and iss is not None) else None
    deflators_hist = {ano: (1.0 if ano == 2025 else
                             (total_br_hist[2025] / total_br_hist[ano] if total_br_hist.get(ano) else None))
                       for ano in HIST_ANOS}

    estados = {}
    for uf in brc.UFS:
        p = params_uf[uf]
        is_df = uf == "DF"

        historico_por_ano = {}
        for ano in HIST_ANOS:
            s = str(ano)
            defl = deflators_hist.get(ano)
            icms_v = (dca_icms_uf.get(s) or {}).get(uf)
            if icms_v is None or defl is None:
                continue
            iss_v = (dca_iss_uf.get(s) or {}).get(uf, 0) or 0
            fecop_v = (dca_fecop_uf.get(s) or {}).get(uf, 0) or 0
            outras_v = (dca_outras_uf.get(s) or {}).get(uf, 0) or 0
            cota_v = 0.0 if is_df else ((dca_transf_uf.get(s) or {}).get(uf) if (dca_transf_uf.get(s) or {}).get(uf) is not None else icms_v * 0.25)
            r_estado = (icms_v - outras_v + iss_v + fecop_v) if is_df else (icms_v - outras_v - cota_v + fecop_v)
            r_muni = None if is_df else (iss_v + cota_v)
            historico_por_ano[ano] = {
                "icms_reais_2025": icms_v * defl,
                "outras_deducoes_reais_2025": outras_v * defl,
                "iss_reais_2025": iss_v * defl,
                "fecop_reais_2025": fecop_v * defl,
                "cota_parte_reais_2025": cota_v * defl,
                "estado_reais_2025": r_estado * defl,
                "municipios_reais_2025": None if r_muni is None else r_muni * defl,
            }

        # Decomposição em 4 categorias e repasse do Seguro-Receita, por
        # esfera. Mesma fórmula de project_uf (não reescrita, só exposta por
        # parte em vez de só o total).
        componentes = {"estado": {}, "total": {}}
        repasse_por_ano = {"estado": {}, "municipio": {}}
        for a in brc.ANOS:
            nac = nacional_by_year[a]
            ca = nac.get("ca", 0.0)
            rp_uf = (repasse_por_uf_lp.get(str(a), {}) or {}).get("repasse_por_uf", {}).get(uf, {})
            repasse_estado = rp_uf.get("estado", 0.0) or 0.0
            repasse_muni = rp_uf.get("municipio", 0.0) or 0.0
            repasse_por_ano["estado"][a] = repasse_estado
            repasse_por_ano["municipio"][a] = repasse_muni

            for esfera, parts, repasse in (
                ("estado", [p["estado"]], repasse_estado),
                ("total", [p["estado"]] + ([p["municipio"]] if p["municipio"] else []), repasse_estado + repasse_muni),
            ):
                origem = sum(nac["icms_iss_residual"] * part["coefNeutro"] for part in parts)
                cpt = sum((1 - ca) * nac["ibs_historico"] * part["coefCPT"] for part in parts)
                destino = sum(nac["ibs_destino_liquido"] * part["coefPleno"] for part in parts)
                seguro = (1 - ca) * repasse
                componentes[esfera][a] = {"origem": origem, "cpt": cpt, "destino": destino, "seguro": seguro}

        estados[uf] = {
            "nome": brc.NOMES_UF[uf],
            "is_df": is_df,
            "coef_neutro_estado_pct": p["estado"]["coefNeutro"] * 100,
            "coef_cpt_estado_pct": p["estado"]["coefCPT"] * 100,
            "coef_pleno_estado_pct": p["estado"]["coefPleno"] * 100,
            "coef_neutro_municipio_pct": None if not p["municipio"] else p["municipio"]["coefNeutro"] * 100,
            "coef_cpt_municipio_pct": None if not p["municipio"] else p["municipio"]["coefCPT"] * 100,
            "coef_pleno_municipio_pct": None if not p["municipio"] else p["municipio"]["coefPleno"] * 100,
            "historico_por_ano": historico_por_ano,
            "componentes_por_ano": componentes,
            "repasse_seguro_receita_por_ano": repasse_por_ano,
        }

    output = {
        "_meta": {
            "descricao": (
                "Complemento por UF ao Estudo 15 (resultados-consolidados-ibs.json), "
                "para o Painel de Indicadores da Reforma Tributária: decomposição da "
                "projeção 2029-2033 em 4 categorias (origem/ICMS-ISS residual, IBS "
                "histórico, IBS destino, Seguro-Receita -- mesma fórmula de project_uf, "
                "só exposta por parte, esferas estado e total), repasse do "
                "Seguro-Receita por ano e esfera (direto de "
                "seguro-receita-repasses-longo-prazo.json), e série histórica "
                "2019-2025 (ICMS bruto, outras deduções do ICMS, ISS, FECOP, "
                "cota-parte, real R$ 2025, mesmo deflator e proporcionalização "
                "de build-coeficientes-uf.py; os mesmos componentes que "
                "formam o coeficiente φCPT do estado em coeficientes-uf.json). "
                "pos/contrafactual/variação por ano já estão publicados em "
                "resultados-consolidados-ibs.json (por_uf, por_uf_estado) e não são "
                "repetidos aqui."
            ),
            "fonte": "Estudos 02, 03, 06, 09, 10, 11, 12, 13, 15 deste site; ver nota-metodologica-ibs.html",
            "anos_projecao": brc.ANOS,
            "anos_historico": HIST_ANOS,
        },
        "estados": estados,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=1)

    print(f"Salvo em {OUT}")
    print(f"UFs: {len(estados)}")


if __name__ == "__main__":
    main()
