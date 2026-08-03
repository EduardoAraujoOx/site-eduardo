#!/usr/bin/env python3
"""
População estimada de cada município brasileiro em 1º de julho de 2025 (IBGE),
mesma fonte e mesma data de referência já usada em
data/icms-iss-vs-populacao-2025.json (nível UF).

Necessária para aplicar o teto de "3 (três) vezes a média nacional por
habitante da respectiva esfera federativa" do art. 132, caput, II, do ADCT
(EC 132/2023) sobre a receita média de cada município no cálculo do
Seguro-Receita -- o teto por UF já é calculável com o dado populacional que
já existe no site, mas o teto por município exigia este novo dado.

Fonte: IBGE, Estimativas da População Residente nos Municípios Brasileiros,
publicação no Diário Oficial da União (arquivo "estimativa_dou_2025.xls"),
disponível em
https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2025/ .
Baixado e cacheado em data/raw/ibge-populacao-2025/ na primeira execução.

Uso:
  python3 build-populacao-municipios.py
"""

import json
import urllib.request
from pathlib import Path

import xlrd

HERE = Path(__file__).parent
RAW_DIR = HERE / "raw" / "ibge-populacao-2025"
RAW_FILE = RAW_DIR / "estimativa_dou_2025.xls"
SOURCE_URL = "https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2025/estimativa_dou_2025.xls"
OUT = HERE / "populacao-municipios-2025.json"


def baixar_se_necessario():
    if RAW_FILE.exists():
        return
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        RAW_FILE.write_bytes(r.read())


def cod2(v):
    """Normaliza célula (str ou float do xlrd) para código com 2 dígitos."""
    return str(int(float(v))).zfill(2)


def cod5(v):
    """Normaliza célula (str ou float do xlrd) para código com 5 dígitos."""
    return str(int(float(v))).zfill(5)


def main():
    baixar_se_necessario()

    book = xlrd.open_workbook(str(RAW_FILE))
    sh = book.sheet_by_name("Municípios")

    municipios = {}
    for row in range(2, sh.nrows):  # linha 0: título; linha 1: cabeçalho
        uf, cod_uf, cod_munic, nome, pop = sh.row_values(row)
        if not uf or not nome:
            continue
        cod7 = cod2(cod_uf) + cod5(cod_munic)
        municipios[cod7] = {"nome": nome, "uf": uf, "pop": int(pop)}

    output = {
        "fonte": (
            "IBGE, Estimativas da População Residente nos Municípios Brasileiros, "
            "publicação no Diário Oficial da União, data de referência 1º de julho de 2025 "
            "(estimativa_dou_2025.xls)"
        ),
        "fonte_url": "https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2025/",
        "data_referencia": "2025-07-01",
        "n_municipios": len(municipios),
        "total_pop": sum(m["pop"] for m in municipios.values()),
        "municipios": municipios,
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {OUT}")
    print(f"Municípios: {len(municipios)} | população total: {output['total_pop']:,}".replace(",", "."))


if __name__ == "__main__":
    main()
