#!/usr/bin/env python3
"""
Estende a série de ISS nacional (DCA Anexo I-C) de 2015-2025 para
2013-2014, para o Estudo 11 (série histórica + projeção do IBS total,
Brasil).

Dois anos com particularidades próprias:
  - 2013: o nome do anexo é "Anexo I-C" (sem o prefixo "DCA-" usado de
    2014 em diante), e a coluna de valor bruto é "Receitas Realizadas"
    (sem "Brutas"). 2014 já usa "DCA-Anexo I-C" e "Receitas Brutas
    Realizadas", como os anos seguintes.
  - Código da conta ISS muda de esquema (numérico legado em 2013-2014,
    ex. "1.1.1.3.05.00.00"), por isso a conta é casada por texto
    ("Serviços de Qualquer Natureza" / "ISSQN"), excluindo Multas, Juros
    e Dívida Ativa — mesmo critério do collect-iss-dca-2015-2018.py.

Uso: python3 collect-iss-dca-2013-2014.py
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ANOS = [2013, 2014]
OUTPUT = Path(__file__).parent / "iss-dca-2013-2014.json"
WORKERS = 6

EXCLUDE_TERMS = ("multas", "juros", "dívida ativa", "divida ativa")


def anexo_para_ano(ano):
    return "Anexo I-C" if ano == 2013 else "DCA-Anexo I-C"


def is_iss_principal(conta_text):
    t = conta_text.lower()
    if any(term in t for term in EXCLUDE_TERMS):
        return False
    return "serviços de qualquer natureza" in t or "issqn" in t


def is_receita_bruta(coluna):
    return coluna.startswith("Receitas") and "Realizadas" in coluna


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
    anexo = anexo_para_ano(ano)

    url = (
        f"{BASE_URL}/dca"
        f"?an_exercicio={ano}&co_esfera=M&id_ente={cod}"
        f"&no_anexo={anexo.replace(' ', '%20')}"
    )
    data = fetch(url)
    val = None
    if data:
        for item in data.get("items", []):
            if is_receita_bruta(item.get("coluna") or "") and is_iss_principal(item.get("conta") or ""):
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
            print(f"[ISS-DCA-2013-2014] {done_count}/{total} ({pct:.1f}%) — {nome} {ano}: "
                  f"{'R$ {:,.0f}'.format(val) if val else 'N/A'}", flush=True)
        if done_count % 500 == 0:
            save_checkpoint()

    time.sleep(0.15)
    return (cod, ano, val)


def save_checkpoint():
    try:
        by_ano_uf = {}
        by_ano_total = {}
        cobertura = {}
        for ano, entes in results.items():
            by_uf = {}
            total = 0.0
            for v in entes.values():
                by_uf[v["uf"]] = by_uf.get(v["uf"], 0.0) + v["valor"]
                total += v["valor"]
            by_ano_uf[ano] = by_uf
            by_ano_total[ano] = total
            cobertura[ano] = len(entes)

        OUTPUT.write_text(json.dumps({
            "dca_iss_por_uf": by_ano_uf,
            "dca_iss_br": by_ano_total,
            "cobertura": cobertura,
        }, ensure_ascii=False, indent=2))
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
    print("\n=== ISS DCA 2013-2014 COLETA CONCLUÍDA ===", flush=True)

    for ano in ANOS:
        entes = results.get(str(ano), {})
        total_val = sum(v["valor"] for v in entes.values())
        print(f"{ano}: {len(entes)}/5570 municípios — R$ {total_val/1e9:.2f}B")


if __name__ == "__main__":
    main()
