#!/usr/bin/env python3
"""
Compara os coeficientes calculados neste repositório (data/coeficientes-uf.json,
data/coeficientes-municipios.json) contra a Nota Técnica nº 02/2026 (SEFAZ-ES,
pacote v22), arquivos em data/raw/nota-v22/.

Uso:
  python3 build-divergencia-vs-nota-v22.py
"""

import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw" / "nota-v22"
OUT = HERE / "divergencia-vs-nota-v22.json"


def read_csv(path, delimiter=";"):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def main():
    with open(HERE / "coeficientes-uf.json") as f:
        cpt_uf = json.load(f)["por_uf"]
    with open(HERE / "coeficientes-municipios.json") as f:
        cpt_munis = json.load(f)["municipios"]

    v22_uf = read_csv(RAW / "cpt_ufs_v22.csv")
    v22_munis_es = read_csv(RAW / "cpt_municipios_es_v22.csv")

    # ── UF ────────────────────────────────────────────────────────────────
    div_uf = {}
    for row in v22_uf:
        uf = row["UF"]
        v22_estado = float(row["Coeficiente_estado"]) if row["Coeficiente_estado"] else None
        v22_munis = float(row["Coeficiente_municipios"]) if row["Coeficiente_municipios"] else None
        v22_total = float(row["Coeficiente_total"]) if row["Coeficiente_total"] else None

        meu = cpt_uf.get(uf, {})
        meu_estado = meu.get("coeficiente_estado_pct")
        meu_munis = meu.get("coeficiente_municipios_pct")
        meu_total = meu.get("coeficiente_total_pct")

        div_uf[uf] = {
            "v22_estado": v22_estado, "meu_estado": meu_estado,
            "diff_estado_pp": (meu_estado - v22_estado) if (meu_estado is not None and v22_estado is not None) else None,
            "v22_municipios": v22_munis, "meu_municipios": meu_munis,
            "diff_municipios_pp": (meu_munis - v22_munis) if (meu_munis is not None and v22_munis is not None) else None,
            "v22_total": v22_total, "meu_total": meu_total,
            "diff_total_pp": (meu_total - v22_total) if (meu_total is not None and v22_total is not None) else None,
        }

    # ── Municípios ES ────────────────────────────────────────────────────
    div_munis_es = {}
    for row in v22_munis_es:
        cod = row["Codigo"]
        v22_cpt = float(row["Coeficiente"]) if row["Coeficiente"] else None
        meu = cpt_munis.get(cod, {})
        meu_cpt = meu.get("coeficiente_pct")
        div_munis_es[cod] = {
            "nome": row["Municipio"],
            "v22": v22_cpt, "meu": meu_cpt,
            "diff_pp": (meu_cpt - v22_cpt) if (meu_cpt is not None and v22_cpt is not None) else None,
        }

    output = {
        "fonte_v22": "Nota Técnica nº 02/2026 (SEFAZ-ES, pacote v22), data/raw/nota-v22/",
        "divergencia_uf": div_uf,
        "divergencia_municipios_es": div_munis_es,
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {OUT}\n")

    print("=== UF: coeficiente TOTAL (estado+municípios), diff em p.p. ===")
    rows = sorted(div_uf.items(), key=lambda kv: -abs(kv[1]["diff_total_pp"] or 0))
    for uf, v in rows:
        if v["diff_total_pp"] is None:
            continue
        print(f"  {uf}: meu={v['meu_total']:.4f}%  v22={v['v22_total']:.4f}%  diff={v['diff_total_pp']:+.4f}pp")

    print("\n=== Municípios ES: maiores divergências (p.p.) ===")
    rows_m = sorted(
        ((cod, v) for cod, v in div_munis_es.items() if v["diff_pp"] is not None),
        key=lambda kv: -abs(kv[1]["diff_pp"])
    )[:15]
    for cod, v in rows_m:
        print(f"  {v['nome']:<25} meu={v['meu']:.5f}%  v22={v['v22']:.5f}%  diff={v['diff_pp']:+.6f}pp")

    sem_correspondencia = [cod for cod, v in div_munis_es.items() if v["meu"] is None]
    print(f"\nMunicípios ES na Nota v22 sem correspondência no meu arquivo: {len(sem_correspondencia)}")


if __name__ == "__main__":
    main()
