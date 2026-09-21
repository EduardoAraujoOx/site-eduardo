#!/usr/bin/env python3
"""
Coleta o dataset "Contratos - Ordem Cronologica de Pagamentos" do ES, que
pareia, por documento, a data de emissao da nota de liquidacao (NL) e da
ordem bancaria (OB) do mesmo pagamento. Diferente do microdado de Despesas
(um livro-razao de eventos onde um unico empenho guarda-chuva pode gerar
centenas de NLs e OBs sem correspondencia 1-para-1 obvia), aqui o prazo
liquidacao -> pagamento vem pronto por linha, o que permite calcular a
distribuicao real de dias entre NL e OB (mediana, p75, p90) por UG.

Limitacao metodologica (censura a direita): a base so registra pagamentos
que ja chegaram a OB. Obrigacoes liquidadas e ainda nao pagas nao aparecem
aqui -- por isso os meses mais recentes tendem a subestimar o prazo real.
Esse indicador deve ser lido em conjunto com o gap liquidado-nao-pago da
execucao orcamentaria (ver collect-execucao-saude-es.py e
collect-orcamentos-execucoes-es.py), nao isoladamente.

2024 tem so ~750 linhas nesse dataset (vs. ~130-190 mil em 2025 e 2026),
sinal de que a publicacao so passou a ser sistematica a partir de 2025;
por isso a comparacao interanual usa 2025 e 2026.

Alem do agregado anual por UG (por_ug), tambem agrega por (UG, ano, mes)
em por_ug_mes -- ano e mes da DataEmissaoNL (nao da OB, nem o "ano" do
recurso baixado), para manter a mesma leitura de censura a direita ja
usada no resto do painel (um NL de um mes recente que ainda nao virou OB
fica de fora daquele mes, entao meses recentes tendem a subestimar o
prazo, nao a superestimar). Usar o ano real da NL, e nao o "ano" do
recurso da API, importa aqui: o recurso de um exercicio inclui OBs de
janeiro pagando NLs de dezembro do ano anterior (NL sempre antecede OB),
entao rotular pelo ano do recurso classificaria esses casos como
dezembro do ano seguinte, um mes que ainda nem tinha acontecido. Isso
permite comparar UG a UG, mes a mes, 2025 contra 2026, em vez de só um
numero por ano inteiro.
"""

import json
import time
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

API = "https://dados.es.gov.br/api/3/action/datastore_search"
PAGE_SIZE = 32000

RESOURCES = {
    2025: "d25a8ba1-03d1-4fb1-b86a-9fdc0b841dcb",
    2026: "8bff110c-0f80-4eff-bc79-503a752bf923",
}

FIELDS = "CodigoUg,UnidadeGestora,DataEmissaoNL,DataEmissaoOB,ValorOB,CodigoOB,CodigoNE"

OUTPUT = Path(__file__).parent / "ordem-cronologica-es.json"


def fetch_page(resource_id, offset, retries=4):
    params = {
        "resource_id": resource_id,
        "fields": FIELDS,
        "limit": PAGE_SIZE,
        "offset": offset,
    }
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.loads(r.read())
        except Exception:
            if i < retries - 1:
                time.sleep(2 ** i)
            else:
                raise


def to_float(s):
    if not s:
        return 0.0
    s = s.strip()
    return float(s.replace(".", "").replace(",", ".")) if s else 0.0


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%d/%m/%Y")
    except ValueError:
        return None


def is_executivo(codigo_ug):
    return len(codigo_ug) == 6


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p
    f, c = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def collect_year(ano, resource_id):
    offset = 0
    rows = []
    while True:
        data = fetch_page(resource_id, offset)
        result = data["result"]
        recs = result["records"]
        total = result["total"]
        rows.extend(recs)
        offset += len(recs)
        print(f"  {ano}: {offset}/{total}", flush=True)
        if offset >= total or not recs:
            break
    return rows


