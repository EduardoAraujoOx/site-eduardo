#!/usr/bin/env python3
"""
Coleta, por UF, as séries de renda usadas na estimação robusta do coeficiente de destino (estima-phi-destino-robusto.py):
  - Censo 2022 (SIDRA 10295): moradores e rendimento médio domiciliar per capita (variáveis 13604 e 13431);
  - Censo 2022 (SIDRA 10296): moradores por classe de rendimento domiciliar per capita em salários mínimos;
  - PNAD Contínua anual (SIDRA 7395): rendimento médio mensal real domiciliar per capita (variável 4196), 2018 a 2023.
Saída: data/renda-uf-censo-pnadc.json
"""
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "renda-uf-censo-pnadc.json"
COD = {"RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17, "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27,
       "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35, "PR": 41, "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53}
INV = {str(v): k for k, v in COD.items()}
CLASSES = {"9692": "sem rendimento", "9681": "ate 1/4 SM", "9682": "1/4 a 1/2", "9683": "1/2 a 1", "9684": "1 a 2", "9685": "2 a 3", "9686": "3 a 5",
           "9687": "5 a 10", "9688": "10 a 15", "9689": "15 a 20", "9690": "mais de 20"}


def sidra(url):
    return json.loads(urllib.request.urlopen(url, timeout=120).read())[1:]


def num(v):
    return float(v) if v not in ("-", "..", "X", "...") else 0.0


def main():
    saida = {"_meta": {"fonte": "IBGE/SIDRA: Censo 2022 (10295, 10296) e PNAD Contínua anual (7395)", "classes": CLASSES}}
    d = sidra("https://apisidra.ibge.gov.br/values/t/10295/n3/all/p/last/v/13604,13431?formato=json")
    saida["censo_2022"] = {}
    for r in d:
        u = INV[r["D1C"]]
        saida["censo_2022"].setdefault(u, {})["moradores" if r["D3C"] == "13604" else "renda_media_pc"] = num(r["V"])
    d = sidra("https://apisidra.ibge.gov.br/values/t/10296/n3/all/p/last/v/13604/c386/all/c2/6794/c86/95251?formato=json")
    saida["classes_sm"] = {}
    for r in d:
        saida["classes_sm"].setdefault(INV[r["D1C"]], {})[r["D4C"]] = num(r["V"])
    saida["pnadc_renda_media_pc"] = {}
    for ano in range(2018, 2024):
        try:
            d = sidra(f"https://apisidra.ibge.gov.br/values/t/7395/n3/all/n1/1/v/4196/p/{ano}?formato=json")
        except Exception:
            continue
        for r in d:
            u = "BR" if r["D1C"] == "1" else INV[r["D1C"]]
            saida["pnadc_renda_media_pc"].setdefault(str(ano), {})[u] = num(r["V"])
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print("salvo", OUT, {k: len(v) for k, v in saida.items() if isinstance(v, dict)})


if __name__ == "__main__":
    main()
