#!/usr/bin/env python3
"""
Estende a série de ISS nacional (DCA Anexo I-C) de 2019-2025 para 2015-2018,
para o Estudo 11 (série histórica + projeção do IBS total, Brasil).

Por que DCA e não RREO: a coleta de ISS-BR via RREO já existente no repo
(reforma-tributaria.json:iss_br, 2019-2025) cobre só ~650-760 dos 5.570
municípios por ano (ver iss_br_detalhes_parcial) — provavelmente por
esgotamento de retries sob rate limit, não por ausência real de dado. Os
valores dca_iss_br (mesma fonte usada pelos Estudos 03/06/09 via
ibs-projecao-parametros.json) têm cobertura muito maior (93-99%, conforme
data/build-coeficientes-municipios.py). Por isso a extensão histórica usa
DCA, replicando a mesma fonte já validada para 2019-2025.

Dificuldade: o código da conta ISS no DCA mudou de esquema ao longo dos
anos (ex.: "1.1.1.3.05.00.00" em 2015, "1.1.1.4.51.1.0" em 2025). Por isso
o filtro usa o texto da conta ("Serviços de Qualquer Natureza" / "ISSQN"),
excluindo explicitamente Multas, Juros e Dívida Ativa (contas separadas,
não fazem parte do ISS corrente).

Uso: python3 collect-iss-dca-2015-2018.py
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ANOS = [2015, 2016, 2017, 2018]
TARGET_COL = "Receitas Brutas Realizadas"
OUTPUT = Path(__file__).parent / "reforma-tributaria.json"
WORKERS = 6

EXCLUDE_TERMS = ("multas", "juros", "dívida ativa", "divida ativa")


def is_iss_principal(conta_text):
    t = conta_text.lower()
    if any(term in t for term in EXCLUDE_TERMS):
        return False
    return "serviços de qualquer natureza" in t or "issqn" in t


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


def get_municipios():
    data = fetch(f"{BASE_URL}/entes")
    if not data:
        return []
    return [i for i in data["items"] if i["esfera"] == "M"]


def process_task(task):
    global done_count
    entity, ano = task
    cod = entity["cod_ibge"]
    nome = entity["ente"]
    uf = entity.get("uf", "")

    url = (
        f"{BASE_URL}/dca"
        f"?an_exercicio={ano}&co_esfera=M&id_ente={cod}"
        f"&no_anexo=DCA-Anexo%20I-C"
    )
    data = fetch(url)
    val = None
    if data:
        for item in data.get("items", []):
            if item["coluna"] == TARGET_COL and is_iss_principal(item["conta"]):
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
        if done_count % 200 == 0 or done_count <= 5:
            total = len(ANOS) * 5570
            pct = done_count / total * 100
            print(f"[ISS-DCA-2015-2018] {done_count}/{total} ({pct:.1f}%) — {nome} {ano}: "
                  f"{'R$ {:,.0f}'.format(val) if val else 'N/A'}", flush=True)
        if done_count % 500 == 0:
            save_checkpoint()

    time.sleep(0.15)
    return (cod, ano, val)


def save_checkpoint():
    try:
        existing = {}
        if OUTPUT.exists():
            with open(OUTPUT) as f:
                existing = json.load(f)

        dca_iss_por_uf = existing.get("dca_iss_por_uf", {})
        dca_iss_br = existing.get("dca_iss_br", {})

        for ano, entes in results.items():
            by_uf = {}
            total = 0.0
            for v in entes.values():
                by_uf[v["uf"]] = by_uf.get(v["uf"], 0.0) + v["valor"]
                total += v["valor"]
            dca_iss_por_uf[ano] = by_uf
            dca_iss_br[ano] = total

        existing["dca_iss_por_uf"] = dca_iss_por_uf
        existing["dca_iss_br"] = dca_iss_br
        existing["dca_iss_2015_2018_cobertura"] = {
            ano: len(entes) for ano, entes in results.items()
        }

        with open(OUTPUT, "w") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Checkpoint error: {e}", flush=True)


def main():
    print("Buscando municípios do SICONFI...", flush=True)
    municipios = get_municipios()
    print(f"Total municípios: {len(municipios)}", flush=True)

    tasks = [(entity, ano) for entity in municipios for ano in ANOS]
    total = len(tasks)
    print(f"Total de chamadas: {total} com {WORKERS} workers paralelos", flush=True)
    print(f"Estimativa: ~{total / WORKERS / 60:.0f} minutos\n", flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(process_task, t): t for t in tasks}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception:
                pass

    save_checkpoint()
    print("\n=== ISS DCA 2015-2018 COLETA CONCLUÍDA ===", flush=True)

    for ano in ANOS:
        entes = results.get(str(ano), {})
        total_val = sum(v["valor"] for v in entes.values())
        print(f"{ano}: {len(entes)}/5570 municípios — R$ {total_val/1e9:.2f}B")


if __name__ == "__main__":
    main()
