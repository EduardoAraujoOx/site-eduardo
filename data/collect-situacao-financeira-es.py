#!/usr/bin/env python3
"""
Coleta indicadores de situação financeira do Governo do Estado do ES via
SICONFI (Poder Executivo, esfera Estadual, id_ente/cod_ibge=32), para
montar uma série histórica 2019-2026 com foco em fragilidade fiscal:

- RGF Anexo 05: disponibilidade de caixa líquida (livre e vinculada) e
  restos a pagar não processados — "sobra caixa livre no fim do ano?"
- RGF Anexo 02: dívida consolidada líquida (DCL) vs RCL e limite do
  Senado, com a decomposição bruta/deduções usada na página 2 do
  diagnóstico — "a dívida líquida está subindo, e o que a compõe?"
- RGF Anexo 01: despesa total com pessoal vs limite da LRF — "a folha
  está pressionando o limite?"
- RGF Anexo 03: garantias concedidas a entidades controladas vs limite
  do Senado — "há passivo contingente relevante em avais?"
- RGF Anexo 04: operações de crédito contratadas vs limite do Senado.
- RREO Anexo 01: receita realizada vs despesa paga/liquidada no
  exercício — "o caixa do ano fechou positivo ou negativo?"
- RREO Anexo 03: receita corrente líquida (RCL), últimos 12 meses.
- RREO Anexo 06: resultado primário (com e sem RPPS) e nominal —
  "o Estado está gerando ou consumindo poupança?"
- RREO Anexo 07: estoque total de restos a pagar — "despesa empurrada
  para o ano seguinte por falta de caixa?"

RGF só tem dado consolidado por quadrimestre; a série 2019-2025 usa o
3º quadrimestre (posição de 31/dez, ano fechado), e 2026 usa o 1º
quadrimestre (único publicado até a data de coleta, posição de 30/abr,
ano corrente). RREO usa o último bimestre publicado no ano (6 = ano
fechado; 2 = mais recente em 2026, ano corrente/último do mandato).

Dados que o diagnóstico usa mas que NÃO são coletados por este script,
por virem de fontes fora do SICONFI (mantidos como citação direta no
HTML, não neste JSON): despesa por função (RREO Anexo 02, série
função/subfunção sem campo de nível confiável na API pública),
passivo atuarial por fundo (IPAJM), CAPAG indicativa de 2025 e
poupança corrente/RTE (SEFAZ-ES), parecer prévio (TCE-ES), Audiência
Pública de 2026 (SEFAZ-ES).

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

ANOS_RGF = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
RGF_QUADRIMESTRE = {ano: 3 for ano in ANOS_RGF}
RGF_QUADRIMESTRE[2026] = 1  # único quadrimestre publicado até a data de coleta
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


def find(items, conta_prefix=None, conta_contains=None, conta_exact=None,
         coluna_contains=None, coluna_exact=None):
    for it in items:
        if conta_exact is not None and it["conta"] != conta_exact:
            continue
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


def collect_rgf_year(ano, quad=None):
    quad = quad if quad is not None else RGF_QUADRIMESTRE.get(ano, 3)
    coluna_quad = f"Até o {quad}º Quadrimestre"

    print(f"  RGF {ano} (Anexo 05 - caixa)...")
    a5 = rgf_items(ano, "05", periodo=quad)
    print(f"  RGF {ano} (Anexo 02 - dívida)...")
    a2 = rgf_items(ano, "02", periodo=quad)
    print(f"  RGF {ano} (Anexo 01 - pessoal)...")
    a1 = rgf_items(ano, "01", periodo=quad)
    print(f"  RGF {ano} (Anexo 03 - garantias)...")
    a3 = rgf_items(ano, "03", periodo=quad)
    print(f"  RGF {ano} (Anexo 04 - operações de crédito)...")
    a4 = rgf_items(ano, "04", periodo=quad)

    if not a5 and not a2 and not a1 and not a3 and not a4:
        return None

    # No Anexo 5, a "líquida" fica só após a inscrição em RPNP; no
    # 1º/2º quadrimestre o rótulo da coluna não muda, mas o quadrimestre
    # de referência do restante dos anexos sim.
    out = {
        "quadrimestre": quad,
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
            coluna_contains=coluna_quad,
        ),
        "divida_consolidada_bruta": find(
            a2, conta_prefix="DÍVIDA CONSOLIDADA - DC (I)",
            coluna_contains=coluna_quad,
        ),
        "disponibilidade_caixa_bruta_dcl": find(
            a2, conta_exact="Disponibilidade de Caixa Bruta",
            coluna_contains=coluna_quad,
        ),
        "disponibilidade_caixa_dcl": find(
            a2, conta_exact="Disponibilidade de Caixa",
            coluna_contains=coluna_quad,
        ),
        "restos_a_pagar_processados_dcl": find(
            a2, conta_contains="Restos a Pagar Processados",
            coluna_contains=coluna_quad,
        ),
        "depositos_restituiveis_valores_vinculados": find(
            a2, conta_contains="Depósitos Restituíveis e Valores Vinculados",
            coluna_contains=coluna_quad,
        ),
        "deducoes_totais_dcl": find(
            a2, conta_prefix="DEDUÇÕES (II)",
            coluna_contains=coluna_quad,
        ),
        "rcl_rgf": find(
            a2, conta_prefix="RECEITA CORRENTE LÍQUIDA - RCL",
            coluna_contains=coluna_quad,
        ),
        "limite_senado_divida": find(
            a2, conta_prefix="LIMITE DEFINIDO POR RESOLUÇÃO DO SENADO",
            coluna_contains=coluna_quad,
        ),
        "passivo_atuarial_rpps": find(
            a2, conta_prefix="Passivo Atuarial",
            coluna_contains=coluna_quad,
        ),
        "demais_haveres_financeiros": find(
            a2, conta_prefix="Demais Haveres Financeiros",
            coluna_contains=coluna_quad,
        ),
        "precatorios_pos_2000_fora_dc": find(
            a2, conta_prefix="Precatórios Posteriores a 05/05/2000",
            coluna_contains=coluna_quad,
        ),
        "rp_nao_processados_total_governo": find(
            a2, conta_prefix="RP Não-Processados",
            coluna_contains=coluna_quad,
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
        "garantias_pct_rcl_ajustada": find(
            a3, conta_contains="% do TOTAL DAS GARANTIAS sobre a RCL AJUSTADA",
            coluna_contains=coluna_quad,
        ),
        "limite_senado_garantias_pct": find(
            a3, conta_prefix="LIMITE DEFINIDO POR RESOLUÇÃO DO SENADO FEDERAL",
            coluna_contains="% SOBRE A RCL AJUSTADA",
        ),
        "operacoes_credito_pct_rcl_ajustada": find(
            a4, conta_prefix="TOTAL CONSIDERADO PARA FINS DA APURAÇÃO DO CUMPRIMENTO DO LIMITE",
            coluna_exact="% SOBRE A RCL AJUSTADA",
        ),
        "limite_senado_operacoes_credito_pct": find(
            a4, conta_prefix="LIMITE GERAL DEFINIDO POR RESOLUÇÃO DO SENADO FEDERAL",
            coluna_exact="% SOBRE A RCL AJUSTADA",
        ),
    }
    return out


def collect_rreo_year(ano, periodo=None):
    periodo = periodo if periodo is not None else RREO_PERIODO[ano]
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

    # "Receita agropecuária, industrial e de serviços" (página 8) é a soma
    # de três contas separadas do RREO Anexo 1, não uma conta única.
    _agro = find(a1, conta_exact="RECEITA AGROPECUÁRIA", coluna_contains="Até o Bimestre (c)")
    _ind = find(a1, conta_exact="RECEITA INDUSTRIAL", coluna_contains="Até o Bimestre (c)")
    _serv = find(a1, conta_exact="RECEITA DE SERVIÇOS", coluna_contains="Até o Bimestre (c)")
    _receita_agro_industrial_servicos = (
        (_agro or 0) + (_ind or 0) + (_serv or 0)
        if any(v is not None for v in (_agro, _ind, _serv)) else None
    )

    out = {
        "periodo_bimestre": periodo,
        "receita_realizada": find(
            a1, conta_prefix="TOTAL DAS RECEITAS",
            coluna_contains="Até o Bimestre (c)",
        ),
        "receita_exceto_intraorcamentaria": find(
            a1, conta_prefix="RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS)",
            coluna_contains="Até o Bimestre (c)",
        ),
        "receita_intraorcamentaria": find(
            a1, conta_prefix="RECEITAS (INTRA-ORÇAMENTÁRIAS)",
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
        "despesa_empenhada": find(
            a1, conta_prefix="TOTAL DAS DESPESAS",
            coluna_contains="DESPESAS EMPENHADAS ATÉ O BIMESTRE",
        ),
        "receita_patrimonial": find(
            a1, conta_prefix="RECEITA PATRIMONIAL",
            coluna_contains="Até o Bimestre (c)",
        ),
        "receita_previsao_atualizada": find(
            a1, conta_prefix="TOTAL DAS RECEITAS",
            coluna_exact="PREVISÃO ATUALIZADA (a)",
        ),
        "receita_pct_previsao_realizado": find(
            a1, conta_prefix="TOTAL DAS RECEITAS",
            coluna_exact="% (c/a)",
        ),
        "despesa_dotacao_atualizada": find(
            a1, conta_prefix="TOTAL DAS DESPESAS",
            coluna_contains="DOTAÇÃO ATUALIZADA",
        ),
        "receita_impostos_taxas": find(
            a1, conta_prefix="IMPOSTOS, TAXAS E CONTRIBUIÇÕES DE MELHORIA",
            coluna_contains="Até o Bimestre (c)",
        ),
        "receita_contribuicoes": find(
            a1, conta_exact="CONTRIBUIÇÕES",
            coluna_contains="Até o Bimestre (c)",
        ),
        "receita_transferencias_correntes": find(
            a1, conta_prefix="TRANSFERÊNCIAS CORRENTES",
            coluna_contains="Até o Bimestre (c)",
        ),
        "receita_agropecuaria_industrial_servicos": _receita_agro_industrial_servicos,
        "receita_outras_correntes": find(
            a1, conta_prefix="OUTRAS RECEITAS CORRENTES",
            coluna_contains="Até o Bimestre (c)",
        ),
        "receita_de_capital": find(
            a1, conta_prefix="RECEITAS DE CAPITAL",
            coluna_contains="Até o Bimestre (c)",
        ),
        "despesa_pessoal_encargos": find(
            a1, conta_prefix="PESSOAL E ENCARGOS SOCIAIS",
            coluna_contains="DESPESAS EMPENHADAS ATÉ O BIMESTRE",
        ),
        "despesa_juros_encargos_divida": find(
            a1, conta_prefix="JUROS E ENCARGOS DA DÍVIDA",
            coluna_contains="DESPESAS EMPENHADAS ATÉ O BIMESTRE",
        ),
        "despesa_outras_correntes": find(
            a1, conta_prefix="OUTRAS DESPESAS CORRENTES",
            coluna_contains="DESPESAS EMPENHADAS ATÉ O BIMESTRE",
        ),
        "despesa_investimentos": find(
            a1, conta_prefix="INVESTIMENTOS",
            coluna_contains="DESPESAS EMPENHADAS ATÉ O BIMESTRE",
        ),
        "despesa_inversoes_financeiras": find(
            a1, conta_prefix="INVERSÕES FINANCEIRAS",
            coluna_contains="DESPESAS EMPENHADAS ATÉ O BIMESTRE",
        ),
        "despesa_amortizacao_divida": find(
            a1, conta_prefix="AMORTIZAÇÃO DA DÍVIDA",
            coluna_contains="DESPESAS EMPENHADAS ATÉ O BIMESTRE",
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
        "fonte": "SICONFI/Tesouro Nacional - RGF (Poder Executivo, Anexos 01/02/03/04/05) e RREO (Anexos 01/03/06/07)",
        "ente": "Governo do Estado do Espírito Santo",
        "cod_ibge": ID_ENTE,
        "nota_metodologica": (
            "RGF usa o 3º quadrimestre (posição em 31/dez, ano fechado) "
            "para 2019-2025 e o 1º quadrimestre (posição em 30/abr, único "
            "publicado até a coleta) para 2026; o campo quadrimestre em "
            "cada registro de rgf indica qual foi usado. RREO usa o "
            "último bimestre disponível em cada ano (6 = ano fechado; "
            "2 = 2026, ano corrente). "
            "passivo_atuarial_rpps, demais_haveres_financeiros e "
            "precatorios_pos_2000_fora_dc são itens de memória do "
            "RGF-Anexo 02 (não entram no cálculo da DCL, exceto haveres "
            "financeiros que já compõem as DEDUÇÕES); "
            "disponibilidade_caixa_bruta_dcl, restos_a_pagar_processados_dcl, "
            "depositos_restituiveis_valores_vinculados e "
            "disponibilidade_caixa_dcl são a decomposição oficial da DCL "
            "(bruta menos RP processados menos depósitos = disponibilidade "
            "de caixa, a dedução usada no cálculo); dcl = "
            "divida_consolidada_bruta menos deducoes_totais_dcl; "
            "rp_nao_processados_total_governo é o estoque de restos a "
            "pagar não processados de todo o governo (não só recursos "
            "não vinculados) informado como memória no mesmo anexo, mais "
            "comparável ano a ano do que o RREO-Anexo 07 (cujo saldo "
            "reflete apenas resíduo de exercícios anteriores, não o "
            "estoque total). receita_realizada é o TOTAL DAS RECEITAS "
            "do RREO Anexo 1 (inclui intra-orçamentárias); "
            "receita_exceto_intraorcamentaria é o subtotal usado na "
            "página 8 do diagnóstico (as sete categorias por natureza "
            "econômica somam esse subtotal, não o total); "
            "receita_intraorcamentaria é a diferença entre os dois, "
            "reconciliada explicitamente na tabela da página 8. "
            "comparaveis_periodo_parcial.2025 traz o RGF do 1º "
            "quadrimestre de 2025 (posição 30/abr) e o RREO do bimestre "
            "2 de 2025, no mesmo período de referência do dado parcial "
            "de 2026, para permitir comparação janeiro-abril entre os "
            "dois anos na página 2 do diagnóstico; não substitui a "
            "série anual fechada de 2025 usada nas demais páginas."
        ),
        "unidade": "R$ nominais (não deflacionados)",
        "rgf": {},
        "rreo": {},
        "comparaveis_periodo_parcial": {},
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

    print("\n=== Coletando período parcial comparável de 2025 (jan-abr) ===")
    r_rgf_2025_1q = collect_rgf_year(2025, quad=1)
    if r_rgf_2025_1q:
        result["comparaveis_periodo_parcial"]["rgf_2025_1q"] = r_rgf_2025_1q
    r_rreo_2025_bim2 = collect_rreo_year(2025, periodo=2)
    if r_rreo_2025_bim2:
        result["comparaveis_periodo_parcial"]["rreo_2025_bim2"] = r_rreo_2025_bim2

    with open(OUTPUT, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nDados salvos em {OUTPUT}")


if __name__ == "__main__":
    main()
