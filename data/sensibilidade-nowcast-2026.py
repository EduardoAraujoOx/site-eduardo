#!/usr/bin/env python3
"""
Nowcast da participação de cada UF no bolo de ICMS em 2026 a partir do RREO de jan-ago (SICONFI) e escala
própria de volatilidade por UF com encolhimento. Não altera nenhum resultado publicado.

Validação: para 2019-2025, regride a variação anual da participação na DCA (UFs sem quebras) sobre a
variação da participação no acumulado jan-ago do RREO. O coeficiente e o desvio residual alimentam o nowcast
de 2026 e reduzem a incerteza do horizonte (o modelo passa a medir a deriva a partir de 2026, não de 2025).
Entrada: data/rreo-icms-mensal.json (collect-rreo-icms-mensal.py). Saída: data/sensibilidade-nowcast-2026.json
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from fundos_art115b import fold  # noqa: E402

EXCLUI = {"DF", "GO", "MS", "MT", "TO", "RO", "CE"}
OUT = HERE / "sensibilidade-nowcast-2026.json"


def main():
    rr = json.loads((HERE / "rreo-icms-mensal.json").read_text(encoding="utf-8"))
    ref = fold(json.loads((HERE / "reforma-tributaria.json").read_text(encoding="utf-8")))
    dca = dict(ref["dca_icms_por_uf"])
    dca.update(json.loads((HERE / "icms-dca-2013-2018.json").read_text(encoding="utf-8")))
    todas = sorted(dca["2025"])
    limpas = [u for u in todas if u not in EXCLUI]

    def janago(ano, uf):
        r = rr.get(str(ano), {}).get(uf)
        if not r or any(v is None for v in r["meses"][4:12]):
            return None
        return float(sum(r["meses"][4:12]))

    def x_relativo(ano, ufs):
        a = np.array([janago(ano, u) for u in ufs], float)
        b = np.array([janago(ano - 1, u) for u in ufs], float)
        if np.isnan(a).any() or np.isnan(b).any():
            return None
        sh = np.log(a / a.sum()) - np.log(b / b.sum())
        ruim = np.abs(sh - np.median(sh)) > 0.4          # erro de dado no RREO (mês zerado ou duplicado)
        sh = np.where(ruim, np.nan, sh)
        return sh - np.nanmean(sh)

    X, Y, anos = [], [], []
    for ano in range(2019, 2026):
        x = x_relativo(ano, limpas)
        if x is None:
            continue
        d = np.array([dca[str(ano)][u] for u in limpas], float)
        d0 = np.array([dca[str(ano - 1)][u] for u in limpas], float)
        y = np.log(d / d.sum()) - np.log(d0 / d0.sum())
        X.append(x)
        Y.append(y - y.mean())
        anos.append(ano)
    Xc, Yc = np.concatenate(X), np.concatenate(Y)
    ok = ~np.isnan(Xc)
    Xc, Yc = Xc[ok], Yc[ok]
    X = [np.where(np.isnan(x), 0.0, x) for x in X]
    beta = float((Xc * Yc).sum() / (Xc * Xc).sum())
    res = Yc - beta * Xc
    val = {"anos": anos, "beta": round(beta, 3), "sd_variacao_anual_DCA": round(float(Yc.std(ddof=1)), 4),
           "sd_residual_nowcast": round(float(res.std(ddof=1)), 4), "corr": round(float(np.corrcoef(Xc, Yc)[0, 1]), 3),
           "por_ano": {str(a): {"corr": round(float(np.corrcoef(x[x != 0], y[x != 0])[0, 1]), 2), "sd_y": round(float(y.std(ddof=1)), 4),
                                "sd_residual": round(float((y - beta * x).std(ddof=1)), 4)} for a, x, y in zip(anos, X, Y)}}
    # validação leave-one-year-out
    loo = []
    for i in range(len(anos)):
        xt = np.concatenate([X[j] for j in range(len(anos)) if j != i]); yt = np.concatenate([Y[j] for j in range(len(anos)) if j != i])
        b = (xt * yt).sum() / (xt * xt).sum()
        loo.append(float(((Y[i] - b * X[i]) ** 2).sum()) / float((Y[i] ** 2).sum()))
    val["razao_EQM_leave_one_year_out"] = round(float(np.mean(loo)), 3)

    # nowcast 2026 (todas as UFs, mesma medida líquida do RREO)
    com_dado = [u for u in todas if u != "DF"]       # o DF não tem RREO no Anexo 03 para esta conta
    x26 = x_relativo(2026, com_dado)
    mu = {u: round(float(beta * v), 5) if not np.isnan(v) else 0.0 for u, v in zip(com_dado, x26)}
    mu["DF"] = 0.0
    prev = {u: rr["2026"][u].get("previsao") for u in com_dado if u in rr.get("2026", {})}

    # escala própria de volatilidade (UFs sem quebras), com encolhimento 50%
    anos_l = list(range(2013, 2026))
    M = np.array([[dca[str(y)][u] for u in limpas] for y in anos_l], float)
    L = np.log(M / M.sum(1, keepdims=True))
    sd = {h: np.array([(L[t + h] - L[t]) - (L[t + h] - L[t]).mean() for t in range(len(L) - h)]) for h in range(1, 7)}
    hs = np.arange(1, 7)
    b, a = np.polyfit(np.log(hs), np.log([sd[h].ravel().std(ddof=1) for h in hs]), 1)
    s1 = np.exp(a)
    k = np.array([np.sqrt(np.mean(np.concatenate([sd[h][:, j] / (s1 * h ** b) for h in hs]) ** 2)) for j in range(len(limpas))])
    ks = np.sqrt(0.5 * k ** 2 + 0.5)
    saida = {"_meta": {"descricao": "Nowcast 2026 da participação por UF (RREO jan-ago) e escala própria de volatilidade (encolhida)",
                       "periodo_rreo": "jan-ago de 2026 contra jan-ago de 2025 (4º bimestre)"},
             "validacao": val, "mu_uf": mu, "sd_residual": val["sd_residual_nowcast"],
             "k_uf": {u: round(float(v), 3) for u, v in zip(limpas, ks)}, "previsao_2026_estado_RREO": prev}
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k_: saida[k_] for k_ in ("validacao",)}, ensure_ascii=False, indent=1))
    print("mu PR/ES/SP/MG/RJ:", {u: mu[u] for u in ("PR", "ES", "SP", "MG", "RJ")})
    print("k PR/ES/SP:", {u: saida["k_uf"].get(u) for u in ("PR", "ES", "SP")})


if __name__ == "__main__":
    main()
