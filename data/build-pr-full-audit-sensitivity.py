#!/usr/bin/env python3
"""
Cenário de sensibilidade integral da auditoria municipal do Paraná.

Tratamentos:
1. cota-parte do ICMS: participação municipal observada no Portal da
   Transparência do Estado do Paraná, reescalada para fechar no total estadual
   da DCA/SICONFI em cada exercício;
2. ISS: mantém a série DCA auditada, mas substitui SOMENTE observações
   temporalmente sinalizadas que foram confirmadas no PIT/TCE-PR com
   divergência direta superior a 20% frente à rubrica anual de ISSQN;
3. recalcula a receita histórica municipal em R$ de 2025, o CPT, a base de
   2025, o Seguro-Receita nacional e as projeções municipais 2029-2033.

O cenário é uma análise de sensibilidade e NÃO altera os arquivos canônicos.
"""
from __future__ import annotations

import csv
import json
import math
import re
import statistics
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from fundos_art115b import fold
import rateio_consumo_compras as rcc
import cpt2026

HERE = Path(__file__).resolve().parent
OUT = HERE / "auditoria-pr-validacao"
ANOS_HIST = list(range(2019, 2026))
ANOS_PROJ = [2029, 2030, 2031, 2032, 2033]
UFS = ['AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT',
       'PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO']


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def dump_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def num(v):
    if v is None or v == "":
        return None
    return float(v)


