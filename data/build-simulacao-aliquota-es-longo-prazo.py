#!/usr/bin/env python3
"""
Fase 2 do teste de sensibilidade por alíquota própria, só para o Espírito
Santo, agora estendida a todo o horizonte de transição do IBS (2029-2077),
não só à etapa que já tem receita publicada por estado no painel
(2029-2033).

A Fase 1 (data/build-simulacao-aliquota-es.py) parou em 2033 porque não
havia, então, receita publicada por estado além desse ano. Mas essa
receita por estado, publicada em painel-estados.json para 2029-2033, é
só um caso particular de uma fórmula genérica, a mesma de project_uf() em
data/build-resultados-consolidados.py: aplicar os três coeficientes fixos
de cada estado (participação neutra, de transição e de destino pleno, os
mesmos coef_neutro_estado_pct / coef_cpt_estado_pct / coef_pleno_estado_pct
de painel-estados.json) aos agregados nacionais do ano. Esses agregados
nacionais já existem também para 2034-2077 (extensão de longo prazo do
Estudo 09/11, data/ibs-projecao-longo-prazo.json), e o repasse de
Seguro-Receita por UF também já existe ano a ano até 2077
(data/seguro-receita-repasses-longo-prazo.json). Bastou reaplicar a mesma
fórmula a esses dados de mais longo prazo, sem coletar nada novo; a
fórmula foi conferida contra os cinco anos já publicados antes de aceitar
a extensão (bate a menos de R$ 1 de diferença).

Para cada ano do horizonte, calcula as duas alíquotas de virada já usadas
na Fase 1: a que faria o ES escapar do Seguro-Receita naquele ano, e a
que fecharia sozinha a lacuna frente ao contrafactual naquele ano.

Fontes: as mesmas da Fase 1 (Estudo 16, painel-estados.json,
resultados-consolidados-ibs.json), mais
data/ibs-projecao-longo-prazo.json e
data/seguro-receita-repasses-longo-prazo.json.
"""
import json

UF = 'ES'
ANOS = list(range(2029, 2078))

painel = json.load(open('data/painel-estados.json'))['estados'][UF]
carga = json.load(open('data/carga-implicita-uf.json'))
esferas = json.load(open('data/aliquota-referencia-esferas.json'))
lp = json.load(open('data/ibs-projecao-longo-prazo.json'))
seguro_lp = json.load(open('data/seguro-receita-repasses-longo-prazo.json'))
rc = json.load(open('data/resultados-consolidados-ibs.json'))['por_uf_estado'][UF]

CONSUMO_FAMILIAS_2025_RS = 1934192e6 + 1992000e6 + 2050092e6 + 2105049e6

coef_neutro = painel['coef_neutro_estado_pct'] / 100
coef_cpt = painel['coef_cpt_estado_pct'] / 100
coef_pleno = painel['coef_pleno_estado_pct'] / 100

uf_carga = next(u for u in carga['ufs'] if u['uf'] == UF)
base_uf = uf_carga['base_consumo_rs']
aliq_ref_estadual = esferas['anos'][0]['aliquota_estadual_bruta_pct'] / 100

nac_by_year = {a['ano']: a for a in lp['projecao']}

serie = []
for ano in ANOS:
    n = nac_by_year[ano]
    ca = n.get('ca', 0.0)
    origem = n['icms_iss_residual'] * coef_neutro
    cpt = (1 - ca) * n['ibs_historico'] * coef_cpt
    destino = n['ibs_destino_liquido'] * coef_pleno
    repasse_oficial = seguro_lp['anos'][str(ano)]['repasse_por_uf'].get(UF, {}).get('estado', 0)
    seguro = (1 - ca) * repasse_oficial
    pos = origem + cpt + destino + seguro
    contra = (n['icms_iss_residual'] + n['ibs_bruto']) * coef_neutro
    lacuna = contra - pos
    peso_destino = n['ibs_destino_liquido'] / CONSUMO_FAMILIAS_2025_RS

    aliq_escapa = aliq_ref_estadual + seguro / (peso_destino * base_uf)
    aliq_zera = aliq_ref_estadual + (seguro + lacuna) / (peso_destino * base_uf)

    serie.append({
        'ano': ano,
        'receita_total_rs': pos,
        'contrafactual_rs': contra,
        'lacuna_rs': lacuna,
        'variacao_pct': (pos / contra - 1) * 100 if contra else None,
        'aliquota_escapa_seguro_receita_pct': aliq_escapa * 100,
        'aliquota_zera_lacuna_pct': aliq_zera * 100,
    })

# Confere contra os 5 anos já publicados (2029-2033) antes de aceitar a extensão.
for ano in range(2029, 2034):
    pub_pos = rc['pos_por_ano'][str(ano)]
    pub_contra = rc['contrafactual_por_ano'][str(ano)]
    calc = next(s for s in serie if s['ano'] == ano)
    assert abs(calc['receita_total_rs'] - pub_pos) < 1, (ano, calc['receita_total_rs'], pub_pos)
    assert abs(calc['contrafactual_rs'] - pub_contra) < 1, (ano, calc['contrafactual_rs'], pub_contra)

saida = {
    '_meta': {
        'descricao': 'Fase 2 (só Espírito Santo) do teste de sensibilidade: estende a Fase 1 (2029-2033) a todo o horizonte de transição do IBS (2029-2077), reaplicando os mesmos três coeficientes fixos do estado (participação neutra, de transição e de destino pleno) aos agregados nacionais de longo prazo e ao repasse de Seguro-Receita por UF, ambos já publicados ano a ano até 2077. Para cada ano, calcula as duas alíquotas de virada: a que faria o ES escapar do Seguro-Receita, e a que fecharia sozinha a lacuna frente ao contrafactual naquele ano.',
        'uf': UF,
        'base_tributavel_rs': base_uf,
        'aliquota_referencia_estadual_pct': aliq_ref_estadual * 100,
        'fonte_coeficientes_estado': 'data/painel-estados.json (coef_neutro/cpt/pleno_estado_pct)',
        'fonte_agregados_nacionais': 'data/ibs-projecao-longo-prazo.json (2029-2077)',
        'fonte_repasse_seguro_receita': 'data/seguro-receita-repasses-longo-prazo.json (2029-2077)',
        'validacao': 'Receita total e contrafactual recalculados aqui batem, a menos de R$ 1, com data/resultados-consolidados-ibs.json (por_uf_estado.ES) nos cinco anos já publicados (2029-2033), o que confirma que a mesma fórmula de project_uf() foi reaplicada corretamente aos dados de mais longo prazo.',
    },
    'serie': serie,
}

with open('data/simulacao-aliquota-es-longo-prazo.json', 'w', encoding='utf-8') as f:
    json.dump(saida, f, ensure_ascii=False, indent=1)

print('validação OK: receita e contrafactual batem com os 5 anos já publicados')
print()
for s in serie:
    if s['ano'] in (2029, 2033, 2034, 2040, 2050, 2060, 2070, 2077):
        print(s['ano'], 'variacao=%.2f%%' % s['variacao_pct'],
              'aliq_escapa=%.2f%%' % s['aliquota_escapa_seguro_receita_pct'],
              'aliq_zera=%.2f%%' % s['aliquota_zera_lacuna_pct'])
