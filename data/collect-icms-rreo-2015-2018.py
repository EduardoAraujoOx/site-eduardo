#!/usr/bin/env python3
"""
Estende a série de ICMS estadual (RREO Anexo 3) de 2019-2025 para 2015-2018,
para o Estudo 11 (série histórica + projeção do IBS total, Brasil).

Só 27 UFs por ano, então RREO é suficiente (ao contrário do ISS municipal,
onde a cobertura do RREO é ruim — ver collect-iss-dca-2015-2018.py). A
reconciliação já feita em data/build-reconciliacao-dca-rreo.py mostra que o
ICMS bruto do RREO bate com o bruto do DCA (diff < 1%), então estender via
RREO aqui é equivalente a usar DCA, sem precisar lidar com a mudança de
código de conta do DCA entre anos.

Grava em reforma-tributaria.json:icms_por_uf e :icms_br (preserva 2019-2026
já existentes).

Uso: python3 collect-icms-rreo-2015-2018.py
"""

import json
import time
import urllib.request
from pathlib import Path

BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ANOS = [2015, 2016, 2017, 2018]
TARGET_COL = "TOTAL (ÚLTIMOS 12 MESES)"
ICMS_COD = "ICMSLiquidoExcetoTransferenciasEFUNDEB"
OUTPUT = Path(__file__).parent / "reforma-tributaria.json"

# O campo "uf" retornado por /entes para esfera=E vem sempre como "BR" (não
# é a sigla do estado) — o cod_ibge de 2 dígitos é que identifica a UF.
COD_IBGE_TO_UF = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL",
    28: "SE", 29: "BA",
    31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS",
    50: "MS", 51: "MT", 52: "GO", 53: "DF",
}


def fetch(url, retries=4):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(2 ** attempt)
    return None


def get_states():
    data = fetch(f"{BASE_URL}/entes")
    if not data:
        return []
    states = [i for i in data["items"] if i["esfera"] == "E"]
    # DF é registrado como esfera=D em /entes, mas seu RREO Anexo 3 só
    # existe sob co_esfera=E (confirmado por teste direto na API).
    states.append({"cod_ibge": 53, "ente": "Distrito Federal", "uf": "BR"})
    return states


def get_valor(id_ente, ano):
    url = (
        f"{BASE_URL}/rreo"
        f"?an_exercicio={ano}&nr_periodo=6"
        f"&co_tipo_demonstrativo=RREO"
        f"&no_anexo=RREO-Anexo%2003"
        f"&co_esfera=E&id_ente={id_ente}"
    )
    data = fetch(url)
    if not data:
        return None
    for item in data.get("items", []):
        if item["cod_conta"] == ICMS_COD and item["coluna"] == TARGET_COL:
            return item["valor"]
    return None


def main():
    print("Buscando estados do SICONFI...")
    states = get_states()
    print(f"Estados: {len(states)}")

    results = {}  # {ano: {uf: valor}}
    total = len(states) * len(ANOS)
    done = 0
    for entity in states:
        uf = COD_IBGE_TO_UF[entity["cod_ibge"]]
        for ano in ANOS:
            done += 1
            val = get_valor(entity["cod_ibge"], ano)
            if val is not None:
                results.setdefault(str(ano), {})[uf] = val
            pct = done / total * 100
            print(f"\r[ICMS-RREO-2015-2018] {done}/{total} ({pct:.0f}%) — {uf} {ano}: "
                  f"{'R$ {:,.0f}'.format(val) if val else 'N/A'}   ", end="", flush=True)
            time.sleep(0.3)
    print()

    existing = {}
    if OUTPUT.exists():
        with open(OUTPUT) as f:
            existing = json.load(f)

    icms_por_uf = existing.get("icms_por_uf", {})
    icms_br = existing.get("icms_br", {})

    for ano, by_uf in results.items():
        for uf, val in by_uf.items():
            icms_por_uf.setdefault(uf, {})[ano] = val
        icms_br[ano] = sum(by_uf.values())

    existing["icms_por_uf"] = icms_por_uf
    existing["icms_br"] = icms_br

    with open(OUTPUT, "w") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"\nGravado em {OUTPUT}")
    print("\n=== RESUMO ICMS BR (RREO) ===")
    for ano in ANOS:
        v = icms_br.get(str(ano))
        print(f"{ano}: {'R$ {:.2f}B'.format(v/1e9) if v else 'N/D'}")


if __name__ == "__main__":
    main()
