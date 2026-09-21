#!/usr/bin/env python3
"""
Consolida os coletores (execucao-saude-es.json, orcamentos-execucoes-es.json,
ordem-cronologica-es.json, execucao-executivo-es.json, receita-executivo-es.json,
despesa-por-fonte-es.json) num unico JSON compacto, pronto para a pagina do
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

        # Um unico ano acima de 2025 pode so' significar que 2025 foi um ano
        # baixo para aquela UG (efeito de base), nao uma deterioracao real --
        # foi exatamente o que aconteceu com a Saude ao comparar com o
        # fechamento em vez do mesmo corte. Para nao repetir o erro num nivel
        # mais fino, verifica se 2026 tambem supera 2023 e 2024 no mesmo
        # corte: so' nesse caso e' um recorde historico de verdade, nao so'
        # uma comparacao favoravel contra um unico ano de referencia.
        anos_anteriores_corte = {a: v for a, v in corte.items() if a != 2026}
        eh_recorde_historico = (
            corte_2026 is not None
            and len(anos_anteriores_corte) >= 2
            and corte_2026 > max(anos_anteriores_corte.values())
        )

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
                "eh_recorde_historico": eh_recorde_historico,
                "historico_mesmo_corte": {str(a): round(v, 2) for a, v in sorted(corte.items())},
            }
        )
    return sorted(ranking, key=lambda x: -x["gap"])


def build_prazos_executivo():
    """Prazo de pagamento (NL->OB) por UG em 2026, com comparativo contra 2025
    (mesma base de dados, os dois unicos anos com cobertura sistematica). So'
    calcula a comparacao quando a UG tambem tem pelo menos 30 pagamentos em
    2025 -- abaixo disso a mediana de 2025 e' ruido, nao um prazo de referencia
    confiavel para julgar se 2026 piorou ou melhorou."""
    d = json.load(open(DATA_DIR / "ordem-cronologica-es.json"))
    por_ug_2025 = {r["codigo_ug"]: r for r in d["por_ug"] if r["ano"] == 2025 and r["n_pagamentos"] >= 30}
    rows = [r for r in d["por_ug"] if r["ano"] == 2026 and r["n_pagamentos"] >= 30]
    prazos = []
    for r in rows:
        r25 = por_ug_2025.get(r["codigo_ug"])
        prazos.append(
            {
                "codigo_ug": r["codigo_ug"],
                "unidade_gestora": r["unidade_gestora"],
                "n_pagamentos": r["n_pagamentos"],
                "dias_p50": r["dias_p50"],
                "dias_p75": r["dias_p75"],
                "dias_p90": r["dias_p90"],
                "dias_p50_2025": r25["dias_p50"] if r25 else None,
                "dias_p75_2025": r25["dias_p75"] if r25 else None,
                "dias_p90_2025": r25["dias_p90"] if r25 else None,
                "delta_p50": round(r["dias_p50"] - r25["dias_p50"], 1) if r25 else None,
            }
        )
    return sorted(prazos, key=lambda x: -x["dias_p90"])


PISO_ARRECADACAO_FONTE = 10_000_000  # abaixo disso a fonte fica de fora da tabela por fonte


def build_receita_executivo():
    """Consolida receita-executivo-es.json (arrecadacao por Fonte, TCE-ES) num
    KPI agregado e numa tabela por Fonte, comparando sempre no mesmo mes de
    corte entre os anos (nunca ano em curso contra fechamento de ano
    encerrado -- ver metodologia em collect-receita-executivo-es.py)."""
    path = DATA_DIR / "receita-executivo-es.json"
    if not path.exists():
        return None
    dados = json.load(open(path))
    fontes = dados["fontes_receita"]
    corte_mes = dados["corte_comparacao_mes"]

    def soma_ano(campo, ano):
        return sum(f[campo].get(str(ano), 0.0) for f in fontes)

    total_arrecadado = {ano: soma_ano("arrecadado_mesmo_corte_por_ano", ano) for ano in (2023, 2024, 2025, 2026)}
    total_previsto_2026 = soma_ano("previsao_atualizada_no_corte_por_ano", 2026)

    por_fonte = []
    for f in fontes:
        arr = f["arrecadado_mesmo_corte_por_ano"]
        arr_2026 = arr.get("2026", 0.0)
        arr_2025 = arr.get("2025", 0.0)
        if arr_2026 < PISO_ARRECADACAO_FONTE:
            continue
        razao_2025 = round(arr_2026 / arr_2025 * 100, 0) if arr_2025 >= PISO_ARRECADACAO_FONTE else None
        prev_2026 = f["previsao_atualizada_no_corte_por_ano"].get("2026", 0.0)

        # Um unico ano abaixo de 2025 pode so' refletir que 2025 foi um ano alto
        # para aquela fonte (efeito de base), nao uma fonte secando de verdade --
        # mesma logica ja aplicada ao estoque represado por UG. So' marca como
        # minimo historico quando 2026 tambem fica abaixo de 2023 e 2024.
        anos_anteriores = {a: v for a, v in arr.items() if a != "2026" and v >= PISO_ARRECADACAO_FONTE}
        eh_minimo_historico = (
            len(anos_anteriores) >= 2 and arr_2026 < min(anos_anteriores.values())
        )

        por_fonte.append(
            {
                "fonte_key": f["fonte_key"],
                "nome_fonte": f["nome_fonte"],
                "eh_minimo_historico": eh_minimo_historico,
                "arrecadado_2026": round(arr_2026, 2),
                "previsao_atualizada_2026": round(prev_2026, 2),
                "pct_previsao_realizada": round(arr_2026 / prev_2026 * 100, 1) if prev_2026 else None,
                "arrecadado_mesmo_corte_por_ano": {a: round(v, 2) for a, v in arr.items()},
                "razao_vs_2025": razao_2025,
            }
        )
    por_fonte.sort(key=lambda x: -x["arrecadado_2026"])

    return {
        "corte_mes": corte_mes,
        "gerado_em": dados["gerado_em"],
        "total_arrecadado_mesmo_corte_por_ano": {str(a): round(v, 2) for a, v in total_arrecadado.items()},
        "total_previsao_atualizada_2026": round(total_previsto_2026, 2),
        "pct_previsao_realizada": round(total_arrecadado[2026] / total_previsto_2026 * 100, 1)
        if total_previsto_2026
        else None,
        "por_fonte": por_fonte,
    }


PISO_ESPACO_FISCAL = 10_000_000  # abaixo disso a fonte fica de fora da tabela cruzada


def build_espaco_fiscal_por_fonte():
    """Cruza despesa-por-fonte-es.json com receita-executivo-es.json pelo
    CodigoFonte (o codigo reduzido de 3 digitos, ex.: "500"), nao pelo nome
    do detalhamento. Testado empiricamente antes de decidir: cruzar pelo
    nome do detalhamento (o nivel mais fino, que distingue por exemplo a
    parcela de uma Fonte vinculada a' Saude da parcela vinculada ao MDE) so'
    bateu 24 das ~67 fontes de receita, porque as duas bases divergem em
    pontuacao, acentuacao e ate' caracteres corrompidos ("?" no lugar de
    travessao em alguns nomes de despesa) -- cobertura baixa demais para
    uma tabela publica. O CodigoFonte reduzido, em compensacao, e' o MESMO
    numero nas duas bases (confirmado: 54 dos ~55-60 codigos batem em
    ambas), entao o cruzamento agrega despesa e receita no nivel da Fonte
    inteira, nao do detalhamento -- perde a distincao mais fina dentro de
    uma mesma Fonte, mas ganha cobertura quase completa em vez de parcial.

    Mostra, por Fonte, quanto da previsao atualizada de receita ja foi
    comprometido em despesa liquidada no mesmo corte: um sinal de espaco
    ORCAMENTARIO por fonte (nao de caixa disponivel, que o painel nao tem),
    sem nenhuma projecao estimada -- so' numeros ja publicados (previsao
    atualizada oficial do governo e despesa liquidada ate' a mesma data).

    Conferido linha a linha (nao so' a cobertura agregada) antes de dar
    esta tabela por definitiva: em valor, a despesa casada cobre 100% do
    liquidado do Executivo no corte e a receita casada cobre 99,94% do
    arrecadado -- as fontes sem par somam menos de R$ 13 milhoes contra
    R$ 19,65 bilhoes arrecadados, residuo irrelevante. Duas ressalvas reais
    sobrevivem a essa checagem, e ficam documentadas em vez de escondidas:
    (1) a fonte 546 (Fundeb - Complementacao da Uniao) tem despesa real sem
    nenhuma previsao de receita registrada nessa base -- tratado abaixo
    como "sem_previsao_com_despesa", nao como ausencia neutra de dado; (2)
    agregar pelo CodigoFonte mistura, dentro da mesma fonte 500, receita
    geral de impostos com pagamento de beneficios previdenciarios do plano
    financeiro (regime de reparticao, cobertos pelo tesouro geral por
    desenho), duas naturezas fiscais diferentes sob o mesmo percentual."""
    path_despesa = DATA_DIR / "despesa-por-fonte-es.json"
    path_receita = DATA_DIR / "receita-executivo-es.json"
    if not path_despesa.exists() or not path_receita.exists():
        return None

    despesa = json.load(open(path_despesa))
    receita = json.load(open(path_receita))

    despesa_por_codigo = defaultdict(lambda: {"liquidado": 0.0, "empenhado": 0.0, "nomes": []})
    for d in despesa["despesa_por_fonte"]:
        desp_2026 = d["despesa_mesmo_corte_por_ano"].get("2026", {})
        agr = despesa_por_codigo[d["codigo_fonte"]]
        agr["liquidado"] += desp_2026.get("liquidado", 0.0)
        agr["empenhado"] += desp_2026.get("empenhado", 0.0)
        agr["nomes"].append(d["detalhamento_fonte"])

    receita_por_codigo = defaultdict(lambda: {"previsao": 0.0, "arrecadado": 0.0, "nomes": []})
    for f in receita["fontes_receita"]:
        agr = receita_por_codigo[f["codigo_fonte_reduzida"]]
        agr["previsao"] += f["previsao_atualizada_no_corte_por_ano"].get("2026", 0.0)
        agr["arrecadado"] += f["arrecadado_mesmo_corte_por_ano"].get("2026", 0.0)
        agr["nomes"].append(f["nome_fonte"])

    linhas = []
    for codigo, d_agr in despesa_por_codigo.items():
        r_agr = receita_por_codigo.get(codigo)
        if r_agr is None:
            continue
        liquidado = d_agr["liquidado"]
        empenhado = d_agr["empenhado"]
        previsao = r_agr["previsao"]
        arrecadado = r_agr["arrecadado"]
        if liquidado < PISO_ESPACO_FISCAL and arrecadado < PISO_ESPACO_FISCAL:
            continue
        # Rotulo: o nome mais curto entre os vistos para essa Fonte costuma
        # ser o nome-base (ex.: "Recursos nao vinculados de Impostos"),
        # nao um sub-detalhamento especifico mais longo.
        nome = min(d_agr["nomes"] + r_agr["nomes"], key=len)
        # Distingue duas leituras bem diferentes de "sem percentual": uma
        # Fonte sem despesa relevante (nada a medir) de uma Fonte com
        # despesa real mas sem previsao de receita registrada nessa base --
        # esse segundo caso e' em si um sinal de atencao, nao uma ausencia
        # de dado neutra, e precisa aparecer marcado, nao como traco mudo.
        sem_previsao_com_despesa = previsao == 0 and liquidado >= PISO_ESPACO_FISCAL
        linhas.append(
            {
                "codigo_fonte": codigo,
                "nome_fonte": nome,
                "receita_arrecadada_2026": round(arrecadado, 2),
                "receita_previsao_atualizada_2026": round(previsao, 2),
                # Falta receber ate' dezembro, assumindo que a previsao
                # atualizada se mantem (e' o mesmo pressuposto ja embutido em
                # comparar liquidado contra ela) -- residuo, nao projecao.
                "receita_falta_receber": round(previsao - arrecadado, 2),
                "despesa_empenhada_2026": round(empenhado, 2),
                "despesa_liquidada_2026": round(liquidado, 2),
                # Espaco que ainda cabe gastar dentro da propria previsao de
                # receita da fonte (o teto legal para despesa vinculada);
                # negativo = ja gastou mais do que a fonte deve arrecadar
                # no ano inteiro.
                "espaco_restante_para_gastar": round(previsao - liquidado, 2),
                "pct_previsao_ja_liquidado": round(liquidado / previsao * 100, 1) if previsao else None,
                "sem_previsao_com_despesa": sem_previsao_com_despesa,
            }
        )
    # Fontes com despesa mas sem previsao registrada sobem para o topo: e'
    # um sinal mais forte que precisa aparecer, nao afundar como se fosse 0%.
    linhas.sort(key=lambda x: (0, 0) if x["sem_previsao_com_despesa"] else (1, -(x["pct_previsao_ja_liquidado"] or 0)))

    # Total do Executivo inteiro, somando TODAS as fontes de cada lado (nao
    # so' as casadas): a pergunta "no agregado, a despesa cabe na receita
    # prevista?" nao depende de nenhuma fonte especifica ter encontrado par
    # do outro lado -- e' simplesmente a soma de tudo que existe em cada base.
    total_receita_arrecadada = sum(r["arrecadado"] for r in receita_por_codigo.values())
    total_receita_previsao = sum(r["previsao"] for r in receita_por_codigo.values())
    total_despesa_liquidada = sum(d["liquidado"] for d in despesa_por_codigo.values())
    total_despesa_empenhada = sum(d["empenhado"] for d in despesa_por_codigo.values())

    return {
        "corte_mes": despesa["corte_comparacao_mes"],
        "gerado_em": despesa["gerado_em"],
        "cobertura": {
            "fontes_casadas": len(linhas),
            "fontes_receita_sem_correspondencia": len(set(receita_por_codigo) - set(despesa_por_codigo)),
            "fontes_despesa_sem_correspondencia": len(set(despesa_por_codigo) - set(receita_por_codigo)),
        },
        "total": {
            "receita_arrecadada": round(total_receita_arrecadada, 2),
            "receita_previsao_atualizada": round(total_receita_previsao, 2),
            "receita_falta_receber": round(total_receita_previsao - total_receita_arrecadada, 2),
            "despesa_liquidada": round(total_despesa_liquidada, 2),
            "despesa_empenhada": round(total_despesa_empenhada, 2),
            "espaco_restante_para_gastar": round(total_receita_previsao - total_despesa_liquidada, 2),
            "pct_previsao_ja_liquidado": round(total_despesa_liquidada / total_receita_previsao * 100, 1)
            if total_receita_previsao
            else None,
        },
        "por_fonte": linhas,
    }


def main():
    serie_saude = build_serie_saude()
    output = {
        "gerado_em": datetime.utcnow().isoformat() + "Z",
        "fontes": [
            "dados.es.gov.br - Despesas-<ano>.csv (funcao Saude), via API DataStore",
            "dados.es.gov.br - OrcamentosExecucoes-<ano>.csv, via API DataStore",
            "dados.es.gov.br - Contratos - Ordem Cronologica de Pagamentos, via API DataStore",
            "dados.es.gov.br - pacote receitas-e-despesas-estaduais (TCE-ES, CidadES)",
        ],
        "kpis": build_kpis(serie_saude),
        "serie_saude_por_dia_do_ano": serie_saude,
        "ranking_executivo": build_ranking_executivo(),
        "prazos_executivo": build_prazos_executivo(),
        "receita_executivo": build_receita_executivo(),
        "espaco_fiscal_por_fonte": build_espaco_fiscal_por_fonte(),
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Salvo em {OUTPUT}")


if __name__ == "__main__":
    main()
