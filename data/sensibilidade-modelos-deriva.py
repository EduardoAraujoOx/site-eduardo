#!/usr/bin/env python3
"""
Comparação fora da amostra (rolling origin) de modelos concorrentes para a deriva da participação de
cada UF no bolo de ICMS, avaliados por CRPS (regra de pontuação estritamente própria), cobertura de
80% e 90% e teste de Kupiec. Não altera nenhum resultado publicado.

Modelos (distribuição preditiva normal para o desvio do log da participação em h anos, relativo à média
cruzada das UFs):
  M0  passeio aleatório: média 0, desvio comum sigma(h) = s1 * h^beta (modelo da simulação principal)
  M1  âncora populacional: média = deriva anual da participação populacional nos 4 anos anteriores x h
      (previsível, ex ante), com coeficiente 1 (ICMS per capita constante); desvio dos resíduos
  M1e idem, com coeficiente estimado no treino
  M4  M0 com escala por porte (sigma_j proporcional a participacao^-gamma, gamma estimado no treino)
Amostra: 20 UFs sem quebras de classificação da DCA, 2013-2025 (ver sensibilidade-calibra-deriva.py).
Saída: data/sensibilidade-modelos-deriva.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from fundos_art115b import fold  # noqa: E402

OUT = HERE / "sensibilidade-modelos-deriva.json"
EXCLUI = {"DF", "GO", "MS", "MT", "TO", "RO", "CE"}
COD = {"RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17, "MA": 21, "PI": 22, "CE": 23,
       "RN": 24, "PB": 25, "PE": 26, "AL": 27, "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35,
       "PR": 41, "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53}
SQ2PI = math.sqrt(2 * math.pi)


def Phi(x):
    return 0.5 * (1 + np.vectorize(math.erf)(np.asarray(x) / math.sqrt(2)))


def crps_normal(y, mu, sig):
    z = (y - mu) / sig
    return sig * (z * (2 * Phi(z) - 1) + 2 * np.exp(-0.5 * z ** 2) / SQ2PI - 1 / math.sqrt(math.pi))


def dm(d):
    return d - d.mean()


def carrega():
    ref = fold(json.loads((HERE / "reforma-tributaria.json").read_text(encoding="utf-8")))
    icms = dict(ref["dca_icms_por_uf"])
    icms.update(json.loads((HERE / "icms-dca-2013-2018.json").read_text(encoding="utf-8")))
    ufs = [u for u in sorted(icms["2025"]) if u not in EXCLUI]
    anos = list(range(2013, 2026))
    M = np.array([[icms[str(y)][u] for u in ufs] for y in anos], float)
    L = np.log(M / M.sum(1, keepdims=True))
    sid = json.loads((HERE / "sidra-pib-pop-uf.json").read_text(encoding="utf-8"))
    pop = {}
    for u in ufs:
        ys = [y for y in anos if sid["pop"].get(str(y), {}).get(str(COD[u]))]
        pop[u] = np.interp(anos, ys, [np.log(sid["pop"][str(y)][str(COD[u])]) for y in ys])
    P = np.array([[pop[u][i] for u in ufs] for i in range(len(anos))])
    P -= np.log(np.exp(P).sum(1, keepdims=True))
    return ufs, anos, L, P


def fit_pl(sd_by_k):
    ks = sorted(sd_by_k)
    b, a = np.polyfit(np.log(ks), np.log([sd_by_k[k] for k in ks]), 1)
    return float(np.exp(a)), float(b)


def main():
    ufs, anos, L, P = carrega()
    n = len(anos)
    share = np.exp(L[-1])
    res = {"M0": [], "M1": [], "M1e": [], "M4": []}
    registros = []
    for i0 in range(6, n - 1):                     # origem: ano de índice i0 (2019..2024)
        kmax = min(4, i0)
        # --- treino: janelas (s, s+k) com s+k <= i0
        y_tr = {k: [dm(L[s + k] - L[s]) for s in range(0, i0 - k + 1)] for k in range(1, kmax + 1)}
        s1, b = fit_pl({k: np.concatenate(v).std(ddof=1) for k, v in y_tr.items()})
        # M1: preditor ex ante (precisa de 4 anos anteriores)
        def mu1(s, k):
            return dm((P[s] - P[s - 4]) / 4 * k)
        tr1 = {k: [(dm(L[s + k] - L[s]), mu1(s, k)) for s in range(4, i0 - k + 1)] for k in range(1, kmax + 1)}
        tr1 = {k: v for k, v in tr1.items() if len(v) >= 1}
        if len(tr1) < 2:
            continue
        # coeficiente estimado
        yy = np.concatenate([a for k, v in tr1.items() for a, _ in v]); xx = np.concatenate([m for k, v in tr1.items() for _, m in v])
        be = float((xx * yy).sum() / (xx * xx).sum())
        s1_1, b_1 = fit_pl({k: np.concatenate([a - 1.0 * m for a, m in v]).std(ddof=1) for k, v in tr1.items()})
        s1_e, b_e = fit_pl({k: np.concatenate([a - be * m for a, m in v]).std(ddof=1) for k, v in tr1.items()})
        # M4: escala por porte
        z = np.concatenate([np.abs(a) / (s1 * k ** b) for k, v in y_tr.items() for a in v])
        ls = np.tile(np.log(share), len(z) // len(share))
        gam = -float(np.polyfit(ls, np.log(z + 1e-9), 1)[0]) if len(z) == len(ls) else 0.0
        gam = max(0.0, min(gam, 0.5))
        sc = share ** (-gam); sc = sc / np.sqrt((sc ** 2).mean())
        # --- teste: alvo i0+h
        for h in range(1, 5):
            if i0 + h > n - 1:
                continue
            y = dm(L[i0 + h] - L[i0])
            preds = {"M0": (np.zeros(len(ufs)), np.full(len(ufs), s1 * h ** b)),
                     "M1": (mu1(i0, h), np.full(len(ufs), s1_1 * h ** b_1)),
                     "M1e": (be * mu1(i0, h), np.full(len(ufs), s1_e * h ** b_e)),
                     "M4": (np.zeros(len(ufs)), s1 * h ** b * sc)}
            for m, (mu, sg) in preds.items():
                c = crps_normal(y, mu, sg)
                zz = (y - mu) / sg
                res[m].append((anos[i0], h, float(c.mean()), float((np.abs(zz) < 1.2816).mean()), float((np.abs(zz) < 1.645).mean()), float(zz.std())))
            registros.append({"origem": anos[i0], "h": h, "gamma": round(gam, 2), "beta_est": round(be, 2)})
    saida = {"_meta": {"amostra": "20 UFs sem quebras da DCA, 2013-2025", "origens": "2019 a 2024, janela expansiva",
                       "horizontes": "1 a 4 anos", "metricas": "CRPS (menor é melhor), cobertura de 80% e 90%"}}
    base = np.mean([r[2] for r in res["M0"]])
    sumario = {}
    for m, rs in res.items():
        a = np.array([[r[2], r[3], r[4], r[5]] for r in rs])
        sumario[m] = {"CRPS_medio": round(float(a[:, 0].mean()), 5), "CRPS_relativo_M0": round(float(a[:, 0].mean() / base), 3),
                      "cob80": round(float(a[:, 1].mean()), 3), "cob90": round(float(a[:, 2].mean()), 3),
                      "sd_z": round(float(a[:, 3].mean()), 3), "n_janelas": len(rs)}
        for h in range(1, 5):
            sel = np.array([r[2] for r in rs if r[1] == h])
            sumario[m][f"CRPS_h{h}_rel_M0"] = round(float(sel.mean() / np.mean([r[2] for r in res["M0"] if r[1] == h])), 3)
    saida["resultados"] = sumario
    saida["coef_populacao_estimado_ultima_origem"] = registros[-1]["beta_est"] if registros else None
    saida["gamma_porte_ultima_origem"] = registros[-1]["gamma"] if registros else None
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(saida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
