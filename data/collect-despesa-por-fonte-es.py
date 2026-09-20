#!/usr/bin/env python3
"""
Coleta despesa (empenhado/liquidado/pago) do Poder Executivo por Fonte de
recurso, 2023-2026, a partir do MESMO microdado bruto de Despesas-<ano>.csv
ja usado em collect-execucao-executivo-es.py -- mas agora incluindo os
campos CodigoFonte/Fonte/CodigoDetalhamentoFonte/DetalhamentoFonte, que a
coleta anterior nao pedia.

Objetivo: permitir cruzar despesa com receita pela mesma Fonte, para
responder se uma Fonte especifica esta' ficando sem espaco fiscal (despesa
empenhada/liquidada perto ou acima da receita prevista/arrecadada daquela
fonte), nao so' olhar os dois lados separados como ja' existia no painel.

Por que nao reaproveitar execucao-executivo-es.json: aquela coleta nao
pediu os campos de Fonte (nao havia necessidade na epoca), entao precisa
de uma nova varredura do mesmo recurso bruto. Como aqui so' interessa o
acumulado ate' um corte, nao a serie diaria completa, agrega direto durante
a coleta em vez de guardar um ponto por dia como o outro coletor faz --
saida bem mais compacta.

Corte: para comparar com a receita (que so' publica ate' um mes fechado,
com defasagem maior que a despesa), usa o MESMO mes de corte da receita
(lido de receita-executivo-es.json) e filtra despesa ate' o ULTIMO DIA
desse mes em cada ano -- nao o corte de 18/09 usado no resto do painel,
que misturaria um ponto do ano mais adiantado do lado da despesa com um
ponto mais atrasado do lado da receita.

Fonte de recurso identificada por (CodigoFonte, DetalhamentoFonte) --
DetalhamentoFonte (nome) e' o campo usado para cruzar com a receita do
TCE-ES, porque os codigos numericos de detalhamento nao sao os mesmos
entre as duas bases (ver collect-receita-executivo-es.py), so' os nomes
batem.
"""

import calendar
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

FIELDS = "Data,CodigoUnidadeGestora,ValorEmpenho,ValorLiquidado,ValorPago,CodigoFonte,Fonte,DetalhamentoFonte"

DATA_DIR = Path(__file__).parent
OUTPUT = DATA_DIR / "despesa-por-fonte-es.json"


def executivo_ugs_do_ano(ano):
    orc = json.load(open(DATA_DIR / "orcamentos-execucoes-es.json"))
    registros = orc["por_ano"][str(ano)]["registros"]
    return [r["codigo_ug"] for r in registros if r["poder"] == "Executivo"]


def corte_mmdd_do_ano(ano, corte_mes):
    ultimo_dia = calendar.monthrange(ano, corte_mes)[1]
    return f"{corte_mes:02d}-{ultimo_dia:02d}"


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
                time.sleep(2**i)
            else:
                raise


def to_float(s):
    if not s:
        return 0.0
    s = s.strip()
    return float(s.replace(".", "").replace(",", ".")) if s else 0.0


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
    receita_path = DATA_DIR / "receita-executivo-es.json"
    if not receita_path.exists():
        raise RuntimeError("Rode collect-receita-executivo-es.py primeiro (precisa do corte de comparacao).")
    corte_mes = json.load(open(receita_path))["corte_comparacao_mes"]

    # (ano, fonte_key) -> {empenhado, liquidado, pago}
    acumulado = defaultdict(lambda: defaultdict(float))
    fonte_nomes = {}
    total_rows = 0

    for ano, rid in sorted(RESOURCES.items()):
        ugs = executivo_ugs_do_ano(ano)
        corte_mmdd = corte_mmdd_do_ano(ano, corte_mes)
        print(f"Coletando {ano} (resource {rid}, {len(ugs)} UGs, corte ate' {corte_mmdd})...", flush=True)
        rows = collect_year(ano, rid, ugs)
        total_rows += len(rows)
        for r in rows:
            data_mmdd = r["Data"][3:5] + "-" + r["Data"][0:2]
            if data_mmdd > corte_mmdd:
                continue
            codigo_fonte = r["CodigoFonte"] or ""
            detalhamento = (r["DetalhamentoFonte"] or r["Fonte"] or "SEM FONTE").strip()
            fonte_key = f"{codigo_fonte}|{detalhamento.upper()}"
            fonte_nomes[fonte_key] = detalhamento
            bucket = acumulado[(ano, fonte_key)]
            bucket["empenhado"] += to_float(r["ValorEmpenho"])
            bucket["liquidado"] += to_float(r["ValorLiquidado"])
            bucket["pago"] += to_float(r["ValorPago"])

    por_fonte = defaultdict(dict)  # fonte_key -> {ano: {empenhado, liquidado, pago}}
    for (ano, fonte_key), vals in acumulado.items():
        por_fonte[fonte_key][ano] = {k: round(v, 2) for k, v in vals.items()}

    saida = []
    for fonte_key, nome in fonte_nomes.items():
        codigo_fonte, _ = fonte_key.split("|", 1)
        anos_dados = por_fonte.get(fonte_key, {})
        saida.append(
            {
                "fonte_key": fonte_key,
                "codigo_fonte": codigo_fonte,
                "detalhamento_fonte": nome,
                "despesa_mesmo_corte_por_ano": {str(a): anos_dados.get(a, {}) for a in RESOURCES},
            }
        )
    saida.sort(key=lambda x: -x["despesa_mesmo_corte_por_ano"].get("2026", {}).get("liquidado", 0))

    output = {
        "fonte": "dados.es.gov.br - Despesas-<ano>.csv, todo o Poder Executivo, via API DataStore",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "escopo": "Poder Executivo",
        "corte_comparacao_mes": corte_mes,
        "total_linhas_coletadas": total_rows,
        "metodologia": (
            "Empenhado/liquidado/pago acumulados desde 1o de janeiro ate' o "
            "ultimo dia do mes de corte (o mesmo mes de corte usado na receita, "
            "por causa da defasagem maior de publicacao da receita), em cada "
            "ano. Fonte identificada por (CodigoFonte, DetalhamentoFonte em "
            "maiusculas) -- o nome, nao o codigo numerico do detalhamento, "
            "porque e' o campo que bate com a nomenclatura da base de receita "
            "do TCE-ES."
        ),
        "despesa_por_fonte": saida,
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nSalvo em {OUTPUT} ({len(saida)} fontes de despesa, {total_rows} linhas coletadas, corte mes={corte_mes})")


if __name__ == "__main__":
    main()
