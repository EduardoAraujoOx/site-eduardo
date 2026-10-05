#!/usr/bin/env python3
"""
TESTE (não altera nenhum resultado publicado): como estimar 2026 para o coeficiente histórico dos MUNICÍPIOS, onde o nowcast por
município não é possível (o RREO municipal é bimestral só para quem tem mais de 50 mil habitantes e o ISS de município pequeno é
volátil). Compara, para cada ano T de 2022 a 2025, a previsão da participação do município na receita de referência
(ISS + cota-parte de ICMS, em % do total nacional) feita só com dados até T-1:
  ISS:         (i) média de todos os anos anteriores; (ii) repetir T-1; (iii) média de T-1 e T-2; (iv) mediana de T-1, T-2 e T-3;
  cota-parte:  (i) média; (ii) repetir T-1; (v) T-1 vezes a variação da participação da UF no ICMS estimada pelo RREO de T (nowcast
               do estado transmitido à cota-parte, sem nowcast municipal).
Erro = |previsão - realizado| / realizado, por município com valor positivo, por classe de população.
Saída: data/teste-cpt-2026-municipios.json
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from fundos_art115b import fold  # noqa: E402

BETA = 0.772


def main():
    d = fold(json.loads((HERE / "reforma-tributaria.json").read_text(encoding="utf-8")))
    det = d["dca_detalhes"]
    rr = json.loads((HERE / "rreo-icms-mensal.json").read_text(encoding="utf-8"))
    pop = json.loads((HERE / "populacao-municipios-media-2019-2026.json").read_text(encoding="utf-8"))["municipios"]
    anos = list(range(2019, 2026))
    ufs_rr = sorted(rr["2025"])

    def janago(ano):
        a = np.array([sum(rr[str(ano)][u]["meses"][4:12]) if u in rr[str(ano)] and all(v is not None for v in rr[str(ano)][u]["meses"][4:12]) else np.nan for u in ufs_rr], float)
        return a

    def mu_uf(T):
        a, b = janago(T), janago(T - 1)
        ok = ~(np.isnan(a) | np.isnan(b))
        sh = np.full(len(ufs_rr), np.nan)
        sh[ok] = np.log(a[ok] / a[ok].sum()) - np.log(b[ok] / b[ok].sum())
        ruim = np.abs(sh - np.nanmedian(sh)) > 0.4
        sh[ruim] = np.nan
        sh = sh - np.nanmean(sh)
        return {u: (BETA * v if not np.isnan(v) else 0.0) for u, v in zip(ufs_rr, sh)}

    # séries por município: ISS e cota-parte (valores nominais) e totais nacionais por ano para obter participações
    cods = {}
    for ano in anos:
        for cod, v in (det.get(str(ano)) or {}).items():
            if v.get("uf") and v["uf"] != "DF":
                cods.setdefault(cod, {"uf": v["uf"], "iss": {}, "cota": {}})
                cods[cod]["iss"][ano] = v.get("valor") or 0.0
                cods[cod]["cota"][ano] = v.get("cota_parte_icms") or 0.0
    tot_iss = {a: sum(c["iss"].get(a, 0) for c in cods.values()) for a in anos}
    tot_cota = {a: sum(c["cota"].get(a, 0) for c in cods.values()) for a in anos}
    classes = [("ate_10_mil", 0, 10e3), ("10_a_50_mil", 10e3, 50e3), ("mais_de_50_mil", 50e3, 1e12)]
    res = {}
    for T in range(2022, 2026):
        muT = mu_uf(T)
        fac = {}
        for u in ufs_rr:
            fac[u] = np.exp(muT.get(u, 0.0))
        for cod, c in cods.items():
            p = (pop.get(cod) or {}).get("pop_media")
            if not p or any(T - k not in c["iss"] for k in (1, 2, 3)):
                continue
            cl = next(n for n, lo, hi in classes if lo <= p < hi)
            for comp, serie, tot in (("iss", c["iss"], tot_iss), ("cota", c["cota"], tot_cota)):
                s = {a: serie.get(a, 0) / tot[a] for a in anos}
                real = s[T]
                if real <= 0:
                    continue
                hist = [s[a] for a in range(2019, T)]
                prev = {"media_historico": np.mean(hist), "repete_T-1": s[T - 1], "media_T-1_T-2": (s[T - 1] + s[T - 2]) / 2,
                        "mediana_3": np.median([s[T - 1], s[T - 2], s[T - 3]])}
                if comp == "cota":
                    prev["T-1_x_nowcast_UF"] = s[T - 1] * fac.get(c["uf"], 1.0)
                for k, v in prev.items():
                    res.setdefault((comp, cl, k), []).append(abs(v - real) / real)
    saida = {}
    for (comp, cl, k), v in sorted(res.items()):
        v = np.array(v)
        saida.setdefault(comp, {}).setdefault(cl, {})[k] = {"n": int(len(v)), "mediana_erro_rel_pct": round(float(np.median(v) * 100), 2),
                                                           "media_aparada_5_95_pct": round(float(np.mean(np.clip(v, 0, np.percentile(v, 95))) * 100), 2)}
    for comp in saida:
        for cl in saida[comp]:
            print(comp, cl, {k: (x["mediana_erro_rel_pct"], x["media_aparada_5_95_pct"]) for k, x in saida[comp][cl].items()})
    (HERE / "teste-cpt-2026-municipios.json").write_text(json.dumps({"_meta": "Erro relativo da previsão da participação do município no ano T com dados até T-1, T=2022..2025", "resultados": saida}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
