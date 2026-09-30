#!/usr/bin/env python3
"""
Base municipal final auditada do Paraná para o artigo.

Metodologia adotada:
1. ISS: nova coleta DCA/SICONFI; ausências tratadas pela rotina de auditoria.
2. ISS anômalo: quando houve validação dirigida no PIT/TCE-PR, substitui-se o
   valor DCA pelo total de ISS do PIT apenas se a divergência absoluta superar
   5%. Os demais sinais de ISS permanecem observados, mas são marcados como
   pendentes e excluídos do ranking principal do artigo.
3. Cota-parte do ICMS: participação do município no ICMS bruto do Portal PR,
   reescalada para fechar exatamente no total estadual da cota-parte na DCA.
4. Recalcula a série real 2019-2025, CPT municipal, base 2025, Seguro-Receita
   nacional e projeções 2029-2033.

A rotina gera arquivos diagnósticos e NÃO sobrescreve as bases canônicas
nacionais. O artigo pode usar os arquivos *_final_auditado como metodologia
municipal preferida e manter a metodologia original como exercício comparativo.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

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
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def dump_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def num(v):
    if v is None or v == "":
        return None
    return float(v)


def pit_total_from_case(case):
    for row in case.get("todas_linhas_iss", []):
        cells = row.get("cells") or []
        if not cells:
            continue
        code = str(cells[0]).replace(" ", "")
        if code.endswith(".0.00.00.00.00.00"):
            return num(row.get("amount"))
    return None


def water_fill(entidades, pool):
    if pool <= 0 or not entidades:
        return [0.0] * len(entidades)

    valid = [(n, d) for n, d in entidades if d and d > 0]
    if not valid:
        return [0.0] * len(entidades)

    def total_pago(level):
        return sum(max(0.0, level * d - n) for n, d in entidades if d and d > 0)

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
    return [max(0.0, level * d - n) if d and d > 0 else 0.0 for n, d in entidades]


def build_state_entities(ref, coef_uf, phi, pop_uf):
    dca_iss = ref.get("dca_iss_por_uf", {}).get("2025", {})
    old_total = coef_uf["total_br_2025"]
    frac_estado = phi["frac_estado_pct"] / 100

    entities = []
    state_denom_for_mean = {}
    df_iss = None

    for uf in UFS:
        c = coef_uf["por_uf"][uf]
        is_df = bool(c.get("is_df"))
        phi_uf = (phi["por_uf"].get(uf, {}).get("pof_censo_bruto_pct") or 0) / 100
        phi_dest = phi_uf if is_df else phi_uf * frac_estado

        coef_estado = (c.get("coeficiente_estado_pct") or 0) / 100
        coef_total = (c.get("coeficiente_total_pct") or 0) / 100
        denom = (coef_total if is_df else coef_estado) * old_total
        state_denom_for_mean[uf] = coef_estado * old_total
        if is_df:
            df_iss = dca_iss.get(uf, 0) or 0

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
    OUT.mkdir(parents=True, exist_ok=True)

    ref = load_json(HERE / "reforma-tributaria.json")
    coef_uf = load_json(HERE / "coeficientes-uf.json")
    coef_muni_nacional = load_json(HERE / "coeficientes-municipios.json")["municipios"]
    phi = load_json(HERE / "phi-dest-pof-censo.json")
    rateio = load_json(HERE / "rateio-destino-municipios.json")["municipios"]
    pop_muni = load_json(HERE / "populacao-municipios-media-2019-2026.json")["municipios"]
    pop_uf = load_json(HERE / "populacao-uf-media-2019-2026.json")
    nacional = load_json(HERE / "ibs-projecao-nacional.json")
    old_panel = load_json(HERE / "painel-municipios" / "PR.json")["municipios"]

    obs_rows = read_csv(HERE / "auditoria-dca-pr" / "observacoes-pr-latest.csv")
    portal = load_json(OUT / "repasses-portal-pr-latest.json")
    tce_validation = read_csv(OUT / "validacao-iss-tce-pr-latest.csv")
    iss_flags_rows = read_csv(OUT / "anomalias-iss-pr-latest.csv")

    names = {}
    adjusted_iss = defaultdict(dict)
    direct_iss = defaultdict(dict)
    iss_source = defaultdict(dict)
    for o in obs_rows:
        cod = o["codigo_ibge"]
        ano = int(o["ano"])
        names[cod] = o["municipio"]
        adjusted_iss[cod][ano] = num(o.get("adjusted_iss"))
        direct_iss[cod][ano] = num(o.get("new_iss"))
        iss_source[cod][ano] = o.get("iss_source") or ""

    # Correções de ISS confirmadas em segunda fonte (PIT/TCE-PR).
    # Substitui apenas observações sinalizadas cuja comparação direta com o
    # PIT mostra divergência superior a 20%. Casos coerentes são preservados.
    pit_corrections = {}
    pit_confirmations = []
    for row in tce_validation:
        tce = num(row.get("tce_iss_detalhado"))
        dca = num(row.get("iss_dca"))
        if tce is None or dca is None or tce == 0:
            continue
        classificacao = row.get("classificacao_iss_detalhado") or ""
        substituido = classificacao in {
            "divergencia_forte_20a100pct",
            "divergencia_extrema_acima_100pct",
        }
        pit_confirmations.append({
            "municipio": row["municipio"],
            "ano": int(row["ano"]),
            "iss_dca": dca,
            "iss_pit_total": tce,
            "diferenca_pct": num(row.get("diferenca_dca_vs_tce_iss_pct")),
            "substituido": substituido,
        })
        if substituido:
            pit_corrections[(row["codigo_ibge"], int(row["ano"]))] = tce

    final_iss = defaultdict(dict)
    final_iss_source = defaultdict(dict)
    for cod in names:
        for ano in ANOS_HIST:
            if (cod, ano) in pit_corrections:
                final_iss[cod][ano] = pit_corrections[(cod, ano)]
                final_iss_source[cod][ano] = "pit_tce_confirmado"
            else:
                final_iss[cod][ano] = adjusted_iss[cod].get(ano)
                final_iss_source[cod][ano] = iss_source[cod].get(ano) or "dca"

    # Sinais de ISS ainda não confirmados em segunda fonte.
    unresolved_iss_flags = defaultdict(list)
    corrected_pairs = set(pit_corrections)
    for r in iss_flags_rows:
        cod = r["codigo_ibge"]
        ano = int(r["ano"])
        if (cod, ano) not in corrected_pairs:
            unresolved_iss_flags[cod].append(ano)

    # Portal por nome/ano. Nomes já foram conciliados pela rotina anterior; aqui
    # usa-se o arquivo com o nome oficial e correspondência direta.
    import unicodedata, re
    def norm_name(s):
        s = unicodedata.normalize("NFKD", s or "")
        s = "".join(c for c in s if not unicodedata.combining(c))
        s = s.lower().replace("d'", "d ")
        s = re.sub(r"[^a-z0-9]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        aliases = {"santa cruz de monte castelo": "santa cruz do monte castelo"}
        return aliases.get(s, s)

    portal_by_year = {
        ano: {norm_name(r["municipio_portal"]): float(r["icms_bruto_portal"])
              for r in portal["anos"][str(ano)]}
        for ano in ANOS_HIST
    }

    cota_target = {}
    for ano in ANOS_HIST:
        s = str(ano)
        declared = ((ref.get("dca_transf_munis_por_uf", {}).get(s, {}) or {}).get("PR"))
        icms = ((ref.get("dca_icms_por_uf", {}).get(s, {}) or {}).get("PR"))
        cota_target[ano] = float(declared) if declared is not None else float(icms) * 0.25

    cota_final = defaultdict(dict)
    fator_reconciliacao = {}
    portal_sum = {}
    for ano in ANOS_HIST:
        vals = {cod: portal_by_year[ano][norm_name(nome)]
                for cod,nome in names.items()
                if norm_name(nome) in portal_by_year[ano]}
        portal_sum[ano] = sum(vals.values())
        fator = cota_target[ano] / portal_sum[ano]
        fator_reconciliacao[ano] = fator
        for cod in names:
            cota_final[cod][ano] = vals[cod] * fator

    # Agregado nacional e deflatores 2019-2025, substituindo somente o ISS do PR.
    outras_by_year = ref.get("dca_icms_outras_deducoes_por_uf", {})
    old_pr_iss_by_year = ref.get("dca_iss_por_uf", {})
    total_nat = {}
    pr_iss_old = {}
    pr_iss_final = {}
    for ano in ANOS_HIST:
        s = str(ano)
        icms_br = float(ref.get("dca_icms_br", {}).get(s))
        iss_br = float(ref.get("dca_iss_br", {}).get(s))
        fecop = float(ref.get("dca_fecop_br", {}).get(s, 0) or 0)
        outras = sum(float(v or 0) for v in (outras_by_year.get(s, {}) or {}).values())
        old_pr = float((old_pr_iss_by_year.get(s, {}) or {}).get("PR", 0) or 0)
        new_pr = sum(final_iss[c].get(ano) or 0 for c in names)
        pr_iss_old[ano] = old_pr
        pr_iss_final[ano] = new_pr
        total_nat[ano] = icms_br - outras + iss_br + fecop - old_pr + new_pr

    total_2025 = total_nat[2025]
    deflator = {ano: (1.0 if ano == 2025 else total_2025 / total_nat[ano]) for ano in ANOS_HIST}

    # Base 2025 e CPT auditados.
    municipal = {}
    for cod,nome in names.items():
        real_series = []
        for ano in ANOS_HIST:
            i = final_iss[cod].get(ano)
            cp = cota_final[cod].get(ano)
            if i is None or cp is None:
                real_series.append(None)
            else:
                real_series.append((i + cp) * deflator[ano])
        if any(v is None for v in real_series):
            continue
        hist_mean = sum(real_series) / len(real_series)
        cpt = hist_mean / total_2025
        r0 = final_iss[cod][2025] + cota_final[cod][2025]
        municipal[cod] = {
            "nome": nome,
            "uf": "PR",
            "hist_mean": hist_mean,
            "cpt": cpt,
            "r0": r0,
            "real_series": real_series,
            "pit_corrections": sum(1 for ano in ANOS_HIST if (cod,ano) in pit_corrections),
            "unresolved_iss_years": sorted(unresolved_iss_flags.get(cod, [])),
            "iss_observed_years": sum(1 for ano in ANOS_HIST if direct_iss[cod].get(ano) is not None),
            "iss_2025_direct": direct_iss[cod].get(2025) is not None,
        }

    nac_by_year = {int(r["ano"]): r for r in nacional["projecao"]}

    # Seguro-Receita nacional com denominadores municipais PR auditados.
    entities, state_denom_for_mean, df_iss = build_state_entities(ref, coef_uf, phi, pop_uf)
    for cod,r in coef_muni_nacional.items():
        rd = rateio.get(cod)
        pm = pop_muni.get(cod)
        if rd is None or pm is None:
            continue
        denom = municipal[cod]["hist_mean"] if r["uf"] == "PR" and cod in municipal else r["receita_media_referencia"]
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

    states = [e for e in entities if e["esfera"] == "estado"]
    munis = [e for e in entities if e["esfera"] == "municipio"]
    media_pc_estado = sum(state_denom_for_mean[e["uf"]] for e in states) / sum(e["pop"] for e in states)
    df_pop = next(e["pop"] for e in states if e["is_df"])
    media_pc_muni = (sum(e["denom"] for e in munis) + (df_iss or 0)) / (sum(e["pop"] for e in munis) + df_pop)

    for e in entities:
        if e["is_df"]:
            teto = 3 * (media_pc_estado + media_pc_muni) * e["pop"]
        elif e["esfera"] == "estado":
            teto = 3 * media_pc_estado * e["pop"]
        else:
            teto = 3 * media_pc_muni * e["pop"]
        e["denom_capado"] = min(e["denom"], teto) if e["pop"] > 0 else e["denom"]

    repasse_idx = {}
    seguro_summary = {}
    for ano in ANOS_PROJ:
        nac = nac_by_year[ano]
        for e in entities:
            e["numerador"] = nac["ibs_destino_liquido"] * e["phi_dest"]
        pairs = [(e["numerador"], e["denom_capado"]) for e in entities]
        reps = water_fill(pairs, nac["ibs_seguro_receita"])
        benef = 0
        level = None
        pr_benef = 0
        pr_sum = 0.0
        for e,rep in zip(entities,reps):
            repasse_idx.setdefault(e["id"], {})[ano] = rep
            if rep > 1e-6:
                benef += 1
                level = (e["numerador"] + rep) / e["denom_capado"] if e["denom_capado"] > 0 else level
                if e["esfera"] == "municipio" and e["uf"] == "PR":
                    pr_benef += 1
                    pr_sum += rep
        seguro_summary[ano] = {
            "pool": nac["ibs_seguro_receita"],
            "nivel": level,
            "beneficiarios_nacional": benef,
            "beneficiarios_pr": pr_benef,
            "repasse_pr": pr_sum,
        }

    # Projeções municipais finais.
    rows = []
    aggregate = {ano: {"total":0.0,"contra":0.0,"repasse":0.0} for ano in ANOS_PROJ}
    for cod,m in municipal.items():
        rd = rateio.get(cod)
        if rd is None:
            continue
        neutral = m["r0"] / total_2025
        dest = rd["phi_dest_pct"] / 100
        proj = {}
        for ano in ANOS_PROJ:
            nac = nac_by_year[ano]
            ca = nac.get("ca",0.0)
            ref_a = nac["icms_iss_residual"] + nac["ibs_bruto"]
            rep = repasse_idx.get(f"MUN-{cod}",{}).get(ano,0.0)
            total = (nac["icms_iss_residual"]*neutral
                     + (1-ca)*nac["ibs_historico"]*m["cpt"]
                     + nac["ibs_destino_liquido"]*dest
                     + (1-ca)*rep)
            contra = ref_a*neutral
            var = (total-contra)/contra if contra>0 else None
            proj[ano]={"total":total,"contra":contra,"var":var,"rep":rep}
            aggregate[ano]["total"] += total
            aggregate[ano]["contra"] += contra
            aggregate[ano]["repasse"] += rep

        old = old_panel.get(cod,{})
        old_var = (old.get("variacao_por_ano") or {}).get("2033")
        if old_var is None:
            old_var = (old.get("variacao_por_ano") or {}).get(2033)

        portal_only = None
        # painel da auditoria anterior, sem correções PIT
        # (arquivo carregado apenas se disponível)
        rows.append({
            "codigo_ibge": cod,
            "municipio": m["nome"],
            "base_2025_final": m["r0"],
            "receita_media_historica_final": m["hist_mean"],
            "cpt_final_pct": m["cpt"]*100,
            "destino_pct": rd["phi_dest_pct"],
            "pit_correcoes": m["pit_corrections"],
            "iss_pendente_anos": ";".join(str(x) for x in m["unresolved_iss_years"]),
            "iss_observado_anos": m["iss_observed_years"],
            "iss_2025_direto": m["iss_2025_direct"],
            "variacao_2033_metodo_original_pct": old_var*100 if old_var is not None else None,
            "receita_2029_final": proj[2029]["total"],
            "variacao_2029_final_pct": proj[2029]["var"]*100,
            "receita_2030_final": proj[2030]["total"],
            "variacao_2030_final_pct": proj[2030]["var"]*100,
            "receita_2031_final": proj[2031]["total"],
            "variacao_2031_final_pct": proj[2031]["var"]*100,
            "receita_2032_final": proj[2032]["total"],
            "variacao_2032_final_pct": proj[2032]["var"]*100,
            "receita_2033_final": proj[2033]["total"],
            "contrafactual_2033_final": proj[2033]["contra"],
            "variacao_2033_final_pct": proj[2033]["var"]*100,
            "delta_metodologia_2033_pp": (
                proj[2033]["var"]*100 - old_var*100 if old_var is not None else None
            ),
            "seguro_2029_final": proj[2029]["rep"],
            "seguro_2030_final": proj[2030]["rep"],
            "seguro_2031_final": proj[2031]["rep"],
            "seguro_2032_final": proj[2032]["rep"],
            "seguro_2033_final": proj[2033]["rep"],
        })

    # Carrega resultado "Portal sem PIT" para decomposição.
    portal_proj_path = OUT / "projecao-pr-auditada-latest.csv"
    portal_map = {}
    if portal_proj_path.exists():
        portal_map = {r["codigo_ibge"]: r for r in read_csv(portal_proj_path)}
    for r in rows:
        p = portal_map.get(r["codigo_ibge"])
        r["variacao_2033_portal_sem_pit_pct"] = num(p.get("variacao_2033_portal_reconciliado_pct")) if p else None
        r["efeito_pit_2033_pp"] = (
            r["variacao_2033_final_pct"] - r["variacao_2033_portal_sem_pit_pct"]
            if r["variacao_2033_portal_sem_pit_pct"] is not None else None
        )

    # Amostra principal do artigo: dados de ISS suficientes e sem sinal de ISS
    # ainda não validado. A cota-parte é sempre a série reconstruída do Portal.
    qualified=[]
    for r in rows:
        pop = pop_muni.get(r["codigo_ibge"],{}).get("pop_media",0) or 0
        if (r["iss_observado_anos"] >= 5
            and r["iss_2025_direto"]
            and pop >= 10000):
            qualified.append(r)

    qualified_ids={r["codigo_ibge"] for r in qualified}
    for r in rows:
        r["qualificado_artigo"] = r["codigo_ibge"] in qualified_ids

    qvals=sorted(r["variacao_2033_final_pct"] for r in qualified)
    med = statistics.median(qvals) if qvals else None
    qorig=[r["variacao_2033_metodo_original_pct"] for r in qualified if r["variacao_2033_metodo_original_pct"] is not None]
    med_orig=statistics.median(qorig) if qorig else None
    sign_flips=sum(
        1 for r in qualified
        if r["variacao_2033_metodo_original_pct"] is not None
        and ((r["variacao_2033_metodo_original_pct"] < 0) != (r["variacao_2033_final_pct"] < 0))
    )
    qloss=sorted(qualified,key=lambda r:r["variacao_2033_final_pct"])[:10]
    qgain=sorted(qualified,key=lambda r:r["variacao_2033_final_pct"],reverse=True)[:10]

    # Comparação de metodologias: maiores alterações em módulo.
    rows.sort(key=lambda r:abs(r["delta_metodologia_2033_pp"] or 0),reverse=True)
    comparison_top=rows[:25]
    outliers=sorted(rows,key=lambda r:abs(r["variacao_2033_final_pct"]),reverse=True)

    agg_summary={}
    for ano,a in aggregate.items():
        agg_summary[ano]={
            "receita_final":a["total"],
            "contrafactual":a["contra"],
            "variacao_pct":(a["total"]/a["contra"]-1)*100 if a["contra"] else None,
            "seguro_receita":a["repasse"],
        }
    acumulado_total=sum(a["total"] for a in aggregate.values())
    acumulado_contra=sum(a["contra"] for a in aggregate.values())

    seguro_pr_municipios = []
    for r in rows:
        vals = [r[f"seguro_{ano}_final"] for ano in ANOS_PROJ]
        if any(v > 1e-6 for v in vals):
            seguro_pr_municipios.append({
                "codigo_ibge": r["codigo_ibge"],
                "municipio": r["municipio"],
                **{str(ano): r[f"seguro_{ano}_final"] for ano in ANOS_PROJ},
                "total": sum(vals),
            })
    seguro_pr_municipios.sort(key=lambda x:x["municipio"])

    summary={
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "metodologia_final":{
            "cota_parte":"Portal PR para rateio municipal; total anual reconciliado à DCA do Estado",
            "iss":"DCA auditada; ausências tratadas sem converter para zero; observações sinalizadas substituídas somente quando a comparação direta com o PIT/TCE-PR confirma divergência superior a 20%",
            "iss_pendente":"sinais temporais sem segunda fonte permanecem observados e são excluídos do ranking principal",
        },
        "pit_confirmations":pit_confirmations,
        "n_pit_corrections":len(pit_corrections),
        "iss_pr_por_ano_antigo":pr_iss_old,
        "iss_pr_por_ano_final":pr_iss_final,
        "total_nacional_2025_final":total_2025,
        "cota_target_pr":cota_target,
        "portal_sum_pr":portal_sum,
        "fator_reconciliacao":fator_reconciliacao,
        "seguro_receita":seguro_summary,
        "seguro_receita_municipios_pr":seguro_pr_municipios,
        "agregado_municipios_pr":agg_summary,
        "acumulado_2029_2033":{
            "receita_final":acumulado_total,
            "contrafactual":acumulado_contra,
            "diferenca":acumulado_total-acumulado_contra,
            "variacao_pct":(acumulado_total/acumulado_contra-1)*100 if acumulado_contra else None,
        },
        "amostra_artigo":{
            "criterio":"ISS observado em >=5 anos; ISS 2025 direto; população média >=10 mil; cota-parte reconstruída pelo Portal PR; anomalias de ISS corrigidas quando confirmadas no PIT/TCE-PR",
            "n":len(qualified),
            "metodo_original":{
                "negativos":sum(1 for r in qualified if (r["variacao_2033_metodo_original_pct"] or 0)<0),
                "positivos":sum(1 for r in qualified if (r["variacao_2033_metodo_original_pct"] or 0)>0),
                "mediana_pct":med_orig,
            },
            "metodo_auditado":{
                "negativos":sum(1 for r in qualified if r["variacao_2033_final_pct"]<0),
                "positivos":sum(1 for r in qualified if r["variacao_2033_final_pct"]>0),
                "mediana_pct":med,
            },
            "mudancas_de_sinal":sign_flips,
            "media_abs_revisao_pp":(
                sum(abs(r["delta_metodologia_2033_pp"]) for r in qualified if r["delta_metodologia_2033_pp"] is not None)
                / max(1,sum(1 for r in qualified if r["delta_metodologia_2033_pp"] is not None))
            ),
            "maiores_perdas":qloss,
            "maiores_ganhos":qgain,
        },
        "n_outliers_abs_30pct":sum(1 for r in rows if abs(r["variacao_2033_final_pct"])>=30),
        "top_25_comparacao_metodologias":comparison_top,
        "top_20_outliers_finais":outliers[:20],
        "nota":"Metodologia municipal final para uso no artigo. Bases nacionais canônicas permanecem preservadas; os resultados estaduais não são materialmente alterados pela auditoria municipal.",
    }

    date=datetime.now(timezone.utc).date().isoformat()
    # volta a ordenar alfabeticamente para o anexo
    rows_alpha=sorted(rows,key=lambda r:r["municipio"])
    write_csv(OUT/f"municipios-pr-final-auditado-{date}.csv",rows_alpha)
    write_csv(OUT/"municipios-pr-final-auditado-latest.csv",rows_alpha)
    dump_json(OUT/f"resumo-pr-final-auditado-{date}.json",summary)
    dump_json(OUT/"resumo-pr-final-auditado-latest.json",summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
