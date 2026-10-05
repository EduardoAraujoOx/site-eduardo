#!/usr/bin/env python3
"""
TESTE (não altera nenhum resultado publicado): como tratar 2026 no coeficiente histórico (CPT, média 2019-2026 na lei).
Três tratamentos para o ano ainda não fechado:
  (a) omitir 2026 (média de 2019-2025: o que o repositório faz hoje);
  (b) repetir 2025 em 2026 (a nota técnica do COMSEFAZ; média com 2025 em dobro);
  (c) nowcast de 2026 pelo RREO de jan-ago (participação de 2025 x exp(β · variação da participação jan-ago); β do nowcast).
Backtest (20 UFs sem quebras da DCA, 2013-2025): para cada ano terminal T de 2020 a 2025, o alvo é a média da participação no
ICMS em T-7..T (oito anos, como na lei), e cada tratamento só usa dados até T-1 (e, em (c), o RREO de T).
Saída: data/teste-cpt-2026.json
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from fundos_art115b import fold  # noqa: E402

EXCLUI = {"DF", "GO", "MS", "MT", "TO", "RO", "CE"}
BETA = 0.772      # sensibilidade-nowcast-2026.json
MU_NOW = None


def main():
    ref = fold(json.loads((HERE / "reforma-tributaria.json").read_text(encoding="utf-8")))
    dca = dict(ref["dca_icms_por_uf"])
    dca.update(json.loads((HERE / "icms-dca-2013-2018.json").read_text(encoding="utf-8")))
    rr = json.loads((HERE / "rreo-icms-mensal.json").read_text(encoding="utf-8"))
    ufs = [u for u in sorted(dca["2025"]) if u not in EXCLUI]

    def share(ano):
        v = np.array([dca[str(ano)][u] for u in ufs], float)
        return v / v.sum()

    S = {a: share(a) for a in range(2013, 2026)}

    def janago(ano):
        a = np.array([sum(rr[str(ano)][u]["meses"][4:12]) for u in ufs], float)
        return a / a.sum()

    def nowcast(ano):
        """participação estimada de `ano` a partir da de ano-1 e da variação jan-ago do RREO."""
        x = np.log(janago(ano)) - np.log(janago(ano - 1))
        ruim = np.abs(x - np.median(x)) > 0.4
        x = np.where(ruim, np.nan, x)
        x = np.nan_to_num(x - np.nanmean(x))
        s = S[ano - 1] * np.exp(BETA * x)
        return s / s.sum()

    res = {"a_omitir": [], "b_repetir_2025": [], "c_nowcast_RREO": []}
    for T in range(2020, 2026):
        alvo = np.mean([S[a] for a in range(T - 7, T + 1)], axis=0)
        ant = [S[a] for a in range(T - 7, T)]               # T-7..T-1 (sete anos)
        a_ = np.mean(ant, axis=0)
        b_ = (np.sum(ant, axis=0) + S[T - 1]) / 8.0
        c_ = (np.sum(ant, axis=0) + nowcast(T)) / 8.0
        for nome, est in (("a_omitir", a_), ("b_repetir_2025", b_), ("c_nowcast_RREO", c_)):
            res[nome].append(((est - alvo) / alvo))
    saida = {}
    for n, v in res.items():
        e = np.concatenate(v)
        saida[n] = {"erro_relativo_medio_abs_pct": round(float(np.abs(e).mean() * 100), 3), "rmse_relativo_pct": round(float(np.sqrt((e ** 2).mean()) * 100), 3),
                    "p90_abs_pct": round(float(np.percentile(np.abs(e), 90) * 100), 3)}
        print(n, saida[n])

    # aplicação a 2026: coeficiente de ICMS (participação média) de cada UF sob os três tratamentos
    ant26 = [S[a] for a in range(2019, 2026)]
    s26 = nowcast(2026)
    aplic = {"a_omitir": np.mean(ant26, axis=0), "b_repetir_2025": (np.sum(ant26, axis=0) + S[2025]) / 8.0, "c_nowcast_RREO": (np.sum(ant26, axis=0) + s26) / 8.0}
    aplic_uf = {u: {n: round(100 * float(v[i]), 4) for n, v in aplic.items()} for i, u in enumerate(ufs)}
    for u in ("PR", "ES", "SP", "MG"):
        print(u, aplic_uf[u])
    (HERE / "teste-cpt-2026.json").write_text(json.dumps({"_meta": "Backtest do tratamento de 2026 no coeficiente histórico; participação no ICMS (20 UFs sem quebras), %", "backtest": saida, "aplicacao_2026_participacao_media_pct": aplic_uf}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
