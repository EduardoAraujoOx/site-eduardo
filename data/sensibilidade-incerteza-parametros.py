#!/usr/bin/env python3
"""
Incerteza sobre a própria incerteza e recalibração da escala (práticas de risco de modelo):
  1. Bootstrap em blocos dos choques anuais da participação de cada UF (blocos de 3 anos) para obter a
     distribuição de (s1, beta) da lei sigma(h) = s1 * h^beta. A simulação principal sorteia um par por rodada.
  2. Fator de escala kappa, estimado por validação cruzada leave-one-origin-out minimizando o CRPS dos
     intervalos do passeio aleatório (M0). kappa < 1 indica intervalos folgados fora da amostra.
Não altera nenhum resultado publicado. Saída: data/sensibilidade-incerteza-parametros.json
"""
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("mod", HERE / "sensibilidade-modelos-deriva.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
OUT = HERE / "sensibilidade-incerteza-parametros.json"
SEED = 20261004
B = 2000
BLOCO = 3


def sd_h(L, hmax=8):
    out = {}
    for h in range(1, hmax + 1):
        d = np.array([mod.dm(L[t + h] - L[t]) for t in range(len(L) - h)])
        out[h] = d.ravel().std(ddof=1)
    return out


def main():
    ufs, anos, L, P = mod.carrega()
    rng = np.random.default_rng(SEED)
    shocks = np.diff(L, axis=0)                      # 12 x 20
    T = len(shocks)
    pontos = mod.fit_pl(sd_h(L))
    pares = []
    for _ in range(B):
        idx = []
        while len(idx) < T:
            s = rng.integers(0, T)
            idx += [(s + j) % T for j in range(BLOCO)]
        idx = idx[:T]
        Lb = np.vstack([np.zeros(L.shape[1]), np.cumsum(shocks[idx], axis=0)])
        pares.append(mod.fit_pl(sd_h(Lb)))
    pares = np.array(pares)
    h8 = pares[:, 0] * 8 ** pares[:, 1]
    h4 = pares[:, 0] * 4 ** pares[:, 1]

    # kappa por leave-one-origin-out (M0)
    n = len(anos)
    obs = []                                          # (origem, h, y, sigma)
    for i0 in range(6, n - 1):
        kmax = min(4, i0)
        y_tr = {k: [mod.dm(L[s + k] - L[s]) for s in range(0, i0 - k + 1)] for k in range(1, kmax + 1)}
        s1, b = mod.fit_pl({k: np.concatenate(v).std(ddof=1) for k, v in y_tr.items()})
        for h in range(1, 5):
            if i0 + h <= n - 1:
                obs.append((i0, h, mod.dm(L[i0 + h] - L[i0]), s1 * h ** b))
    grade = np.arange(0.5, 1.31, 0.05)

    def crps_med(sel, k):
        return np.mean([mod.crps_normal(y, 0.0, k * sg).mean() for _, _, y, sg in sel])
    origens = sorted({o[0] for o in obs})
    cv = []
    for o in origens:
        treino = [x for x in obs if x[0] != o]
        k = grade[int(np.argmin([crps_med(treino, g) for g in grade]))]
        teste = [x for x in obs if x[0] == o]
        cv.append((crps_med(teste, k), crps_med(teste, 1.0), k))
    kappa_all = float(grade[int(np.argmin([crps_med(obs, g) for g in grade]))])
    saida = {"_meta": {"descricao": "Incerteza dos parâmetros da deriva (bootstrap em blocos) e fator de escala kappa (validação cruzada)",
                       "B": B, "bloco_anos": BLOCO, "seed": SEED, "amostra": "20 UFs sem quebras da DCA, 2013-2025"},
             "ponto": {"s1": round(pontos[0], 4), "beta": round(pontos[1], 3)},
             "bootstrap": {"s1": {"p05": round(float(np.percentile(pares[:, 0], 5)), 4), "p50": round(float(np.percentile(pares[:, 0], 50)), 4), "p95": round(float(np.percentile(pares[:, 0], 95)), 4)},
                           "beta": {"p05": round(float(np.percentile(pares[:, 1], 5)), 3), "p50": round(float(np.percentile(pares[:, 1], 50)), 3), "p95": round(float(np.percentile(pares[:, 1], 95)), 3)},
                           "sigma_h4": {"p05": round(float(np.percentile(h4, 5)), 4), "p50": round(float(np.percentile(h4, 50)), 4), "p95": round(float(np.percentile(h4, 95)), 4)},
                           "sigma_h8": {"p05": round(float(np.percentile(h8, 5)), 4), "p50": round(float(np.percentile(h8, 50)), 4), "p95": round(float(np.percentile(h8, 95)), 4)}},
             "kappa": {"otimo_amostra_toda": round(kappa_all, 2),
                       "por_origem_cv": [round(c[2], 2) for c in cv],
                       "CRPS_cv_kappa": round(float(np.mean([c[0] for c in cv])), 5),
                       "CRPS_cv_kappa1": round(float(np.mean([c[1] for c in cv])), 5),
                       "ganho_relativo_cv": round(float(1 - np.mean([c[0] for c in cv]) / np.mean([c[1] for c in cv])), 4)},
             "pares_s1_beta": [[round(float(a), 5), round(float(b), 4)] for a, b in pares[:1000]]}
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in saida.items() if k != "pares_s1_beta"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
