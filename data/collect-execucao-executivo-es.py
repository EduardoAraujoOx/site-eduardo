#!/usr/bin/env python3
"""
Generaliza collect-execucao-saude-es.py para o Poder Executivo inteiro (nao
so' a funcao Saude), agregando por dia e por Unidade Gestora, 2023-2026.

Em vez de filtrar por CodigoFuncao, filtra pela lista de UGs do Executivo
de cada ano (ja classificadas em orcamentos-execucoes-es.json pelo numero
de digitos do codigo de UG). Isso permite, para qualquer UG, comparar o
gap acumulado no MESMO corte de calendario entre anos -- e nao so' contra
o fechamento do ano inteiro anterior, que e' o que o ranking do painel
usa hoje por falta dessa granularidade diaria fora da Saude.

Volume esperado: ~950 mil linhas/ano (quase todo o total de ~1 milhao/ano,
ja' que so' exclui Legislativo/TCE/Judiciario/MP/Defensoria). Roda como
job de fundo; pode levar dezenas de minutos.
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
    2023: "2c3328bd-329e-4db6-b742-630619b0dd65",
    2024: "b34ae52a-a739-412a-9bab-80f53ba72f4f",
    2025: "b9c229f8-884c-4fa6-85a9-15469172d6a8",
    2026: "1d4a0ae2-5e0c-41d2-8e36-45e092afe109",
}

FIELDS = "Data,CodigoUnidadeGestora,UnidadeGestora,ValorEmpenho,ValorLiquidado,ValorPago,ValorRap"

DATA_DIR = Path(__file__).parent
OUTPUT = DATA_DIR / "execucao-executivo-es.json"


def executivo_ugs_do_ano(ano):
    orc = json.load(open(DATA_DIR / "orcamentos-execucoes-es.json"))
    registros = orc["por_ano"][str(ano)]["registros"]
    return [r["codigo_ug"] for r in registros if r["poder"] == "Executivo"]


def fetch_page(resource_id, ugs, offset, retries=4):
    params = {
        "resource_id": resource_id,
        "fields": FIELDS,
        "filters": json.dumps({"CodigoUnidadeGestora": ugs}),
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
    return datetime.strptime(s[:10], "%d/%m/%Y").strftime("%Y-%m-%d")


def collect_year(ano, resource_id, ugs):
    offset = 0
    rows = []
    while True:
        data = fetch_page(resource_id, ugs, offset)
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
    # (ano, ug_code) -> data -> {empenhado, liquidado, pago, rap}
    daily_por_ug = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    ug_names = {}
    total_rows = 0

    for ano, rid in sorted(RESOURCES.items()):
        ugs = executivo_ugs_do_ano(ano)
        print(f"Coletando {ano} (resource {rid}, {len(ugs)} UGs do Executivo)...", flush=True)
        rows = collect_year(ano, rid, ugs)
        total_rows += len(rows)
        for r in rows:
            date = parse_date(r["Data"])
            ug_code = r["CodigoUnidadeGestora"]
            if not ug_code:
                continue
            ug_names[ug_code] = r["UnidadeGestora"]
            bucket = daily_por_ug[(ano, ug_code)][date]
            bucket["empenhado"] += to_float(r["ValorEmpenho"])
            bucket["liquidado"] += to_float(r["ValorLiquidado"])
            bucket["pago"] += to_float(r["ValorPago"])
            bucket["rap"] += to_float(r["ValorRap"])

    saida = {}
    for (ano, ug_code), dias in daily_por_ug.items():
        chave = f"{ano}|{ug_code}"
        saida[chave] = {
            "ano": ano,
            "codigo_ug": ug_code,
            "unidade_gestora": ug_names.get(ug_code, ""),
            "diario": [
                {"data": d, **{k: round(v, 2) for k, v in vals.items()}}
                for d, vals in sorted(dias.items())
            ],
        }

    output = {
        "fonte": "dados.es.gov.br - Despesas-<ano>.csv, todo o Poder Executivo, via API DataStore",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "total_linhas_coletadas": total_rows,
        "metodologia": (
            "Mesma logica de collect-execucao-saude-es.py, generalizada para "
            "todas as UGs do Executivo (nao so' funcao Saude). Permite comparar "
            "o gap acumulado no mesmo corte de calendario entre anos, para "
            "qualquer UG, em vez de comparar ano em curso contra fechamento do "
            "ano inteiro anterior."
        ),
        "series": saida,
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nSalvo em {OUTPUT} ({len(saida)} combinacoes ano/UG, {total_rows} linhas coletadas)")


if __name__ == "__main__":
    main()
