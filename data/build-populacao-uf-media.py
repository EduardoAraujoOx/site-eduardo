#!/usr/bin/env python3
"""
População média de cada UF entre 2019 e 2026 (IBGE), para o mesmo motivo do
build-populacao-municipios.py: o teto do art. 117, §§3º-6º, da LC 227/2026
usa "a média da população... entre 2019 e 2026" tanto para o grupo dos
Estados quanto para o dos Municípios -- não só municípios.

data/icms-iss-vs-populacao-2025.json já existe, mas é intencionalmente um
retrato de 2025 (usado pelo Estudo 05, que compara participação tributária
2025 x população 2025 -- um recorte de um único ano é o correto para aquele
estudo). Este script gera um arquivo separado, específico para o teto do
Seguro-Receita, reaproveitando os mesmos arquivos brutos do IBGE já
baixados por build-populacao-municipios.py (aba "BRASIL E UFs" dos mesmos
"estimativa_dou_AAAA.xls").

Mesma limitação de cobertura: 2019, 2020, 2021, 2024 e 2025 disponíveis;
2022-2023 (Censo Demográfico substituiu a estimativa) e 2026 (ainda não
publicado) ficam de fora da média.

Uso:
  python3 build-populacao-uf-media.py
"""

import json
import re
import urllib.request
from pathlib import Path

import xlrd

HERE = Path(__file__).parent
OUT = HERE / "populacao-uf-media-2019-2026.json"

ANOS_DISPONIVEIS = [2019, 2020, 2021, 2024, 2025]
ANOS_INDISPONIVEIS = {
    2022: "Censo Demográfico 2022 substituiu a estimativa anual normal.",
    2023: "Censo Demográfico 2022 substituiu a estimativa anual normal.",
    2026: "Ainda não publicado pelo IBGE.",
}

NOME_PARA_UF = {
    "Rondônia": "RO", "Acre": "AC", "Amazonas": "AM", "Roraima": "RR", "Pará": "PA",
    "Amapá": "AP", "Tocantins": "TO", "Maranhão": "MA", "Piauí": "PI", "Ceará": "CE",
    "Rio Grande do Norte": "RN", "Paraíba": "PB", "Pernambuco": "PE", "Alagoas": "AL",
    "Sergipe": "SE", "Bahia": "BA", "Minas Gerais": "MG", "Espírito Santo": "ES",
    "Rio de Janeiro": "RJ", "São Paulo": "SP", "Paraná": "PR", "Santa Catarina": "SC",
    "Rio Grande do Sul": "RS", "Mato Grosso do Sul": "MS", "Mato Grosso": "MT",
    "Goiás": "GO", "Distrito Federal": "DF",
}


def raw_path(ano):
    d = HERE / "raw" / f"ibge-populacao-{ano}"
    return d, d / f"estimativa_dou_{ano}.xls"


def baixar_se_necessario(ano):
    raw_dir, raw_file = raw_path(ano)
    if raw_file.exists():
        return raw_file
    raw_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_{ano}/estimativa_dou_{ano}.xls"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw_file.write_bytes(r.read())
    return raw_file


def parse_pop(v):
    """População pode vir como número, ou texto com separador de milhar e nota de
    rodapé colada sem espaço (ex.: '3.273.227(1)')."""
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        m = re.match(r"\s*([\d.,]+)", v)
        if m and m.group(1).strip(".,"):
            return int(m.group(1).replace(".", "").replace(",", ""))
    return None


def carregar_ano(ano):
    raw_file = baixar_se_necessario(ano)
    book = xlrd.open_workbook(str(raw_file))
    sh = book.sheet_by_name("BRASIL E UFs")

    ufs = {}
    for row in range(2, sh.nrows):
        valores = sh.row_values(row)
        nome = valores[0]
        uf = NOME_PARA_UF.get(nome)
        if uf is None:
            continue  # linhas de região (Norte, Nordeste, ...), "Brasil" ou notas de rodapé
        # A população está na primeira coluna não vazia após o nome (a posição varia por ano).
        pop = next((parse_pop(v) for v in valores[1:] if parse_pop(v) is not None), None)
        if pop is None:
            raise ValueError(f"{ano}: população não encontrada para {nome!r} -- linha {valores!r}")
        ufs[uf] = pop
    return ufs


def main():
    por_ano = {ano: carregar_ano(ano) for ano in ANOS_DISPONIVEIS}
    for ano, ufs in por_ano.items():
        print(f"{ano}: {len(ufs)} UFs, população total {sum(ufs.values()):,}".replace(",", "."))

    resultado = {}
    for uf in NOME_PARA_UF.values():
        valores = {ano: por_ano[ano][uf] for ano in ANOS_DISPONIVEIS if uf in por_ano[ano]}
        resultado[uf] = {
            "pop_media": sum(valores.values()) / len(valores),
            "anos_com_dado": sorted(valores.keys()),
            "pop_por_ano": valores,
        }

    output = {
        "fonte": (
            "IBGE, Estimativas da População Residente no Brasil e Unidades da Federação, "
            "publicação no Diário Oficial da União (estimativa_dou_AAAA.xls)"
        ),
        "metodo": (
            "Média aritmética simples da população de cada UF nos anos efetivamente "
            "disponíveis -- LC 227/2026, art. 117, §§3º-6º, pede a média entre 2019 e 2026."
        ),
        "anos_considerados": ANOS_DISPONIVEIS,
        "anos_indisponiveis": ANOS_INDISPONIVEIS,
        "ufs": resultado,
        "total_pop_media": sum(v["pop_media"] for v in resultado.values()),
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSalvo em {OUT}")
    print(f"População média total (27 UFs): {output['total_pop_media']:,.0f}".replace(",", "."))


if __name__ == "__main__":
    main()
