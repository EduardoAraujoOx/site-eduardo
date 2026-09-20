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


def _dia_para_mmdd(ano, dia_do_ano_int):
    from datetime import timedelta
    d = date(ano, 1, 1) + timedelta(days=dia_do_ano_int - 1)
    return d.strftime("%m-%d")


def build_serie_saude():
    """Serie diaria do Fundo Estadual de Saude especificamente (nao a funcao
    Saude inteira, que tambem inclui hospitais e superintendencias regionais).
    Usa execucao-executivo-es.json (coleta por UG) quando disponivel, que e'
    mais preciso e consistente com o resto do painel (ranking, KPIs), todos
    por UG; cai para a serie por funcao (execucao-saude-es.json) so' se a
    coleta do Executivo inteiro ainda nao tiver rodado."""
    path_executivo = DATA_DIR / "execucao-executivo-es.json"
    por_ano = defaultdict(list)
    cum = defaultdict(lambda: {"liq": 0.0, "pago": 0.0})

    if path_executivo.exists():
        serie = json.load(open(path_executivo))["series"]
        pontos_por_ano = defaultdict(list)
        for chave, info in serie.items():
            ano_str, ug = chave.split("|")
            if ug != FES_CODIGO_UG:
                continue
            pontos_por_ano[ano_str] = info["diario"]
        for ano, pontos in pontos_por_ano.items():
            for row in sorted(pontos, key=lambda p: p["data"]):
                cum[ano]["liq"] += row["liquidado"]
                cum[ano]["pago"] += row["pago"]
                por_ano[ano].append(
                    {"dia": dia_do_ano(row["data"]), "gap_acum": round(cum[ano]["liq"] - cum[ano]["pago"], 2)}
                )
    else:
        d = json.load(open(DATA_DIR / "execucao-saude-es.json"))
        for row in d["diario"]:
            ano = row["data"][:4]
            cum[ano]["liq"] += row["liquidado"]
            cum[ano]["pago"] += row["pago"]
            por_ano[ano].append(
                {"dia": dia_do_ano(row["data"]), "gap_acum": round(cum[ano]["liq"] - cum[ano]["pago"], 2)}
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

    # Comparativo no MESMO corte do calendario (ate' CUTOFF_MMDD em cada ano).
    # Cuidado: nao da' para pegar so' o ultimo ponto de "serie_saude", porque
    # anos ja encerrados (2023-2025) tem a serie inteira ate' 31/12 -- o ultimo
    # ponto deles e' o fechamento do ano, nao o corte de setembro. Precisa
    # filtrar explicitamente por CUTOFF_MMDD em cada ano antes de pegar o
    # ultimo valor acumulado.
    comparativo_corte = []
    for ano, pontos in serie_saude.items():
        pontos_ate_corte = [p for p in pontos if _dia_para_mmdd(int(ano), p["dia"]) <= CUTOFF_MMDD]
        if pontos_ate_corte:
            comparativo_corte.append({"ano": int(ano), "gap_no_corte": pontos_ate_corte[-1]["gap_acum"]})

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


def build_gap_mesmo_corte_por_ug():
    """Le' execucao-executivo-es.json (serie diaria, todo o Executivo, 2023-2026)
    e devolve, por UG, o gap acumulado (liquidado-pago) ate' o mesmo dia do ano
    (CUTOFF_MMDD) em cada ano -- comparacao ano-contra-ano de verdade, em vez de
    ano em curso contra fechamento do ano inteiro anterior."""
    path = DATA_DIR / "execucao-executivo-es.json"
    if not path.exists():
        return {}
    serie = json.load(open(path))["series"]
    resultado = defaultdict(dict)  # codigo_ug -> {ano: gap_no_corte}
    for chave, info in serie.items():
        ano_str, ug = chave.split("|")
        cum_liq = cum_pago = 0.0
        for ponto in info["diario"]:
            if ponto["data"][5:] > CUTOFF_MMDD:
                break
            cum_liq += ponto["liquidado"]
            cum_pago += ponto["pago"]
        resultado[ug][int(ano_str)] = cum_liq - cum_pago
    return resultado


def build_ranking_executivo():
    orc = json.load(open(DATA_DIR / "orcamentos-execucoes-es.json"))
    rows = [r for r in orc["por_ano"]["2026"]["registros"] if r["poder"] == "Executivo"]
    gap_2025 = {r["codigo_ug"]: r["liquidado_nao_pago"] for r in orc["por_ano"]["2025"]["registros"]}
    gap_2024 = {r["codigo_ug"]: r["liquidado_nao_pago"] for r in orc["por_ano"]["2024"]["registros"]}
    gap_mesmo_corte = build_gap_mesmo_corte_por_ug()

    ranking = []
    for r in rows:
        pct_pago = (r["pago"] / r["liquidado"] * 100) if r["liquidado"] else None
        g25 = gap_2025.get(r["codigo_ug"])
        g24 = gap_2024.get(r["codigo_ug"])

        # Comparacao ano-contra-ano no MESMO corte de calendario (ate' 18/09 em
        # todos os anos), a partir da serie diaria -- substitui a comparacao
        # contra o fechamento do ano inteiro anterior, que misturava ano
        # incompleto com ano encerrado. So' cai no fallback do fechamento
        # quando a UG nao aparece na serie diaria (nao deveria acontecer).
        corte = gap_mesmo_corte.get(r["codigo_ug"], {})
        corte_2026 = corte.get(2026)
        corte_2025 = corte.get(2025)
        if corte_2026 is not None and corte_2025 and corte_2025 >= 1_000_000:
            razao_2025 = corte_2026 / corte_2025 * 100
        else:
            # Piso de materialidade: com base de comparacao muito pequena
            # (< R$1 mi), a razao vira um numero enorme e sem sentido
            # comparativo (ex.: de R$5 mil para R$1 mi "e'" 20000%, mas so'
            # descreve que a UG saiu do irrelevante, nao uma deterioracao real).
            razao_2025 = (r["liquidado_nao_pago"] / g25 * 100) if g25 and g25 >= 1_000_000 else None

        # Espaco orcamentario: quanto da dotacao atualizada (autorizacao legal
        # para gastar) ja foi empenhado. Isso e' ortogonal ao gap de pagamento
        # -- uma UG pode ter caixa apertado com MUITO espaco de dotacao sobrando
        # (problema e' so' de fluxo de caixa), ou pode estar no limite da propria
        # autorizacao orcamentaria (problema e' tambem de orcamento, nao so' de
        # caixa). Nenhuma das duas leituras aparece no gap liquidado-pago sozinho.
        pct_dotacao = (r["empenhado"] / r["dotacao_atualizada"] * 100) if r["dotacao_atualizada"] else None
        ranking.append(
            {
                "codigo_ug": r["codigo_ug"],
                "unidade_gestora": r["unidade_gestora"],
                "dotacao_atualizada": r["dotacao_atualizada"],
                "liquidado": r["liquidado"],
                "pago": r["pago"],
                "gap": r["liquidado_nao_pago"],
                "rap": r["rap"],
                "pct_pago": round(pct_pago, 1) if pct_pago is not None else None,
                "pct_dotacao_empenhada": round(pct_dotacao, 1) if pct_dotacao is not None else None,
                "gap_fechamento_2025": g25,
                "gap_fechamento_2024": g24,
                "gap_mesmo_corte_2025": round(corte_2025, 2) if corte_2025 is not None else None,
                "razao_vs_fechamento_2025": round(razao_2025, 0) if razao_2025 is not None else None,
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
