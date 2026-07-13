#!/usr/bin/env python3
"""
Coleta PIB nominal (BCB/SGS) e IPCA (BCB/SGS), combina com ICMS+ISS
(data/ibs-projecao-parametros.json, mesma base DCA usada nos Estudos 03 e
06 desta página) e calcula:

  - o "bolo" ICMS+ISS nominal, deflacionado (IPCA, reais de 2025) e como
    proporção do PIB, 2019-2025;
  - a Receita-Base de referência estimada para 2029-2033, sob a hipótese
    contrafactual de que não há inflação nem crescimento do PIB a partir
    de 2025: o bolo permanece congelado no valor de 2025 em todos os anos.

Fontes:
  - ICMS+ISS nacional (DCA): data/ibs-projecao-parametros.json, mesma base
    de TotalBR_2025 usada nos Estudos 03 e 06 (SICONFI/STN, DCA Anexo I-C)
  - PIB nominal anual: BCB/SGS série 1207 (Contas Nacionais Trimestrais/IBGE)
  - IPCA mensal: BCB/SGS série 433

Uso: python3 collect-ibs-carga-constante.py
"""

import json
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent
OUTPUT = DATA_DIR / "ibs-carga-constante.json"

ANO_BASE = 2025
ANOS_RESPOSTA = list(range(2029, 2034))  # 2029-2033


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def bcb_serie(codigo, data_inicial, data_final):
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
        f"?formato=json&dataInicial={data_inicial}&dataFinal={data_final}"
    )
    return fetch_json(url)


def main():
    parametros = json.load(open(DATA_DIR / "ibs-projecao-parametros.json"))
    totais_dca = parametros["global"]["totais_nacionais_dca"]

    # ── IPCA mensal, 2019-12/2025: índice acumulado (base arbitrária) ──
    ipca = bcb_serie(433, "01/01/2019", "31/12/2025")
    idx = {}
    val = 100.0
    for row in ipca:
        _, mm, yyyy = row["data"].split("/")
        val *= 1 + float(row["valor"]) / 100
        idx[f"{yyyy}-{mm}"] = val

    refs_periodo = {y: f"{y}-12" for y in range(2019, 2026)}
    deflator_to_2025 = {y: idx[refs_periodo[ANO_BASE]] / idx[refs_periodo[y]] for y in refs_periodo}

    # ── PIB nominal anual (BCB/SGS série 1207, já em R$, não em R$ milhões) ──
    pib_anual = bcb_serie(1207, "01/01/2019", "31/12/2025")
    pib_ano = {int(r["data"].split("/")[2]): float(r["valor"]) for r in pib_anual}

    # ── Série histórica: bolo nominal, real (reais de 2025) e % do PIB ──
    historico = []
    for y in range(2019, 2026):
        bolo_nominal = totais_dca[str(y)]["total"]
        bolo_real = bolo_nominal * deflator_to_2025[y]
        pib = pib_ano[y]
        historico.append({
            "ano": y,
            "bolo_nominal": round(bolo_nominal, 2),
            "bolo_real_2025": round(bolo_real, 2),
            "pib_nominal": round(pib, 2),
            "bolo_pct_pib": round(bolo_nominal / pib * 100, 4),
        })

    # ── A resposta: Receita-Base de referência 2029-2033, bolo congelado ──
    # Sem inflação nem crescimento do PIB a partir de 2025, o bolo nominal,
    # o bolo real e o bolo como % do PIB coincidem e não se alteram: o valor
    # de 2025 (mesmo TotalBR_2025 usado nos Estudos 03 e 06) se repete, sem
    # qualquer correção, em todos os anos do período 2029-2033.
    bolo_base = totais_dca[str(ANO_BASE)]["total"]
    pib_base = pib_ano[ANO_BASE]
    resposta = {
        "ano_base": ANO_BASE,
        "bolo_base": round(bolo_base, 2),
        "pib_base": round(pib_base, 2),
        "bolo_pct_pib_base": round(bolo_base / pib_base * 100, 4),
        "anos": [{"ano": y, "bolo": round(bolo_base, 2), "bolo_pct_pib": round(bolo_base / pib_base * 100, 4)} for y in ANOS_RESPOSTA],
    }

    output = {
        "_meta": {
            "descricao": "Bolo ICMS+ISS 2019-2025 (nominal, real e %PIB, base DCA) e a Receita-Base de referência estimada para 2029-2033 sob a hipótese de bolo congelado (sem inflação, sem crescimento do PIB a partir de 2025).",
            "fontes": {
                "icms_iss": "data/ibs-projecao-parametros.json (SICONFI/STN, DCA Anexo I-C) — mesma base de TotalBR_2025 usada nos Estudos 03 e 06 desta página",
                "pib_anual": "BCB/SGS série 1207 (Contas Nacionais Trimestrais, IBGE), 2019-2025",
                "ipca": "BCB/SGS série 433 (IPCA, variação mensal)",
            },
        },
        "historico": historico,
        "resposta": resposta,
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Gravado em {OUTPUT}")
    print(f"Receita-Base de referência (bolo congelado, base {ANO_BASE}): R$ {bolo_base/1e9:.1f} bi, {resposta['bolo_pct_pib_base']:.2f}% do PIB, repetida em 2029-2033")


if __name__ == "__main__":
    main()
