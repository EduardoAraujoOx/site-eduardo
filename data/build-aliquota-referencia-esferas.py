#!/usr/bin/env python3
"""
Divide a alíquota de referência bruta simplificada (data/aliquota-base-referencia.json,
Estudo 16) entre a fatia estadual (ICMS + FECOP) e a fatia municipal (ISS), seguindo o
mesmo texto legal que já fundamenta o restante deste estudo: o art. 361 da LC 214/2025
fixa uma alíquota de referência do IBS estadual e uma do IBS municipal, separada e
independentemente, não uma derivada da outra.

A separação usa a participação média de cada esfera na receita de referência (ICMS+ISS+
FECOP) nos mesmos anos de calibração que a lei usa para a alíquota combinada, 2024 a 2026
(LC 214/2025, arts. 361 a 365). 2024 e 2025 vêm do dado fechado (DCA) já publicado em
data/ibs-projecao-nacional.json; 2026 ainda não fechou, e usa a mesma estimativa
preliminar (RREO 12 meses) que o restante deste site já usa para o bolo combinado,
lida diretamente de data/reforma-tributaria.json (icms_br/iss_br, ano 2026) e do último
FECOP fechado (2025), a mesma regra de "carregar o último dado fechado" já aplicada em
data/build-ibs-projecao-nacional.py.

A participação (não o nível) é o que se mantém constante ao longo da transição, a mesma
lógica de neutralidade já usada para a razão bolo/PIB e para a razão consumo/PIB: dividir
a alíquota bruta simplificada projetada ano a ano nas duas fatias, na mesma proporção
observada na média 2024-2026, não é uma hipótese adicional, é a aplicação da mesma regra
já embutida no resto do estudo a uma nova pergunta.

Fontes:
- ICMS, ISS e FECOP fechados (DCA), 2024-2025: data/ibs-projecao-nacional.json (historico)
- ICMS e ISS preliminares (RREO), 2026: data/reforma-tributaria.json (icms_br, iss_br)
- FECOP preliminar, 2026: data/reforma-tributaria.json (dca_fecop_br, valor de 2025)
- Alíquota bruta simplificada combinada, por ano: data/aliquota-base-referencia.json
"""
import json

NACIONAL = json.load(open('data/ibs-projecao-nacional.json'))
REF = json.load(open('data/reforma-tributaria.json'))
COMBINADA = json.load(open('data/aliquota-base-referencia.json'))

historico_por_ano = {h['ano']: h for h in NACIONAL['historico']}

icms_2026 = REF['icms_br']['2026']
iss_2026 = REF['iss_br']['2026']
fecop_2026 = REF['dca_fecop_br'].get('2025', 0) or 0

anos_calibracao = {
    2024: historico_por_ano[2024],
    2025: historico_por_ano[2025],
    2026: {'icms': icms_2026, 'iss': iss_2026, 'fecop': fecop_2026},
}

shares_estadual = []
shares_municipal = []
detalhe_anos = []
for ano, h in anos_calibracao.items():
    bolo = h['icms'] + h['iss'] + h['fecop']
    share_estadual = (h['icms'] + h['fecop']) / bolo
    share_municipal = h['iss'] / bolo
    shares_estadual.append(share_estadual)
    shares_municipal.append(share_municipal)
    detalhe_anos.append({
        'ano': ano,
        'icms': round(h['icms'], 2),
        'iss': round(h['iss'], 2),
        'fecop': round(h['fecop'], 2),
        'share_estadual_pct': round(share_estadual * 100, 4),
        'share_municipal_pct': round(share_municipal * 100, 4),
    })

share_estadual_media = sum(shares_estadual) / len(shares_estadual)
share_municipal_media = sum(shares_municipal) / len(shares_municipal)

anos = []
for a in COMBINADA['anos']:
    aliquota_combinada = a['aliquota_bruta_simplificada_pct']
    anos.append({
        'ano': a['ano'],
        'aliquota_combinada_pct': aliquota_combinada,
        'aliquota_estadual_bruta_pct': aliquota_combinada * share_estadual_media,
        'aliquota_municipal_bruta_pct': aliquota_combinada * share_municipal_media,
    })

saida = {
    '_meta': {
        'descricao': 'Divisão da alíquota de referência bruta simplificada (Estudo 16) entre a fatia estadual (ICMS + FECOP) e a municipal (ISS), pela participação média de cada esfera na receita de referência nos anos de calibração legal (2024-2026, LC 214/2025 arts. 361 a 365).',
        'fonte_icms_iss_fecop_2024_2025': 'data/ibs-projecao-nacional.json (historico, dado fechado DCA)',
        'fonte_icms_iss_2026': 'data/reforma-tributaria.json (icms_br, iss_br; estimativa preliminar RREO, mesma regra do bolo combinado)',
        'fonte_fecop_2026': 'data/reforma-tributaria.json (dca_fecop_br, valor de 2025 usado como estimativa preliminar)',
        'detalhe_anos_calibracao': detalhe_anos,
        'share_estadual_medio_pct': round(share_estadual_media * 100, 4),
        'share_municipal_medio_pct': round(share_municipal_media * 100, 4),
    },
    'anos': anos,
}

with open('data/aliquota-referencia-esferas.json', 'w', encoding='utf-8') as f:
    json.dump(saida, f, ensure_ascii=False, indent=1)

print('participacao media 2024-2026: estadual=%.4f%% municipal=%.4f%%' % (share_estadual_media * 100, share_municipal_media * 100))
for a in anos:
    print(a['ano'], 'combinada=%.4f' % a['aliquota_combinada_pct'], '| estadual=%.4f' % a['aliquota_estadual_bruta_pct'], '| municipal=%.4f' % a['aliquota_municipal_bruta_pct'])
