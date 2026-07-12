#!/usr/bin/env python3
"""
Coleta PIB nominal (BCB/SGS) e IPCA (BCB/SGS), combina com ICMS+ISS
(data/reforma-tributaria.json) e calcula:

  - o "bolo" ICMS+ISS nominal, deflacionado (IPCA, reais de abr/2026) e
    como proporção do PIB, 2019-2026;
  - uma projeção estilizada 2027-2033 da alíquota de referência do IBS
    sob três cenários de indexação do "bolo": nominal congelado, corrigido
    pelo IPCA e corrigido pelo PIB nominal (o alvo do art. 130 do ADCT).

Fontes:
  - PIB nominal anual: BCB/SGS série 1207 (Contas Nacionais Trimestrais/IBGE)
  - PIB acumulado 12 meses (para 2026, ano incompleto): BCB/SGS série 4382
  - IPCA mensal: BCB/SGS série 433
  - ICMS+ISS nacional: data/reforma-tributaria.json (SICONFI/STN, RREO Anexo 3)

Uso: python3 collect-ibs-carga-constante.py
"""

import json
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent
OUTPUT = DATA_DIR / "ibs-carga-constante.json"

# Estimativa inicial (jul/2024) da alíquota de referência do IBS, publicada pela
# Secretaria Extraordinária da Reforma Tributária (SERT/MF): 17,7% (IBS) + 8,8%
# (CBS) = 26,5% do total. Usada como âncora da simulação (Cenário C = 17,7% fixo).
ALIQUOTA_IBS_REF_2026 = 0.177

# Janela usada para o "crescimento nominal do PIB" que projeta a base
# tributável do consumo e o cenário "corrigido pelo PIB": média geométrica
# 2022-2025 (exclui o efeito de base do choque pandêmico de 2020-2021).
ANO_INICIO_CAGR_PIB = 2022
ANO_FIM_CAGR_PIB = 2025

ANOS_PROJECAO = list(range(2027, 2034))  # 2027-2033

