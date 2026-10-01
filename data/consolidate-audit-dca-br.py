#!/usr/bin/env python3
"""Consolida as auditorias de DCA municipal por UF (audit-dca-uf.py) em um ranking nacional.

Lê data/auditoria-dca-<uf>/{diagnostico,municipios,anomalias-temporais}-<uf>-latest.*
e grava em data/auditoria-dca-br/:
  - resumo-uf-latest.csv: uma linha por UF (cobertura, ausências, anomalias, outliers)
  - ranking-anomalias-latest.csv: todas as anomalias temporais do país, ordenadas por
    grau (forte primeiro) e materialidade, para triagem manual
Apenas auditoria: não altera a base canônica do site.
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "auditoria-dca-br"


def main():
    OUT.mkdir(exist_ok=True)
    resumo, ranking = [], []
    for d in sorted(HERE.glob("auditoria-dca-??")):
        uf = d.name[-2:]
        diag_p = d / f"diagnostico-{uf}-latest.json"
        if not diag_p.exists():
            continue
        diag = json.loads(diag_p.read_text(encoding="utf-8"))
        st = diag.get("status_nova_coleta", {})
        at = diag.get("anomalias_temporais", {})
        n_obs = diag.get("n_observacoes_municipio_ano") or 1
        resumo.append({
            "uf": uf.upper(),
            "n_municipios": diag.get("n_municipios"),
            "obs_ok": st.get("ok", 0),
            "obs_ausente_dca": st.get("absent_dca", 0),
            "obs_parcial": st.get("partial", 0),
            "obs_erro_api": st.get("api_error", 0),
            "pct_obs_incompletas": round(100 * (n_obs - st.get("ok", 0)) / n_obs, 2),
            "municipios_com_imputacao": diag.get("municipios_com_imputacao_temporal"),
            "municipios_nao_resolvidos": diag.get("municipios_com_componente_nao_resolvido"),
            "outliers_projecao_30pct": diag.get("municipios_outlier_abs_30pct_apos_ajuste"),
            "anomalias_temporais_fortes": at.get("n_forte"),
            "anomalias_temporais_moderadas": at.get("n_moderado"),
            "municipios_com_anomalia_temporal": at.get("n_municipios_afetados"),
        })
        csv_p = d / f"anomalias-temporais-{uf}-latest.csv"
        if csv_p.exists():
            for r in csv.DictReader(csv_p.open(encoding="utf-8-sig")):
                r["uf"] = uf.upper()
                ranking.append(r)

    def key(r):
        m = r.get("materialidade_pct_receita_media")
        return (r["grau"] != "forte", -(float(m) if m not in (None, "") else 0.0))

    ranking.sort(key=key)
    for name, rows in (("resumo-uf-latest.csv", resumo), ("ranking-anomalias-latest.csv", ranking)):
        if not rows:
            continue
        with (OUT / name).open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"UFs consolidadas: {len(resumo)}; anomalias temporais: {len(ranking)}")


if __name__ == "__main__":
    main()
