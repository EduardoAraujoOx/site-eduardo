#!/usr/bin/env python3
"""
Merge dos resultados de coleta SICONFI.
Lê o output log do script principal e reconstrói o JSON com todos os dados coletados.
"""
import json, re
from pathlib import Path

LOG = Path("/tmp/claude-0/-home-user-site-eduardo/bac4e619-9fda-5b6b-94fc-2753cc676c44/tasks/b5izi1hyh.output")
OUTPUT = Path(__file__).parent / "reforma-tributaria.json"
ANOS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]

icms_data = {}  # {uf: {ano: valor}}
iss_es_data = {}  # {municipio: {ano: valor}}

def parse_log():
    if not LOG.exists():
        print(f"Log not found: {LOG}")
        return

    text = LOG.read_text(errors='ignore')

    # Parse ICMS lines: [ICMS] N/182 (P%) — Estado ANO: R$ VVV
    icms_pattern = re.compile(
        r'\[ICMS\] \d+/\d+ \(\d+%\) — (.+?) (\d{4}): (?:R\$ ([\d,]+)|N/A)'
    )
    for m in icms_pattern.finditer(text):
        estado, ano, val_str = m.group(1), int(m.group(2)), m.group(3)
        if val_str:
            val = float(val_str.replace(',', ''))
            icms_data.setdefault(estado, {})[ano] = val

    # Parse ISS-ES lines: [ISS-ES] N/546 (P%) — Municipio ANO: R$ VVV
    iss_pattern = re.compile(
        r'\[ISS-ES\] \d+/\d+ \(\d+%\) — (.+?) (\d{4}): (?:R\$ ([\d,]+)|N/A)'
    )
    for m in iss_pattern.finditer(text):
        muni, ano, val_str = m.group(1), int(m.group(2)), m.group(3)
        if val_str:
            val = float(val_str.replace(',', ''))
            iss_es_data.setdefault(muni, {})[ano] = val

def main():
    print("Parsing log file...")
    parse_log()
    print(f"ICMS estados encontrados: {len(icms_data)}")
    print(f"ISS ES municípios com dados: {len(iss_es_data)}")

    # Aggregate ICMS
    icms_br = {}
    icms_es = {}

    ES_NOMES = ["Espírito Santo", "Espirito Santo"]

    for estado, anos_vals in icms_data.items():
        for ano, val in anos_vals.items():
            icms_br[ano] = icms_br.get(ano, 0) + val
            if estado in ES_NOMES or "spírito" in estado or "spirito" in estado:
                icms_es[ano] = val

    # Aggregate ISS ES
    iss_es = {}
    for muni, anos_vals in iss_es_data.items():
        for ano, val in anos_vals.items():
            iss_es[ano] = iss_es.get(ano, 0) + val

    # Load existing ISS BR (from checkpoint)
    existing = {}
    if OUTPUT.exists():
        try:
            existing = json.loads(OUTPUT.read_text())
        except Exception:
            pass

    iss_br = existing.get("iss_br", {})
    # Convert to int keys for comparison
    iss_br_by_ano = {int(k): v for k, v in iss_br.items()}

    # Build output
    output = {
        "fonte": "SICONFI (STN) — RREO Anexo 3, período 6 (bimestre nov-dez), Total Últimos 12 Meses",
        "unidade": "R$ nominais",
        "anos": ANOS,
        "icms_br": {str(a): icms_br.get(a) for a in ANOS},
        "icms_es": {str(a): icms_es.get(a) for a in ANOS},
        "iss_es": {str(a): iss_es.get(a) for a in ANOS},
        "iss_br": {str(a): iss_br_by_ano.get(a) for a in ANOS},
        "iss_br_cobertura": existing.get("iss_br_detalhes_parcial", {}),
        "detalhes_icms": {
            estado: {str(a): v for a, v in anos_vals.items()}
            for estado, anos_vals in icms_data.items()
        },
        "detalhes_iss_es": {
            muni: {str(a): v for a, v in anos_vals.items()}
            for muni, anos_vals in iss_es_data.items()
        },
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nSalvo: {OUTPUT}")

    print(f"\n{'Ano':<6} {'ICMS ES':>15} {'ICMS BR':>15} {'ISS ES':>15} {'ISS BR (parcial)':>18}")
    for a in ANOS:
        def fmt(v): return f"R$ {v/1e9:.2f}B" if v else "N/D"
        print(f"{a:<6} {fmt(icms_es.get(a)):>15} {fmt(icms_br.get(a)):>15} {fmt(iss_es.get(a)):>15} {fmt(iss_br_by_ano.get(a)):>18}")


if __name__ == "__main__":
    main()
