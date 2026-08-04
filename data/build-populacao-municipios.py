#!/usr/bin/env python3
"""
População média de cada município brasileiro entre 2019 e 2026 (IBGE),
conforme exigido pelo art. 117, §§3º-6º, da LC 227/2026: o teto do
Seguro-Receita usa "a média da população... entre 2019 e 2026" de cada
ente, não um único ano.

Uma primeira versão deste script usava só a população de 2025 (ponto
único), como simplificação. Esta versão constrói a média real dos anos
disponíveis: o IBGE publica "Estimativas da População Residente nos
Municípios Brasileiros" (DOU) para 2019, 2020, 2021, 2024 e 2025 --
2022 e 2023 não têm estimativa anual normal (foram os anos do Censo
Demográfico 2022, que substituiu a estimativa nesses dois anos), e 2026
ainda não foi publicado pelo IBGE (verificado em ftp.ibge.gov.br em
04/08/2026: pasta Estimativas_2026 inexistente). A média aqui é,
portanto, dos 5 anos efetivamente disponíveis (2019, 2020, 2021, 2024,
2025) -- mesmo espírito de "usar o que existe, sem estimar o que falta"
já adotado para dados faltantes de DCA em coeficientes-municipios.json.

Necessária para aplicar o teto de "3 (três) vezes a média nacional por
habitante da respectiva esfera federativa" do art. 132, caput, II, do
ADCT (EC 132/2023) e art. 117 da LC 227/2026 sobre a receita média de
cada ente no cálculo do Seguro-Receita.

Fonte: IBGE, Estimativas da População Residente nos Municípios
Brasileiros, publicação no Diário Oficial da União (arquivos
"estimativa_dou_AAAA.xls"), disponíveis em
https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_AAAA/ .
Baixados e cacheados em data/raw/ibge-populacao-AAAA/ na primeira
execução.

Uso:
  python3 build-populacao-municipios.py
"""

import json
import re
import urllib.request
from pathlib import Path

import xlrd

HERE = Path(__file__).parent
OUT = HERE / "populacao-municipios-media-2019-2026.json"

ANOS_DISPONIVEIS = [2019, 2020, 2021, 2024, 2025]
ANOS_INDISPONIVEIS = {
    2022: "Censo Demográfico 2022 substituiu a estimativa anual normal.",
    2023: "Censo Demográfico 2022 substituiu a estimativa anual normal.",
    2026: "Ainda não publicado pelo IBGE.",
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


def cod2(v):
    """Normaliza célula (str ou float do xlrd) para código com 2 dígitos."""
    return str(int(float(v))).zfill(2)


def cod5(v):
    """Normaliza célula (str ou float do xlrd) para código com 5 dígitos."""
    return str(int(float(v))).zfill(5)


def parse_pop(v):
    """Alguns anos trazem população como texto, com separador de milhar ('548.952') e/ou
    nota de rodapé ('529544 (1)')."""
    if isinstance(v, str):
        m = re.match(r"\s*([\d.,]+)", v)
        if not m:
            return None
        return int(m.group(1).replace(".", "").replace(",", ""))
    return int(v)


def carregar_ano(ano):
    raw_file = baixar_se_necessario(ano)
    book = xlrd.open_workbook(str(raw_file))
    nome_aba = "Municípios" if "Municípios" in book.sheet_names() else "MUNICÍPIOS"
    sh = book.sheet_by_name(nome_aba)

    municipios = {}
    for row in range(2, sh.nrows):  # linha 0: título; linha 1: cabeçalho
        uf, cod_uf, cod_munic, nome, pop_raw = sh.row_values(row)
        if not uf or not nome:
            continue
        pop = parse_pop(pop_raw)
        if pop is None:
            continue
        cod7 = cod2(cod_uf) + cod5(cod_munic)
        municipios[cod7] = {"nome": nome, "uf": uf, "pop": pop}
    return municipios


def main():
    por_ano = {ano: carregar_ano(ano) for ano in ANOS_DISPONIVEIS}
    for ano, m in por_ano.items():
        print(f"{ano}: {len(m)} municípios, população total {sum(v['pop'] for v in m.values()):,}".replace(",", "."))

    todos_cods = set()
    for m in por_ano.values():
        todos_cods |= set(m.keys())

    resultado = {}
    for cod in todos_cods:
        valores = {ano: por_ano[ano][cod]["pop"] for ano in ANOS_DISPONIVEIS if cod in por_ano[ano]}
        if not valores:
            continue
        ref = next(por_ano[ano][cod] for ano in ANOS_DISPONIVEIS if cod in por_ano[ano])
        resultado[cod] = {
            "nome": ref["nome"],
            "uf": ref["uf"],
            "pop_media": sum(valores.values()) / len(valores),
            "anos_com_dado": sorted(valores.keys()),
            "pop_por_ano": valores,
        }

    output = {
        "fonte": (
            "IBGE, Estimativas da População Residente nos Municípios Brasileiros, "
            "publicação no Diário Oficial da União (estimativa_dou_AAAA.xls)"
        ),
        "fonte_url": "https://ftp.ibge.gov.br/Estimativas_de_Populacao/",
        "metodo": (
            "Média aritmética simples da população de cada município nos anos "
            "efetivamente disponíveis, sem estimar os anos faltantes -- LC 227/2026, "
            "art. 117, §§3º-6º, pede a média entre 2019 e 2026."
        ),
        "anos_considerados": ANOS_DISPONIVEIS,
        "anos_indisponiveis": ANOS_INDISPONIVEIS,
        "n_municipios": len(resultado),
        "total_pop_media": sum(m["pop_media"] for m in resultado.values()),
        "municipios": resultado,
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSalvo em {OUT}")
    print(f"Municípios: {len(resultado)} | população média total: {output['total_pop_media']:,.0f}".replace(",", "."))
    cobertura_incompleta = sum(1 for m in resultado.values() if len(m["anos_com_dado"]) < len(ANOS_DISPONIVEIS))
    print(f"Municípios com cobertura incompleta (menos de {len(ANOS_DISPONIVEIS)}/{len(ANOS_DISPONIVEIS)} anos disponíveis): {cobertura_incompleta}")


if __name__ == "__main__":
    main()
