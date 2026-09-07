#!/usr/bin/env python3
"""
Coleta a linha "Outras Deduções da Receita" do ICMS (DCA Anexo I-C, SICONFI)
por UF, 2019-2025.

Contexto: o pipeline usa "Receitas Brutas Realizadas" do ICMS (dca_icms_por_uf)
como base do φ^CPT e do Seguro-Receita, líquida apenas da cota-parte municipal
(Deduções - Transferências Constitucionais). Mas a própria contabilidade do
Tesouro Nacional (DCA Anexo I-C) tem uma quarta linha de dedução na conta do
ICMS -- "Outras Deduções da Receita" -- que o pipeline nunca extraiu. Para a
maioria dos estados essa linha é desprezível (<1% do bruto), mas para
MT, TO, MS, RO e GO ela é grande (9%-37% do bruto em anos recentes; GO teve
32% em 2019-2020 e caiu a ~0 depois -- provavelmente ligada a mecanismos de
diferimento/incentivo fiscal do ICMS sobre o agronegócio, ex.: FETHAB/MT,
FUNDERSUL/MS). Confirmado batendo a receita líquida resultante contra os
valores publicados por Gobetti e Monteiro para esses 4 estados (MT/MS/TO/RO
fecham a menos de 1% de diferença; GO não tem esse teste porque seu gap com
Gobetti vai na direção oposta e por outro motivo).

O código da conta do ICMS mudou de plano de contas em 2022:
  2019-2021: RO1.1.1.8.02.1.0
  2022-2025: RO1.1.1.4.50.1.0

Uso:
  python3 collect-dca-outras-deducoes.py
"""
import json
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUTPUT = HERE / "reforma-tributaria.json"
BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ANOS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
ICMS_CODES = ["RO1.1.1.4.50.1.0", "RO1.1.1.8.02.1.0"]

UF_COD = {
    "AC": 12, "AL": 27, "AM": 13, "AP": 16, "BA": 29, "CE": 23, "DF": 53, "ES": 32,
    "GO": 52, "MA": 21, "MG": 31, "MS": 50, "MT": 51, "PA": 15, "PB": 25, "PE": 26,
    "PI": 22, "PR": 41, "RJ": 33, "RN": 24, "RO": 11, "RR": 14, "RS": 43, "SC": 42,
    "SE": 28, "SP": 35, "TO": 17,
}


def fetch(url, retries=4):
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return json.loads(r.read())
        except Exception:
            if i < retries - 1:
                time.sleep(1.5 * (i + 1))
    return None


def get_outras_deducoes_icms(cod_ibge, ano):
    url = (f"{BASE_URL}/dca?an_exercicio={ano}&id_ente={cod_ibge}"
           f"&no_anexo=DCA-Anexo%20I-C")
    data = fetch(url)
    if not data:
        return None
    items = data.get("items", [])
    for code in ICMS_CODES:
        rows = {i["coluna"]: i["valor"] for i in items if i["cod_conta"] == code}
        if rows:
            return rows.get("Outras Deduções da Receita", 0.0) or 0.0
    return None


def main():
    resultado = {}
    total = len(UF_COD) * len(ANOS)
    n = 0
    for uf, cod in UF_COD.items():
        for ano in ANOS:
            n += 1
            val = get_outras_deducoes_icms(cod, ano)
            resultado.setdefault(str(ano), {})[uf] = val if val is not None else 0.0
            print(f"[{n}/{total}] {uf} {ano}: R$ {(val or 0)/1e6:.1f}mi" if val is not None
                  else f"[{n}/{total}] {uf} {ano}: N/D")
            time.sleep(0.3)

    with open(OUTPUT) as f:
        ref_data = json.load(f)
    ref_data["dca_icms_outras_deducoes_por_uf"] = resultado
    with open(OUTPUT, "w") as f:
        json.dump(ref_data, f, ensure_ascii=False, indent=2)

    print(f"\nGravado em {OUTPUT} (campo dca_icms_outras_deducoes_por_uf)")


if __name__ == "__main__":
    main()
