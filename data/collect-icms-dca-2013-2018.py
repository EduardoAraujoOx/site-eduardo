#!/usr/bin/env python3
"""
Coleta ICMS via DCA Anexo I-C para os 27 estados + DF, 2013-2018 —
estendendo (e substituindo, para esses anos) a base de ICMS que hoje usa
RREO Anexo 3 para 2015-2018 e DCA para 2019-2025.

O nome do anexo muda de formato conforme o ano: "Anexo I-C" em 2013,
"DCA-Anexo I-C" de 2014 em diante. O código da conta também muda de
esquema (numérico legado em 2013-2014, ex. "1.1.1.3.02.00.00", vs. nome
em 2019+, ex. "ICMSLiquidoExcetoTransferenciasEFUNDEB"), por isso a conta
é casada por texto ("ICMS" no nome, excluindo linhas de multas/dívida
ativa) em vez de por código fixo. A coluna de valor bruto também varia:
"Receitas Realizadas" em 2013, "Receitas Brutas Realizadas" de 2014 em
diante — casada por prefixo, não por nome exato.

Uso: python3 collect-icms-dca-2013-2018.py
"""

import json
import time
import urllib.request
from pathlib import Path

BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ANOS = [2013, 2014, 2015, 2016, 2017, 2018]
OUTPUT = Path(__file__).parent / "icms-dca-2013-2018.json"

EXCLUIR = ("multa", "dívida", "divida", "adicional", "fundo estadual", "desoneração", "desoneracao")

# A API do SICONFI retorna uf="BR" para todos os entes estaduais (esfera=E)
# em /entes -- bug/particularidade da própria API. O código IBGE do estado
# é confiável, então mapeamos cod_ibge -> sigla UF nós mesmos.
COD_IBGE_PARA_UF = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL",
    28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF",
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


def anexo_para_ano(ano):
    return "Anexo I-C" if ano == 2013 else "DCA-Anexo I-C"


def get_estados():
    data = fetch(f"{BASE_URL}/entes")
    items = data["items"]
    return [i for i in items if i["esfera"] == "E"]


def icms_do_ano(id_ente, ano):
    anexo = anexo_para_ano(ano)
    url = (
        f"{BASE_URL}/dca?an_exercicio={ano}&co_esfera=E&id_ente={id_ente}"
        f"&no_anexo={anexo.replace(' ', '%20')}"
    )
    data = fetch(url)
    if not data:
        return None
    total = 0.0
    achou = False
    for it in data.get("items", []):
        conta = (it.get("conta") or "").lower()
        coluna = it.get("coluna") or ""
        if "icms" not in conta and "circula" not in conta:
            continue
        if any(x in conta for x in EXCLUIR):
            continue
        if not coluna.startswith("Receitas") or "Realizadas" not in coluna:
            continue
        val = it.get("valor")
        if val is not None:
            total += val
            achou = True
    return total if achou else None


def main():
    estados = get_estados()
    print(f"{len(estados)} estados. Anos: {ANOS}")

    resultado = {}  # {ano: {uf: valor}}
    total = len(estados) * len(ANOS)
    done = 0
    for ano in ANOS:
        resultado[str(ano)] = {}
        for e in estados:
            done += 1
            uf = COD_IBGE_PARA_UF.get(e["cod_ibge"], e["uf"])
            val = icms_do_ano(e["cod_ibge"], ano)
            if val is not None:
                resultado[str(ano)][uf] = val
            print(f"\r{done}/{total} — {ano} {uf}: {'R$ %.0f' % val if val else 'N/A'}    ", end="", flush=True)
            time.sleep(0.3)
    print()

    OUTPUT.write_text(json.dumps(resultado, ensure_ascii=False, indent=2))
    print(f"Gravado em {OUTPUT}")
    for ano in ANOS:
        s = sum(resultado[str(ano)].values())
        print(f"{ano}: R$ {s/1e9:.2f} bi ({len(resultado[str(ano)])} estados)")


if __name__ == "__main__":
    main()