def norm_name(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("d'", "d ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    aliases = {"santa cruz de monte castelo": "santa cruz do monte castelo"}
    return aliases.get(s, s)


def water_fill(entidades, pool):
    if pool <= 0 or not entidades:
        return [0.0] * len(entidades)

    valid = [(n, d) for n, d in entidades if d > 0]
    if not valid:
        return [0.0] * len(entidades)

    def total_pago(level):
        return sum(max(0.0, level * d - n) for n, d in entidades if d > 0)

    lo = min(n / d for n, d in valid)
    hi = lo + 1.0
    total_denom = sum(d for _, d in valid)
    while total_pago(hi) < pool:
        hi = lo + (hi - lo) * 2 if hi > lo else hi + pool / total_denom + 1
    for _ in range(100):
        mid = (lo + hi) / 2
        if total_pago(mid) < pool:
            lo = mid
        else:
            hi = mid
    level = (lo + hi) / 2
    return [max(0.0, level * d - n) if d > 0 else 0.0 for n, d in entidades]


def build_state_entities(ref, coef_uf, phi, pop_uf):
    dca_icms = ref.get("dca_icms_por_uf", {}).get("2025", {})
    dca_iss = ref.get("dca_iss_por_uf", {}).get("2025", {})
    dca_fecop = ref.get("dca_fecop_por_uf", {}).get("2025", {})
    old_total = coef_uf["total_br_2025"]
    frac_estado = phi["frac_estado_pct"] / 100

    entities = []
    state_denom_for_mean = {}
    df_iss = None
    for uf in UFS:
        c = coef_uf["por_uf"][uf]
        is_df = bool(c.get("is_df"))
        iss = dca_iss.get(uf, 0) or 0
        phi_dest, _ = rcc.esferas_uf(phi["por_uf"].get(uf, {}), is_df, frac_estado, 0)

        coef_estado = (c.get("coeficiente_estado_pct") or 0) / 100
        coef_total = (c.get("coeficiente_total_pct") or 0) / 100
        denom = (coef_total if is_df else coef_estado) * old_total
        state_denom_for_mean[uf] = coef_estado * old_total
        if is_df:
            df_iss = iss

        entities.append({
            "id": f"UF-{uf}", "nome": uf, "uf": uf, "esfera": "estado",
            "is_df": is_df, "denom": denom, "phi_dest": phi_dest,
            "pop": pop_uf["ufs"].get(uf, {}).get("pop_media", 0),
        })
    return entities, state_denom_for_mean, df_iss


def main():
    ref = fold(load_json(HERE / "reforma-tributaria.json"))
    coef_uf = load_json(HERE / "coeficientes-uf.json")
    coef_muni = load_json(HERE / "coeficientes-municipios.json")["municipios"]
    phi = load_json(HERE / "phi-dest-pof-censo.json")
    rateio = load_json(HERE / "rateio-destino-municipios.json")["municipios"]
    pop_muni = load_json(HERE / "populacao-municipios-media-2019-2026.json")["municipios"]
    pop_uf = load_json(HERE / "populacao-uf-media-2019-2026.json")
    nacional = load_json(HERE / "ibs-projecao-nacional.json")
    portal = load_json(OUT / "repasses-portal-pr-latest.json")

    obs_rows = read_csv(HERE / "auditoria-dca-pr" / "observacoes-pr-latest.csv")
    diag_rows = read_csv(HERE / "auditoria-dca-pr" / "municipios-pr-latest.csv")
    tce_rows = read_csv(OUT / "validacao-iss-tce-pr-latest.csv")

    names = {}
    obs_by_code = defaultdict(list)
    iss = defaultdict(dict)
    cota_old = defaultdict(dict)
    for o in obs_rows:
        cod = o["codigo_ibge"]
        ano = int(o["ano"])
        names[cod] = o["municipio"]
        obs_by_code[cod].append(o)
        iss[cod][ano] = num(o.get("adjusted_iss"))
        cota_old[cod][ano] = num(o.get("adjusted_cota"))

    # Substituição ISS estritamente conservadora: somente comparações exatas
    # PIT x DCA com divergência >20%.
    replacements = []
    for r in tce_rows:
        cls = r.get("classificacao_iss_detalhado")
        if cls not in {"divergencia_forte_20a100pct", "divergencia_extrema_acima_100pct"}:
            continue
        cod = r["codigo_ibge"]
        ano = int(r["ano"])
        old = iss[cod].get(ano)
        new = num(r.get("tce_iss_detalhado"))
        if new is None:
            continue
        iss[cod][ano] = new
        replacements.append({
            "codigo_ibge": cod,
            "municipio": r["municipio"],
            "ano": ano,
            "iss_dca_usado_antes": old,
            "iss_tce": new,
            "diferenca_dca_vs_tce_pct": num(r.get("diferenca_dca_vs_tce_iss_pct")),
            "classificacao": cls,
            "url_tce": r.get("url_iss_detalhado"),
        })

    # Cota-parte via Portal PR, reescalada para o agregado estadual.
    portal_by_year = {
        ano: {
            norm_name(r["municipio_portal"]): float(r["icms_bruto_portal"])
            for r in portal["anos"][str(ano)]
        }
        for ano in ANOS_HIST
    }
    cota_target = {}
    recon_cota = defaultdict(dict)
    portal_sum = {}
    for ano in ANOS_HIST:
        s = str(ano)
        declared = ((ref.get("dca_transf_munis_por_uf", {}).get(s, {}) or {}).get("PR"))
        icms_pr = ((ref.get("dca_icms_por_uf", {}).get(s, {}) or {}).get("PR"))
        target = float(declared) if declared is not None else float(icms_pr) * 0.25
        cota_target[ano] = target
        vals = {cod: portal_by_year[ano].get(norm_name(nome)) for cod, nome in names.items()}
        vals = {cod: v for cod, v in vals.items() if v is not None}
        portal_sum[ano] = sum(vals.values())
        factor = target / portal_sum[ano]
        for cod in names:
            v = vals.get(cod)
            recon_cota[cod][ano] = v * factor if v is not None else None

    # Recalcula o agregado nacional histórico apenas na margem afetada pela
    # auditoria de ISS do Paraná. Mantém as demais UFs como no modelo.
    outras_by_year = ref.get("dca_icms_outras_deducoes_por_uf", {})
    old_pr_iss_by_year = ref.get("dca_iss_por_uf", {})
    total_nat = {}
    delta_pr_iss = {}
    for ano in ANOS_HIST:
        s = str(ano)
        icms_br = float(ref["dca_icms_br"][s])
        iss_br = float(ref["dca_iss_br"][s])
        fecop = float(ref.get("dca_fecop_br", {}).get(s, 0) or 0)
        outras = sum((outras_by_year.get(s, {}) or {}).values())
        old_pr_iss = float((old_pr_iss_by_year.get(s, {}) or {}).get("PR", 0) or 0)
        new_pr_iss = sum(v[ano] for v in iss.values() if v.get(ano) is not None)
        delta_pr_iss[ano] = new_pr_iss - old_pr_iss
        total_nat[ano] = icms_br - outras + iss_br + fecop - old_pr_iss + new_pr_iss

    total_2025 = total_nat[2025]
    deflator = {
        ano: 1.0 if ano == 2025 else total_2025 / total_nat[ano]
        for ano in ANOS_HIST
    }

    fi26, fr26, n_anos = cpt2026.fatores_uf(ref, "PR")     # 2026 estimado (cpt2026.py)
    diag = {r["codigo_ibge"]: r for r in diag_rows}
    audited = {}
    reconstruction_rows = []
    for cod, nome in names.items():
        annual = []
        unresolved = False
        for ano in ANOS_HIST:
            i = iss[cod].get(ano)
            cp = recon_cota[cod].get(ano)
            if i is None or cp is None:
                unresolved = True
                annual.append(None)
            else:
                annual.append((i + cp) * deflator[ano])

        est26 = 0.0 if (unresolved or n_anos == len(ANOS_HIST)) else iss[cod][2025] * fr26 + recon_cota[cod][2025] * fi26
        hist = None if unresolved else (sum(annual) + est26) / n_anos
        cpt = hist / total_2025 if hist is not None else None
        base = None
        if iss[cod].get(2025) is not None and recon_cota[cod].get(2025) is not None:
            base = iss[cod][2025] + recon_cota[cod][2025]

        old = diag.get(cod, {})
        old_cpt = num(old.get("coef_cpt_adjusted_pct"))
        old_base = num(old.get("r0_2025_adjusted"))
        audited[cod] = {
            "nome": nome, "base": base, "cpt": cpt,
            "old_cpt_pct": old_cpt, "old_base": old_base,
        }
        reconstruction_rows.append({
            "codigo_ibge": cod,
            "municipio": nome,
            "base_2025_pre_auditoria": old_base,
            "base_2025_auditada": base,
            "delta_base_pct": (base / old_base - 1) * 100 if base is not None and old_base not in (None, 0) else None,
            "cpt_pre_auditoria_pct": old_cpt,
            "cpt_auditado_pct": cpt * 100 if cpt is not None else None,
            "delta_cpt_pp": cpt * 100 - old_cpt if cpt is not None and old_cpt is not None else None,
            "unresolved": unresolved,
        })

    # Seguro-Receita: entidades estaduais permanecem canônicas; municípios
    # do PR recebem denom histórico auditado; demais municípios permanecem.
    entities, state_denom_for_mean, df_iss = build_state_entities(ref, coef_uf, phi, pop_uf)
    for cod, r in coef_muni.items():
        rd = rateio.get(cod)
        pm = pop_muni.get(cod)
        if rd is None or pm is None:
            continue
        if r["uf"] == "PR" and cod in audited and audited[cod]["cpt"] is not None:
            denom = audited[cod]["cpt"] * total_2025
        else:
            denom = r["receita_media_referencia"]
        entities.append({
            "id": f"MUN-{cod}", "nome": r["nome"], "uf": r["uf"],
            "esfera": "municipio", "is_df": False, "denom": denom,
            "phi_dest": rd["phi_dest_pct"] / 100,
            "pop": pm["pop_media"],
        })

    states = [e for e in entities if e["esfera"] == "estado"]
    munis = [e for e in entities if e["esfera"] == "municipio"]
    media_pc_estado = (
        sum(state_denom_for_mean[e["uf"]] for e in states)
        / sum(e["pop"] for e in states)
    )
    df_pop = next(e["pop"] for e in states if e["is_df"])
    media_pc_muni = (
        sum(e["denom"] for e in munis) + (df_iss or 0)
    ) / (
        sum(e["pop"] for e in munis) + df_pop
    )

    for e in entities:
        if e["is_df"]:
            teto = 3 * (media_pc_estado + media_pc_muni) * e["pop"]
        elif e["esfera"] == "estado":
            teto = 3 * media_pc_estado * e["pop"]
        else:
            teto = 3 * media_pc_muni * e["pop"]
        e["denom_capado"] = min(e["denom"], teto) if e["pop"] > 0 else e["denom"]

    nac_by_year = {int(r["ano"]): r for r in nacional["projecao"]}
    repasse_idx = {}
    seguro_meta = {}
    for ano in ANOS_PROJ:
        nac = nac_by_year[ano]
        for e in entities:
            e["numerador"] = nac["ibs_destino_liquido"] * e["phi_dest"]
        reps = water_fill(
            [(e["numerador"], e["denom_capado"]) for e in entities],
            nac["ibs_seguro_receita"],
        )
        for e, rep in zip(entities, reps):
            repasse_idx.setdefault(e["id"], {})[ano] = rep
        seguro_meta[ano] = {
            "pool": nac["ibs_seguro_receita"],
            "soma_repasses": sum(reps),
            "beneficiarios": sum(1 for x in reps if x > 1e-6),
        }

    # Projeções PR.
    projection_rows = []
    for cod, a in audited.items():
        if a["base"] is None or a["cpt"] is None or cod not in rateio:
            continue
        neutral = a["base"] / total_2025
        dest = rateio[cod]["phi_dest_pct"] / 100

        result = {}
        for ano in ANOS_PROJ:
            nac = nac_by_year[ano]
            ca = nac.get("ca", 0.0)
            ref_a = nac["icms_iss_residual"] + nac["ibs_bruto"]
            rep = repasse_idx.get(f"MUN-{cod}", {}).get(ano, 0.0)
            total = (
                nac["icms_iss_residual"] * neutral
                + (1 - ca) * nac["ibs_historico"] * a["cpt"]
                + nac["ibs_destino_liquido"] * dest
                + (1 - ca) * rep
            )
            contra = ref_a * neutral
            var = (total - contra) / contra if contra > 0 else None
            result[ano] = {"total": total, "contra": contra, "var": var, "repasse": rep}

        old_diag = diag.get(cod, {})
        old_var = num(old_diag.get("old_variacao_2033"))
        adjusted_var = num(old_diag.get("adjusted_variacao_2033"))
        v33 = result[2033]["var"]
        projection_rows.append({
            "codigo_ibge": cod,
            "municipio": a["nome"],
            "variacao_2033_original_pct": old_var * 100 if old_var is not None else None,
            "variacao_2033_apos_faltantes_pct": adjusted_var * 100 if adjusted_var is not None else None,
            "variacao_2033_auditada_pct": v33 * 100 if v33 is not None else None,
            "base_2025_auditada": a["base"],
            "cpt_auditado_pct": a["cpt"] * 100,
            "destino_pct": rateio[cod]["phi_dest_pct"],
            "seguro_2033": result[2033]["repasse"],
            "receita_2033": result[2033]["total"],
            "contrafactual_2033": result[2033]["contra"],
        })

    # Mesma regra de elegibilidade do diagnóstico anterior, mas agora com a
    # cota validada externamente e as cinco correções confirmadas de ISS.
    qualified = []
    for r in projection_rows:
        cod = r["codigo_ibge"]
        obs_c = obs_by_code.get(cod, [])
        iss_observed_years = sum(1 for o in obs_c if o.get("new_iss") not in (None, ""))
        o25 = next((o for o in obs_c if int(o["ano"]) == 2025), None)
        direct_iss_2025 = bool(o25 and o25.get("new_iss") not in (None, ""))
        pop = pop_muni.get(cod, {}).get("pop_media", 0) or 0
        if iss_observed_years >= 5 and direct_iss_2025 and pop >= 10000:
            qualified.append(r)

    qvars = sorted(r["variacao_2033_auditada_pct"] for r in qualified)
    mid = len(qvars) // 2
    mediana_q = (
        qvars[mid] if len(qvars) % 2
        else (qvars[mid - 1] + qvars[mid]) / 2
    ) if qvars else None

    qloss = sorted(qualified, key=lambda r: r["variacao_2033_auditada_pct"])[:20]
    qgain = sorted(qualified, key=lambda r: r["variacao_2033_auditada_pct"], reverse=True)[:20]
    outliers = sorted(
        projection_rows,
        key=lambda r: abs(r["variacao_2033_auditada_pct"] or 0),
        reverse=True,
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "metodo": (
            "Cota-parte ICMS via Portal PR reconciliada ao total estadual DCA; "
            "ISS DCA substituído pelo PIT/TCE-PR somente nas observações "
            "sinalizadas em que a comparação direta mostrou divergência >20%; "
            "CPT, base 2025, Seguro-Receita e projeções recalculados."
        ),
        "n_substituicoes_iss_tce": len(replacements),
        "substituicoes_iss_tce": replacements,
        "delta_iss_pr_vs_dca_por_ano": delta_pr_iss,
        "total_nacional_2025_auditado": total_2025,
        "seguro_receita": seguro_meta,
        "amostra_artigo": {
            "criterio": (
                "ISS observado em >=5 anos; ISS 2025 observado diretamente; "
                "população média >=10 mil; cota-parte auditada via Portal PR"
            ),
            "n_municipios": len(qualified),
            "n_negativos": sum(1 for r in qualified if r["variacao_2033_auditada_pct"] < 0),
            "n_positivos": sum(1 for r in qualified if r["variacao_2033_auditada_pct"] > 0),
            "mediana_variacao_2033_pct": mediana_q,
            "maiores_perdas": qloss[:10],
            "maiores_ganhos": qgain[:10],
        },
        "n_outliers_abs_30pct_2033_todos_399": sum(
            1 for r in projection_rows
            if abs(r["variacao_2033_auditada_pct"] or 0) >= 30
        ),
        "top_20_outliers_todos_399": outliers[:20],
        "nota": (
            "Cenário de sensibilidade, não substituição canônica. Observações "
            "TCE com diferença de 5%-20% permanecem sinalizadas sem substituição."
        ),
    }

    date = datetime.now(timezone.utc).date().isoformat()
    reconstruction_rows.sort(key=lambda r: abs(r["delta_base_pct"] or 0), reverse=True)
    projection_rows.sort(key=lambda r: abs(r["variacao_2033_auditada_pct"] or 0), reverse=True)
    write_csv(OUT / f"reconstrucao-pr-auditoria-integral-{date}.csv", reconstruction_rows)
    write_csv(OUT / "reconstrucao-pr-auditoria-integral-latest.csv", reconstruction_rows)
    write_csv(OUT / f"projecao-pr-auditoria-integral-{date}.csv", projection_rows)
    write_csv(OUT / "projecao-pr-auditoria-integral-latest.csv", projection_rows)
    dump_json(OUT / f"resumo-pr-auditoria-integral-{date}.json", summary)
    dump_json(OUT / "resumo-pr-auditoria-integral-latest.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
