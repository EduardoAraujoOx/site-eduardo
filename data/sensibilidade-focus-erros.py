#!/usr/bin/env python3
"""
Erros de previsão do Focus (BCB, mediana das expectativas anuais de PIB) frente ao crescimento realizado
(IBGE, SIDRA 6784), para calibrar a incerteza do crescimento real do PIB na análise de sensibilidade.
Pesquisa mais próxima de 1º de outubro de cada ano T; erro = crescimento acumulado realizado menos previsto
nos anos T+1..T+k (k = 1 a 4). Compara com o desvio implícito no bootstrap estacionário (Politis-Romano)
dos desvios históricos de crescimento, para escolher o comprimento médio de bloco.
Não altera nenhum resultado publicado. Saída: data/sensibilidade-focus-erros.json
"""
import datetime as dt
import json
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
OUT = HERE / "sensibilidade-focus-erros.json"
BASE = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais"


def baixa():
    rows = []
    for a0 in range(2002, 2026, 6):
        q = {"$filter": f"Indicador eq 'PIB Total' and Data ge '{a0}-01-01' and Data lt '{a0 + 6}-01-01' and baseCalculo eq 0",
             "$select": "Data,DataReferencia,Mediana", "$top": "100000", "$format": "json"}
        rows += json.load(urllib.request.urlopen(BASE + "?" + urllib.parse.urlencode(q, quote_via=urllib.parse.quote), timeout=120))["value"]
    return rows


def main():
    rows = baixa()
    by = {}
    for r in rows:
        by.setdefault(r["Data"], {})[int(r["DataReferencia"])] = r["Mediana"]
    dates = sorted(by)
    g = {int(k): v for k, v in json.loads((HERE / "sidra-pib-crescimento-brasil.json").read_text(encoding="utf-8"))["crescimento_real_pct"].items()}
    res = {k: [] for k in range(1, 5)}
    for T in range(2003, 2023):
        t0 = dt.date(T, 10, 1)
        cand = [d for d in dates if abs((dt.date.fromisoformat(d) - t0).days) <= 10 and len(by[d]) >= 5]
        if not cand:
            continue
        f = by[min(cand, key=lambda d: abs((dt.date.fromisoformat(d) - t0).days))]
        for k in range(1, 5):
            ys = [T + j for j in range(1, k + 1)]
            if all(y in f for y in ys) and all(y in g for y in ys):
                res[k].append((T, sum(np.log1p(g[y] / 100) for y in ys) - sum(np.log1p(f[y] / 100) for y in ys)))
    foc = {}
    for k, v in res.items():
        e = np.array([x for _, x in v])
        foc[k] = {"n": len(e), "vies_pct": round(float(e.mean() * 100), 2), "rmse_pct": round(float(np.sqrt((e ** 2).mean()) * 100), 2),
                  "sd_pct": round(float(e.std(ddof=1) * 100), 2)}
    x = np.array([g[y] for y in sorted(g)]) / 100
    dev = x - x.mean()
    n = len(dev)
    rng = np.random.default_rng(2)
    N = 60000
    alvo = np.array([foc[k]["sd_pct"] for k in range(1, 5)])
    modelo = {}
    for L in (1, 2, 3, 4, 5, 6):
        out = np.zeros((N, 4))
        pos = rng.integers(0, n, N)
        for t in range(4):
            if t > 0:
                novo = rng.random(N) < 1 / L
                pos = np.where(novo, rng.integers(0, n, N), (pos + 1) % n)
            out[:, t] = dev[pos]
        sd = np.cumsum(out, axis=1).std(axis=0) * 100
        modelo[L] = {"sd_acum_k1_a_k4": [round(float(s), 2) for s in sd], "distancia_media_ao_Focus": round(float(np.abs(sd - alvo).mean()), 2)}
    saida = {"_meta": {"fonte": "BCB Olinda, ExpectativasMercadoAnuais (PIB Total, mediana); IBGE SIDRA 6784",
                       "leitura": "erro de previsão do Focus por horizonte e bootstrap estacionário que melhor o reproduz"},
             "erro_focus_acumulado": foc, "bootstrap_estacionario_por_bloco_medio": modelo, "bloco_adotado": 4}
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(saida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
