#!/usr/bin/env python3
"""
A previsão atualizada de receita de ICMS do próprio estado (RREO, 4º bimestre) acrescenta informação ao acumulado
jan-ago para prever a variação da participação na DCA? Regressão agrupada (20 UFs, 2019-2025), validação leave-one-year-out.
Saída: data/sensibilidade-previsao-rreo.json
"""
import json, sys
import numpy as np
sys.path.insert(0, 'data')
from fundos_art115b import fold
r = fold(json.load(open('data/reforma-tributaria.json')))
dca = dict(r['dca_icms_por_uf']); dca.update(json.load(open('data/icms-dca-2013-2018.json')))
rr = json.load(open('data/rreo-icms-mensal.json'))
EX = {'DF', 'GO', 'MS', 'MT', 'TO', 'RO', 'CE'}
ufs = [u for u in sorted(dca['2025']) if u not in EX]
def lsh(v): v = np.array(v, float); return np.log(v / v.sum())
rows = {}
for a in range(2019, 2026):
    try:
        ja = [sum(rr[str(a)][u]['meses'][4:12]) for u in ufs]; jb = [sum(rr[str(a - 1)][u]['meses'][4:12]) for u in ufs]
        pv = [rr[str(a)][u]['previsao'] for u in ufs]; pvb = [dca[str(a - 1)][u] for u in ufs]
    except Exception as e:
        continue
    if any(x is None for x in ja + jb + pv): continue
    x1 = lsh(ja) - lsh(jb); x2 = lsh(pv) - lsh(pvb)
    y = lsh([dca[str(a)][u] for u in ufs]) - lsh([dca[str(a - 1)][u] for u in ufs])
    bad = np.abs(x1 - np.median(x1)) > 0.4
    x1 = np.where(bad, np.nan, x1); x1 = x1 - np.nanmean(x1); x1 = np.nan_to_num(x1)
    rows[a] = (x1, x2 - x2.mean(), y - y.mean(), bad)
anos = sorted(rows)
def loyo(cols):
    se = []
    for t in anos:
        tr = [a for a in anos if a != t]
        X = np.vstack([np.column_stack([rows[a][c] for c in cols])[~rows[a][3]] for a in tr]); y = np.concatenate([rows[a][2][~rows[a][3]] for a in tr])
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        m = ~rows[t][3]
        e = rows[t][2][m] - np.column_stack([rows[t][c] for c in cols])[m] @ b
        se.append(np.mean(e ** 2))
    return float(np.sqrt(np.mean(se)))
base = float(np.sqrt(np.mean([np.mean(rows[a][2][~rows[a][3]] ** 2) for a in anos])))
out = {'sem_preditor': 1.0, 'so_acumulado_janago': loyo([0]) / base, 'so_previsao_estado': loyo([1]) / base, 'acumulado_e_previsao': loyo([0, 1]) / base}
for k, v in out.items(): print(f'{k:24s} {v:.3f}')
open('data/sensibilidade-previsao-rreo.json', 'w').write(json.dumps({'_meta': 'RMSE leave-one-year-out relativo ao modelo sem preditor, variação anual da participação, 20 UFs, 2019-2025', 'anos': anos, 'resultados': {k: round(v, 3) for k, v in out.items()}}, ensure_ascii=False, indent=1))
