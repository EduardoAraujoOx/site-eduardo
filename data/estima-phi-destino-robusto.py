#!/usr/bin/env python3
"""
Coeficiente de destino (φ_dest) robusto: participação de cada UF na BASE TRIBUTÁVEL do IBS, estimada por três rotas
independentes que usam fontes públicas e são reportadas lado a lado, mais um estimador composto e uma medida de incerteza.
NÃO altera nenhum resultado publicado: grava data/phi-dest-robusto.json, que o painel só usa se for adotado.

Por que mudar o φ atual (POF 2017-18 por domicílio x domicílios do Censo 2022, consumo bruto):
  (1) o consumo bruto inclui o aluguel imputado, a alimentação de alíquota zero e o transporte coletivo, que não compõem a
      base do IBS; a base tributável usa os pesos da LC 214/2025 (teste-base-tributavel-pof.py, cenário S1);
  (2) a intensidade de consumo é a de 2018: não acompanha a renda relativa de cada UF até 2022.

Rotas (todas em participação % da base tributável, soma 100):
  A  POF 2017-18, base tributável por pessoa x moradores do Censo 2022 (sem atualização de renda);
  B  A atualizada pela renda relativa da PNAD Contínua, 2018 -> 2022, com a elasticidade-renda estimada na própria POF
     (0,75; pof-elasticidade-consumo.json). Mesma definição de renda nos dois anos, por isso não mistura fontes;
  C  distribuição de renda por classe de salário mínimo do Censo 2022 (moradores por UF e classe) x base tributável por
     pessoa em cada classe na POF (média nacional, com encolhimento de 50% para a média da grande região).
Composto = média simples das três rotas. Incerteza por UF = dispersão entre rotas e entre variantes (elasticidade 0,5 a 1,0;
alimentação toda a zero ou toda a 0,4; encolhimento 0 a 1) somada ao erro de validação estrutural (abaixo).

Validação (leave-one-UF-out dentro da POF 2017-18): prediz a participação de cada UF no consumo observado a partir de
(i) população, (ii) massa de renda, (iii) classes de renda com κ nacional, (iv) classes com κ regional encolhido. Mede o erro
típico (RMSE em pp e erro relativo médio), que alimenta a incerteza do φ no modelo de projeção.
Comparadores externos (não usados como alvo): Gobetti e Monteiro (2023), base IBS 2025 da nota técnica do COMSEFAZ.

Uso: python3 data/estima-phi-destino-robusto.py <pasta_pof> [--cache pasta]
  (o cache precisa de pof_uc.pkl e pof_uc_cat.pkl, gerados por estima-elasticidade-pof.py e teste-base-tributavel-pof.py;
   a renda por UF vem de data/renda-uf-censo-pnadc.json, de collect-renda-uf-censo-pnadc.py)
Saída: data/phi-dest-robusto.json
"""
import importlib.util
import json
import pickle
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
OUT = HERE / "phi-dest-robusto.json"
SM_POF = 954.0          # salário mínimo de jan/2018 (referência dos valores deflacionados da POF)
EPS = 0.75              # elasticidade-renda do consumo (pof-elasticidade-consumo.json, brasil.cons_total)
LAMBDA = 0.5            # encolhimento regional dos κ das classes
KEY = ["COD_UPA", "NUM_DOM", "NUM_UC"]
CLASSES = ["sem", "<=1/4", "1/4-1/2", "1/2-1", "1-2", "2-3", "3-5", "5-10", "10-15", "15-20", ">20"]
COD_CLASSE = ["9692", "9681", "9682", "9683", "9684", "9685", "9686", "9687", "9688", "9689", "9690"]
REG = {"RO": "N", "AC": "N", "AM": "N", "RR": "N", "PA": "N", "AP": "N", "TO": "N", "MA": "NE", "PI": "NE", "CE": "NE", "RN": "NE",
       "PB": "NE", "PE": "NE", "AL": "NE", "SE": "NE", "BA": "NE", "MG": "SE", "ES": "SE", "RJ": "SE", "SP": "SE", "PR": "S",
       "SC": "S", "RS": "S", "MS": "CO", "MT": "CO", "GO": "CO", "DF": "CO"}


def carrega_tb():
    spec = importlib.util.spec_from_file_location("tb", HERE / "teste-base-tributavel-pof.py")
    tb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tb)
    return tb


def sh(d):
    s = float(sum(d.values()))
    return {k: 100.0 * v / s for k, v in d.items()}


def parse_comsefaz():
    L = (HERE / "referencias-externas" / "NT_COMSEFAZ_RefTributaria_v3.md").read_text(encoding="utf-8").split("\n")
    i2 = next(i for i, x in enumerate(L) if x.startswith("Tabela 2 —"))
    i3 = next(i for i, x in enumerate(L) if x.startswith("Tabela 3 —"))
    rx = r"\| ([A-Z]{2}) \| ([\d,]+)% \| ([\d,]+)% \| ([\d,]+)% \| ([\d,]+)% \|"
    t2, t3 = {}, {}
    for ln in L[i2:i2 + 40]:
        m = re.match(rx, ln)
        if m:
            t2[m.group(1)] = [float(x.replace(",", ".")) for x in m.groups()[1:]]
    for ln in L[i3:i3 + 40]:
        m = re.match(rx, ln)
        if m:
            t3[m.group(1)] = [float(x.replace(",", ".")) for x in m.groups()[1:]]
    return t2, t3


