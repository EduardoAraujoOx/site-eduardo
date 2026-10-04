#!/usr/bin/env python3
"""
Coleta da DCA da União (SICONFI/Tesouro Nacional, Anexo I-C, receitas brutas realizadas) as
receitas dos tributos federais sobre o consumo que o IBS/CBS substituem (LC 214/2025, art. 350, I):
PIS/PASEP, Cofins (contribuição para o financiamento da seguridade social) e IPI.

Uso na calibração do peso das compras governamentais (data/calibra-peso-compras.py): o IBS que o
ente comprador recebe sobre suas compras equivale, pela neutralidade do art. 370, aos tributos
antigos (federais e subnacionais) embutidos nessas compras.

Saída: data/tributos-federais-dca-uniao.json
"""
import gzip
import json
import urllib.request
from pathlib import Path

ANO = 2024
URL = ("https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca?an_exercicio=%d"
       "&no_anexo=DCA-Anexo%%20I-C&id_ente=1" % ANO)
CONTAS = {
    "RO1.1.1.4.01.0.0": "IPI",
    "RO1.2.1.1.00.0.0": "Cofins (contribuição para financiamento da seguridade social)",
    "RO1.2.1.2.00.0.0": "PIS/PASEP",
}
OUT = Path(__file__).parent / "tributos-federais-dca-uniao.json"


def main():
    with urllib.request.urlopen(URL, timeout=90) as r:
        raw = r.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    itens = json.loads(raw)["items"]
    val = {}
    for x in itens:
        if x["cod_conta"] in CONTAS and x["coluna"] == "Receitas Brutas Realizadas":
            val[x["cod_conta"]] = x["valor"]
    saida = {
        "fonte": "SICONFI/Tesouro Nacional, DCA Anexo I-C, União (id_ente=1), receitas brutas realizadas",
        "ano": ANO, "url": URL,
        "tributos": {CONTAS[c]: {"codigo": c, "valor_reais": v} for c, v in val.items()},
        "total_reais": sum(val.values()),
    }
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1))
    print(saida["total_reais"] / 1e9, {CONTAS[c]: round(v / 1e9, 1) for c, v in val.items()})


if __name__ == "__main__":
    main()
