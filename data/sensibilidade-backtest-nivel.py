#!/usr/bin/env python3
"""
Backtest do NÍVEL da arrecadação: a faixa do modelo (crescimento real do PIB por bootstrap estacionário
mais ruído da razão bolo/PIB) cobre o crescimento real acumulado do bolo ICMS+ISS+FECOP observado em 2013-2025?
Para cada janela (origem T, horizonte h = 1 a 8) compara o log do crescimento acumulado do bolo real
(DCA, R$ de 2025) com h x mu (mu = crescimento médio histórico do PIB) e a faixa implícita no modelo.
Não altera nenhum resultado publicado. Saída: data/sensibilidade-backtest-nivel.json
"""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
OUT = HERE / "sensibilidade-backtest-nivel.json"
SD_RATIO_PONTO = 0.037  # desvio anual histórico (log) da razão bolo/PIB
SD_RATIO_ADOTADO = 0.06  # calibrado pelo CRPS neste backtest
SD_REF = 0.012
GRADE = [0.0, 0.03, 0.037, 0.05, 0.06, 0.07, 0.08]
L_BLOCO = 4


def main():
    g = json.loads((HERE / "sidra-pib-crescimento-brasil.json").read_text(encoding="utf-8"))["crescimento_real_pct"]
    x = np.array([g[k] for k in sorted(g, key=int)]) / 100
    dev = x - x.mean()
    mu = np.log1p(x).mean()
    n = len(dev)
    rng = np.random.default_rng(3)
    N = 60000
    out = np.zeros((N, 8))
    pos = rng.integers(0, n, N)
    for t in range(8):
        if t > 0:
            novo = rng.random(N) < 1 / L_BLOCO
            pos = np.where(novo, rng.integers(0, n, N), (pos + 1) % n)
        out[:, t] = dev[pos]
    sd_g = np.cumsum(out, axis=1).std(axis=0)
    hist = json.loads((HERE / "ibs-projecao-nacional.json").read_text(encoding="utf-8"))["historico"]
    lb = np.log([r["bolo_real_2025"] for r in hist])
    anos = [r["ano"] for r in hist]
    import math

    def crps(y, sig):
        zz = y / sig
        Phi = 0.5 * (1 + np.vectorize(math.erf)(zz / math.sqrt(2)))
        return sig * (zz * (2 * Phi - 1) + 2 * np.exp(-0.5 * zz * zz) / math.sqrt(2 * math.pi) - 1 / math.sqrt(math.pi))
    erros = [(h, lb[i + h] - lb[i] - h * mu) for h in range(1, 9) for i in range(len(lb) - h)]
    grade = {}
    for s_ in GRADE:
        zs = np.array([e / np.hypot(np.hypot(sd_g[h - 1], s_), SD_REF) for h, e in erros])
        grade[str(s_)] = {"cobertura80": round(float((np.abs(zs) < 1.2816).mean()), 2), "cobertura90": round(float((np.abs(zs) < 1.645).mean()), 2),
                          "CRPS_medio_pct": round(float(np.mean([crps(e, np.hypot(np.hypot(sd_g[h - 1], s_), SD_REF)) for h, e in erros]) * 100), 3)}
    SD_RATIO = np.hypot(SD_RATIO_ADOTADO, SD_REF)
    z = {h: [] for h in range(1, 9)}
    for h in range(1, 9):
        sd = np.hypot(sd_g[h - 1], SD_RATIO)
        for i in range(len(lb) - h):
            z[h].append((lb[i + h] - lb[i] - h * mu) / sd)
    res = {}
    todos = np.concatenate([np.array(v) for v in z.values()])
    for h, v in z.items():
        v = np.array(v)
        res[h] = {"n_janelas": len(v), "sd_modelo_pct": round(float(np.hypot(sd_g[h - 1], SD_RATIO) * 100), 1),
                  "sd_empirico_pct": round(float(((v * np.hypot(sd_g[h - 1], SD_RATIO)).std(ddof=1)) * 100), 1) if len(v) > 1 else None,
                  "cobertura80": round(float((np.abs(v) < 1.2816).mean()), 2), "cobertura90": round(float((np.abs(v) < 1.645).mean()), 2)}
    saida = {"_meta": {"descricao": "Cobertura da faixa do nível da arrecadação (bolo real) em janelas de 2013-2025", "nota": "janelas sobrepostas e poucas; mu e sigma são de amostra inteira (dentro da amostra)"},
             "grade_ruido_da_razao": grade, "ruido_adotado": SD_RATIO_ADOTADO, "por_horizonte": res, "geral": {"n": int(len(todos)), "cobertura80": round(float((np.abs(todos) < 1.2816).mean()), 2),
                                             "cobertura90": round(float((np.abs(todos) < 1.645).mean()), 2), "sd_z": round(float(todos.std(ddof=1)), 2)}}
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(saida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