def main():
    dias_por_ug = defaultdict(list)  # (ano, ug_code) -> [dias, ...]
    dias_por_ug_mes = defaultdict(list)  # (ano, mes, ug_code) -> [dias, ...]
    dias_geral = defaultdict(list)  # ano -> [dias, ...]
    ug_names = {}
    sem_data_ob = defaultdict(int)  # ano -> contagem (censura a direita)
    valor_por_ug = defaultdict(float)
    hoje = datetime.now()
    datas_futuras_descartadas = 0

    for ano, rid in sorted(RESOURCES.items()):
        print(f"Coletando {ano} (resource {rid})...", flush=True)
        rows = collect_year(ano, rid)
        for r in rows:
            ug = r["CodigoUg"]
            if not ug or not is_executivo(ug):
                continue
            ug_names[ug] = r["UnidadeGestora"]
            nl = parse_date(r["DataEmissaoNL"])
            ob = parse_date(r["DataEmissaoOB"])
            if ob is None:
                sem_data_ob[ano] += 1
                continue
            if nl is None:
                continue
            if nl > hoje or ob > hoje:
                # DataEmissaoNL/OB no futuro so' pode ser erro de digitacao na
                # base de origem (ex.: ano trocado): descarta, senao um unico
                # registro corrompido pode virar um mes inteiro de 2026 que
                # ainda nem aconteceu, com um "prazo" de centenas de dias.
                datas_futuras_descartadas += 1
                continue
            dias = (ob - nl).days
            if dias < 0:
                continue  # descarta inconsistencias de data
            dias_por_ug[(ano, ug)].append(dias)
            # Chave pelo ano/mes REAIS da NL, nao pelo "ano" do recurso baixado:
            # o recurso de um exercicio inclui OBs de janeiro pagando NLs de
            # dezembro do ano anterior (normal, NL sempre antecede OB), entao
            # usar o "ano" do recurso aqui rotularia esses dezembros como se
            # fossem do ano seguinte (ex.: dezembro/2025 aparecendo como
            # dezembro/2026, que ainda nem tinha acontecido).
            dias_por_ug_mes[(nl.year, nl.month, ug)].append(dias)
            dias_geral[ano].append(dias)
            valor_por_ug[(ano, ug)] += to_float(r["ValorOB"])

    print(f"Descartados por data no futuro (NL ou OB pos-hoje): {datas_futuras_descartadas}")

    por_ug = []
    for (ano, ug), dias in dias_por_ug.items():
        dias.sort()
        por_ug.append(
            {
                "ano": ano,
                "codigo_ug": ug,
                "unidade_gestora": ug_names.get(ug, ""),
                "n_pagamentos": len(dias),
                "valor_total_ob": round(valor_por_ug[(ano, ug)], 2),
                "dias_p50": round(percentile(dias, 0.5), 1),
                "dias_p75": round(percentile(dias, 0.75), 1),
                "dias_p90": round(percentile(dias, 0.9), 1),
                "dias_medio": round(sum(dias) / len(dias), 1),
            }
        )

    por_ug_mes = []
    for (ano, mes, ug), dias in dias_por_ug_mes.items():
        dias.sort()
        por_ug_mes.append(
            {
                "ano": ano,
                "mes": mes,
                "codigo_ug": ug,
                "unidade_gestora": ug_names.get(ug, ""),
                "n_pagamentos": len(dias),
                "dias_p50": round(percentile(dias, 0.5), 1),
                "dias_p75": round(percentile(dias, 0.75), 1),
                "dias_p90": round(percentile(dias, 0.9), 1),
            }
        )

    geral = []
    for ano, dias in dias_geral.items():
        dias.sort()
        geral.append(
            {
                "ano": ano,
                "n_pagamentos": len(dias),
                "sem_data_ob_censurado": sem_data_ob[ano],
                "dias_p50": round(percentile(dias, 0.5), 1),
                "dias_p75": round(percentile(dias, 0.75), 1),
                "dias_p90": round(percentile(dias, 0.9), 1),
                "dias_medio": round(sum(dias) / len(dias), 1),
            }
        )

    output = {
        "fonte": "dados.es.gov.br - [Portal da Transparencia] Contratos - Ordem Cronologica de Pagamentos, via API DataStore",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "escopo": "Poder Executivo (UGs com codigo de 6 digitos)",
        "metodologia": (
            "Dias = DataEmissaoOB - DataEmissaoNL, por documento. Sujeito a "
            "censura a direita: linhas sem DataEmissaoOB (ainda nao pagas) sao "
            "contadas em 'sem_data_ob_censurado' e excluidas do calculo de dias. "
            "2024 tem cobertura muito baixa (~750 linhas) e foi excluido da "
            "comparacao interanual; usar 2025 vs 2026. Em por_ug_mes, ano e "
            "mes sao os da DataEmissaoNL (nao da OB, nem o 'ano' do recurso "
            "da API), pela mesma razao de censura a direita: um NL de um mes "
            "recente sem OB ainda fica de fora daquele mes. Linhas com "
            "DataEmissaoNL ou DataEmissaoOB no futuro "
            "(impossivel, so' pode ser erro de digitacao na base de origem, "
            "como um ano trocado) sao descartadas -- contagem em "
            "'datas_futuras_descartadas'."
        ),
        "datas_futuras_descartadas": datas_futuras_descartadas,
        "geral_por_ano": sorted(geral, key=lambda x: x["ano"]),
        "por_ug": sorted(por_ug, key=lambda x: (x["ano"], -x["dias_p90"])),
        "por_ug_mes": sorted(por_ug_mes, key=lambda x: (x["codigo_ug"], x["ano"], x["mes"])),
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Salvo em {OUTPUT} ({len(por_ug)} combinacoes ano/UG, {len(por_ug_mes)} combinacoes ano/mes/UG)")


if __name__ == "__main__":
    main()
