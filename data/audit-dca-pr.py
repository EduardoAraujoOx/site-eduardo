#!/usr/bin/env python3
"""
Auditoria e nova coleta do DCA municipal do Paraná (2019-2025).

Objetivos:
1. Recoletar diretamente da API SICONFI sem sobrescrever a base canônica.
2. Distinguir ausência real no DCA, resposta parcial e erro de API.
3. Comparar a nova fotografia com a base já arquivada no repositório.
4. Construir uma série ajustada em que dado faltante não é tratado como zero.
5. Recalcular CPT, receita-base de 2025 e projeções municipais de 2033 apenas
   para diagnóstico, preservando os demais parâmetros do modelo.
6. Produzir relatórios para identificar quanto dos outliers municipais decorre
   de cobertura/qualidade dos dados e quanto permanece após o tratamento.

A rotina NÃO modifica data/reforma-tributaria.json, coeficientes-municipios.json
ou qualquer outro arquivo usado pelo site. A promoção dos dados ajustados para a
base canônica deve ser uma decisão posterior, após revisão do diagnóstico.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
UF = "PR"
ANOS = list(range(2019, 2026))
BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
TARGET_COL = "Receitas Brutas Realizadas"
ISS_COD_NEW = "RO1.1.1.4.51.1.0"
COTA_COD_NEW = "RO1.7.2.1.50.0.0"
ISS_COD_OLD = "RO1.1.1.8.02.3.0"
COTA_COD_OLD = "RO1.7.2.8.01.1.0"
USER_AGENT = "auditoria-dca-pr/1.0 (estudo-reforma-tributaria)"


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def as_number(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(".", "").replace(",", "."))
    except Exception:
        return None


def fetch_json(url: str, retries: int = 6, timeout: int = 45):
    errors = []
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8")
                return {
                    "ok": True,
                    "status": getattr(r, "status", 200),
                    "attempts": attempt,
                    "data": json.loads(raw),
                    "error": None,
                }
        except urllib.error.HTTPError as e:
            errors.append(f"HTTP {e.code}: {e.reason}")
        except Exception as e:
            errors.append(f"{type(e).__name__}: {e}")
        if attempt < retries:
            time.sleep(min(2 ** (attempt - 1), 16))
    return {
        "ok": False,
        "status": None,
        "attempts": retries,
        "data": None,
        "error": " | ".join(errors[-3:]),
    }


def dca_url(cod: str, ano: int):
    params = {
        "an_exercicio": ano,
        "co_tipo_demonstrativo": "DCA",
        "no_anexo": "DCA-Anexo I-C",
        "co_esfera": "M",
        "id_ente": cod,
    }
    return f"{BASE_URL}/dca?{urllib.parse.urlencode(params)}"


def parse_dca_response(resp: dict, ano: int):
    if not resp["ok"]:
        return {
            "request_status": "api_error",
            "data_status": "api_error",
            "iss": None,
            "cota_raw": None,
            "iss_matches": 0,
            "cota_matches": 0,
            "attempts": resp["attempts"],
            "http_status": resp["status"],
            "error": resp["error"],
        }

    iss_cod = ISS_COD_NEW if ano >= 2022 else ISS_COD_OLD
    cota_cod = COTA_COD_NEW if ano >= 2022 else COTA_COD_OLD
    iss_vals, cota_vals = [], []
    for item in (resp["data"] or {}).get("items", []):
        if item.get("coluna") != TARGET_COL:
            continue
        if item.get("cod_conta") == iss_cod:
            v = as_number(item.get("valor"))
            if v is not None:
                iss_vals.append(v)
        elif item.get("cod_conta") == cota_cod:
            v = as_number(item.get("valor"))
            if v is not None:
                cota_vals.append(v)

    iss = sum(iss_vals) if iss_vals else None
    cota = sum(cota_vals) if cota_vals else None
    if iss is not None and cota is not None:
        data_status = "ok"
    elif iss is None and cota is None:
        data_status = "absent_dca"
    else:
        data_status = "partial"

    return {
        "request_status": "ok",
        "data_status": data_status,
        "iss": iss,
        "cota_raw": cota,
        "iss_matches": len(iss_vals),
        "cota_matches": len(cota_vals),
        "attempts": resp["attempts"],
        "http_status": resp["status"],
        "error": None,
    }


def collect_snapshot(sleep_seconds: float = 0.15):
    entes_resp = fetch_json(f"{BASE_URL}/entes")
    if not entes_resp["ok"]:
        raise RuntimeError(f"Falha ao obter lista de entes: {entes_resp['error']}")
    munis = [
        i for i in entes_resp["data"].get("items", [])
        if i.get("uf") == UF and i.get("esfera") == "M"
    ]
    munis.sort(key=lambda x: str(x.get("ente") or ""))

    snapshot = {
        "_meta": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "uf": UF,
            "anos": ANOS,
            "source": "SICONFI/STN, DCA Anexo I-C",
            "base_url": BASE_URL,
            "target_column": TARGET_COL,
            "n_municipios_api": len(munis),
            "classification": {
                "ok": "ISS e cota-parte encontrados",
                "partial": "apenas um dos dois componentes encontrado",
                "absent_dca": "requisição bem-sucedida, mas contas-alvo ausentes",
                "api_error": "requisição não concluída após todas as tentativas",
            },
        },
        "municipios": {},
    }

    total = len(munis) * len(ANOS)
    done = 0
    for ent in munis:
        cod = str(ent.get("cod_ibge"))
        rec = {"nome": ent.get("ente"), "uf": UF, "anos": {}}
        for ano in ANOS:
            parsed = parse_dca_response(fetch_json(dca_url(cod, ano)), ano)
            rec["anos"][str(ano)] = parsed
            done += 1
            if done % 100 == 0 or done == total:
                print(f"Coleta PR: {done}/{total} chamadas concluídas")
            if sleep_seconds:
                time.sleep(sleep_seconds)
        snapshot["municipios"][cod] = rec
    return snapshot


def old_detail(ref_data, cod: str, ano: int):
    v = (ref_data.get("dca_detalhes", {}).get(str(ano), {}) or {}).get(cod)
    if not v:
        return {"iss": None, "cota_raw": None}
    return {"iss": as_number(v.get("valor")), "cota_raw": as_number(v.get("cota_parte_icms"))}


def first_available(new_v, old_v):
    if new_v is not None:
        return new_v, "new_observed"
    if old_v is not None:
        return old_v, "legacy_snapshot"
    return None, None


def nearest_year_estimates(target_year: int, available_years: list[int]):
    if not available_years:
        return []
    mind = min(abs(y - target_year) for y in available_years)
    return [y for y in available_years if abs(y - target_year) == mind]


def build_adjusted_series(snapshot: dict, ref_data: dict):
    codes = sorted(snapshot["municipios"].keys())
    base_iss = {c: {} for c in codes}
    base_iss_source = {c: {} for c in codes}
    base_cota = {c: {} for c in codes}
    base_cota_source = {c: {} for c in codes}

    for cod in codes:
        for ano in ANOS:
            new = snapshot["municipios"][cod]["anos"][str(ano)]
            old = old_detail(ref_data, cod, ano)
            v, src = first_available(new.get("iss"), old["iss"])
            base_iss[cod][ano] = v
            base_iss_source[cod][ano] = src
            v, src = first_available(new.get("cota_raw"), old["cota_raw"])
            base_cota[cod][ano] = v
            base_cota_source[cod][ano] = src

    growth_cache = {}
    def common_iss_growth(source_year: int, target_year: int):
        key = (source_year, target_year)
        if key in growth_cache:
            return growth_cache[key]
        pairs = [
            (base_iss[c][source_year], base_iss[c][target_year])
            for c in codes
            if base_iss[c][source_year] is not None and base_iss[c][target_year] is not None
        ]
        den = sum(a for a, _ in pairs)
        num = sum(b for _, b in pairs)
        ratio = (num / den) if den > 0 and len(pairs) >= 20 else None
        growth_cache[key] = ratio
        return ratio

    adjusted_iss = {c: {} for c in codes}
    adjusted_iss_source = {c: {} for c in codes}
    for cod in codes:
        available = [y for y in ANOS if base_iss[cod][y] is not None]
        for ano in ANOS:
            if base_iss[cod][ano] is not None:
                adjusted_iss[cod][ano] = base_iss[cod][ano]
                adjusted_iss_source[cod][ano] = base_iss_source[cod][ano]
                continue
            candidates = nearest_year_estimates(ano, available)
            estimates = []
            for src_year in candidates:
                ratio = common_iss_growth(src_year, ano)
                if ratio is not None:
                    estimates.append(base_iss[cod][src_year] * ratio)
            if estimates:
                adjusted_iss[cod][ano] = sum(estimates) / len(estimates)
                adjusted_iss_source[cod][ano] = "imputed_temporal"
            else:
                adjusted_iss[cod][ano] = None
                adjusted_iss_source[cod][ano] = "unresolved"

    denom_cota = {
        ano: sum(base_cota[c][ano] for c in codes if base_cota[c][ano] is not None)
        for ano in ANOS
    }
    share_cota = {c: {} for c in codes}
    for cod in codes:
        for ano in ANOS:
            den = denom_cota[ano]
            v = base_cota[cod][ano]
            share_cota[cod][ano] = (v / den) if (v is not None and den > 0) else None

    cota_targets = {}
    for ano in ANOS:
        s = str(ano)
        declared = (ref_data.get("dca_transf_munis_por_uf", {}).get(s, {}) or {}).get(UF)
        icms = (ref_data.get("dca_icms_por_uf", {}).get(s, {}) or {}).get(UF)
        cota_targets[ano] = as_number(declared) if declared is not None else ((as_number(icms) or 0) * 0.25)

    weights = {c: {} for c in codes}
    adjusted_cota_source = {c: {} for c in codes}
    for cod in codes:
        available = [y for y in ANOS if share_cota[cod][y] is not None]
        for ano in ANOS:
            if share_cota[cod][ano] is not None:
                weights[cod][ano] = share_cota[cod][ano]
                adjusted_cota_source[cod][ano] = base_cota_source[cod][ano]
                continue
            candidates = nearest_year_estimates(ano, available)
            vals = [share_cota[cod][y] for y in candidates if share_cota[cod][y] is not None]
            if vals:
                weights[cod][ano] = sum(vals) / len(vals)
                adjusted_cota_source[cod][ano] = "imputed_temporal"
            else:
                weights[cod][ano] = None
                adjusted_cota_source[cod][ano] = "unresolved"

    adjusted_cota = {c: {} for c in codes}
    for ano in ANOS:
        resolved_sum = sum(weights[c][ano] for c in codes if weights[c][ano] is not None)
        for cod in codes:
            w = weights[cod][ano]
            adjusted_cota[cod][ano] = (
                cota_targets[ano] * w / resolved_sum
                if w is not None and resolved_sum > 0 and cota_targets[ano] is not None
                else None
            )

    return {
        "codes": codes,
        "adjusted_iss": adjusted_iss,
        "adjusted_iss_source": adjusted_iss_source,
        "adjusted_cota": adjusted_cota,
        "adjusted_cota_source": adjusted_cota_source,
        "cota_targets": cota_targets,
    }


def national_totals_adjusted(ref_data: dict, adjusted: dict):
    old_total, new_total, old_pr_iss, new_pr_iss = {}, {}, {}, {}
    outras_by_year = ref_data.get("dca_icms_outras_deducoes_por_uf", {})
    for ano in ANOS:
        s = str(ano)
        icms = as_number(ref_data.get("dca_icms_br", {}).get(s))
        iss = as_number(ref_data.get("dca_iss_br", {}).get(s))
        fecop = as_number(ref_data.get("dca_fecop_br", {}).get(s)) or 0.0
        outras = sum(as_number(v) or 0.0 for v in (outras_by_year.get(s, {}) or {}).values())
        old_total[ano] = (icms - outras + iss + fecop) if icms is not None and iss is not None else None
        old_pr_iss[ano] = as_number((ref_data.get("dca_iss_por_uf", {}).get(s, {}) or {}).get(UF)) or 0.0
        vals = [adjusted["adjusted_iss"][c][ano] for c in adjusted["codes"]]
        new_pr_iss[ano] = sum(v for v in vals if v is not None)
        new_total[ano] = old_total[ano] - old_pr_iss[ano] + new_pr_iss[ano] if old_total[ano] is not None else None

    total_2025 = new_total[2025]
    defl = {
        ano: (1.0 if ano == 2025 else (total_2025 / new_total[ano] if new_total.get(ano) else None))
        for ano in ANOS
    }
    return {
        "old_total": old_total,
        "new_total": new_total,
        "old_pr_iss": old_pr_iss,
        "new_pr_iss": new_pr_iss,
        "total_2025": total_2025,
        "deflators": defl,
    }


def project_municipio(r0_2025, coef_cpt, coef_pleno, cod, nacional_by_year, repasse_idx, total_br_2025):
    coef_neutro = r0_2025 / total_br_2025 if total_br_2025 else 0
    out = {}
    for ano in [2029, 2030, 2031, 2032, 2033]:
        nac = nacional_by_year[ano]
        ref_a = nac["icms_iss_residual"] + nac["ibs_bruto"]
        ca = nac.get("ca", 0.0)
        repasse = repasse_idx.get(f"MUN-{cod}", {}).get(ano, 0.0)
        total = (
            nac["icms_iss_residual"] * coef_neutro
            + (1 - ca) * nac["ibs_historico"] * coef_cpt
            + nac["ibs_destino_liquido"] * coef_pleno
            + (1 - ca) * repasse
        )
        contra = ref_a * coef_neutro
        out[ano] = {
            "total": total,
            "contrafactual": contra,
            "variacao": (total - contra) / contra if contra > 0 else None,
        }
    return out


def robust_ratio_flag(value, series, low=0.2, high=5.0):
    positive = [x for x in series if x is not None and x > 0]
    if value is None or not positive:
        return False, None
    med = statistics.median(positive)
    ratio = value / med if med > 0 else None
    return (ratio is not None and (ratio < low or ratio > high)), ratio


def build_diagnostics(snapshot: dict, adjusted: dict, ref_data: dict):
    nat = national_totals_adjusted(ref_data, adjusted)
    coef_dest = load_json(HERE / "rateio-destino-municipios.json").get("municipios", {})
    nac = load_json(HERE / "ibs-projecao-nacional.json")
    nacional_by_year = {int(x["ano"]): x for x in nac["projecao"]}
    seguro = load_json(HERE / "seguro-receita-repasses.json")
    repasse_idx = {}
    for ano in [2029, 2030, 2031, 2032, 2033]:
        for e in (seguro.get("anos", {}).get(str(ano), {}) or {}).get("entidades", []):
            if e.get("esfera") == "municipio":
                repasse_idx.setdefault(e["id"], {})[ano] = e.get("repasse") or 0.0

    old_panel_path = HERE / "painel-municipios" / "PR.json"
    old_panel = load_json(old_panel_path).get("municipios", {}) if old_panel_path.exists() else {}

    rows, details = [], []
    for cod in adjusted["codes"]:
        nome = snapshot["municipios"][cod]["nome"]
        totals_real = []
        unresolved = False
        complete_new = any_new = imputed_iss = imputed_cota = legacy_iss = legacy_cota = 0

        for ano in ANOS:
            raw = snapshot["municipios"][cod]["anos"][str(ano)]
            if raw["data_status"] == "ok":
                complete_new += 1
            if raw["data_status"] in ("ok", "partial"):
                any_new += 1
            iss = adjusted["adjusted_iss"][cod][ano]
            cota = adjusted["adjusted_cota"][cod][ano]
            iss_src = adjusted["adjusted_iss_source"][cod][ano]
            cota_src = adjusted["adjusted_cota_source"][cod][ano]
            imputed_iss += int(iss_src == "imputed_temporal")
            imputed_cota += int(cota_src == "imputed_temporal")
            legacy_iss += int(iss_src == "legacy_snapshot")
            legacy_cota += int(cota_src == "legacy_snapshot")

            if iss is None or cota is None or nat["deflators"][ano] is None:
                unresolved = True
                total_real = None
            else:
                total_real = (iss + cota) * nat["deflators"][ano]
                totals_real.append(total_real)

            old = old_detail(ref_data, cod, ano)
            details.append({
                "codigo_ibge": cod,
                "municipio": nome,
                "ano": ano,
                "request_status": raw["request_status"],
                "data_status": raw["data_status"],
                "new_iss": raw.get("iss"),
                "legacy_iss": old["iss"],
                "adjusted_iss": iss,
                "iss_source": iss_src,
                "new_cota_raw": raw.get("cota_raw"),
                "legacy_cota_raw": old["cota_raw"],
                "adjusted_cota": cota,
                "cota_source": cota_src,
                "cota_target_pr": adjusted["cota_targets"][ano],
                "total_real_2025": total_real,
                "api_attempts": raw.get("attempts"),
                "api_error": raw.get("error"),
            })

        hist_mean = (sum(totals_real) / len(ANOS)) if (not unresolved and len(totals_real) == len(ANOS)) else None
        r0 = None
        if adjusted["adjusted_iss"][cod][2025] is not None and adjusted["adjusted_cota"][cod][2025] is not None:
            r0 = adjusted["adjusted_iss"][cod][2025] + adjusted["adjusted_cota"][cod][2025]

        coef_cpt = hist_mean / nat["total_2025"] if hist_mean is not None and nat["total_2025"] else None
        rd = coef_dest.get(cod) or {}
        coef_pleno = (rd.get("phi_dest_pct") / 100) if rd.get("phi_dest_pct") is not None else None
        projection = None
        if r0 is not None and coef_cpt is not None and coef_pleno is not None:
            projection = project_municipio(r0, coef_cpt, coef_pleno, cod, nacional_by_year, repasse_idx, nat["total_2025"])

        old = old_panel.get(cod, {})
        old_var = (old.get("variacao_por_ano") or {}).get("2033")
        if old_var is None:
            old_var = (old.get("variacao_por_ano") or {}).get(2033)
        new_var = projection[2033]["variacao"] if projection else None

        base_flag, base_ratio = robust_ratio_flag(
            r0,
            [
                (adjusted["adjusted_iss"][cod][y] + adjusted["adjusted_cota"][cod][y])
                if adjusted["adjusted_iss"][cod][y] is not None and adjusted["adjusted_cota"][cod][y] is not None
                else None for y in ANOS[:-1]
            ],
            low=0.25,
            high=4.0,
        )
        iss_flag, iss_ratio = robust_ratio_flag(
            adjusted["adjusted_iss"][cod][2025],
            [adjusted["adjusted_iss"][cod][y] for y in ANOS[:-1]],
            low=0.2,
            high=5.0,
        )
        cota_flag, cota_ratio = robust_ratio_flag(
            adjusted["adjusted_cota"][cod][2025],
            [adjusted["adjusted_cota"][cod][y] for y in ANOS[:-1]],
            low=0.2,
            high=5.0,
        )

        flags = []
        if unresolved:
            flags.append("unresolved_component")
        if imputed_iss or imputed_cota:
            flags.append("temporal_imputation")
        if legacy_iss or legacy_cota:
            flags.append("legacy_snapshot_used")
        if base_flag:
            flags.append("base_2025_anomaly")
        if iss_flag:
            flags.append("iss_2025_anomaly")
        if cota_flag:
            flags.append("cota_2025_anomaly")
        if new_var is not None and abs(new_var) >= 0.30:
            flags.append("projection_outlier_30pct")
        if old_var is not None and new_var is not None and abs(new_var - old_var) >= 0.10:
            flags.append("projection_changed_10pp")

        rows.append({
            "codigo_ibge": cod,
            "municipio": nome,
            "complete_years_new": complete_new,
            "years_with_any_new_component": any_new,
            "imputed_iss_years": imputed_iss,
            "imputed_cota_years": imputed_cota,
            "legacy_iss_years": legacy_iss,
            "legacy_cota_years": legacy_cota,
            "unresolved": unresolved,
            "r0_2025_adjusted": r0,
            "historical_mean_adjusted": hist_mean,
            "base_2025_to_prev_median_ratio": base_ratio,
            "iss_2025_to_prev_median_ratio": iss_ratio,
            "cota_2025_to_prev_median_ratio": cota_ratio,
            "coef_cpt_adjusted_pct": coef_cpt * 100 if coef_cpt is not None else None,
            "coef_destino_pct": coef_pleno * 100 if coef_pleno is not None else None,
            "old_pre_2025": old.get("pre_2025"),
            "old_variacao_2033": old_var,
            "adjusted_variacao_2033": new_var,
            "delta_variacao_pp": (new_var - old_var) * 100 if old_var is not None and new_var is not None else None,
            "adjusted_revenue_2033": projection[2033]["total"] if projection else None,
            "adjusted_counterfactual_2033": projection[2033]["contrafactual"] if projection else None,
            "flags": ";".join(flags),
        })

    return rows, details, nat


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def summarize(snapshot: dict, rows: list[dict], details: list[dict], nat: dict):
    status_counts = Counter()
    for rec in snapshot["municipios"].values():
        for ano in ANOS:
            status_counts[rec["anos"][str(ano)]["data_status"]] += 1

    outliers = [r for r in rows if r["adjusted_variacao_2033"] is not None]
    outliers.sort(key=lambda r: abs(r["adjusted_variacao_2033"]), reverse=True)
    changed = [r for r in rows if r["delta_variacao_pp"] is not None]
    changed.sort(key=lambda r: abs(r["delta_variacao_pp"]), reverse=True)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "uf": UF,
        "n_municipios": len(rows),
        "n_observacoes_municipio_ano": len(details),
        "status_nova_coleta": dict(status_counts),
        "municipios_com_imputacao_temporal": sum(1 for r in rows if r["imputed_iss_years"] or r["imputed_cota_years"]),
        "municipios_com_snapshot_legado_utilizado": sum(1 for r in rows if r["legacy_iss_years"] or r["legacy_cota_years"]),
        "municipios_com_componente_nao_resolvido": sum(1 for r in rows if r["unresolved"]),
        "municipios_outlier_abs_30pct_apos_ajuste": sum(
            1 for r in rows if r["adjusted_variacao_2033"] is not None and abs(r["adjusted_variacao_2033"]) >= 0.30
        ),
        "municipios_com_mudanca_10pp_ou_mais": sum(
            1 for r in rows if r["delta_variacao_pp"] is not None and abs(r["delta_variacao_pp"]) >= 10
        ),
        "total_br_2025_antigo": nat["old_total"][2025],
        "total_br_2025_ajustado_pr": nat["total_2025"],
        "iss_pr_2025_antigo": nat["old_pr_iss"][2025],
        "iss_pr_2025_nova_serie_ajustada": nat["new_pr_iss"][2025],
        "top_20_outliers_ajustados": [
            {
                "codigo_ibge": r["codigo_ibge"],
                "municipio": r["municipio"],
                "variacao_2033_pct": r["adjusted_variacao_2033"] * 100,
                "variacao_antiga_pct": r["old_variacao_2033"] * 100 if r["old_variacao_2033"] is not None else None,
                "delta_pp": r["delta_variacao_pp"],
                "flags": r["flags"],
            }
            for r in outliers[:20]
        ],
        "top_20_maiores_revisoes": [
            {
                "codigo_ibge": r["codigo_ibge"],
                "municipio": r["municipio"],
                "delta_pp": r["delta_variacao_pp"],
                "variacao_antiga_pct": r["old_variacao_2033"] * 100 if r["old_variacao_2033"] is not None else None,
                "variacao_ajustada_pct": r["adjusted_variacao_2033"] * 100 if r["adjusted_variacao_2033"] is not None else None,
                "flags": r["flags"],
            }
            for r in changed[:20]
        ],
        "nota_metodologica": (
            "A série ajustada prioriza a nova coleta. Se a API atual não devolve um componente, "
            "preserva-se o valor arquivado na fotografia anterior, quando existente. Apenas na ausência "
            "de ambos ocorre imputação temporal. ISS é atualizado pela variação agregada entre municípios "
            "comuns aos dois anos. A cota-parte usa a participação municipal no(s) ano(s) mais próximo(s), "
            "renormalizada para fechar no total estadual da cota-parte. Valores observados extremos não são "
            "substituídos automaticamente; são apenas sinalizados."
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(HERE / "auditoria-dca-pr"))
    ap.add_argument("--sleep", type=float, default=0.15)
    ap.add_argument("--snapshot", help="Usar uma fotografia JSON já coletada em vez de acessar a API")
    args = ap.parse_args()

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()

    ref_data = load_json(HERE / "reforma-tributaria.json")
    snapshot = load_json(Path(args.snapshot)) if args.snapshot else collect_snapshot(args.sleep)
    dump_json(outdir / f"coleta-pr-{today}.json", snapshot)
    dump_json(outdir / "coleta-pr-latest.json", snapshot)

    adjusted = build_adjusted_series(snapshot, ref_data)
    rows, details, nat = build_diagnostics(snapshot, adjusted, ref_data)
    summary = summarize(snapshot, rows, details, nat)

    dump_json(outdir / f"diagnostico-pr-{today}.json", summary)
    dump_json(outdir / "diagnostico-pr-latest.json", summary)
    write_csv(outdir / f"municipios-pr-{today}.csv", rows)
    write_csv(outdir / "municipios-pr-latest.csv", rows)
    write_csv(outdir / f"observacoes-pr-{today}.csv", details)
    write_csv(outdir / "observacoes-pr-latest.csv", details)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nArquivos gravados em: {outdir}")
    print("A base canônica NÃO foi sobrescrita.")


if __name__ == "__main__":
    main()

# Workflow de auditoria habilitado em 2026-09-29.
