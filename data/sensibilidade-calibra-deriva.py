#!/usr/bin/env python3
"""
Calibra a deriva do contrafactual (desvio da participação de cada UF no bolo de ICMS em relação à
participação congelada em 2025) usada em data/sensibilidade-projecao-mc.py, e testa se dá para
estreitar o intervalo de forma legítima. Não altera nenhum resultado publicado.

Achados que motivam o desenho (ver materiais/sensibilidade-projecao-mc.md):
  1. A série DCA bruta 2013-2018 tem quebras de classificação em GO, MS, MT, TO, RO ("outras deduções"
     que só aparecem separadas a partir de 2019) e um erro em CE/2018. Elas inflavam a dispersão.
     A amostra limpa exclui essas UFs (e o DF, sem ICMS em 2013-2018).
  2. Validação fora da amostra: calibra em 2013-2019 (UFs limpas) e testa em 2019-2025 (série líquida,
     como no modelo, 27 UFs), medindo cobertura de intervalos de 80% e 90%.
  3. Heterogeneidade: escala própria por UF (bruta e encolhida) versus escala comum.
  4. Preditores conhecidos (população; PIB regional, que não é conhecido antecipadamente).

Entrada extra: data/sidra-pib-pop-uf.json (SIDRA: tabelas 5938 e 6579, por UF). Saída:
data/sensibilidade-calibra-deriva.json
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from fundos_art115b import fold  # noqa: E402

OUT = HERE / "sensibilidade-calibra-deriva.json"
EXCLUI = {"DF", "GO", "MS", "MT", "TO", "RO", "CE"}
COD = {"RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17, "MA": 21, "PI": 22, "CE": 23,
       "RN": 24, "PB": 25, "PE": 26, "AL": 27, "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35,
       "PR": 41, "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53}


def dm(d):
    return d - d.mean()


def carrega():
    ref = fold(json.loads((HERE / "reforma-tributaria.json").read_text(encoding="utf-8")))
    icms = dict(ref["dca_icms_por_uf"])
    icms.update(json.loads((HERE / "icms-dca-2013-2018.json").read_text(encoding="utf-8")))
    return icms, ref["dca_icms_outras_deducoes_por_uf"]


def logshare(icms, ufs, anos, outras=None):
    M = np.array([[icms[str(y)][u] - (outras[str(y)][u] if outras else 0) for u in ufs] for y in anos], float)
    return np.log(M / M.sum(1, keepdims=True))


def desvios(L, h):
    return np.array([dm(L[t + h] - L[t]) for t in range(len(L) - h)])


def ajusta(L, hmax):
    hs = list(range(1, hmax + 1))
    sd = [desvios(L, h).ravel().std(ddof=1) for h in hs]
    b, a = np.polyfit(np.log(hs), np.log(sd), 1)
    return float(np.exp(a)), float(b), {h: round(float(s), 4) for h, s in zip(hs, sd)}


def cobertura(d, sig):
    z = d / sig
    return float((np.abs(z) < 1.2816).mean()), float((np.abs(z) < 1.645).mean()), float(z.std())


def main():
    icms, outras = carrega()
    todas = sorted(icms["2025"])
    limpas = [u for u in todas if u not in EXCLUI]
    saida = {"_meta": {"excluidas_amostra_limpa": sorted(EXCLUI),
                       "motivo": "quebras de classificação na DCA bruta (outras deduções só separadas a partir de 2019; CE/2018)"}}

    # 1. contaminação: amostra bruta 26 UFs vs limpa vs líquida 2019-2025
    anos = list(range(2013, 2026))
    s1c, bc, sdc = ajusta(logshare(icms, [u for u in todas if u != "DF"], anos), 8)
    s1l, bl, sdl = ajusta(logshare(icms, limpas, anos), 8)
    s1n, bn, sdn = ajusta(logshare(icms, todas, list(range(2019, 2026)), outras), 6)
    saida["amostras"] = {
        "bruta_26UFs_2013_2025": {"s1": round(s1c, 4), "beta": round(bc, 3), "sd_h": sdc, "sd_h8": round(s1c * 8 ** bc, 4)},
        "limpa_20UFs_2013_2025": {"s1": round(s1l, 4), "beta": round(bl, 3), "sd_h": sdl, "sd_h8": round(s1l * 8 ** bl, 4)},
        "liquida_27UFs_2019_2025": {"s1": round(s1n, 4), "beta": round(bn, 3), "sd_h": sdn, "sd_h6": round(s1n * 6 ** bn, 4),
                                    "sd_h8_extrapolado": round(s1n * 8 ** bn, 4)}}
    saida["parametros_adotados"] = {"amostra": "limpa_20UFs_2013_2025", "s1": round(s1l, 4), "beta": round(bl, 3)}

    # 2. validação fora da amostra: treina 2013-2019 (UFs limpas, bruto), testa 2019-2025 (líquido, UFs limpas)
    Ltr = logshare(icms, limpas, list(range(2013, 2020)))
    Lte_all = logshare(icms, todas, list(range(2019, 2026)), outras)
    idx = [todas.index(u) for u in limpas]
    s1t, bt, _ = ajusta(Ltr, 6)
    s1x, bx, _ = ajusta(logshare(icms, [u for u in todas if u != "DF"], list(range(2013, 2020))), 6)  # calibração contaminada
    val = {}
    for h in [2, 3, 4]:
        d = desvios(Lte_all, h)[:, idx]
        val[h] = {"limpa": dict(zip(["cob80", "cob90", "sd_z"], map(lambda v: round(v, 3), cobertura(d, s1t * h ** bt)))),
                  "contaminada": dict(zip(["cob80", "cob90", "sd_z"], map(lambda v: round(v, 3), cobertura(d, s1x * h ** bx))))}
    saida["validacao_fora_da_amostra"] = {"treino": "2013-2019 bruto", "teste": "2019-2025 líquido, UFs limpas",
                                           "alvo": {"cob80": 0.80, "cob90": 0.90}, "resultado": val,
                                           "sd_h4_treino": {"limpa": round(s1t * 4 ** bt, 4), "contaminada": round(s1x * 4 ** bx, 4)}}

    # 3. heterogeneidade por UF (escala própria vs comum) fora da amostra
    hs = range(1, 7)
    z = [[(desvios(Ltr, h)[:, j] / (s1t * h ** bt)) for h in hs] for j in range(len(limpas))]
    k = np.array([np.sqrt(np.mean(np.square(np.concatenate(zz)))) for zz in z])
    ks = np.sqrt(0.5 * k ** 2 + 0.5)
    het = {}
    for h in [2, 3, 4]:
        d = desvios(Lte_all, h)[:, idx]
        row = {}
        for nome, sc in [("comum", np.ones(len(limpas))), ("propria", k), ("propria_encolhida", ks)]:
            sig = s1t * h ** bt * sc[None, :]
            zz = d / sig
            row[nome] = {"cob80": round(float((np.abs(zz) < 1.2816).mean()), 3),
                         "loglik": round(float((-0.5 * np.log(2 * np.pi * sig ** 2) - 0.5 * zz ** 2).sum()), 1)}
        het[h] = row
    saida["heterogeneidade_por_UF"] = {"resultado": het, "leitura": "escala própria não melhora fora da amostra; mantém-se a escala comum"}

    # 4. caudas
    zs = np.concatenate([(desvios(Ltr, h) / (s1t * h ** bt)).ravel() for h in hs])
    saida["curtose_padronizada"] = round(float(((zs - zs.mean()) ** 4).mean() / zs.var() ** 2), 2)

    # 5. preditores (UFs limpas, 2013-2023 por causa do PIB regional)
    p = HERE / "sidra-pib-pop-uf.json"
    if p.exists():
        sid = json.loads(p.read_text(encoding="utf-8"))
        Y = list(range(2013, 2024))
        L = logshare(icms, limpas, Y)
        pop = {}
        for u in limpas:
            ys = [y for y in range(2013, 2026) if sid["pop"].get(str(y), {}).get(str(COD[u]))]
            pop[u] = np.interp(range(2013, 2026), ys, [np.log(sid["pop"][str(y)][str(COD[u])]) for y in ys])
        Lp = np.array([[pop[u][y - 2013] for u in limpas] for y in Y])
        Lp -= np.log(np.exp(Lp).sum(1, keepdims=True))
        G = np.array([[sid["pib"][str(y)][str(COD[u])] for u in limpas] for y in Y], float)
        Lg = np.log(G / G.sum(1, keepdims=True))
        h = 4
        T = range(len(Y) - h)
        y = np.concatenate([dm(L[t + h] - L[t]) for t in T])
        pr = {}
        for nome, fx in [("variacao_participacao_populacao", lambda t: dm(Lp[t + h] - Lp[t])),
                         ("variacao_participacao_PIB", lambda t: dm(Lg[t + h] - Lg[t])),
                         ("nivel_ICMS_relativo_populacao", lambda t: dm(L[t] - Lp[t])),
                         ("nivel_ICMS_relativo_PIB", lambda t: dm(L[t] - Lg[t])),
                         ("desvio_anterior_4a", lambda t: dm(L[t] - L[t - h]) if t >= h else np.zeros(len(limpas)))]:
            x = np.concatenate([fx(t) for t in T])
            b = np.polyfit(x, y, 1)
            r2 = 1 - (y - np.polyval(b, x)).var() / y.var()
            pr[nome] = {"beta": round(float(b[0]), 3), "R2": round(float(r2), 3)}
        saida["preditores_h4"] = {"amostra": "20 UFs, janelas 2013-2023", "resultados": pr,
                                  "leitura": "população (conhecida, projetada pelo IBGE) explica ~18% da variância; "
                                             "PIB regional explica mais mas não é conhecido antecipadamente; "
                                             "persistência e convergência de nível não explicam"}
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(json.dumps(saida, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    main()
