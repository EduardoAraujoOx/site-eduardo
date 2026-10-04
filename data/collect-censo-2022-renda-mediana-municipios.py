#!/usr/bin/env python3
"""
Coleta o rendimento nominal MEDIANO mensal domiciliar per capita, por municipio,
do Censo Demografico 2022 (IBGE, SIDRA tabela 10295, variavel 13534, nivel N6).

Complementa data/collect-censo-2022-renda-municipios.py (variavel 13431, media).
Com media e mediana de cada municipio, e possivel aproximar a distribuicao de
renda por uma lognormal (sigma^2 = 2 ln(media/mediana)) e calcular o consumo
esperado com elasticidade-renda menor que 1 (E[y^e] = mediana^e exp(e^2 sigma^2/2)),
em vez de supor consumo proporcional a renda media -- ver
data/simula-rateio-compras-consumo.py e data/estima-elasticidade-pof.py.

Uso:
  python3 collect-censo-2022-renda-mediana-municipios.py
"""

import gzip
import io
import json
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUTPUT = HERE / "censo-2022-renda-mediana-municipios.json"

AGREGADO = 10295
VARIAVEL = 13534  # Valor do rendimento nominal MEDIANO mensal domiciliar per capita (R$)
PERIODO = 2022
CLASSIFICACAO = "2[6794]|86[95251]|58[95253]"  # Sexo=Total, Cor/raca=Total, Idade=Total

URL = (
    f"https://servicodados.ibge.gov.br/api/v3/agregados/{AGREGADO}/periodos/{PERIODO}"
    f"/variaveis/{VARIAVEL}?localidades=N6[all]&classificacao={CLASSIFICACAO}"
)


def fetch_json(url, tentativas=5):
    ultimo_erro = None
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
                if r.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except Exception as e:
            ultimo_erro = e
            print(f"  tentativa {i+1}/{tentativas} falhou: {e}")
            time.sleep(2 * (i + 1))
    raise ultimo_erro


def main():
    data = fetch_json(URL)

    series = data[0]["resultados"][0]["series"]
    municipios = {}
    sem_dado = []
    for item in series:
        loc = item["localidade"]
        cod = loc["id"]
        nome_uf = loc["nome"]  # "Alta Floresta D'Oeste - RO"
        valor_raw = item["serie"].get(str(PERIODO))
        if valor_raw is None or valor_raw in ("...", "-", "X"):
            sem_dado.append(cod)
            continue
        municipios[cod] = {
            "nome": nome_uf.rsplit(" - ", 1)[0],
            "uf": nome_uf.rsplit(" - ", 1)[1] if " - " in nome_uf else None,
            "renda_mediana_domiciliar_per_capita_2022": float(valor_raw),
        }

    output = {
        "fonte": (
            "IBGE, Censo Demografico 2022, modulo Trabalho e Rendimento. SIDRA tabela 10295, "
            "variavel 13534 (valor do rendimento nominal medio mensal domiciliar per capita, "
            "R$), Sexo/Cor-raca/Grupo de idade = Total, nivel Municipio."
        ),
        "fonte_url": (
            f"https://servicodados.ibge.gov.br/api/v3/agregados/{AGREGADO}/periodos/{PERIODO}"
            f"/variaveis/{VARIAVEL}?localidades=N6[all]&classificacao={CLASSIFICACAO}"
        ),
        "metodo": (
            "Complemento da media (variavel 13431): permite aproximar a distribuicao de renda "
            "do municipio e aplicar a elasticidade-renda do consumo (POF 2017-18) a ela."
        ),
        "n_municipios": len(municipios),
        "n_sem_dado": len(sem_dado),
        "codigos_sem_dado": sem_dado,
        "municipios": municipios,
    }

    with open(OUTPUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {OUTPUT}")
    print(f"Municipios com dado: {len(municipios)} | sem dado: {len(sem_dado)}")
    if sem_dado:
        print(f"Codigos sem dado: {sem_dado[:20]}{'...' if len(sem_dado) > 20 else ''}")
    exemplo = next(iter(municipios.items()))
    print(f"Exemplo: {exemplo}")


if __name__ == "__main__":
    main()
