#!/usr/bin/env python3
"""
Análise de sensibilidade (Monte Carlo) da variação projetada da receita dos entes, 2029-2033.

NÃO altera nenhum resultado publicado: lê as mesmas entradas de build-resultados-consolidados.py,
reproduz o caso central (verificação de consistência) e acrescenta choques estocásticos calibrados
em dados observados.

Fontes de incerteza simuladas
  A. Deriva do contrafactual: a participação de cada UF no bolo ICMS+ISS não fica congelada em 2025
     (hipótese do modelo central). O desvio logarítmico da participação ao longo de h anos é calibrado
     por backtest em 2013-2025 (DCA, 26 UFs, DF fora por falta de série): sd(h) = s1 * h^beta,
     estimada por MQO em log. Persistência dos desvios é ~nula (correlação entre desvios sucessivos
     de 4 anos ~0,1), logo não há viés a corrigir, apenas dispersão.
  B. Erro de medida do coeficiente de distribuição por destino (φ): choque lognormal por UF com
     sigma = dispersão observada entre fontes independentes (POF/Censo x Gobetti 2023).
Os choques são renormalizados para somar 1 entre UFs (o bolo nacional é dado pela lei).

Saída: data/sensibilidade-projecao-mc.json
"""
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("brc", HERE / "build-resultados-consolidados.py")
brc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brc)
from fundos_art115b import fold  # noqa: E402

OUT = HERE / "sensibilidade-projecao-mc.json"
ANOS = brc.ANOS
UFS = brc.UFS
N_SIM = 20000
SEED = 20261004
SIGMA_PHI = 0.10          # central: erro relativo médio entre fontes (~10%)
KAPPA = 1.0              # fator de escala dos intervalos (1 = sem recalibração; ver sensibilidade-incerteza-parametros.py)
USAR_BOOT = True         # sorteia (s1, beta) do bootstrap em blocos (incerteza dos parâmetros)
SIGMA_PHI_ALTO = 0.19     # sensibilidade: dispersão log entre POF/Censo e Gobetti 2023 (inclui UFs pequenas)


def backtest():
    ref = fold(json.loads((HERE / "reforma-tributaria.json").read_text(encoding="utf-8")))
    icms = dict(ref["dca_icms_por_uf"])
    icms.update(json.loads((HERE / "icms-dca-2013-2018.json").read_text(encoding="utf-8")))
    ufs = [u for u in UFS if u != "DF"]
    anos = list(range(2013, 2026))
    M = np.array([[icms[str(y)][u] for u in ufs] for y in anos], dtype=float)
    L = np.log(M / M.sum(1, keepdims=True))

    def dispersao(ano_max=2025):
        idx = [i for i, y in enumerate(anos) if y <= ano_max]
        out = {}
        for h in range(1, 9):
            ds = []
            for t in idx:
                if t + h in idx:
                    d = L[t + h] - L[t]
                    ds.append(d - d.mean())          # desvio em relação à média da seção
            if ds:
                out[h] = (float(np.std(np.concatenate(ds), ddof=1)), len(ds))
        return out

    def ajusta(disp):
        hs = np.array(sorted(disp))
        sd = np.array([disp[h][0] for h in hs])
        b, a = np.polyfit(np.log(hs), np.log(sd), 1)
        return float(np.exp(a)), float(b)

    res = {}
    for nome, amax in [("2013-2025", 2025), ("2013-2021 (antes do choque dos combustíveis)", 2021)]:
        d = dispersao(amax)
        s1, b = ajusta(d)
        res[nome] = {"sd_por_horizonte": {h: round(v[0], 4) for h, v in d.items()},
                     "janelas": {h: v[1] for h, v in d.items()}, "s1": round(s1, 4), "beta": round(b, 3)}
    # persistência: desvio dos 4 anos seguintes vs. 4 anos anteriores
    pers = []
    for t in range(0, len(anos) - 8):
        a = L[t + 4] - L[t]
        c = L[t + 8] - L[t + 4]
        pers.append(float(np.corrcoef(a, c)[0, 1]))
    res["persistencia_corr_4a_4a"] = {"media": round(float(np.mean(pers)), 3),
                                      "valores": [round(x, 3) for x in pers]}
    # por tamanho
    sz = np.exp(L[-1])
    big = sz > np.median(sz)
    d4 = np.array([L[t + 4] - L[t] - (L[t + 4] - L[t]).mean() for t in range(len(anos) - 4)])
    res["sd_4a_grandes_vs_pequenas"] = {"grandes": round(float(d4[:, big].std(ddof=1)), 4),
                                         "pequenas": round(float(d4[:, ~big].std(ddof=1)), 4)}
    return res