def main():
    base = Path(sys.argv[1])
    cache = Path(sys.argv[sys.argv.index("--cache") + 1]) if "--cache" in sys.argv else base
    tb = carrega_tb()
    CATS, PESOS, UFS = tb.CATS, tb.PESOS, tb.UFS
    uc = pickle.loads((cache / "pof_uc.pkl").read_bytes())
    cat = pickle.loads((cache / "pof_uc_cat.pkl").read_bytes())
    m = uc.merge(cat.drop(columns=["UF", "peso", "pessoas"]), on=KEY)
    m["uf"] = m["UF"].astype(int).map(UFS)
    m["w"] = m["peso"] * m["pessoas"]
    m["rpc"] = m["renda"] / m["pessoas"]
    m["reg"] = m["uf"].map(REG)
    bins = [-1, 1e-9] + [x * SM_POF for x in (0.25, 0.5, 1, 2, 3, 5, 10, 15, 20)] + [1e12]
    m["cl"] = pd.cut(m["rpc"], bins=bins, labels=CLASSES, right=True)
    m["cons"] = m[CATS].sum(axis=1)
    for nome in ("S1", "S1a", "S1b"):
        m["base_" + nome] = sum(m[c] * PESOS[nome][c] for c in CATS)
    ufs = sorted(UFS.values())

    rd = json.loads((HERE / "renda-uf-censo-pnadc.json").read_text(encoding="utf-8"))
    pop22 = {u: rd["censo_2022"][u]["moradores"] for u in ufs}
    classes22 = {u: [rd["classes_sm"][u][c] for c in COD_CLASSE] for u in ufs}
    pn = rd["pnadc_renda_media_pc"]
    rel = {a: {u: pn[a][u] / pn[a]["BR"] for u in ufs} for a in pn}

    def por_pessoa(col):
        return m.groupby("uf").apply(lambda x: float((x[col] * x["peso"]).sum() / x["w"].sum()))

    def kappa(df, col, vazio=None):
        g = df.groupby("cl", observed=False).apply(lambda x: float(np.average(x[col] / x["pessoas"], weights=x["w"])) if x["w"].sum() > 0 else np.nan)
        g = g.reindex(CLASSES)
        return g.fillna(vazio) if vazio is not None else g

    def rota_A(col):
        pc = por_pessoa(col)
        return sh({u: pop22[u] * pc[u] for u in ufs})

    def rota_B(col, eps=EPS, a0="2018", a1="2022"):
        pc = por_pessoa(col)
        return sh({u: pop22[u] * pc[u] * (rel[a1][u] / rel[a0][u]) ** eps for u in ufs})

    def rota_C(col, lam=LAMBDA):
        kn = kappa(m, col)
        v = {}
        for u in ufs:
            kr = kappa(m[m["reg"] == REG[u]], col, vazio=kn)
            k = lam * kr + (1 - lam) * kn
            v[u] = float(np.dot(classes22[u], k.values))
        return sh(v)

    rotas = {"A": rota_A("base_S1"), "B": rota_B("base_S1"), "C": rota_C("base_S1")}
    comp = sh({u: np.mean([rotas[r][u] for r in rotas]) for u in ufs})

    variantes = {}
    for nome in ("S1", "S1a", "S1b"):
        col = "base_" + nome
        variantes[f"A_{nome}"] = rota_A(col)
        for e in (0.5, 0.75, 1.0):
            variantes[f"B_{nome}_eps{e}"] = rota_B(col, eps=e)
        for lam in (0.0, 0.5, 1.0):
            variantes[f"C_{nome}_lam{lam}"] = rota_C(col, lam=lam)
    # consumo bruto, para comparação com o φ atual
    brutas = {"A_bruto": rota_A("cons"), "B_bruto": rota_B("cons"), "C_bruto": rota_C("cons")}

    # validação leave-one-UF-out dentro da POF 2017-18
    tgt = m.groupby("uf").apply(lambda x: float((x["cons"] * x["peso"]).sum()))
    tgt = sh(tgt.to_dict())
    npc = m.pivot_table(index="uf", columns="cl", values="w", aggfunc="sum", fill_value=0, observed=False)[CLASSES]
    pop = sh(npc.sum(axis=1).to_dict())
    massa = sh(m.groupby("uf").apply(lambda x: float((x["renda"] * x["peso"]).sum())).to_dict())
    loo = {"populacao": pop, "massa_renda": massa}
    for lam, nome in ((0.0, "classes_kappa_nacional"), (0.5, "classes_kappa_regional")):
        pred = {}
        for u in ufs:
            tr = m[m["uf"] != u]
            kn = kappa(tr, "cons")
            if lam > 0:
                kr = kappa(tr[tr["reg"] == REG[u]], "cons", vazio=kn)
                k = lam * kr + (1 - lam) * kn
            else:
                k = kn
            pred[u] = float((npc.loc[u] * k.fillna(0)).sum())
        loo[nome] = sh(pred)
    valid = {}
    for n, p in loo.items():
        e = np.array([p[u] - tgt[u] for u in ufs])
        r = np.array([(p[u] - tgt[u]) / tgt[u] for u in ufs])
        valid[n] = {"rmse_pp": round(float(np.sqrt((e ** 2).mean())), 3), "erro_relativo_medio_pct": round(float(np.abs(r).mean() * 100), 2)}
    erro_estrutural = valid["classes_kappa_regional"]["erro_relativo_medio_pct"] / 100.0

    # comparadores externos
    phi = json.loads((HERE / "phi-dest-pof-censo.json").read_text(encoding="utf-8"))["por_uf"]
    t2, t3 = parse_comsefaz()
    ext = {"phi_atual_POFxCenso_bruto": {u: phi[u]["pof_censo_bruto_pct"] for u in ufs},
           "gobetti_2023": {u: phi[u]["gobetti_tabela1_2023_pct"] for u in ufs},
           "comsefaz_base_IBS_2025": sh({u: t3[u][3] for u in ufs}),
           "comsefaz_base_TRU_2018": sh({u: t2[u][3] for u in ufs})}

    def rmse(a, b):
        return round(float(np.sqrt(np.mean([(a[u] - b[u]) ** 2 for u in ufs]))), 3)

    comparacao = {n: {"rmse_pp_vs_composto": rmse(comp, v), "PR": round(v["PR"], 3)} for n, v in ext.items()}
    comparacao["composto"] = {"PR": round(comp["PR"], 3)}
    for r, v in rotas.items():
        comparacao["rota_" + r] = {"PR": round(v["PR"], 3), "rmse_pp_vs_comsefaz_2025": rmse(v, ext["comsefaz_base_IBS_2025"]),
                                   "rmse_pp_vs_gobetti": rmse(v, ext["gobetti_2023"])}
    comparacao["composto"]["rmse_pp_vs_comsefaz_2025"] = rmse(comp, ext["comsefaz_base_IBS_2025"])
    comparacao["composto"]["rmse_pp_vs_gobetti"] = rmse(comp, ext["gobetti_2023"])
    comparacao["phi_atual_POFxCenso_bruto"]["rmse_pp_vs_comsefaz_2025"] = rmse(ext["phi_atual_POFxCenso_bruto"], ext["comsefaz_base_IBS_2025"])
    comparacao["phi_atual_POFxCenso_bruto"]["rmse_pp_vs_gobetti"] = rmse(ext["phi_atual_POFxCenso_bruto"], ext["gobetti_2023"])

    por_uf = {}
    for u in ufs:
        vs = [v[u] for v in variantes.values()]
        disp = float(np.std([rotas[r][u] for r in rotas], ddof=0)) / comp[u]
        faixa = (min(vs), max(vs))
        por_uf[u] = {"phi_robusto_pct": comp[u], "rota_A_pct": rotas["A"][u], "rota_B_pct": rotas["B"][u], "rota_C_pct": rotas["C"][u],
                     "faixa_variantes_pct": list(faixa),
                     "dispersao_rotas_rel": disp,
                     "incerteza_rel": float(np.sqrt(disp ** 2 + erro_estrutural ** 2)),
                     "phi_atual_bruto_pct": phi[u]["pof_censo_bruto_pct"]}
    saida = {"_meta": {"descricao": "φ de destino robusto (base tributável, três rotas, composto); NÃO alimenta resultado publicado",
                       "rotas": {"A": "POF 2017-18 base tributável por pessoa x moradores Censo 2022",
                                 "B": "A x (renda relativa PNAD Contínua 2022/2018)^eps, eps = %.2f" % EPS,
                                 "C": "classes de renda do Censo 2022 x base tributável por pessoa/classe da POF (encolhimento regional %.1f)" % LAMBDA},
                       "pesos_base": "LC 214/2025, cenário S1 de teste-base-tributavel-pof.py (aluguel imputado e transporte coletivo fora; alimentação item a item)",
                       "erro_estrutural_rel": erro_estrutural},
             "validacao_leave_one_uf_out_POF": valid,
             "comparacao": comparacao,
             "por_uf": por_uf,
             "consumo_bruto_rotas_pct": {k: {u: v[u] for u in ufs} for k, v in brutas.items()}}
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print("validação (leave-one-UF-out, POF):", json.dumps(valid, ensure_ascii=False))
    for n, v in comparacao.items():
        print(f"{n:28s}", v)
    print("PR por rota:", {r: round(v['PR'], 3) for r, v in rotas.items()}, "composto %.3f" % comp["PR"], "faixa variantes", [round(x, 2) for x in por_uf['PR']['faixa_variantes_pct']], "incerteza_rel %.3f" % por_uf["PR"]["incerteza_rel"])


if __name__ == "__main__":
    main()
