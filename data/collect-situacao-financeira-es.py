#!/usr/bin/env python3
"""
Coleta indicadores de situação financeira do Governo do Estado do ES via
SICONFI (Poder Executivo, esfera Estadual, id_ente/cod_ibge=32), para
montar uma série histórica 2019-2026 com foco em fragilidade fiscal:

- RGF Anexo 05: disponibilidade de caixa líquida (livre e vinculada) e
  restos a pagar não processados — "sobra caixa livre no fim do ano?"
- RGF Anexo 02: dívida consolidada líquida (DCL) vs RCL e limite do
  Senado — "a dívida líquida está subindo?"
- RGF Anexo 01: despesa total com pessoal vs limite da LRF — "a folha
  está pressionando o limite?"
- RREO Anexo 01: receita realizada vs despesa paga/liquidada no
  exercício — "o caixa do ano fechou positivo ou negativo?"
- RREO Anexo 03: receita corrente líquida (RCL), últimos 12 meses.
- RREO Anexo 06: resultado primário (com e sem RPPS) e nominal —
  "o Estado está gerando ou consumindo poupança?"
- RREO Anexo 07: estoque total de restos a pagar — "despesa empurrada
  para o ano seguinte por falta de caixa?"

RGF só tem dado consolidado (Q3 = até 31/dez) publicado para o ES nos
anos testados; por isso a série de RGF é anual (fim de exercício). RREO
usa o último bimestre publicado no ano (6 = ano fechado; 2 = mais
recente em 2026, ano corrente/último do mandato).

Uso:
  python3 collect-situacao-financeira-es.py
"""

import json
import time
import urllib.request
from pathlib import Path

BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ID_ENTE = 32  # cod_ibge do Estado do Espírito Santo
ESFERA = "E"
PODER = "E"  # Poder Executivo

ANOS_RGF = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
RREO_PERIODO = {
    2019: 6, 2020: 6, 2021: 6, 2022: 6, 2023: 6, 2024: 6, 2025: 6,
    2026: 2,  # bimestre mar-abr, mais recente disponível em 2026
}

OUTPUT = Path(__file__).parent / "situacao-financeira-es.json"


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


def rgf_items(ano, anexo, periodo=3):
    url = (
        f"{BASE}/rgf?an_exercicio={ano}&in_periodicidade=Q"
        f"&nr_periodo={periodo}&co_tipo_demonstrativo=RGF"
        f"&no_anexo=RGF-Anexo%20{anexo}&co_esfera={ESFERA}"
        f"&id_ente={ID_ENTE}&co_poder={PODER}"
    )
    data = fetch(url)
    time.sleep(1.1)
    return data.get("items", []) if data else []


def rreo_items(ano, anexo, periodo):
    url = (
        f"{BASE}/rreo?an_exercicio={ano}&nr_periodo={periodo}"
        f"&co_tipo_demonstrativo=RREO&no_anexo=RREO-Anexo%20{anexo}"
        f"&co_esfera={ESFERA}&id_ente={ID_ENTE}"
    )
    data = fetch(url)
    time.sleep(1.1)
    return data.get("items", []) if data else []


def find(items, conta_prefix=None, conta_contains=None, coluna_contains=None, coluna_exact=None):
    for it in items:
        if conta_prefix is not None and not it["conta"].startswith(conta_prefix):
            continue
        if conta_contains is not None and conta_contains not in it["conta"]:
            continue
        if coluna_exact is not None and it["coluna"] != coluna_exact:
            continue
        if coluna_contains is not None and coluna_contains not in it["coluna"]:
            continue
        return it["valor"]
    return None


def collect_rgf_year(ano):
    print(f"  RGF {ano} (Anexo 05 - caixa)...")
    a5 = rgf_items(ano, "05")
    print(f"  RGF {ano} (Anexo 02 - dívida)...")
    a2 = rgf_items(ano, "02")
    print(f"  RGF {ano} (Anexo 01 - pessoal)...")
    a1 = rgf_items(ano, "01")

    if not a5 and not a2 and not a1:
        return None

    out = {
        "caixa_bruta_nao_vinculada": find(
            a5, conta_contains="RECURSOS NÃO VINCULADOS (I)",
            coluna_contains="CAIXA BRUTA",
        ),
        "caixa_liquida_nao_vinculada": find(
            a5, conta_contains="RECURSOS NÃO VINCULADOS (I)",
            coluna_contains="LÍQUIDA (APÓS A INSCRIÇÃO",
        ),
        "caixa_bruta_vinculada": find(
            a5, conta_contains="RECURSOS VINCULADOS (EXCETO AO RPPS) (II)",
            coluna_contains="CAIXA BRUTA",
        ),
        "caixa_liquida_vinculada": find(
            a5, conta_contains="RECURSOS VINCULADOS (EXCETO AO RPPS) (II)",
            coluna_contains="LÍQUIDA (APÓS A INSCRIÇÃO",
        ),
        "restos_a_pagar_nao_processados_nao_vinc": find(
            a5, conta_contains="RECURSOS NÃO VINCULADOS (I)",
            coluna_contains="RESTOS A PAGAR EMPENHADOS E NÃO LIQUIDADOS DO EXERCÍCIO",
        ),
        "dcl": find(
            a2, conta_prefix="DÍVIDA CONSOLIDADA LÍQUIDA",
            coluna_contains="Até o 3º Quadrimestre",
        ),
        "rcl_rgf": find(
            a2, conta_prefix="RECEITA CORRENTE LÍQUIDA - RCL",
            coluna_contains="Até o 3º Quadrimestre",
        ),
        "limite_senado_divida": find(
            a2, conta_prefix="LIMITE DEFINIDO POR RESOLUÇÃO DO SENADO",
            coluna_contains="Até o 3º Quadrimestre",
        ),
        "despesa_pessoal_valor": find(
            a1, conta_prefix="DESPESA TOTAL COM PESSOAL",
            coluna_exact="Valor",
        ),
        "despesa_pessoal_pct_rcl": find(
            a1, conta_prefix="DESPESA TOTAL COM PESSOAL",
            coluna_contains="% sobre a RCL",
        ),
        "limite_pessoal_maximo_pct": find(
            a1, conta_prefix="LIMITE MÁXIMO",
            coluna_contains="% sobre a RCL",
        ),
    }
    return out


