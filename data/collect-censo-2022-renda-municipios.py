#!/usr/bin/env python3
"""
Coleta o rendimento nominal mensal domiciliar per capita medio, por
municipio, do Censo Demografico 2022 (IBGE, SIDRA tabela 10295, variavel
13431, nivel N6). Usado como proxy de "intensidade" de consumo por
municipio (analogo ao papel da POF na formula UF: despesa media familiar
x domicilios) para repartir a fatia PROPRIA do IBS municipal (sucessora
do ISS, resolvida por destino) entre os municipios de uma mesma UF -- ver
data/build-rateio-destino-municipios.py.

Por que renda, nao despesa: a POF (Pesquisa de Orcamentos Familiares) nao
abre por municipio, so por UF -- nao ha como replicar a formula POF x
Censo em nivel de cidade. O Censo 2022 e a unica fonte com abertura por
municipio; ela mede RENDA, nao consumo. O proprio Gobetti e Monteiro
(Carta de Conjuntura 60, IPEA, 2023, p. 2) registram que pretendiam usar
exatamente esse dado para refinar a base de consumo por municipio, mas
que "tais dados ainda nao estao disponiveis ao publico" na epoca -- em
ago/2026, o modulo Censo 2022 Trabalho e Rendimento ja foi divulgado.

Limitacao conhecida (nao corrigida): consumo e uma funcao concava da
renda (familias mais pobres consomem quase 100% do que ganham; familias
mais ricas poupam uma fracao maior). Usar renda linearmente como proxy de
consumo tende a superestimar a fatia de municipios mais ricos. Nao ha
dado publico de propensao a consumir por faixa de renda e por municipio
para corrigir isso -- aplicar uma correcao inventada seria pior do que
nao corrigir. Documentado como limitacao, nao escondido.

Uso:
  python3 collect-censo-2022-renda-municipios.py
"""

import gzip
import io
import json
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUTPUT = HERE / "censo-2022-renda-municipios.json"

AGREGADO = 10295
VARIAVEL = 13431  # Valor do rendimento nominal medio mensal domiciliar per capita (R$)
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
            "renda_domiciliar_per_capita_2022": float(valor_raw),
        }

    output = {
        "fonte": (
            "IBGE, Censo Demografico 2022, modulo Trabalho e Rendimento. SIDRA tabela 10295, "
            "variavel 13431 (valor do rendimento nominal medio mensal domiciliar per capita, "
            "R$), Sexo/Cor-raca/Grupo de idade = Total, nivel Municipio."
        ),
        "fonte_url": (
            f"https://servicodados.ibge.gov.br/api/v3/agregados/{AGREGADO}/periodos/{PERIODO}"
            f"/variaveis/{VARIAVEL}?localidades=N6[all]&classificacao={CLASSIFICACAO}"
        ),
        "metodo": (
            "Proxy de intensidade de consumo por municipio, usado para repartir a fatia "
            "PROPRIA do IBS municipal (sucessora do ISS, LC 227/2026 art. 106) entre os "
            "municipios de uma mesma UF -- ver data/build-rateio-destino-municipios.py. "
            "Limitacao: renda nao e consumo; a propensao a consumir cai com a renda, entao "
            "este proxy tende a superestimar a fatia de municipios mais ricos. Sem dado "
            "publico de propensao a consumir por municipio para corrigir isso."
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
