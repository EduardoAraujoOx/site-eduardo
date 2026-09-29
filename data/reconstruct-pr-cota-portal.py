#!/usr/bin/env python3
"""
Reconstrução diagnóstica do componente municipal da cota-parte do ICMS no PR.

Princípio:
- O total estadual da cota-parte continua vindo do DCA do Estado do Paraná
  (ou 25% do ICMS bruto quando a declaração estadual estiver ausente).
- A distribuição entre os 399 municípios passa a usar o ICMS bruto efetivamente
  repassado a cada município no Portal da Transparência do Paraná.
- A distribuição é reescalada para fechar exatamente no total estadual do DCA.
- O ISS vem da série ajustada produzida por audit-dca-pr.py.

Objetivo: medir quanto o CPT municipal muda quando substituímos registros
municipais inconsistentes/ausentes de cota-parte por uma fonte estadual
independente e reconciliada.

Esta rotina é diagnóstica e NÃO altera a base canônica nem recalcula o
Seguro-Receita.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
import unicodedata
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "auditoria-pr-validacao"
ANOS = list(range(2019, 2026))


def norm_name(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("d'", "d ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    aliases = {"santa cruz de monte castelo": "santa cruz do monte castelo"}
    return aliases.get(s, s)


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def read_csv(p):
    with Path(p).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(p, rows):
    if not rows:
        Path(p).write_text("", encoding="utf-8")
        return
    with Path(p).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def dump_json(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def num(v):
    if v is None or v == "":
        return None
    return float(v)


def main():
    obs = read_csv(HERE / "auditoria-dca-pr" / "observacoes-pr-latest.csv")
    muni_diag = read_csv(HERE / "auditoria-dca-pr" / "municipios-pr-latest.csv")
    portal = load_json(OUT / "repasses-portal-pr-latest.json")
    ref = load_json(HERE / "reforma-tributaria.json")

    names = {}
    iss = defaultdict(dict)
    old_adj_cota = defaultdict(dict)
    for o in obs:
        cod = o["codigo_ibge"]
        ano = int(o["ano"])
        names[cod] = o["municipio"]
        iss[cod][ano] = num(o.get("adjusted_iss"))
        old_adj_cota[cod][ano] = num(o.get("adjusted_cota"))

    # Portal por nome normalizado.
    portal_by_year = {}
    for ano in ANOS:
        rows = portal["anos"][str(ano)]
        portal_by_year[ano] = {norm_name(r["municipio_portal"]): float(r["icms_bruto_portal"]) for r in rows}

    # Total estadual alvo por ano.
    cota_target = {}
    for ano in ANOS:
        s = str(ano)
        declared = ((ref.get("dca_transf_munis_por_uf", {}).get(s, {}) or {}).get("PR"))
        icms = ((ref.get("dca_icms_por_uf", {}).get(s, {}) or {}).get("PR"))
        cota_target[ano] = float(declared) if declared is not None else (float(icms) * 0.25 if icms is not None else None)

    # Rateio reconstruído com Portal, reescalado ao agregado estadual.
    recon_cota = defaultdict(dict)
    portal_sum = {}
    missing_portal = []
    for ano in ANOS:
        vals = {}
        for cod, nome in names.items():
            v = portal_by_year[ano].get(norm_name(nome))
            if v is None:
                missing_portal.append({"codigo_ibge": cod, "municipio": nome, "ano": ano})
            else:
                vals[cod] = v
        portal_sum[ano] = sum(vals.values())
        factor = cota_target[ano] / portal_sum[ano] if cota_target[ano] and portal_sum[ano] else None
        for cod in names:
            v = vals.get(cod)
            recon_cota[cod][ano] = v * factor if (v is not None and factor is not None) else None

    # Total nacional ajustado: mesma lógica da auditoria municipal. A troca do
    # rateio da cota-parte não altera o bolo nacional; apenas o ISS ajustado do PR.
    outras_by_year = ref.get("dca_icms_outras_deducoes_por_uf", {})
    old_pr_iss_by_year = ref.get("dca_iss_por_uf", {})
    total_nat = {}
    for ano in ANOS:
        s = str(ano)
        icms_br = ref.get("dca_icms_br", {}).get(s)
        iss_br = ref.get("dca_iss_br", {}).get(s)
        fecop = ref.get("dca_fecop_br", {}).get(s, 0) or 0
        outras = sum((outras_by_year.get(s, {}) or {}).values())
        old_pr_iss = (old_pr_iss_by_year.get(s, {}) or {}).get("PR", 0) or 0
        new_pr_iss = sum(v[ano] for v in iss.values() if v.get(ano) is not None)
        total_nat[ano] = float(icms_br) - outras + float(iss_br) + float(fecop) - float(old_pr_iss) + new_pr_iss

    total_2025 = total_nat[2025]
    deflator = {ano: (1.0 if ano == 2025 else total_2025 / total_nat[ano]) for ano in ANOS}

    old_diag = {r["codigo_ibge"]: r for r in muni_diag}
    rows = []
    for cod, nome in names.items():
        annual = []
        unresolved = False
        for ano in ANOS:
            i = iss[cod].get(ano)
            cp = recon_cota[cod].get(ano)
            if i is None or cp is None:
                unresolved = True
                annual.append(None)
            else:
                annual.append((i + cp) * deflator[ano])

        hist = None if unresolved else sum(annual) / len(ANOS)
        cpt = hist / total_2025 if hist is not None else None
        base = None
        if iss[cod].get(2025) is not None and recon_cota[cod].get(2025) is not None:
            base = iss[cod][2025] + recon_cota[cod][2025]

        old = old_diag.get(cod, {})
        old_cpt = num(old.get("coef_cpt_adjusted_pct"))
        old_base = num(old.get("r0_2025_adjusted"))
        delta_cpt_pp = cpt * 100 - old_cpt if cpt is not None and old_cpt is not None else None
        delta_base_pct = (base / old_base - 1) * 100 if base is not None and old_base not in (None, 0) else None

        # Quanto a reconstrução altera a cota-parte nos sete anos.
        diffs = []
        for ano in ANOS:
            a = old_adj_cota[cod].get(ano)
            b = recon_cota[cod].get(ano)
            if a is not None and b is not None and b != 0:
                diffs.append(abs(a / b - 1))
        max_cota_gap = max(diffs) * 100 if diffs else None

        rows.append({
            "codigo_ibge": cod,
            "municipio": nome,
            "base_2025_ajustada_anterior": old_base,
            "base_2025_reconstruida": base,
            "delta_base_2025_pct": delta_base_pct,
            "cpt_ajustado_anterior_pct": old_cpt,
            "cpt_reconstruido_portal_pct": cpt * 100 if cpt is not None else None,
            "delta_cpt_pp": delta_cpt_pp,
            "max_divergencia_cota_7anos_pct": max_cota_gap,
            "unresolved": unresolved,
        })

    rows.sort(key=lambda r: abs(r["delta_cpt_pp"] or 0), reverse=True)
    strong = [r for r in rows if r["delta_cpt_pp"] is not None and abs(r["delta_cpt_pp"]) >= 0.001]
    base10 = [r for r in rows if r["delta_base_2025_pct"] is not None and abs(r["delta_base_2025_pct"]) >= 10]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "metodo": (
            "ICMS municipal por ano = participação no ICMS bruto do Portal PR "
            "multiplicada pelo total estadual da cota-parte no DCA; ISS = série "
            "ajustada da auditoria DCA. Valores anuais convertidos para preços de 2025 "
            "pelo mesmo agregado nacional ajustado."
        ),
        "total_nacional_2025_ajustado": total_2025,
        "cota_target_pr": cota_target,
        "portal_sum_pr": portal_sum,
        "fator_reconciliacao": {
            str(y): cota_target[y] / portal_sum[y] if portal_sum[y] else None for y in ANOS
        },
        "n_municipios": len(rows),
        "n_municipios_portal_ausente": len({x["codigo_ibge"] for x in missing_portal}),
        "portal_ausentes": missing_portal,
        "n_cpt_mudanca_abs_0_001pp": len(strong),
        "n_base_2025_mudanca_abs_10pct": len(base10),
        "top_25_revisoes_cpt": rows[:25],
        "nota": (
            "Este resultado mede o efeito da reconstrução da cota-parte sobre a base e o CPT. "
            "Não é projeção final 2033, porque qualquer adoção definitiva exige recalcular "
            "também o Seguro-Receita e toda a cadeia de projeções."
        ),
    }

    date = datetime.now(timezone.utc).date().isoformat()
    write_csv(OUT / f"reconstrucao-cpt-portal-pr-{date}.csv", rows)
    write_csv(OUT / "reconstrucao-cpt-portal-pr-latest.csv", rows)
    dump_json(OUT / f"resumo-reconstrucao-cpt-pr-{date}.json", summary)
    dump_json(OUT / "resumo-reconstrucao-cpt-pr-latest.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