# TotalBR_2025 usado como "bolo" fixo nos Estudos 03 e 06 desta página
# (data/ibs-projecao-parametros.json), para a comparação de validade do
# método de projeção com bolo constante.
TOTAL_BR_2025_ESTUDOS_03_06 = 1029573688573.62
ANO_TERMINAL_ESTUDOS_03_06 = 2033


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
    rt = json.load(open(DATA_DIR / "reforma-tributaria.json"))
    icms_br = rt["icms_br"]
    iss_br = rt["iss_br"]

    # ── IPCA mensal, 2019-06/2026: índice acumulado (base arbitrária) ──
    ipca = bcb_serie(433, "01/01/2019", "30/06/2026")
    idx = {}
    val = 100.0
    for row in ipca:
        _, mm, yyyy = row["data"].split("/")
        val *= 1 + float(row["valor"]) / 100
        idx[f"{yyyy}-{mm}"] = val

    refs_periodo = {
        2019: "2019-12", 2020: "2020-12", 2021: "2021-12", 2022: "2022-12",
        2023: "2023-12", 2024: "2024-12", 2025: "2025-12", 2026: "2026-04",
    }
    deflator_to_abr2026 = {y: idx[refs_periodo[2026]] / idx[refs_periodo[y]] for y in refs_periodo}

    # IPCA acumulado nos últimos 12 meses (jul/2025-jun/2026): premissa de
    # inflação usada no Cenário B da projeção.
    ipca_12m = bcb_serie(433, "01/07/2025", "30/06/2026")
    ipca_acum_12m = 1.0
    for row in ipca_12m:
        ipca_acum_12m *= 1 + float(row["valor"]) / 100
    ipca_acum_12m -= 1

    # ── PIB nominal anual (série 1207) e acumulado 12m (série 4382, p/ 2026) ──
    # Série 1207 já vem em R$ (não em R$ milhões, diferente da série 4382).
    pib_anual = bcb_serie(1207, "01/01/2019", "31/12/2025")
    pib_ano = {int(r["data"].split("/")[2]): float(r["valor"]) for r in pib_anual}

    pib_12m = bcb_serie(4382, "01/01/2019", "31/05/2026")
    pib_12m_por_periodo = {}
    for r in pib_12m:
        _, mm, yyyy = r["data"].split("/")
        pib_12m_por_periodo[f"{yyyy}-{mm}"] = float(r["valor"]) * 1e6
    pib_ano[2026] = pib_12m_por_periodo["2026-04"]  # mesmo período-base do bolo 2026 (RREO período 2)

    g_pib_proj = (pib_ano[ANO_FIM_CAGR_PIB] / pib_ano[ANO_INICIO_CAGR_PIB]) ** (
        1 / (ANO_FIM_CAGR_PIB - ANO_INICIO_CAGR_PIB)
    ) - 1

    # ── Crescimento REAL do PIB (BCB/SGS série 7326, variação real anual %) ──
    # Duas janelas: a média 2012-2021, mesmo período usado pelo art. 130, §3º,
    # I e II do ADCT para o "Teto de Referência"; e a média 2022-2025 (ritmo
    # recente), para comparar a sensibilidade do exercício de validade do
    # "bolo fixo" dos Estudos 03 e 06 a cada uma dessas janelas.
    pib_real_var = bcb_serie(7326, "01/01/2012", "31/12/2025")
    pib_real_var_ano = {int(r["data"].split("/")[2]): float(r["valor"]) for r in pib_real_var}
    g_real_2012_2021 = sum(pib_real_var_ano[y] for y in range(2012, 2022)) / 10 / 100
    g_real_2022_2025 = sum(pib_real_var_ano[y] for y in range(2022, 2026)) / 4 / 100

    n_terminal = ANO_TERMINAL_ESTUDOS_03_06 - 2025
    bolo_2033_baixo = TOTAL_BR_2025_ESTUDOS_03_06 * (1 + g_real_2012_2021) ** n_terminal
    bolo_2033_alto = TOTAL_BR_2025_ESTUDOS_03_06 * (1 + g_real_2022_2025) ** n_terminal

    # ── Série histórica: bolo nominal, real (reais de abr/2026) e % do PIB ──
    historico = []
    for y in range(2019, 2027):
        bolo_nominal = icms_br[str(y)] + iss_br[str(y)]
        bolo_real = bolo_nominal * deflator_to_abr2026[y]
        pib = pib_ano[y]
        historico.append({
            "ano": y,
            "bolo_nominal": round(bolo_nominal, 2),
            "bolo_real_abr2026": round(bolo_real, 2),
            "pib_nominal": round(pib, 2),
            "bolo_pct_pib": round(bolo_nominal / pib * 100, 4),
        })

    bolo_2026 = historico[-1]["bolo_nominal"]
    base_tributavel_2026 = bolo_2026 / ALIQUOTA_IBS_REF_2026

    # ── Projeção 2027-2033: três cenários de indexação do "bolo" ──
    projecao = []
    for y in ANOS_PROJECAO:
        n = y - 2026
        base_projetada = base_tributavel_2026 * (1 + g_pib_proj) ** n
        bolo_nominal_congelado = bolo_2026
        bolo_ipca = bolo_2026 * (1 + ipca_acum_12m) ** n
        bolo_pib = bolo_2026 * (1 + g_pib_proj) ** n
        projecao.append({
            "ano": y,
            "base_tributavel_projetada": round(base_projetada, 2),
            "bolo_nominal_congelado": round(bolo_nominal_congelado, 2),
            "bolo_corrigido_ipca": round(bolo_ipca, 2),
            "bolo_corrigido_pib": round(bolo_pib, 2),
            "aliquota_nominal_congelado": round(bolo_nominal_congelado / base_projetada * 100, 4),
            "aliquota_corrigido_ipca": round(bolo_ipca / base_projetada * 100, 4),
            "aliquota_corrigido_pib": round(bolo_pib / base_projetada * 100, 4),
        })

    output = {
        "_meta": {
            "descricao": "Bolo ICMS+ISS 2019-2026 (nominal, real e %PIB) e projeção estilizada 2027-2033 da alíquota de referência do IBS sob três cenários de indexação, ilustrando a premissa de neutralidade de carga tributária do art. 130 do ADCT (EC 132/2023, LC 214/2025).",
            "fontes": {
                "icms_iss": "data/reforma-tributaria.json (SICONFI/STN, RREO Anexo 3, Total Últimos 12 Meses)",
                "pib_anual": "BCB/SGS série 1207 (Contas Nacionais Trimestrais, IBGE), 2019-2025",
                "pib_12m_2026": "BCB/SGS série 4382 (PIB acumulado 12 meses, valores correntes), período mar-abr/2026",
                "ipca": "BCB/SGS série 433 (IPCA, variação mensal)",
            },
            "parametros": {
                "aliquota_ibs_referencia_2026": ALIQUOTA_IBS_REF_2026,
                "aliquota_ibs_referencia_2026_fonte": "Nota Técnica SERT/MF, jul/2024: alíquota total estimada 26,5% = 17,7% (IBS) + 8,8% (CBS)",
                "g_pib_nominal_proj": round(g_pib_proj, 6),
                "g_pib_nominal_proj_janela": f"CAGR nominal do PIB, {ANO_INICIO_CAGR_PIB}-{ANO_FIM_CAGR_PIB} (BCB/SGS 1207)",
                "ipca_acumulado_12m": round(ipca_acum_12m, 6),
                "ipca_acumulado_12m_janela": "jul/2025-jun/2026 (BCB/SGS 433)",
                "base_tributavel_implicita_2026": round(base_tributavel_2026, 2),
            },
        },
        "historico": historico,
        "projecao": projecao,
        "validade_bolo_fixo": {
            "descricao": "Comparação entre o 'bolo' fixo em preços de 2025 usado nos Estudos 03 e 06 desta página (TotalBR_2025, sem correção) e o que a meta de proporcionalidade ao PIB do art. 130 do ADCT implicaria em 2033, sob duas janelas de crescimento real do PIB.",
            "total_br_2025": TOTAL_BR_2025_ESTUDOS_03_06,
            "ano_terminal": ANO_TERMINAL_ESTUDOS_03_06,
            "g_real_2012_2021": round(g_real_2012_2021, 6),
            "g_real_2012_2021_fonte": "BCB/SGS série 7326 (variação real anual do PIB), média 2012-2021 — mesma janela do 'Teto de Referência' no art. 130, §3º, I e II, do ADCT",
            "g_real_2022_2025": round(g_real_2022_2025, 6),
            "g_real_2022_2025_fonte": "BCB/SGS série 7326, média 2022-2025 (ritmo recente)",
            "bolo_2033_flat": round(TOTAL_BR_2025_ESTUDOS_03_06, 2),
            "bolo_2033_baixo": round(bolo_2033_baixo, 2),
            "bolo_2033_alto": round(bolo_2033_alto, 2),
        },
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Gravado em {OUTPUT}")
    print(f"g_pib_proj={g_pib_proj:.4%}  ipca_12m={ipca_acum_12m:.4%}  base_2026=R$ {base_tributavel_2026/1e9:.1f} bi")
    print(f"g_real_2012_2021={g_real_2012_2021:.4%}  g_real_2022_2025={g_real_2022_2025:.4%}")
    print(f"bolo_2033: flat={TOTAL_BR_2025_ESTUDOS_03_06/1e9:.1f}  baixo={bolo_2033_baixo/1e9:.1f}  alto={bolo_2033_alto/1e9:.1f}")


if __name__ == "__main__":
    main()
