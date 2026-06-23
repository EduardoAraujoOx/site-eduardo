#!/usr/bin/env python3
"""
Coleta dados de ISS e ICMS do SICONFI (RREO Anexo 3) para cálculo do
coeficiente histórico da Reforma Tributária.

- ICMS: Estados (co_esfera=E), conta ICMSLiquidoExcetoTransferenciasEFUNDEB
- ISS: Municípios (co_esfera=M), conta ISSLiquidoExcetoTransferenciasEFUNDEB
- Coluna alvo: "TOTAL (ÚLTIMOS 12 MESES)" do período 6 (bimestre nov-dez)

Uso:
  python3 collect-siconfi.py           # coleta ICMS (estados) e ISS ES
  python3 collect-siconfi.py --all     # coleta também ISS BR (~11h)
"""

import json
import time
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ANOS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
TARGET_COL = "TOTAL (ÚLTIMOS 12 MESES)"
ICMS_COD = "ICMSLiquidoExcetoTransferenciasEFUNDEB"
ISS_COD = "ISSLiquidoExcetoTransferenciasEFUNDEB"
OUTPUT = Path(__file__).parent / "reforma-tributaria.json"


def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == retries - 1:
                return None
            time.sleep(2 ** attempt)
    return None


def get_entes():
    data = fetch(f"{BASE_URL}/entes")
    if not data:
        return [], []
    items = data["items"]
    states = [i for i in items if i["esfera"] == "E"]
    municipalities = [i for i in items if i["esfera"] == "M"]
    return states, municipalities


def get_valor(id_ente, esfera, ano, cod_conta):
    url = (
        f"{BASE_URL}/rreo"
        f"?an_exercicio={ano}&nr_periodo=6"
        f"&co_tipo_demonstrativo=RREO"
        f"&no_anexo=RREO-Anexo%2003"
        f"&co_esfera={esfera}&id_ente={id_ente}"
    )
    data = fetch(url)
    if not data:
        return None
    for item in data.get("items", []):
        if item["cod_conta"] == cod_conta and item["coluna"] == TARGET_COL:
            return item["valor"]
    return None


def collect(entities, esfera, cod_conta, label):
    results = {}  # {ano: {cod_ibge: valor}}
    total = len(entities) * len(ANOS)
    done = 0
    for entity in entities:
        cod = entity["cod_ibge"]
        nome = entity["ente"]
        uf = entity.get("uf", "")
        for ano in ANOS:
            done += 1
            val = get_valor(cod, esfera, ano, cod_conta)
            if val is not None:
                results.setdefault(str(ano), {})[str(cod)] = {
                    "ente": nome,
                    "uf": uf,
                    "valor": val,
                }
            pct = done / total * 100
            print(
                f"\r[{label}] {done}/{total} ({pct:.0f}%) — {nome} {ano}: "
                f"{'R$ {:,.0f}'.format(val) if val else 'N/A'}   ",
                end="",
                flush=True,
            )
            time.sleep(1.05)  # respect 1 req/sec limit
    print()
    return results


def aggregate(results):
    """Soma todos os valores por ano."""
    totals = {}
    for ano, entes in results.items():
        totals[ano] = sum(v["valor"] for v in entes.values())
    return totals


def aggregate_by_uf(results, uf):
    """Soma valores de um estado específico por ano."""
    totals = {}
    for ano, entes in results.items():
        totals[ano] = sum(
            v["valor"] for v in entes.values() if v["uf"] == uf
        )
    return totals


def main():
    collect_all_br = "--all" in sys.argv

    print("Buscando lista de entes do SICONFI...")
    states, municipalities = get_entes()
    es_munis = [m for m in municipalities if m["uf"] == "ES"]

    print(f"Estados: {len(states)} | Municípios ES: {len(es_munis)} | Municípios BR: {len(municipalities)}")

    # Load existing data if any
    existing = {}
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            existing = json.load(f)

    # --- ICMS: todos os estados ---
    print("\n=== Coletando ICMS (estados) ===")
    icms_raw = collect(states, "E", ICMS_COD, "ICMS")

    icms_br = aggregate(icms_raw)
    icms_es_by_year = {}
    for ano, entes in icms_raw.items():
        for cod, v in entes.items():
            if v["uf"] == "ES":
                icms_es_by_year[ano] = v["valor"]

    # --- ISS: municípios do ES ---
    print("\n=== Coletando ISS (municípios ES) ===")
    iss_es_raw = collect(es_munis, "M", ISS_COD, "ISS-ES")
    iss_es = aggregate(iss_es_raw)

    # --- ISS BR (opcional, demora ~11h) ---
    iss_br = existing.get("iss_br", {})
    if collect_all_br:
        print("\n=== Coletando ISS BR (todos os municípios) ===")
        iss_br_raw = collect(municipalities, "M", ISS_COD, "ISS-BR")
        iss_br = aggregate(iss_br_raw)

    # Build output
    output = {
        "fonte": "SICONFI - RREO Anexo 3 (Período 6, TOTAL ÚLTIMOS 12 MESES)",
        "unidade": "R$ (valores nominais)",
        "anos": ANOS,
        "icms_br": {str(a): icms_br.get(str(a)) for a in ANOS},
        "icms_es": {str(a): icms_es_by_year.get(str(a)) for a in ANOS},
        "iss_es": {str(a): iss_es.get(str(a)) for a in ANOS},
        "iss_br": {str(a): iss_br.get(str(a)) for a in ANOS},
        "detalhes": {
            "icms": icms_raw,
            "iss_es": iss_es_raw,
        },
    }

    with open(OUTPUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDados salvos em {OUTPUT}")
    print("\n=== RESUMO ===")
    print(f"{'Ano':<6} {'ICMS ES':>18} {'ICMS BR':>18} {'ISS ES':>18} {'ISS BR':>18}")
    for a in ANOS:
        a = str(a)
        def fmt(v): return f"R$ {v/1e9:.2f}B" if v else "N/D"
        print(f"{a:<6} {fmt(output['icms_es'].get(a)):>18} {fmt(output['icms_br'].get(a)):>18} {fmt(output['iss_es'].get(a)):>18} {fmt(output['iss_br'].get(a)):>18}")


if __name__ == "__main__":
    main()
