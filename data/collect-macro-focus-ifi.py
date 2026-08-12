#!/usr/bin/env python3
"""
Coleta os parâmetros macroeconômicos para o Estudo 11 (projeção do IBS
total, Brasil, 2029-2033):

  - PIB nominal anual (BCB/SGS série 1207) e IPCA mensal (BCB/SGS série
    433), 2013-2025 (histórico realizado; mesma janela do Estudo 11, que
    também só tem ICMS/ISS via DCA a partir de 2013). Chegou a se testar
    uma janela mais longa (2005-2025) para comparar a média de crescimento
    real de longo prazo com a premissa da IFI, mas a decisão (autor do
    site, 12/ago/2026) foi manter a IFI: o risco de mudança de metodologia
    nas Contas Nacionais em anos mais distantes (rebase de referência,
    revisões retroativas) tornaria essa comparação pouco confiável sem
    uma verificação à parte que este estudo não faz.
  - Mediana do Boletim Focus (BCB, Sistema de Expectativas de Mercado,
    API Olinda) para crescimento real do PIB e IPCA, 2026-2030 — o Focus
    não projeta além de ~5 anos à frente
  - Para 2031-2033, o Focus não cobre: usa-se a projeção da IFI
    (Instituição Fiscal Independente, vinculada ao Senado Federal),
    RAF 107 (dez/2025): PIB real 2,2% a.a. entre 2027-2035, IPCA
    convergindo suavemente a 3,0% (centro da meta contínua). Como a IFI
    não detalha ano a ano dentro desse intervalo, adota-se 2,2% a.a. e
    3,0% a.a. constantes para 2031-2033 — a simplificação está descrita
    explicitamente na página do estudo.

Uso: python3 collect-macro-focus-ifi.py
"""

import json
import urllib.request
import urllib.parse
from pathlib import Path

DATA_DIR = Path(__file__).parent
OUTPUT = DATA_DIR / "macro-parametros.json"

ANO_HIST_INICIO = 2013
ANO_HIST_FIM = 2025
ANOS_FOCUS = [2026, 2027, 2028, 2029, 2030]
ANOS_IFI = [2031, 2032, 2033]

IFI_PIB_REAL = 0.022   # RAF 107, dez/2025: PIB real 2,2% a.a., 2027-2035
IFI_IPCA = 0.030       # RAF 107, dez/2025: convergência suave ao centro da meta contínua (3,0%)


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def bcb_sgs(codigo, data_inicial, data_final):
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
        f"?formato=json&dataInicial={data_inicial}&dataFinal={data_final}"
    )
    return fetch_json(url)


def bcb_focus_anual(indicador, data_referencia):
    filtro = f"Indicador eq '{indicador}' and DataReferencia eq '{data_referencia}' and baseCalculo eq 0"
    url = (
        "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais"
        f"?$filter={urllib.parse.quote(filtro)}&$orderby={urllib.parse.quote('Data desc')}&$top=1&$format=json"
    )
    data = fetch_json(url)
    items = data.get("value", [])
    return items[0] if items else None


def main():
    # ── PIB nominal e IPCA histórico, 2015-2025 ──
    pib_anual_raw = bcb_sgs(1207, f"01/01/{ANO_HIST_INICIO}", f"31/12/{ANO_HIST_FIM}")
    pib_ano = {int(r["data"].split("/")[2]): float(r["valor"]) for r in pib_anual_raw}

    ipca_raw = bcb_sgs(433, f"01/01/{ANO_HIST_INICIO}", f"31/12/{ANO_HIST_FIM}")
    idx = {}
    val = 100.0
    for row in ipca_raw:
        _, mm, yyyy = row["data"].split("/")
        val *= 1 + float(row["valor"]) / 100
        idx[f"{yyyy}-{mm}"] = val
    base2025 = idx[f"{ANO_HIST_FIM}-12"]
    deflator_to_2025 = {
        y: base2025 / idx[f"{y}-12"] for y in range(ANO_HIST_INICIO, ANO_HIST_FIM + 1)
    }

    # ── Boletim Focus (mediana, base de cálculo padrão), 2026-2030 ──
    focus = {}
    focus_data_pesquisa = None
    for ano in ANOS_FOCUS:
        pib_item = bcb_focus_anual("PIB Total", str(ano))
        ipca_item = bcb_focus_anual("IPCA", str(ano))
        focus[str(ano)] = {
            "pib_real_pct": pib_item["Mediana"] / 100 if pib_item else None,
            "ipca_pct": ipca_item["Mediana"] / 100 if ipca_item else None,
            "n_respondentes_pib": pib_item["numeroRespondentes"] if pib_item else None,
            "n_respondentes_ipca": ipca_item["numeroRespondentes"] if ipca_item else None,
        }
        if pib_item:
            focus_data_pesquisa = pib_item["Data"]

    # ── IFI RAF 107 (dez/2025), 2031-2033 ──
    ifi = {str(ano): {"pib_real_pct": IFI_PIB_REAL, "ipca_pct": IFI_IPCA} for ano in ANOS_IFI}

    output = {
        "_meta": {
            "descricao": "Parâmetros macroeconômicos para o Estudo 11 (projeção do IBS total, Brasil, 2029-2033).",
            "fontes": {
                "pib_nominal_historico": "BCB/SGS série 1207 (Contas Nacionais Trimestrais/IBGE), 2013-2025",
                "ipca_historico": "BCB/SGS série 433 (IPCA, variação mensal), 2013-2025",
                "projecao_2026_2030": "BCB, Sistema de Expectativas de Mercado (Boletim Focus), mediana, baseCalculo=0, consulta via API Olinda",
                "projecao_2031_2033": "IFI (Instituição Fiscal Independente, Senado Federal), RAF 107, 18/dez/2025: PIB real 2,2% a.a. (2027-2035), IPCA convergindo suavemente a 3,0% (centro da meta contínua)",
            },
            "data_pesquisa_focus": focus_data_pesquisa,
            "nota_ifi": "A IFI não detalha o crescimento do PIB nem o IPCA ano a ano dentro do intervalo 2027-2035; para 2031-2033 (fora do horizonte do Focus) adotam-se os valores constantes de 2,2% a.a. (PIB real) e 3,0% a.a. (IPCA), simplificação explícita.",
        },
        "pib_nominal_historico": {str(y): pib_ano[y] for y in range(ANO_HIST_INICIO, ANO_HIST_FIM + 1)},
        "deflator_ipca_para_2025": {str(y): deflator_to_2025[y] for y in range(ANO_HIST_INICIO, ANO_HIST_FIM + 1)},
        "projecao_2026_2030_focus": focus,
        "projecao_2031_2033_ifi": ifi,
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Gravado em {OUTPUT}")
    print(f"\nData da pesquisa Focus usada: {focus_data_pesquisa}")
    print("\n=== Focus 2026-2030 (mediana) ===")
    for ano in ANOS_FOCUS:
        f = focus[str(ano)]
        print(f"{ano}: PIB real {f['pib_real_pct']*100:.2f}% | IPCA {f['ipca_pct']*100:.2f}%")
    print("\n=== IFI 2031-2033 ===")
    for ano in ANOS_IFI:
        print(f"{ano}: PIB real {IFI_PIB_REAL*100:.1f}% | IPCA {IFI_IPCA*100:.1f}%")


if __name__ == "__main__":
    main()
