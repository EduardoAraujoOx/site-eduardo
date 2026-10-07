#!/usr/bin/env python3
"""
Projeção diagnóstica dos municípios do Paraná após auditoria da cota-parte.

Usa:
- base 2025 e CPT municipais reconstruídos com o Portal de Transferências do PR;
- phi_dest municipal do modelo vigente;
- projeção nacional vigente;
- recalcula o Seguro-Receita nacionalmente, substituindo apenas as receitas
  médias de referência dos municípios do Paraná pela série auditada.

Objetivo: medir a consequência prática da qualidade dos dados sobre as
projeções municipais sem alterar a base canônica.

NÃO sobrescreve coeficientes, Seguro-Receita ou resultados oficiais do site.
"""
from __future__ import annotations

import csv
import json
import seguro_lei
from pathlib import Path
from datetime import datetime, timezone
import rateio_consumo_compras as rcc

HERE = Path(__file__).resolve().parent
OUT = HERE / "auditoria-pr-validacao"
ANOS = [2029, 2030, 2031, 2032, 2033]
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


def water_fill(entidades, pool):
    if pool <= 0 or not entidades:
        return [0.0] * len(entidades)

    def total_pago(level):
        return sum(max(0.0, level * d - n) for n, d in entidades)

    valid = [(n, d) for n, d in entidades if d > 0]
    if not valid:
        return [0.0] * len(entidades)
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
    dca_cota = ref.get("dca_transf_munis_por_uf", {}).get("2025", {})
    dca_outras = ref.get("dca_icms_outras_deducoes_por_uf", {}).get("2025", {})
    old_total = coef_uf["total_br_2025"]

    frac_estado = phi["frac_estado_pct"] / 100
    entities = []
    state_denom_for_mean = {}
    df_iss = None

    for uf in UFS:
        c = coef_uf["por_uf"][uf]
        is_df = bool(c.get("is_df"))
        icms = dca_icms.get(uf, 0) or 0
        iss = dca_iss.get(uf, 0) or 0
        fecop = dca_fecop.get(uf, 0) or 0
        outras = dca_outras.get(uf, 0) or 0
        phi_dest, _ = rcc.esferas_uf(phi["por_uf"].get(uf, {}), is_df, frac_estado, 0)

        coef_estado = (c.get("coeficiente_estado_pct") or 0) / 100
        coef_total = (c.get("coeficiente_total_pct") or 0) / 100
        denom = (coef_total if is_df else coef_estado) * old_total
        denom_estado_mean = coef_estado * old_total
        state_denom_for_mean[uf] = denom_estado_mean
        if is_df:
            df_iss = iss

        entities.append({
            "id": f"UF-{uf}",
            "nome": uf,
            "uf": uf,
            "esfera": "estado",
            "is_df": is_df,
            "denom": denom,
            "phi_dest": phi_dest,
            "pop": pop_uf["ufs"].get(uf, {}).get("pop_media", 0),
        })
    return entities, state_denom_for_mean, df_iss