def collect_rreo_year(ano):
    periodo = RREO_PERIODO[ano]
    print(f"  RREO {ano} p{periodo} (Anexo 01 - orçamento)...")
    a1 = rreo_items(ano, "01", periodo)
    print(f"  RREO {ano} p{periodo} (Anexo 03 - RCL)...")
    a3 = rreo_items(ano, "03", periodo)
    print(f"  RREO {ano} p{periodo} (Anexo 06 - resultado primário)...")
    a6 = rreo_items(ano, "06", periodo)
    print(f"  RREO {ano} p{periodo} (Anexo 07 - restos a pagar)...")
    a7 = rreo_items(ano, "07", periodo)

    if not a1 and not a3 and not a6 and not a7:
        return None

    out = {
        "periodo_bimestre": periodo,
        "receita_realizada": find(
            a1, conta_prefix="TOTAL DAS RECEITAS",
            coluna_contains="Até o Bimestre (c)",
        ),
        "despesa_paga": find(
            a1, conta_prefix="TOTAL DAS DESPESAS",
            coluna_contains="DESPESAS PAGAS ATÉ O BIMESTRE",
        ),
        "despesa_liquidada": find(
            a1, conta_prefix="TOTAL DAS DESPESAS",
            coluna_contains="DESPESAS LIQUIDADAS ATÉ O BIMESTRE",
        ),
        "rcl_rreo": find(
            a3, conta_prefix="RECEITA CORRENTE LÍQUIDA (III)",
            coluna_exact="TOTAL (ÚLTIMOS 12 MESES)",
        ),
        "resultado_primario_com_rpps": find(
            a6, conta_prefix="RESULTADO PRIMÁRIO (COM RPPS)",
            coluna_exact="VALOR",
        ),
        "resultado_primario_sem_rpps": find(
            a6, conta_prefix="RESULTADO PRIMÁRIO (SEM RPPS) - Acima da Linha",
            coluna_exact="VALOR",
        ),
        "resultado_nominal_sem_rpps": find(
            a6, conta_prefix="RESULTADO NOMINAL (SEM RPPS) - Acima da Linha",
            coluna_exact="VALOR",
        ),
        "restos_a_pagar_estoque_total": find(
            a7, conta_prefix="TOTAL (III)",
            coluna_contains="Saldo Total",
        ),
    }
    return out


def main():
    result = {
        "fonte": "SICONFI/Tesouro Nacional - RGF (Poder Executivo, Anexos 01/02/05) e RREO (Anexos 01/03/06/07)",
        "ente": "Governo do Estado do Espírito Santo",
        "cod_ibge": ID_ENTE,
        "nota_metodologica": (
            "RGF só possui publicação consolidada (3º quadrimestre = "
            "posição em 31/dez) para o ES nos anos testados; a série de "
            "caixa/dívida/pessoal é, portanto, um retrato de fim de "
            "exercício. RREO usa o último bimestre disponível em cada "
            "ano (6 = ano fechado; 2 = 2026, ano corrente)."
        ),
        "unidade": "R$ nominais (não deflacionados)",
        "rgf": {},
        "rreo": {},
    }

    print("=== Coletando RGF (posição de fim de ano) ===")
    for ano in ANOS_RGF:
        r = collect_rgf_year(ano)
        if r:
            result["rgf"][str(ano)] = r

    print("\n=== Coletando RREO (execução orçamentária) ===")
    for ano in sorted(RREO_PERIODO):
        r = collect_rreo_year(ano)
        if r:
            result["rreo"][str(ano)] = r

    with open(OUTPUT, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nDados salvos em {OUTPUT}")


if __name__ == "__main__":
    main()
