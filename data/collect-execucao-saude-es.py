#!/usr/bin/env python3
"""
Coleta a execucao orcamentario-financeira da funcao Saude no Estado do ES,
via API DataStore do CKAN (dados.es.gov.br), agregando por dia e por
Unidade Gestora.

Por que via DataStore e nao baixando o CSV bruto: o arquivo "Despesas-<ano>.csv"
do dataset "[Portal da Transparencia] Despesas - Execucao orcamentaria e
financeira" passa de 1 GB por ano (microdado por documento/evento, todos os
orgaos do Estado). O mesmo recurso esta indexado no DataStore do CKAN, que
permite filtrar (CodigoFuncao=10 = Saude) e selecionar apenas os campos
necessarios no servidor, paginando em blocos de ate 32000 linhas (teto do
proprio servidor). Isso reduz a coleta de ~1 GB/ano para poucas dezenas de MB.
A acao datastore_search_sql (SQL livre, com agregacao no servidor) esta
desabilitada nessa instancia; por isso a agregacao diaria e feita aqui, apos
a paginacao.
"""

import json
import time
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

API = "https://dados.es.gov.br/api/3/action/datastore_search"
PAGE_SIZE = 32000  # teto do servidor por requisicao

# resource_id do arquivo "Despesas-<ano>.csv" dentro do dataset de despesas
# (dataset id 99e16b13-0e6f-4504-8544-00de842ab1fd em dados.es.gov.br)
RESOURCES = {
    2023: "2c3328bd-329e-4db6-b742-630619b0dd65",
    2024: "b34ae52a-a739-412a-9bab-80f53ba72f4f",
    2025: "b9c229f8-884c-4fa6-85a9-15469172d6a8",
    2026: "1d4a0ae2-5e0c-41d2-8e36-45e092afe109",
}

FIELDS = "Data,CodigoUnidadeGestora,UnidadeGestora,ValorEmpenho,ValorLiquidado,ValorPago,ValorRap"
FILTERS = {"CodigoFuncao": "10"}  # 10 = Saude, classificacao funcional (mais confiavel que CodigoOrgao)

OUTPUT = Path(__file__).parent / "execucao-saude-es.json"


def fetch_page(resource_id, offset, retries=4):
    params = {
        "resource_id": resource_id,
        "fields": FIELDS,
        "filters": json.dumps(FILTERS),
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
    return None


def to_float(s):
    if not s:
        return 0.0
    s = s.strip()
    if not s:
        return 0.0
    return float(s.replace(".", "").replace(",", "."))


def parse_date(s):
    return datetime.strptime(s[:10], "%d/%m/%Y").strftime("%Y-%m-%d")


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
    daily = defaultdict(lambda: defaultdict(float))
    by_ug = defaultdict(lambda: defaultdict(float))
    ug_names = {}
    total_rows = 0

    for ano, rid in sorted(RESOURCES.items()):
        print(f"Coletando {ano} (resource {rid})...", flush=True)
        rows = collect_year(ano, rid)
        total_rows += len(rows)
        for r in rows:
            date = parse_date(r["Data"])
            emp = to_float(r["ValorEmpenho"])
            liq = to_float(r["ValorLiquidado"])
            pago = to_float(r["ValorPago"])
            rap = to_float(r["ValorRap"])

            daily[date]["empenhado"] += emp
            daily[date]["liquidado"] += liq
            daily[date]["pago"] += pago
            daily[date]["rap"] += rap

            ug_code = r["CodigoUnidadeGestora"]
            if ug_code:
                ug_names[ug_code] = r["UnidadeGestora"]
                key = f"{ano}|{ug_code}"
                by_ug[key]["liquidado"] += liq
                by_ug[key]["pago"] += pago

    daily_sorted = [
        {"data": d, **{k: round(v, 2) for k, v in vals.items()}}
        for d, vals in sorted(daily.items())
    ]

    ug_summary = []
    for key, vals in by_ug.items():
        ano, ug_code = key.split("|")
        ug_summary.append(
            {
                "ano": int(ano),
                "codigo_ug": ug_code,
                "unidade_gestora": ug_names.get(ug_code, ""),
                "liquidado": round(vals["liquidado"], 2),
                "pago": round(vals["pago"], 2),
                "gap": round(vals["liquidado"] - vals["pago"], 2),
            }
        )

    output = {
        "fonte": "dados.es.gov.br - Portal da Transparencia ES / SIGEFES, via API DataStore (CodigoFuncao=10, Saude)",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "total_linhas_coletadas": total_rows,
        "metodologia": (
            "Cada linha do microdado de despesas representa um evento datado "
            "(empenho, reforco/anulacao de empenho, liquidacao ou pagamento) de um "
            "documento (NE/NL/OB) de uma Unidade Gestora. Os valores diarios abaixo "
            "sao a soma desses eventos, filtrados pela funcao orcamentaria Saude "
            "(CodigoFuncao=10). O indicador de alerta e o gap acumulado "
            "(liquidado - pago): um estoque crescente e persistente de despesa "
            "reconhecida (liquidada) e nao paga, concentrado numa UG, e o sinal "
            "mais proximo de insuficiencia financeira que da para extrair desses "
            "dados publicos -- nao e o saldo de caixa do Tesouro, que nao e aberto."
        ),
        "diario": daily_sorted,
        "por_ug": sorted(ug_summary, key=lambda x: (x["ano"], -x["liquidado"])),
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(
        f"\nSalvo em {OUTPUT} "
        f"({len(daily_sorted)} dias, {len(ug_summary)} combinacoes ano/UG, "
        f"{total_rows} linhas coletadas)"
    )


if __name__ == "__main__":
    main()
