#!/usr/bin/env python3
"""
Gera os dados por estado da seção "E por estado? A carga tributária
implícita sobre o consumo" do Estudo 16 (estudos/aliquota-base-referencia-ibs.html).

Não confundir com a alíquota de referência: aquela é um único número
nacional, fixado por lei (LC 214/2025 art. 361) para preservar a
arrecadação em proporção ao PIB. O que este script calcula é outra coisa,
a razão entre a receita total projetada de cada estado, no cenário de
transição já publicado pelo painel, e uma estimativa independente de sua
base de consumo em reais. Como a receita de transição ainda mistura, em
2033, 91% de critério histórico (baseado em ICMS/ISS arrecadados na
origem) com só 9% de critério de destino (baseado em consumo), essa razão
varia de verdade entre estados, ao contrário da razão calculada só sobre
a fatia de destino, que cancela por construção (toda ela é proporcional a
φdest).

Fontes:
- Receita total projetada por estado, 2029-2033: data/painel-estados.json
  (componentes_por_ano.estado: origem + cpt + destino + seguro)
- Participação de cada estado na base nacional de destino (φdest já
  aplicado o fator estadual/municipal, LC 214/2025 art. 361):
  data/painel-estados.json (coef_pleno_estado_pct)
- Nível agregado da base de consumo das famílias, 2025: Contas Nacionais
  do IBGE (SIDRA, tabela 1846), mesmo número usado na seção nacional do
  Estudo 16.
"""
import json

PAINEL = json.load(open('data/painel-estados.json'))['estados']
CONSUMO_FAMILIAS_2025_RS = 1934192e6 + 1992000e6 + 2050092e6 + 2105049e6  # Estudo 16

ANOS = ['2029', '2030', '2031', '2032', '2033']

ufs = []
for uf, e in PAINEL.items():
    base_rs = e['coef_pleno_estado_pct'] / 100 * CONSUMO_FAMILIAS_2025_RS
    comp = e['componentes_por_ano']['estado']
    por_ano = []
    for a in ANOS:
        c = comp[a]
        total = c['origem'] + c['cpt'] + c['destino'] + c['seguro']
        carga = total / base_rs * 100 if base_rs else None
        por_ano.append({'ano': int(a), 'receita_total': total, 'carga_implicita_pct': carga})
    ufs.append({
        'uf': uf,
        'nome': e['nome'],
        'is_df': e.get('is_df', False),
        'base_consumo_rs': base_rs,
        'coef_cpt_estado_pct': e['coef_cpt_estado_pct'],
        'coef_pleno_estado_pct': e['coef_pleno_estado_pct'],
        'por_ano': por_ano,
    })

ufs.sort(key=lambda r: r['por_ano'][-1]['carga_implicita_pct'])

saida = {
    '_meta': {
        'descricao': 'Carga tributária implícita sobre o consumo por estado: receita total projetada (origem + cpt + destino + seguro, já publicada pelo painel) dividida por uma estimativa independente da base de consumo do estado (participação de destino do estado aplicada ao consumo das famílias das Contas Nacionais, mesma âncora nacional do Estudo 16). Não é a alíquota de referência, essa é um único número nacional definido por lei. A variação entre estados reflete a mistura, ainda predominante em 2033, entre critério histórico (origem, ICMS/ISS) e critério de destino (consumo) na fórmula de transição.',
        'fonte_receita': 'data/painel-estados.json (componentes_por_ano.estado)',
        'fonte_base': 'IBGE, Contas Nacionais Trimestrais, SIDRA tabela 1846, mesma consulta do Estudo 16',
        'consumo_familias_2025_rs': CONSUMO_FAMILIAS_2025_RS,
    },
    'ufs': ufs,
}

with open('data/carga-implicita-uf.json', 'w', encoding='utf-8') as f:
    json.dump(saida, f, ensure_ascii=False, indent=1)

print('carga implicita 2033, min/max:')
print(' ', ufs[0]['uf'], round(ufs[0]['por_ano'][-1]['carga_implicita_pct'], 2))
print(' ', ufs[-1]['uf'], round(ufs[-1]['por_ano'][-1]['carga_implicita_pct'], 2))
print('total ufs:', len(ufs))
