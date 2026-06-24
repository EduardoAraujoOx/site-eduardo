#!/usr/bin/env python3
"""
Complemento: coleta dados de 2026 (período 2 = bimestre mar-abr, mais recente disponível).
Merges com o arquivo reforma-tributaria.json existente.
"""

import json
import time
import urllib.request
from pathlib import Path

BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ANO = 2026
PERIODO = 2  # bimestre mar-abr, mais recente disponível
TARGET_COL = "TOTAL (ÚLTIMOS 12 MESES)"
ICMS_COD = "ICMSLiquidoExcetoTransferenciasEFUNDEB"
ISS_COD = "ISSLiquidoExcetoTransferenciasEFUNDEB"
OUTPUT = Path(__file__).parent / "reforma-tributaria.json"


def fetch(url, retries=4):
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except Exception:
            if i < retries - 1:
                time.sleep(2 ** i)
    return None


def get_valor(id_ente, esfera, cod_conta):
    url = (
        f"{BASE_URL}/rreo"
        f"?an_exercicio={ANO}&nr_periodo={PERIODO}"
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


def main():
    print(f"Coletando dados de {ANO} (período {PERIODO})...")

    data = fetch(f"{BASE_URL}/entes")
    if not data:
        print("Erro ao buscar entes")
        return

    items = data["items"]
    states = [i for i in items if i["esfera"] == "E"]
    es_munis = [i for i in items if i["esfera"] == "M" and i.get("uf") == "ES"]

    print(f"Estados: {len(states)} | Municípios ES: {len(es_munis)}")

    # ICMS dos estados
    icms_br_total = 0
    icms_es = None
    icms_por_uf_2026 = {}  # {uf_sigla: valor}
    print("\n=== ICMS Estados ===")
    for i, state in enumerate(states):
        val = get_valor(state["cod_ibge"], "E", ICMS_COD)
        if val:
            icms_br_total += val
            uf = state.get("uf", "")
            if uf:
                icms_por_uf_2026[uf] = val
            if uf == "ES":
                icms_es = val
        print(f"  [{i+1}/{len(states)}] {state['ente']}: {'R$ {:,.0f}'.format(val) if val else 'N/A'}")
        time.sleep(1.05)

    # ISS municípios ES
    iss_es_total = 0
    print("\n=== ISS Municípios ES ===")
    for i, muni in enumerate(es_munis):
        val = get_valor(muni["cod_ibge"], "M", ISS_COD)
        if val:
            iss_es_total += val
        print(f"  [{i+1}/{len(es_munis)}] {muni['ente']}: {'R$ {:,.0f}'.format(val) if val else 'N/A'}")
        time.sleep(1.05)

    print(f"\n=== Resultados {ANO} (período {PERIODO}) ===")
    print(f"ICMS BR: R$ {icms_br_total/1e9:.2f}B")
    print(f"ICMS ES: R$ {(icms_es or 0)/1e9:.2f}B")
    print(f"ISS ES:  R$ {iss_es_total/1e9:.2f}B")

    # Load and update existing file
    existing = {}
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            existing = json.load(f)

    # Update anos list
    anos = existing.get("anos", [2019, 2020, 2021, 2022, 2023, 2024, 2025])
    if ANO not in anos:
        anos = sorted(anos + [ANO])
        existing["anos"] = anos

    existing.setdefault("icms_br", {})[str(ANO)] = icms_br_total if icms_br_total else None
    existing.setdefault("icms_es", {})[str(ANO)] = icms_es
    existing.setdefault("iss_es", {})[str(ANO)] = iss_es_total if iss_es_total else None
    existing.setdefault("periodo_usado", {})[str(ANO)] = PERIODO

    # Salva ICMS por UF para 2026 (necessário para tabela comparativa todas as UFs)
    icms_por_uf = existing.get("icms_por_uf", {})
    for uf, val in icms_por_uf_2026.items():
        icms_por_uf.setdefault(uf, {})[str(ANO)] = val
    existing["icms_por_uf"] = icms_por_uf

    with open(OUTPUT, "w") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"\nAtualizado: {OUTPUT}")


if __name__ == "__main__":
    main()
