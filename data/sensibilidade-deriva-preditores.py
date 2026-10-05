#!/usr/bin/env python3
"""
Teste de preditores para a deriva da participação de cada UF no bolo de ICMS (20 UFs sem quebras da DCA, 2013-2025).
Pergunta: algum dado conhecido na origem (momentum da participação, distância à participação populacional ou do PIB,
variação futura da participação populacional, que o IBGE projeta) reduz o erro fora da amostra da variação da
participação em h = 1 a 4 anos? Regressão agrupada, rolling origin (treino só com janelas que terminam até a origem).
Não altera nenhum resultado publicado. Saída: data/sensibilidade-deriva-preditores.json
"""
import json, sys
import numpy as np
sys.path.insert(0, 'data')
from fundos_art115b import fold
r = fold(json.load(open('data/reforma-tributaria.json')))
icms = dict(r['dca_icms_por_uf']); icms.update(json.load(open('data/icms-dca-2013-2018.json')))
sp = json.load(open('data/sidra-pib-pop-uf.json'))
EX = {'DF', 'GO', 'MS', 'MT', 'TO', 'RO', 'CE'}
COD = {"RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17, "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27, "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35, "PR": 41, "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53}
ufs = [u for u in sorted(icms['2025']) if u not in EX]
Y = list(range(2013, 2026))
def sh(vals):
    v = np.array(vals, float); return np.log(v / v.sum())
S = np.array([sh([icms[str(y)][u] for u in ufs]) for y in Y]).T          # UF x ano
anos_pop = sorted(sp['pop']); anos_pib = sorted(sp['pib'])
def serie(tab, anos):
    out = {}
    for y in anos:
        v = np.array([tab[y].get(str(COD[u]), np.nan) for u in ufs], float)
        out[int(y)] = np.log(v / np.nansum(v))
    return out
P = serie(sp['pop'], anos_pop); G = serie(sp['pib'], anos_pib)
def preenche(D):
    ys = sorted(D)
    for y in range(ys[0], ys[-1] + 1):
        if y not in D:
            a = max(k for k in D if k < y); b = min(k for k in D if k > y)
            D[y] = D[a] + (D[b] - D[a]) * (y - a) / (b - a)
preenche(P); preenche(G)
print('pop', anos_pop[0], anos_pop[-1], 'pib', anos_pib[0], anos_pib[-1])
def dm(x): return x - np.nanmean(x)
def feats(i, h):
    """i: índice do ano de origem em Y"""
    y0 = Y[i]; f = {}
    f['mom1'] = dm(S[:, i] - S[:, i - 1]) if i >= 1 else None
    f['mom3'] = dm((S[:, i] - S[:, i - 3]) / 3) if i >= 3 else None
    f['gap_pop'] = dm(S[:, i] - P[y0]) if y0 in P else None
    f['gap_pib'] = dm(S[:, i] - G[min(y0, max(G))])
    f['dpop_fut'] = dm(P[y0 + h] - P[y0]) if (y0 + h) in P else (dm(P[max(P)] - P[y0]) * h / max(1, max(P) - y0) if y0 in P else None)
    return f
nomes = ['mom1', 'mom3', 'gap_pop', 'gap_pib', 'dpop_fut']
conj = {'M0_zero': [], 'M1_momentum': ['mom1'], 'M2_mom3': ['mom3'], 'M3_gap_pop': ['gap_pop'], 'M4_gap_pib': ['gap_pib'],
        'M5_pop_futura': ['dpop_fut'], 'M6_pop_fut+gap': ['dpop_fut', 'gap_pop'], 'M7_pop_fut+mom3': ['dpop_fut', 'mom3']}
def janela(i, h):
    if i + h >= len(Y): return None
    f = feats(i, h)
    if any(f[k] is None for k in nomes): return None
    return f, dm(S[:, i + h] - S[:, i])
res = {m: {'se': [], 'z': []} for m in conj}
for i0 in range(5, len(Y) - 1):          # origem
    for h in range(1, min(4, len(Y) - 1 - i0) + 1):
        alvo = janela(i0, h)
        if alvo is None: continue
        f0, y0 = alvo
        for m, cols in conj.items():
            # treino: janelas (i, h) com i + h <= i0
            X, yy = [], []
            for hh in range(1, 5):
                for i in range(0, i0 - hh + 1):
                    w = janela(i, hh)
                    if w is None: continue
                    fw, yw = w
                    X.append(np.column_stack([fw[c] / np.sqrt(hh) if False else fw[c] for c in cols]) if cols else np.zeros((len(ufs), 0)))
                    yy.append(yw)
            if not yy: continue
            # modelo por horizonte: beta*h para dpop_fut já escalada; demais crescem com h
            Xa = np.vstack(X); ya = np.concatenate(yy)
            if cols:
                b = np.linalg.lstsq(Xa, ya, rcond=None)[0]
                pred = np.column_stack([f0[c] for c in cols]) @ b
                resid_tr = ya - Xa @ b
            else:
                pred = np.zeros(len(ufs)); resid_tr = ya
            e = y0 - pred
            res[m]['se'].append(np.mean(e ** 2)); res[m]['z'].append((h, np.mean(y0 ** 2)))
out = {}
base = np.mean(res['M0_zero']['se'])
for m in conj:
    rm = np.sqrt(np.mean(res[m]['se']) / base)
    out[m] = {'razao_rmse_vs_zero': round(float(rm), 3), 'n_janelas': len(res[m]['se'])}
    print(f'{m:18s} RMSE/zero = {rm:.3f}  n={len(res[m]["se"])}')
import pathlib
pathlib.Path('data/sensibilidade-deriva-preditores.json').write_text(json.dumps({'_meta': 'Razão do RMSE fora da amostra (variação da participação em h=1..4 anos) de cada preditor contra o modelo sem preditor; 20 UFs, DCA 2013-2025', 'resultados': out}, ensure_ascii=False, indent=1), encoding='utf-8')
