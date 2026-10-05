#!/usr/bin/env python3
"""
Coleta do RREO (Anexo 03, SICONFI) o ICMS líquido mensal dos estados e do DF nos 12 meses até o 4º bimestre
(jan-ago) de cada ano de 2018 a 2026, mais a previsão atualizada do ano (2026). Serve para um nowcast da
participação de cada UF no ano corrente e para validar quanto o acumulado jan-ago prevê a variação anual.
Saída: data/rreo-icms-mensal.json  {ano: {UF: {"meses": [MR-11..MR], "total12m": x, "previsao": y}}}
"""
import json
import time
import urllib.request
from pathlib import Path

BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
OUT = Path(__file__).parent / "rreo-icms-mensal.json"
COD = "ICMSLiquidoExcetoTransferenciasEFUNDEB"
UFS = {11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO", 21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB",
       26: "PE", 27: "AL", 28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP", 41: "PR", 42: "SC", 43: "RS", 50: "MS",
       51: "MT", 52: "GO", 53: "DF"}


def fetch(url, tries=5):
    for i in range(tries):
        try:
            return json.loads(urllib.request.urlopen(url, timeout=60).read())
        except Exception:
            time.sleep(2 ** i)
    return None


def main():
    saida = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for ano in range(2018, 2027):
        saida.setdefault(str(ano), {})
        for cod, uf in UFS.items():
            if uf in saida[str(ano)]:
                continue
            esfera = "D" if uf == "DF" else "E"
            d = fetch(f"{BASE}/rreo?an_exercicio={ano}&nr_periodo=4&co_tipo_demonstrativo=RREO&no_anexo=RREO-Anexo%2003&co_esfera={esfera}&id_ente={cod}")
            its = [i for i in (d or {}).get("items", []) if i["cod_conta"] == COD]
            if its:
                v = {i["coluna"]: i["valor"] for i in its}
                meses = [v.get("<MR>" if k == 0 else f"<MR-{k}>") for k in range(11, -1, -1)]
                saida[str(ano)][uf] = {"meses": meses, "total12m": v.get("TOTAL (ÚLTIMOS 12 MESES)"),
                                       "previsao": v.get("PREVISÃO ATUALIZADA %d" % ano) or v.get("PREVISÃO ATUALIZADA")}
            print(ano, uf, "ok" if its else "sem dado", flush=True)
            OUT.write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
            time.sleep(1.0)


if __name__ == "__main__":
    main()
