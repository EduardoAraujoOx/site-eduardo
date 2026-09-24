#!/usr/bin/env python3
"""
Estudo: alíquota de referência do IBS/CBS e a base tributável de consumo.

Constrói uma estimativa própria, independente, da alíquota de referência
combinada do IBS/CBS, seguindo a orientação metodológica de Orair e Gobetti
(2019, IPEA) e reafirmada por Gobetti, Orair e Monteiro (2023, IPEA, Carta
de Conjuntura 59, nota 17): a base agregada deve vir das Contas Nacionais do
IBGE (não da POF, que os próprios autores apontam subestimar o consumo das
famílias em cerca de 10% frente às Contas Nacionais), e só a distribuição
relativa entre entes deve vir do cruzamento POF x Censo -- que este painel
já calcula (data/phi-dest-pof-censo.json).

Fontes primárias:
- Receita de referência (bolo) e PIB projetados 2029-2033: data/ibs-projecao-nacional.json
  (já reconciliado com SICONFI/STN e Banco Central; ver data/build-ibs-projecao-nacional.py)
- Despesa de consumo das famílias e PIB, ano-base 2025: IBGE, Contas Nacionais
  Trimestrais, SIDRA tabela 1846 (variável 585, "Valores a preços correntes"),
  categorias 93404 ("Despesa de consumo das famílias") e 90707 ("PIB a preços
  de mercado"), soma dos 4 trimestres de 2025. Consultado via API pública:
  https://apisidra.ibge.gov.br/values/t/1846/n1/all/v/585/p/202501-202504/c11255/93404,90707/f/n
"""
import json

NACIONAL = json.load(open('data/ibs-projecao-nacional.json'))

# IBGE, Contas Nacionais Trimestrais, SIDRA tabela 1846, R$ milhões, soma dos
# 4 trimestres de 2025 (consultado em setembro de 2026).
CONSUMO_FAMILIAS_2025_MI = 1934192 + 1992000 + 2050092 + 2105049  # = 8.081.333
PIB_2025_MI = 3024723 + 3200345 + 3235708 + 3277790  # = 12.738.566, bate com NACIONAL

pib_2025_nacional = None
for r in NACIONAL['historico']:
    if r['ano'] == 2025:
        pib_2025_nacional = r.get('pib_nominal') or r.get('pib_real')
        break

consumo_pct_pib_2025 = CONSUMO_FAMILIAS_2025_MI / PIB_2025_MI

anos = []
for r in NACIONAL['projecao']:
    if r['ano'] > 2033:
        continue
    bolo = r['bolo_projetado']
    pib = r['pib_real']
    bolo_pct_pib = bolo / pib
    # Hipótese explícita: a razão consumo das famílias / PIB de 2025
    # permanece constante ao longo da transição -- a mesma lógica de
    # neutralidade (razão bolo/PIB fixa) já usada pelo resto do painel para
    # projetar o "bolo" (LC 214/2025 arts. 361-365). Não há projeção própria
    # de Contas Nacionais para 2029-2033; esta é a extrapolação mais simples
    # e mais transparente disponível, não uma previsão do IBGE.
    consumo_familias = pib * consumo_pct_pib_2025
    aliquota_bruta = bolo / consumo_familias
    anos.append({
        'ano': r['ano'],
        'bolo': bolo,
        'bolo_pct_pib': bolo_pct_pib * 100,
        'pib': pib,
        'consumo_familias_estimado': consumo_familias,
        'consumo_pct_pib': consumo_pct_pib_2025 * 100,
        'aliquota_bruta_simplificada_pct': aliquota_bruta * 100,
    })

saida = {
    '_meta': {
        'descricao': 'Estimativa própria e simplificada da alíquota de referência combinada do IBS/CBS, a partir da razão entre a receita de referência já projetada pelo painel (bolo) e uma projeção do consumo das famílias (Contas Nacionais/IBGE, ano-base 2025, mantido constante como proporção do PIB). Não desconta itens não monetários, tributos embutidos no preço, nem regimes diferenciados e específicos -- por isso é um piso, não a alíquota que de fato entrará em vigor. Ver estudo para a comparação com estimativas de terceiros que fazem esses ajustes.',
        'fonte_bolo_pib': 'data/ibs-projecao-nacional.json (SICONFI/STN, Banco Central)',
        'fonte_consumo_familias': 'IBGE, Contas Nacionais Trimestrais, SIDRA tabela 1846, variável 585, categorias 93404 e 90707, soma dos 4 trimestres de 2025',
        'consumo_familias_2025_rs': CONSUMO_FAMILIAS_2025_MI * 1e6,
        'pib_2025_rs_sidra': PIB_2025_MI * 1e6,
        'pib_2025_rs_painel': pib_2025_nacional,
        'consumo_pct_pib_2025': consumo_pct_pib_2025 * 100,
    },
    'anos': anos,
}

with open('data/aliquota-base-referencia.json', 'w', encoding='utf-8') as f:
    json.dump(saida, f, ensure_ascii=False, indent=1)

print('consumo_pct_pib_2025:', round(consumo_pct_pib_2025 * 100, 4), '%')
for a in anos:
    print(a['ano'], 'bolo/pib:', round(a['bolo_pct_pib'], 4), '| aliquota_bruta:', round(a['aliquota_bruta_simplificada_pct'], 4))
print('PIB 2025 (SIDRA):', PIB_2025_MI * 1e6, '| PIB 2025 (painel):', pib_2025_nacional)
