#!/usr/bin/env python3
"""
Fase 1 do teste de sensibilidade por alíquota própria, só para o Espírito Santo
(2029-2033). Testa, para uma lista de alíquotas hipotéticas de IBS estadual,
qual seria o efeito em reais na receita de destino do ES, quanto desse efeito
o Seguro-Receita absorve, e como isso mudaria a variação do ES frente ao
contrafactual já publicado no painel.

O mecanismo do Seguro-Receita não é uma absorção proporcional, é um degrau:
enquanto a receita própria do ente (histórico + destino, antes do repasse)
ficar abaixo do piso garantido, qualquer receita extra de destino apenas
reduz o repasse na mesma medida, e a receita total do ente não se altera
nem um real. Só a partir do ponto em que a receita própria ultrapassa o
piso é que o ganho passa a valer integralmente. Como o piso, nesta fase da
transição, é a própria receita total já publicada (pos_por_ano), dá para
calcular os dois pontos de virada:

- alíquota que escapa do Seguro-Receita no ano = alíquota de referência +
  repasse do ano / (peso do destino no ano * base tributável do ES)
- alíquota que zera a perda frente ao contrafactual no ano = alíquota de
  referência + (repasse do ano + lacuna frente ao contrafactual no ano) /
  (peso do destino no ano * base tributável do ES)

Fontes: as mesmas já usadas no Estudo 16 (base tributável e alíquota de
referência estadual) e o mesmo painel-estados.json / resultados-consolidados
já publicados (receita própria, repasse de Seguro-Receita, contrafactual e
variação).
"""
import json

UF = 'ES'

painel = json.load(open('data/painel-estados.json'))['estados']
carga = json.load(open('data/carga-implicita-uf.json'))
nac = json.load(open('data/ibs-projecao-nacional.json'))
esferas = json.load(open('data/aliquota-referencia-esferas.json'))
rc = json.load(open('data/resultados-consolidados-ibs.json'))

CONSUMO_FAMILIAS_2025_RS = 1934192e6 + 1992000e6 + 2050092e6 + 2105049e6

uf_carga = next(u for u in carga['ufs'] if u['uf'] == UF)
base_uf = uf_carga['base_consumo_rs']
aliq_ref_estadual_pct = esferas['anos'][0]['aliquota_estadual_bruta_pct']
aliq_ref_estadual = aliq_ref_estadual_pct / 100

uf_rc = rc['por_uf_estado'][UF]
seguro_por_ano = painel[UF]['repasse_seguro_receita_por_ano']['estado']

ANOS = [2029, 2030, 2031, 2032, 2033]

pesos_destino = {}
for a in nac['projecao']:
    if a['ano'] in ANOS:
        pesos_destino[a['ano']] = a['ibs_destino_liquido'] / CONSUMO_FAMILIAS_2025_RS

# limiares de referência (não são cenários simuláveis por si, são pontos de
# virada informativos, calculados ano a ano)
limiares_por_ano = {}
for ano in ANOS:
    peso = pesos_destino[ano]
    seguro = seguro_por_ano[str(ano)]
    pos = uf_rc['pos_por_ano'][str(ano)]
    contra = uf_rc['contrafactual_por_ano'][str(ano)]
    lacuna = contra - pos
    aliq_escapa = aliq_ref_estadual + seguro / (peso * base_uf)
    aliq_zera = aliq_ref_estadual + (seguro + lacuna) / (peso * base_uf)
    limiares_por_ano[ano] = {
        'seguro_rs': seguro,
        'lacuna_vs_contrafactual_rs': lacuna,
        'aliquota_escapa_seguro_receita_pct': aliq_escapa * 100,
        'aliquota_zera_lacuna_pct': aliq_zera * 100,
    }

# cenários simuláveis: uma alíquota fixa, aplicada em todos os anos de uma vez
deltas_pp = [0, 1, 2, 3, 4, 10, 20, round(limiares_por_ano[2033]['aliquota_escapa_seguro_receita_pct'] - aliq_ref_estadual_pct, 2)]
deltas_pp = sorted(set(deltas_pp))