def main():
    ref = load_json(HERE / "reforma-tributaria.json")
    coef_uf = load_json(HERE / "coeficientes-uf.json")
    coef_muni = load_json(HERE / "coeficientes-municipios.json")["municipios"]
    phi = load_json(HERE / "phi-dest-pof-censo.json")
    rateio = load_json(HERE / "rateio-destino-municipios.json")["municipios"]
    pop_muni = load_json(HERE / "populacao-municipios-media-2019-2026.json")["municipios"]
    pop_uf = load_json(HERE / "populacao-uf-media-2019-2026.json")
    nacional = load_json(HERE / "ibs-projecao-nacional.json")
    recon_rows = read_csv(OUT / "reconstrucao-cpt-portal-pr-latest.csv")
    adjusted_rows = read_csv(HERE / "auditoria-dca-pr" / "municipios-pr-latest.csv")
    obs_rows = read_csv(HERE / "auditoria-dca-pr" / "observacoes-pr-latest.csv")

    recon = {r["codigo_ibge"]: r for r in recon_rows}
    adjusted = {r["codigo_ibge"]: r for r in adjusted_rows}
    obs_by_code = {}
    for o in obs_rows:
        obs_by_code.setdefault(o["codigo_ibge"], []).append(o)
    nac_by_year = {int(r["ano"]): r for r in nacional["projecao"]}

    # Total usado para transformar o CPT reconstruído (%) em receita média (R$).
    # Ele está documentado no resumo da reconstrução.
    recon_summary = load_json(OUT / "resumo-reconstrucao-cpt-pr-latest.json")
    total_adjusted_2025 = recon_summary["total_nacional_2025_ajustado"]

    # Estados
    entities, state_denom_for_mean, df_iss = build_state_entities(ref, coef_uf, phi, pop_uf)

    # Municípios do Brasil: denom original para fora do PR; denom reconstruído no PR.
    for cod, r in coef_muni.items():
        rd = rateio.get(cod)
        pm = pop_muni.get(cod)
        if rd is None or pm is None:
            continue

        if r["uf"] == "PR" and cod in recon:
            rr = recon[cod]
            cpt_pct = num(rr.get("cpt_reconstruido_portal_pct"))
            denom = cpt_pct / 100 * total_adjusted_2025 if cpt_pct is not None else r["receita_media_referencia"]
        else:
            denom = r["receita_media_referencia"]

        entities.append({
            "id": f"MUN-{cod}",
            "nome": r["nome"],
            "uf": r["uf"],
            "esfera": "municipio",
            "is_df": False,
            "denom": denom,
            "phi_dest": rd["phi_dest_pct"] / 100,
            "pop": pm["pop_media"],
        })

    # Teto do Seguro-Receita por esfera.
    states = [e for e in entities if e["esfera"] == "estado"]
    munis = [e for e in entities if e["esfera"] == "municipio"]

    soma_denom_estado = sum(state_denom_for_mean[e["uf"]] for e in states)
    soma_pop_estado = sum(e["pop"] for e in states)
    media_pc_estado = soma_denom_estado / soma_pop_estado

    df_pop = next(e["pop"] for e in states if e["is_df"])
    soma_denom_muni = sum(e["denom"] for e in munis) + (df_iss or 0)
    soma_pop_muni = sum(e["pop"] for e in munis) + df_pop
    media_pc_muni = soma_denom_muni / soma_pop_muni

    for e in entities:
        if e["is_df"]:
            teto = 3 * (media_pc_estado + media_pc_muni) * e["pop"]
        elif e["esfera"] == "estado":
            teto = 3 * media_pc_estado * e["pop"]
        else:
            teto = 3 * media_pc_muni * e["pop"]
        e["denom_capado"] = min(e["denom"], teto) if e["pop"] > 0 else e["denom"]

    # Seguro-Receita auditado, nacionalmente recalculado.
    repasse_idx = {}
    seguro_meta = {}
    for ano in ANOS:
        nac = nac_by_year[ano]
        reps, nums = seguro_lei.seguro_ano([e["denom_capado"] for e in entities], [e["phi_dest"] for e in entities],
                                           nac_by_year, ano, water_fill)
        for e, n_ in zip(entities, nums):
            e["numerador"] = n_
        level = None
        beneficiaries = 0
        for e, rep in zip(entities, reps):
            repasse_idx.setdefault(e["id"], {})[ano] = rep
            if rep > 1e-6:
                beneficiaries += 1
                level = (e["numerador"] + rep) / e["denom_capado"] if e["denom_capado"] > 0 else level
        seguro_meta[ano] = {
            "pool": nac["ibs_seguro_receita"],
            "soma_repasses": sum(reps),
            "beneficiarios": beneficiaries,
            "nivel_aprox": level,
        }

    # Projeção PR com base e CPT reconstruídos.
    output_rows = []
    for cod, rr in recon.items():
        if cod not in rateio:
            continue
        nome = rr["municipio"]
        r0 = num(rr.get("base_2025_reconstruida"))
        cpt_pct = num(rr.get("cpt_reconstruido_portal_pct"))
        if r0 is None or cpt_pct is None:
            continue
        cpt = cpt_pct / 100
        dest = rateio[cod]["phi_dest_pct"] / 100
        neutral = r0 / total_adjusted_2025

        old_adj = adjusted.get(cod, {})
        old_original_var = num(old_adj.get("old_variacao_2033"))
        missing_adjusted_var = num(old_adj.get("adjusted_variacao_2033"))

        res = {}
        for ano in ANOS:
            nac = nac_by_year[ano]
            ca = nac.get("ca", 0.0)
            referencia = nac["icms_iss_residual"] + nac["ibs_bruto"]
            repasse = repasse_idx.get(f"MUN-{cod}", {}).get(ano, 0.0)

            total = (
                nac["icms_iss_residual"] * neutral
                + (1 - ca) * nac["ibs_historico"] * cpt
                + nac["ibs_destino_liquido"] * dest
                + (1 - ca) * repasse
            )
            contra = referencia * neutral
            var = (total - contra) / contra if contra > 0 else None
            res[ano] = (total, contra, var, repasse)

        v33 = res[2033][2]
        output_rows.append({
            "codigo_ibge": cod,
            "municipio": nome,
            "variacao_2033_base_original_pct": old_original_var * 100 if old_original_var is not None else None,
            "variacao_2033_apos_faltantes_pct": missing_adjusted_var * 100 if missing_adjusted_var is not None else None,
            "variacao_2033_portal_reconciliado_pct": v33 * 100 if v33 is not None else None,
            "delta_portal_vs_apos_faltantes_pp": (
                (v33 - missing_adjusted_var) * 100
                if v33 is not None and missing_adjusted_var is not None else None
            ),
            "base_2025_reconstruida": r0,
            "cpt_reconstruido_pct": cpt_pct,
            "destino_pct": rateio[cod]["phi_dest_pct"],
            "seguro_2033": res[2033][3],
            "receita_2033": res[2033][0],
            "contrafactual_2033": res[2033][1],
        })

    output_rows.sort(
        key=lambda r: abs(r["delta_portal_vs_apos_faltantes_pp"] or 0),
        reverse=True
    )

    outliers = sorted(
        [r for r in output_rows if r["variacao_2033_portal_reconciliado_pct"] is not None],
        key=lambda r: abs(r["variacao_2033_portal_reconciliado_pct"]),
        reverse=True,
    )
    large_revision = [
        r for r in output_rows
        if r["delta_portal_vs_apos_faltantes_pp"] is not None
        and abs(r["delta_portal_vs_apos_faltantes_pp"]) >= 10
    ]

    # Subamostra de maior qualidade para substituir, quando validada, o
    # ranking do artigo. Como a cota-parte agora vem do Portal PR, a cobertura
    # relevante do DCA é a do ISS: >=5 anos observados, ISS de 2025 observado
    # diretamente e população média >=10 mil habitantes.
    qualified = []
    for r in output_rows:
        cod = r["codigo_ibge"]
        obs_c = obs_by_code.get(cod, [])
        iss_observed_years = sum(1 for o in obs_c if o.get("new_iss") not in (None, ""))
        o25 = next((o for o in obs_c if o.get("ano") == "2025"), None)
        direct_iss_2025 = bool(o25 and o25.get("new_iss") not in (None, ""))
        pop = pop_muni.get(cod, {}).get("pop_media", 0) or 0
        if iss_observed_years >= 5 and direct_iss_2025 and pop >= 10000:
            qualified.append(r)

    qvars = sorted(r["variacao_2033_portal_reconciliado_pct"] for r in qualified
                   if r["variacao_2033_portal_reconciliado_pct"] is not None)
    if qvars:
        mid = len(qvars) // 2
        mediana_q = qvars[mid] if len(qvars) % 2 else (qvars[mid-1] + qvars[mid]) / 2
    else:
        mediana_q = None
    qloss = sorted(qualified, key=lambda r: r["variacao_2033_portal_reconciliado_pct"])[:10]
    qgain = sorted(qualified, key=lambda r: r["variacao_2033_portal_reconciliado_pct"], reverse=True)[:10]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "metodo": (
            "Cenário diagnóstico: substitui no PR a cota-parte municipal declarada no DCA "
            "pela participação observada no Portal de Transferências do Estado, reconciliada "
            "ao total estadual do DCA. Mantém o ISS ajustado da auditoria, o destino e a "
            "projeção nacional vigentes e recalcula nacionalmente o Seguro-Receita."
        ),
        "n_municipios_pr": len(output_rows),
        "seguro_receita": seguro_meta,
        "n_revisoes_10pp_portal_vs_faltantes": len(large_revision),
        "n_outliers_abs_30pct_2033": sum(
            1 for r in output_rows
            if r["variacao_2033_portal_reconciliado_pct"] is not None
            and abs(r["variacao_2033_portal_reconciliado_pct"]) >= 30
        ),
        "amostra_artigo": {
            "criterio": "ISS observado em >=5 anos; ISS 2025 observado diretamente; população média >=10 mil; cota-parte via Portal PR",
            "n_municipios": len(qualified),
            "n_negativos": sum(1 for r in qualified if r["variacao_2033_portal_reconciliado_pct"] < 0),
            "n_positivos": sum(1 for r in qualified if r["variacao_2033_portal_reconciliado_pct"] > 0),
            "mediana_variacao_2033_pct": mediana_q,
            "maiores_perdas": qloss,
            "maiores_ganhos": qgain,
        },
        "top_20_revisoes_portal": output_rows[:20],
        "top_20_outliers_finais": outliers[:20],
        "nota": (
            "Não é ainda a base canônica. O exercício isola a consequência de reconciliar "
            "a cota-parte do Paraná com a fonte estadual e recalcular o Seguro-Receita. "
            "Anomalias de ISS sinalizadas permanecem sem correção até validação externa."
        ),
    }

    date = datetime.now(timezone.utc).date().isoformat()
    write_csv(OUT / f"projecao-pr-auditada-{date}.csv", output_rows)
    write_csv(OUT / "projecao-pr-auditada-latest.csv", output_rows)
    dump_json(OUT / f"resumo-projecao-pr-auditada-{date}.json", summary)
    dump_json(OUT / "resumo-projecao-pr-auditada-latest.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
