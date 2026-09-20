#!/usr/bin/env python3
"""
Consolida os tres coletores (execucao-saude-es.json, orcamentos-execucoes-es.json,
ordem-cronologica-es.json) num unico JSON compacto, pronto para a pagina do
painel consumir direto, sem reprocessar nada no navegador.
"""

import json
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

DATA_DIR = Path(__file__).parent
OUTPUT = DATA_DIR / "painel-execucao-es.json"

FES_CODIGO_UG = "440901"
CUTOFF_MMDD = "09-18"  # ultimo dia com cobertura completa nas 4 series de despesas


def dia_do_ano(data_iso):
    y, m, d = (int(x) for x in data_iso.split("-"))
    return (date(y, m, d) - date(y, 1, 1)).days + 1


def build_serie_saude():
    d = json.load(open(DATA_DIR / "execucao-saude-es.json"))
    por_ano = defaultdict(list)
    cum = defaultdict(lambda: {"liq": 0.0, "pago": 0.0})
    for row in d["diario"]:
        ano = row["data"][:4]
        cum[ano]["liq"] += row["liquidado"]
        cum[ano]["pago"] += row["pago"]
        por_ano[ano].append(
            {
                "dia": dia_do_ano(row["data"]),
                "gap_acum": round(cum[ano]["liq"] - cum[ano]["pago"], 2),
            }
        )
    return {ano: v for ano, v in sorted(por_ano.items())}


def build_kpis(serie_saude):
    orc = json.load(open(DATA_DIR / "orcamentos-execucoes-es.json"))
    ordem = json.load(open(DATA_DIR / "ordem-cronologica-es.json"))

    ano_atual = orc["por_ano"]["2026"]["registros"]
    exec_ugs = [r for r in ano_atual if r["poder"] == "Executivo"]
    exec_liq = sum(r["liquidado"] for r in exec_ugs)
    exec_pago = sum(r["pago"] for r in exec_ugs)
    exec_gap = exec_liq - exec_pago

    fes = next(r for r in ano_atual if r["codigo_ug"] == FES_CODIGO_UG)
    fes_2024 = next(r for r in orc["por_ano"]["2024"]["registros"] if r["codigo_ug"] == FES_CODIGO_UG)
    fes_2025 = next(r for r in orc["por_ano"]["2025"]["registros"] if r["codigo_ug"] == FES_CODIGO_UG)

    # comparativo no mesmo corte do calendario (jan-set), a partir da serie diaria
    comparativo_corte = []
    for ano, pontos in serie_saude.items():
        pontos_corte = [p for p in pontos]
        if pontos_corte:
            ultimo = pontos_corte[-1]
            comparativo_corte.append({"ano": int(ano), "gap_no_corte": ultimo["gap_acum"]})

    geral_prazo = {g["ano"]: g for g in ordem["geral_por_ano"]}
    fes_prazo = {r["ano"]: r for r in ordem["por_ug"] if r["codigo_ug"] == FES_CODIGO_UG}

    return {
        "executivo": {
            "n_ugs": len(exec_ugs),
            "liquidado": round(exec_liq, 2),
            "pago": round(exec_pago, 2),
            "gap": round(exec_gap, 2),
            "prazo_p50_2025": geral_prazo[2025]["dias_p50"],
            "prazo_p50_2026": geral_prazo[2026]["dias_p50"],
            "prazo_p90_2025": geral_prazo[2025]["dias_p90"],
            "prazo_p90_2026": geral_prazo[2026]["dias_p90"],
        },
        "saude_fes": {
            "liquidado": fes["liquidado"],
            "pago": fes["pago"],
            "gap_atual": fes["liquidado_nao_pago"],
            "gap_fechamento_2024": fes_2024["liquidado_nao_pago"],
            "gap_fechamento_2025": fes_2025["liquidado_nao_pago"],
            "comparativo_mesmo_corte": sorted(comparativo_corte, key=lambda x: x["ano"]),
            "prazo_p50_2025": fes_prazo.get(2025, {}).get("dias_p50"),
            "prazo_p50_2026": fes_prazo.get(2026, {}).get("dias_p50"),
            "prazo_p90_2025": fes_prazo.get(2025, {}).get("dias_p90"),
            "prazo_p90_2026": fes_prazo.get(2026, {}).get("dias_p90"),
            "prazo_n_2026": fes_prazo.get(2026, {}).get("n_pagamentos"),
        },
    }


def build_ranking_executivo():
    orc = json.load(open(DATA_DIR / "orcamentos-execucoes-es.json"))
    rows = [r for r in orc["por_ano"]["2026"]["registros"] if r["poder"] == "Executivo"]
    ranking = []
    for r in rows:
        pct_pago = (r["pago"] / r["liquidado"] * 100) if r["liquidado"] else None
        ranking.append(
            {
                "codigo_ug": r["codigo_ug"],
                "unidade_gestora": r["unidade_gestora"],
                "liquidado": r["liquidado"],
                "pago": r["pago"],
                "gap": r["liquidado_nao_pago"],
                "rap": r["rap"],
                "pct_pago": round(pct_pago, 1) if pct_pago is not None else None,
            }
        )
    return sorted(ranking, key=lambda x: -x["gap"])


def build_prazos_executivo():
    d = json.load(open(DATA_DIR / "ordem-cronologica-es.json"))
    rows = [r for r in d["por_ug"] if r["ano"] == 2026 and r["n_pagamentos"] >= 30]
    prazos = [
        {
            "codigo_ug": r["codigo_ug"],
            "unidade_gestora": r["unidade_gestora"],
            "n_pagamentos": r["n_pagamentos"],
            "dias_p50": r["dias_p50"],
            "dias_p75": r["dias_p75"],
            "dias_p90": r["dias_p90"],
        }
        for r in rows
    ]
    return sorted(prazos, key=lambda x: -x["dias_p90"])


def main():
    serie_saude = build_serie_saude()
    output = {
        "gerado_em": datetime.utcnow().isoformat() + "Z",
        "fontes": [
            "dados.es.gov.br - Despesas-<ano>.csv (funcao Saude), via API DataStore",
            "dados.es.gov.br - OrcamentosExecucoes-<ano>.csv, via API DataStore",
            "dados.es.gov.br - Contratos - Ordem Cronologica de Pagamentos, via API DataStore",
        ],
        "kpis": build_kpis(serie_saude),
        "serie_saude_por_dia_do_ano": serie_saude,
        "ranking_executivo": build_ranking_executivo(),
        "prazos_executivo": build_prazos_executivo(),
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Salvo em {OUTPUT}")


if __name__ == "__main__":
    main()
