#!/usr/bin/env python3
"""Malha das UFs, obtida por dissolução da malha municipal já versionada.

Entrada : data/malha-municipios.json  (5.570 municípios, qualidade generalizada)
Saída   : data/malha-uf.json          (27 UFs, GeoJSON FeatureCollection, propriedade "uf")

Usada pelo portal municipiosnareforma.com.br para o mapa de abertura, sem depender
de serviço externo em tempo de execução. Reexecutar sempre que a malha municipal mudar.
Requer: shapely (pip install shapely).
"""
import json
from collections import defaultdict
from pathlib import Path
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

RAIZ = Path(__file__).resolve().parent
UF_POR_PREFIXO = {'11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
                  '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',
                  '28': 'SE', '29': 'BA', '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP', '41': 'PR',
                  '42': 'SC', '43': 'RS', '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'}

geo = json.loads((RAIZ / 'malha-municipios.json').read_text(encoding='utf-8'))
por_uf = defaultdict(list)
for f in geo['features']:
    uf = UF_POR_PREFIXO[f['properties']['cod'][:2]]
    por_uf[uf].append(shape(f['geometry']).buffer(0))

def arredonda(obj, casas=3):
    if isinstance(obj, (list, tuple)):
        return [arredonda(x, casas) for x in obj]
    return round(obj, casas) if isinstance(obj, float) else obj

feats = []
for uf in sorted(por_uf):
    uniao = unary_union(por_uf[uf]).simplify(0.01, preserve_topology=True)
    g = mapping(uniao)
    feats.append({'type': 'Feature', 'properties': {'uf': uf},
                  'geometry': {'type': g['type'], 'coordinates': arredonda(g['coordinates'])}})

saida = RAIZ / 'malha-uf.json'
saida.write_text(json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'{len(feats)} UFs -> {saida} ({saida.stat().st_size // 1024} KB)')