cenarios = []
for delta_pp in deltas_pp:
    aliq_cenario = aliq_ref_estadual + delta_pp / 100
    if delta_pp == 0:
        label = f'Referência ({aliq_ref_estadual_pct:.2f}%)'
    else:
        label = f'+{delta_pp:g} p.p. ({aliq_cenario*100:.2f}%)'
    anos_out = []
    for ano in ANOS:
        peso = pesos_destino[ano]
        seguro = seguro_por_ano[str(ano)]
        pos = uf_rc['pos_por_ano'][str(ano)]
        contra = uf_rc['contrafactual_por_ano'][str(ano)]

        delta_bruto = (aliq_cenario - aliq_ref_estadual) * peso * base_uf
        delta_absorvido_seguro = min(max(delta_bruto, 0), seguro)
        delta_liquido = max(delta_bruto - seguro, 0) if delta_bruto > 0 else delta_bruto
        # Nota: para delta_bruto negativo (alíquota abaixo da referência), o
        # repasse do Seguro-Receita cresceria na mesma proporção (o ente já
        # está abaixo do piso), então o efeito líquido também é zero por
        # construção nesta faixa; delta_liquido = delta_bruto só voltaria a
        # valer se o ente já tivesse escapado do Seguro-Receita, o que não é
        # o caso do ES neste horizonte, então travamos em zero.
        if delta_bruto < 0:
            delta_liquido = 0.0
            delta_absorvido_seguro = 0.0

        nova_receita = pos + delta_liquido
        nova_variacao_pct = (nova_receita / contra - 1) * 100

        anos_out.append({
            'ano': ano,
            'delta_bruto_destino_rs': delta_bruto,
            'delta_absorvido_seguro_receita_rs': delta_absorvido_seguro,
            'delta_liquido_receita_total_rs': delta_liquido,
            'receita_total_original_rs': pos,
            'receita_total_nova_rs': nova_receita,
            'contrafactual_rs': contra,
            'variacao_original_pct': uf_rc['variacao_por_ano'][str(ano)] * 100,
            'variacao_nova_pct': nova_variacao_pct,
        })
    cenarios.append({
        'delta_pp': delta_pp,
        'aliquota_pct': aliq_cenario * 100,
        'label': label,
        'anos': anos_out,
    })

saida = {
    '_meta': {
        'descricao': 'Fase 1 (só Espírito Santo, 2029-2033) do teste de sensibilidade: efeito de uma alíquota própria de IBS estadual diferente da referência sobre a receita total do estado, considerando o degrau do Seguro-Receita e o novo confronto com o contrafactual já publicado.',
        'uf': UF,
        'base_tributavel_rs': base_uf,
        'aliquota_referencia_estadual_pct': aliq_ref_estadual_pct,
        'limiares_por_ano': limiares_por_ano,
        'fonte_base_e_aliquota_referencia': 'Estudo 16 (data/carga-implicita-uf.json, data/aliquota-referencia-esferas.json)',
        'fonte_receita_contrafactual_variacao': 'data/resultados-consolidados-ibs.json (por_uf_estado.ES)',
        'fonte_seguro_receita': 'data/painel-estados.json (repasse_seguro_receita_por_ano.estado)',
        'mecanismo_seguro_receita': 'Degrau, não absorção proporcional: enquanto a receita própria (antes do repasse) ficar abaixo do piso garantido, qualquer receita extra de destino só reduz o repasse, sem mudar a receita total; o ganho líquido só começa a valer depois que a receita extra ultrapassa o valor do repasse do ano.',
    },
    'cenarios': cenarios,
}

with open('data/simulacao-aliquota-es.json', 'w', encoding='utf-8') as f:
    json.dump(saida, f, ensure_ascii=False, indent=1)

print('base ES (bi):', round(base_uf/1e9,1), '| aliquota referencia estadual:', round(aliq_ref_estadual_pct,4),'%')
print()
for ano in ANOS:
    l = limiares_por_ano[ano]
    print(ano, 'seguro=%.1fmi'%(l['seguro_rs']/1e6), 'lacuna=%.1fmi'%(l['lacuna_vs_contrafactual_rs']/1e6),
          'aliq_escapa=%.2f%%'%l['aliquota_escapa_seguro_receita_pct'], 'aliq_zera=%.2f%%'%l['aliquota_zera_lacuna_pct'])
print()
for c in cenarios:
    print(c['label'])
    for a in c['anos']:
        print('  ', a['ano'], 'delta_liquido=%.2fmi'%(a['delta_liquido_receita_total_rs']/1e6), 'nova_variacao=%.3f%%'%a['variacao_nova_pct'], '(original %.3f%%)'%a['variacao_original_pct'])
