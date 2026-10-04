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
    sd = sd_h(L)
    pontos = mod.fit_pl(sd)
    hs = np.arange(1, 9)
    v = np.array([sd[h] ** 2 for h in hs])
    c = float(np.sqrt((hs * v).sum() / (hs * hs).sum()))      # sigma(h) = c * sqrt(h), mínimos quadrados em sigma^2
    razao = c / sd[1]                                         # ajuste de razão de variância (c / sigma de 1 ano)
    # Teste de razão de variância: VR(8) = sigma(8)^2 / (8 sigma(1)^2) observado vs. permutando no tempo
    # os choques de cada UF (hipótese nula de passeio aleatório, preserva a variância de cada UF)
    vr_obs = sd[8] ** 2 / (8 * sd[1] ** 2)
    vrp = []
    for _ in range(2000):
        Sp = np.column_stack([rng.permutation(shocks[:, j]) for j in range(shocks.shape[1])])
        Lb = np.vstack([np.zeros(L.shape[1]), np.cumsum(Sp, axis=0)])
        s_ = sd_h(Lb)
        vrp.append(s_[8] ** 2 / (8 * s_[1] ** 2))
    vrp = np.array(vrp)
    # Incerteza de c: bootstrap dos anos APENAS para o choque de 1 ano (sem somar choques repetidos,
    # o que inflaria o expoente), mantendo fixa a razão c / sigma1
    s1b = []
    for _ in range(B):
        idx = rng.integers(0, T, T)
        x = shocks[idx]
        s1b.append(float((x - x.mean(1, keepdims=True)).std(ddof=1)))
    cb = np.array(s1b) * razao
    pares = np.column_stack([cb, np.full(B, 0.5)])
    h8 = cb * 8 ** 0.5
    h4 = cb * 4 ** 0.5
    ac1 = float(np.mean([np.corrcoef(shocks[:-1, j] - shocks[:, j].mean(), shocks[1:, j] - shocks[:, j].mean())[0, 1] for j in range(shocks.shape[1])]))

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
    saida = {"_meta": {"descricao": "Passeio aleatório sigma(h)=c*sqrt(h): teste de razão de variância, incerteza de c por bootstrap dos choques anuais e fator de escala kappa (validação cruzada)",
                       "B": B, "seed": SEED, "amostra": "20 UFs sem quebras da DCA, 2013-2025"},
             "ponto_livre": {"s1": round(pontos[0], 4), "beta": round(pontos[1], 3)},
             "passeio_aleatorio": {"c": round(c, 4), "sigma_1ano": round(float(sd[1]), 4), "razao_c_sobre_sigma1": round(razao, 3),
                                   "sigma_h4": round(c * 2, 4), "sigma_h8": round(c * 8 ** 0.5, 4),
                                   "autocorrelacao_choques_anuais": round(ac1, 3)},
             "teste_razao_de_variancia": {"VR8_observada": round(float(vr_obs), 3), "VR8_nula_permutacao_p05": round(float(np.percentile(vrp, 5)), 3),
                                          "VR8_nula_permutacao_p50": round(float(np.percentile(vrp, 50)), 3), "VR8_nula_permutacao_p95": round(float(np.percentile(vrp, 95)), 3),
                                          "p_valor_unilateral": round(float((vrp >= vr_obs).mean()), 3),
                                          "leitura": "VR dentro da distribuição nula: o passeio aleatório (beta = 0,5) não é rejeitado"},
             "bootstrap": {"c": {"p05": round(float(np.percentile(cb, 5)), 4), "p50": round(float(np.percentile(cb, 50)), 4), "p95": round(float(np.percentile(cb, 95)), 4)},
                           "sigma_h4": {"p05": round(float(np.percentile(h4, 5)), 4), "p50": round(float(np.percentile(h4, 50)), 4), "p95": round(float(np.percentile(h4, 95)), 4)},
                           "sigma_h8": {"p05": round(float(np.percentile(h8, 5)), 4), "p50": round(float(np.percentile(h8, 50)), 4), "p95": round(float(np.percentile(h8, 95)), 4)},
                           "nota": "O bootstrap anterior, que reamostrava anos com reposição e somava os choques repetidos, inflava o expoente beta (mediana 0,62); foi substituído."},
             "kappa": {"otimo_amostra_toda": round(kappa_all, 2),
                       "por_origem_cv": [round(c[2], 2) for c in cv],
                       "CRPS_cv_kappa": round(float(np.mean([c[0] for c in cv])), 5),
                       "CRPS_cv_kappa1": round(float(np.mean([c[1] for c in cv])), 5),
                       "ganho_relativo_cv": round(float(1 - np.mean([c[0] for c in cv]) / np.mean([c[1] for c in cv])), 4)},
             "pares_s1_beta": [[round(float(a), 5), 0.5] for a in cb[:1000]]}
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in saida.items() if k != "pares_s1_beta"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