def main():
    ref_data = fold(brc.load("reforma-tributaria.json"))
    coef_uf = brc.load("coeficientes-uf.json")
    phi_dest = brc.load("phi-dest-pof-censo.json")
    nac_data = brc.load("ibs-projecao-nacional.json")
    seguro = brc.load("seguro-receita-repasses.json")
    nac = {r["ano"]: r for r in nac_data["projecao"]}
    params, _ = brc.compute_params_uf(ref_data, coef_uf, phi_dest)
    ridx = brc.build_repasse_index(seguro, ANOS)
    central = json.loads((HERE / "resultados-consolidados-ibs.json").read_text(encoding="utf-8"))

    # parâmetros da deriva: amostra limpa de quebras de classificação da DCA (ver
    # sensibilidade-calibra-deriva.py); a calibração anterior (bruta, 26 UFs) fica só como comparação
    cal = json.loads((HERE / "sensibilidade-calibra-deriva.json").read_text(encoding="utf-8"))
    s1, beta = cal["parametros_adotados"]["s1"], cal["parametros_adotados"]["beta"]
    bt = {"adotada": cal["amostras"]["limpa_20UFs_2013_2025"], "anterior_contaminada": cal["amostras"]["bruta_26UFs_2013_2025"],
          "liquida_2019_2025": cal["amostras"]["liquida_27UFs_2019_2025"],
          "validacao_fora_da_amostra": cal["validacao_fora_da_amostra"]}

    # vetores por UF (esfera estado e agregado UF), por ano
    def parte(uf, esfera):
        p = params[uf]
        parts = [p["estado"]] if esfera == "estado" else [p["estado"]] + ([p["municipio"]] if p["municipio"] else [])
        n = sum(x["coefNeutro"] for x in parts)
        c = sum(x["coefCPT"] for x in parts)
        pl = sum(x["coefPleno"] for x in parts)
        rep = {}
        if uf in ridx:
            for a in ANOS:
                rep[a] = ridx[uf]["estado"].get(a, 0) + (ridx[uf]["municipio"].get(a, 0) if esfera == "total" and p["municipio"] else 0)
        return n, c, pl, rep

    # participação de cada UF (estado+município) para renormalizar os choques
    n_uf = np.array([parte(u, "total")[0] for u in UFS])
    pl_uf = np.array([parte(u, "total")[2] for u in UFS])

    def calcula(esfera, shock_n, shock_phi, acumulado=False, reais=False):
        """shock_n: (N, 27, nanos) multiplicador de participação; shock_phi: (N, 27).
        acumulado=True devolve a variação acumulada 2029-2033 (soma pós / soma contrafactual - 1), (N, 27)."""
        N = shock_phi.shape[0]
        out = np.zeros((N, len(UFS), len(ANOS)))
        arr_t = np.zeros((N, len(UFS), len(ANOS)))
        arr_c = np.zeros((N, len(UFS), len(ANOS)))
        sum_t = np.zeros((N, len(UFS)))
        sum_c = np.zeros((N, len(UFS)))
        for j, u in enumerate(UFS):
            n0, c0, pl0, rep = parte(u, esfera)
            for k, a in enumerate(ANOS):
                r = nac[a]
                ref_a = r["icms_iss_residual"] + r["ibs_bruto"]
                ca = r.get("ca", 0.0)
                nn = n0 * shock_n[:, j, k]
                pp = pl0 * shock_phi[:, j]
                tot = (r["icms_iss_residual"] * nn + (1 - ca) * r["ibs_historico"] * c0
                       + r["ibs_destino_liquido"] * pp + (1 - ca) * rep.get(a, 0.0))
                con = ref_a * nn
                out[:, j, k] = tot / con - 1
                arr_t[:, j, k] = tot
                arr_c[:, j, k] = con
                sum_t[:, j] += tot
                sum_c[:, j] += con
        if reais:
            return arr_t, arr_c
        if acumulado:
            return sum_t / sum_c - 1
        return out

    # verificação: caso central reproduz o arquivo publicado
    um_n = np.ones((1, len(UFS), len(ANOS)))
    um_p = np.ones((1, len(UFS)))
    base_estado = calcula("estado", um_n, um_p)[0]
    maxdif = 0.0
    for j, u in enumerate(UFS):
        for k, a in enumerate(ANOS):
            pub = central["por_uf_estado"][u]["variacao_por_ano"][str(a)]
            maxdif = max(maxdif, abs(pub - base_estado[j, k]))
    print(f"verificação do caso central (estado): dif. máxima {maxdif:.2e}")

    rng = np.random.default_rng(SEED)
    horizontes = np.array([a - 2025 for a in ANOS], dtype=float)
    pares = None
    inc = HERE / "sensibilidade-incerteza-parametros.json"
    if USAR_BOOT and inc.exists():
        pares = np.array(json.loads(inc.read_text(encoding="utf-8"))["pares_s1_beta"])

    def sd_sim(n, hs):
        """Desvio da deriva por rodada e horizonte, shape (n, len(hs)): kappa * s1_i * h^beta_i."""
        if pares is None:
            return np.tile(KAPPA * s1 * hs ** beta, (n, 1))
        i = rng.integers(0, len(pares), n)
        return KAPPA * pares[i, 0][:, None] * hs[None, :] ** pares[i, 1][:, None]

    def sorteia(fontes, sigma_phi):
        z = rng.standard_normal((N_SIM, len(UFS)))
        eps = z[:, :, None] * sd_sim(N_SIM, horizontes)[:, None, :] if "A" in fontes else np.zeros((N_SIM, len(UFS), len(ANOS)))
        # participação UF (agregado estado+município): choque multiplicativo e renormalização
        m = np.exp(eps)
        den = (n_uf[None, :, None] * m).sum(1, keepdims=True)
        sn = m / den * n_uf.sum()
        if "B" in fontes:
            eta = rng.standard_normal((N_SIM, len(UFS))) * sigma_phi
            mp = np.exp(eta)
            sp = mp / (pl_uf[None, :] * mp).sum(1, keepdims=True) * pl_uf.sum()
        else:
            sp = np.ones((N_SIM, len(UFS)))
        return sn, sp

    resultados = {}
    for esfera in ["estado", "total"]:
        cen = calcula(esfera, um_n, um_p)[0]
        comb = {}
        for rot, fontes, sg in [("A+B", "AB", SIGMA_PHI), ("A", "A", SIGMA_PHI), ("B", "B", SIGMA_PHI),
                                ("A+B (σφ alto)", "AB", SIGMA_PHI_ALTO)]:
            sn, sp = sorteia(fontes, sg)
            comb[rot] = calcula(esfera, sn, sp)
        full = comb["A+B"]
        sn_c, sp_c = sorteia("AB", SIGMA_PHI)
        acum = calcula(esfera, sn_c, sp_c, acumulado=True)
        acum_cen = calcula(esfera, um_n, um_p, acumulado=True)[0]
        acum_res = {u: {"central": round(float(acum_cen[j]), 5), "p10": round(float(np.percentile(acum[:, j], 10)), 5),
                        "p90": round(float(np.percentile(acum[:, j], 90)), 5),
                        "prob_ganho": round(float((acum[:, j] > 0).mean()), 4)} for j, u in enumerate(UFS)}
        por_uf = {}
        for j, u in enumerate(UFS):
            d = {}
            for k, a in enumerate(ANOS):
                x = full[:, j, k]
                d[str(a)] = {"central": round(float(cen[j, k]), 5),
                             "p05": round(float(np.percentile(x, 5)), 5), "p10": round(float(np.percentile(x, 10)), 5),
                             "p50": round(float(np.percentile(x, 50)), 5), "p90": round(float(np.percentile(x, 90)), 5),
                             "p95": round(float(np.percentile(x, 95)), 5),
                             "prob_ganho": round(float((x > 0).mean()), 4),
                             "sd": round(float(x.std()), 5)}
            por_uf[u] = d
        # decomposição de variância em 2033
        k = len(ANOS) - 1
        var = {}
        for j, u in enumerate(UFS):
            vt = comb["A+B"][:, j, k].var()
            var[u] = {"parte_A": round(float(comb["A"][:, j, k].var() / vt), 3),
                      "parte_B": round(float(comb["B"][:, j, k].var() / vt), 3),
                      "sd_A+B": round(float(np.sqrt(vt)), 4),
                      "sd_A+B_phi_alto": round(float(comb["A+B (σφ alto)"][:, j, k].std()), 4)}
        # quantas UFs têm sinal robusto (p10>0 ou p90<0) em 2033
        robusto = {"ganho": [u for u in UFS if por_uf[u]["2033"]["p10"] > 0],
                   "perda": [u for u in UFS if por_uf[u]["2033"]["p90"] < 0]}
        # métricas de risco em R$ (valores de 2025): receita em risco (perda frente ao contrafactual)
        tot_r, con_r = calcula(esfera, sn_c, sp_c, reais=True)
        risco = {}
        for j, u in enumerate(UFS):
            r = {}
            for rot, perda, ref0 in [("2033", (con_r[:, j, -1] - tot_r[:, j, -1]), con_r[:, j, -1].mean()),
                                     ("acumulado", (con_r[:, j, :] - tot_r[:, j, :]).sum(1), con_r[:, j, :].sum(1).mean())]:
                q95 = float(np.percentile(perda, 95))
                cauda = perda[perda >= q95]
                r[rot] = {"RaR95_bi": round(q95 / 1e9, 3), "ES95_bi": round(float(cauda.mean()) / 1e9, 3),
                          "RaR95_pct_contra": round(q95 / ref0, 4),
                          "P_perda_maior_5pct": round(float((perda > 0.05 * ref0).mean()), 4),
                          "P_perda_maior_10pct": round(float((perda > 0.10 * ref0).mean()), 4)}
            risco[u] = r
        resultados[esfera] = {"risco_em_reais": risco, "acumulado_2029_2033": acum_res, "por_uf": por_uf, "variancia_2033": var, "sinal_robusto_2033_p10_p90": robusto}

    # ── Longo prazo (2040, 2050, 2060, 2077): o contrafactual deixa de ser identificável (deriva
    # extrapolada), então reporta-se A+B e também B isolado (contrafactual congelado em 2025)
    lp = {r["ano"]: r for r in brc.load("ibs-projecao-longo-prazo.json")["projecao"]}
    seguro_lp = brc.load("seguro-receita-repasses-longo-prazo.json")["anos"]
    longo = {}
    for esfera in ["estado", "total"]:
        longo[esfera] = {}
        for a in [2040, 2050, 2060, 2077]:
            r = lp[a]
            ca = r.get("ca", 0.0)
            ref_a = r["icms_iss_residual"] + r["ibs_bruto"]
            h = a - 2025
            z = rng.standard_normal((N_SIM, len(UFS)))
            eta = rng.standard_normal((N_SIM, len(UFS))) * SIGMA_PHI
            mp = np.exp(eta)
            sp = mp / (pl_uf[None, :] * mp).sum(1, keepdims=True) * pl_uf.sum()
            mA = np.exp(z * sd_sim(N_SIM, np.array([float(h)]))[:, :1])
            sn = mA / (n_uf[None, :] * mA).sum(1, keepdims=True) * n_uf.sum()
            res_a = {}
            for j, u in enumerate(UFS):
                n0, c0, pl0, _ = parte(u, esfera)
                rp = seguro_lp.get(str(a), {}).get("repasse_por_uf", {}).get(u, {})
                rep = rp.get("estado", 0) + (rp.get("municipio", 0) if esfera == "total" and params[u]["municipio"] else 0)
                def dp(nn, pp):
                    tot = (r["icms_iss_residual"] * nn + (1 - ca) * r["ibs_historico"] * c0
                           + r["ibs_destino_liquido"] * pp + (1 - ca) * rep)
                    return tot / (ref_a * nn) - 1
                cen = float(dp(n0, pl0))
                x_b = dp(n0 * np.ones(N_SIM), pl0 * sp[:, j])
                x_ab = dp(n0 * sn[:, j], pl0 * sp[:, j])
                res_a[u] = {"central": round(cen, 5),
                            "B_p10": round(float(np.percentile(x_b, 10)), 5), "B_p90": round(float(np.percentile(x_b, 90)), 5),
                            "B_prob_ganho": round(float((x_b > 0).mean()), 4),
                            "AB_p10": round(float(np.percentile(x_ab, 10)), 5), "AB_p90": round(float(np.percentile(x_ab, 90)), 5)}
            longo[esfera][str(a)] = res_a

    saida = {"_meta": {
        "descricao": "Monte Carlo da variação (receita pós-reforma / contrafactual - 1). Não altera resultados publicados.",
        "n_sim": N_SIM, "seed": SEED, "sigma_phi_central": SIGMA_PHI, "sigma_phi_alto": SIGMA_PHI_ALTO,
        "deriva_contrafactual": {"sd_h": "kappa * c * sqrt(h) com c sorteado do bootstrap (ou s1 * h^beta se USAR_BOOT=False)", "s1": s1, "beta": beta, "kappa": KAPPA,
                                 "incerteza_parametros_bootstrap": pares is not None, "fonte": "sensibilidade-calibra-deriva.json; sensibilidade-incerteza-parametros.json"},
        "verificacao_caso_central_dif_max": maxdif,
        "fora_do_mc": "nível do bolo (cancela na razão), Seguro-Receita (fixo no central), base do ICMS na transição "
                      "(cenário jurídico), compras governamentais (faixa de f), base ampla/conformidade (afetam a alíquota)"},
        "backtest": bt, "resultados": resultados, "longo_prazo": longo}
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps(bt, ensure_ascii=False, indent=1))
    for esfera in ["estado", "total"]:
        print(f"\n== {esfera} (2033): central | p10 | p90 | P(ganho) | sd | %var A")
        for u in UFS:
            d = resultados[esfera]["por_uf"][u]["2033"]
            v = resultados[esfera]["variancia_2033"][u]
            print(f"{u} {d['central']*100:6.1f}% | {d['p10']*100:6.1f}% | {d['p90']*100:6.1f}% | {d['prob_ganho']:.2f} | {d['sd']*100:5.1f} | A={v['parte_A']:.2f} B={v['parte_B']:.2f}")
        print("sinal robusto:", resultados[esfera]["sinal_robusto_2033_p10_p90"])
    for a in ["2040", "2050", "2077"]:
        print(f"\n== longo prazo {a} (estado): central | B p10..p90 | P(ganho|B)")
        for u in UFS:
            d = longo["estado"][a][u]
            print(f"{u} {d['central']*100:7.1f}% | {d['B_p10']*100:7.1f}..{d['B_p90']*100:7.1f} | {d['B_prob_ganho']:.2f}")


if __name__ == "__main__":
    main()
