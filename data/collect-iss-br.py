#!/usr/bin/env python3
"""
Coleta ISS de todos os municípios brasileiros do SICONFI.
Usa 8 threads paralelas para reduzir tempo de ~11h para ~1.5h.
"""

import json
import time
import sys
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ANOS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
TARGET_COL = "TOTAL (ÚLTIMOS 12 MESES)"
ISS_COD = "ISSLiquidoExcetoTransferenciasEFUNDEB"
OUTPUT = Path(__file__).parent / "reforma-tributaria.json"
WORKERS = 6

lock = Lock()
results = {}  # {ano: {cod_ibge: {ente, uf, valor}}}
done_count = 0


def fetch(url, retries=4):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 ** (attempt + 1))
            elif attempt == retries - 1:
                return None
            else:
                time.sleep(1)
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(1)
    return None


def get_entes():
    data = fetch(f"{BASE_URL}/entes")
    if not data:
        return [], []
    items = data["items"]
    return [i for i in items if i["esfera"] == "M"]


def process_task(task):
    global done_count
    entity, ano = task
    cod = entity["cod_ibge"]
    nome = entity["ente"]
    uf = entity.get("uf", "")

    url = (
        f"{BASE_URL}/rreo"
        f"?an_exercicio={ano}&nr_periodo=6"
        f"&co_tipo_demonstrativo=RREO"
        f"&no_anexo=RREO-Anexo%2003"
        f"&co_esfera=M&id_ente={cod}"
    )
    data = fetch(url)
    val = None
    if data:
        for item in data.get("items", []):
            if item["cod_conta"] == ISS_COD and item["coluna"] == TARGET_COL:
                val = item["valor"]
                break

    with lock:
        done_count += 1
        if val is not None:
            results.setdefault(str(ano), {})[str(cod)] = {
                "ente": nome,
                "uf": uf,
                "valor": val,
            }
        if done_count % 100 == 0 or done_count <= 5:
            total = len(ANOS) * 5570
            pct = done_count / total * 100
            elapsed_msg = f"{done_count}/{total} ({pct:.1f}%)"
            print(f"[ISS-BR] {elapsed_msg} — {nome} {ano}: {'R$ {:,.0f}'.format(val) if val else 'N/A'}", flush=True)
            # Save checkpoint every 500
        if done_count % 500 == 0:
            save_checkpoint()

    time.sleep(0.15)  # slight delay per thread to avoid hammering
    return (cod, ano, val)


def save_checkpoint():
    try:
        existing = {}
        if OUTPUT.exists():
            with open(OUTPUT) as f:
                existing = json.load(f)

        iss_br_totals = {}
        for ano, entes in results.items():
            iss_br_totals[ano] = sum(v["valor"] for v in entes.values())

        existing["iss_br"] = {str(a): iss_br_totals.get(str(a)) for a in ANOS}
        existing["iss_br_detalhes_parcial"] = {
            ano: len(entes) for ano, entes in results.items()
        }

        with open(OUTPUT, "w") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Checkpoint error: {e}", flush=True)


def main():
    print("Buscando municípios do SICONFI...", flush=True)
    municipalities = get_entes()
    print(f"Total municípios: {len(municipalities)}", flush=True)

    # Build task list
    tasks = [(entity, ano) for entity in municipalities for ano in ANOS]
    total = len(tasks)
    print(f"Total de chamadas: {total} com {WORKERS} workers paralelos", flush=True)
    print(f"Estimativa: ~{total/WORKERS/60:.0f} minutos\n", flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(process_task, t): t for t in tasks}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                pass

    # Final save
    save_checkpoint()
    print("\n=== ISS BR COLETA CONCLUÍDA ===", flush=True)

    iss_br_totals = {}
    for ano, entes in results.items():
        iss_br_totals[ano] = sum(v["valor"] for v in entes.values())

    print(f"{'Ano':<6} {'ISS BR':>18}")
    for a in ANOS:
        v = iss_br_totals.get(str(a))
        print(f"{a:<6} {'R$ {:.2f}B'.format(v/1e9) if v else 'N/D':>18}")


if __name__ == "__main__":
    main()
