#!/usr/bin/env python3
"""
Sensibilidade do φ de destino robusto à subestimação das rendas altas no Censo (a nota técnica do COMSEFAZ corrige com o IRPF,
sem documentar a extração). Aqui a correção usa dados públicos: Grandes Números do IRPF, ano-calendário 2024 (Tabela 8).
Fator por UF = participação da UF na renda total declarada nas faixas de topo (160 salários mínimos anuais ou mais) dividida pela
participação da UF na massa de renda das classes acima de 10 salários mínimos per capita do Censo 2022, normalizada para que o total
nacional de pessoas no topo não mude (só a redistribuição entre UFs conta). O fator reponderaria as classes de topo da rota C
(pessoas movidas da classe de 5 a 10 salários mínimos). O composto com a rota C corrigida é comparado com o composto sem correção.
NÃO altera nenhum resultado publicado. Uso: python3 data/estima-phi-destino-irpf.py <pasta_pof> [--cache pasta]
Entradas: data/phi-dest-robusto.json, data/renda-uf-censo-pnadc.json, data/irpf-uf-faixas-ac2024.json. Saída: data/phi-dest-robusto-irpf.json
"""
import importlib.util
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("ph", HERE / "estima-phi-destino-robusto.py")
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)
TOPO = ["De 160 a 240", "De 240 a 320", "Mais de 320"]
MEDIA_SM = np.array([12.5, 17.5, 30.0])      # renda média das classes 10-15, 15-20, >20 SM per capita


def main():
    base = Path(sys.argv[1])
    cache = Path(sys.argv[sys.argv.index("--cache") + 1]) if "--cache" in sys.argv else base
    tb = ph.carrega_tb()
    CATS, PESOS, UFS = tb.CATS, tb.PESOS, tb.UFS
    uc = pickle.loads((cache / "pof_uc.pkl").read_bytes())
    cat = pickle.loads((cache / "pof_uc_cat.pkl").read_bytes())
    m = uc.merge(cat.drop(columns=["UF", "peso", "pessoas"]), on=ph.KEY)
    m["uf"] = m["UF"].astype(int).map(UFS)
    m["w"] = m["peso"] * m["pessoas"]
    m["rpc"] = m["renda"] / m["pessoas"]
    m["reg"] = m["uf"].map(ph.REG)
    bins = [-1, 1e-9] + [x * ph.SM_POF for x in (0.25, 0.5, 1, 2, 3, 5, 10, 15, 20)] + [1e12]
    m["cl"] = pd.cut(m["rpc"], bins=bins, labels=ph.CLASSES, right=True)
    m["base"] = sum(m[c] * PESOS["S1"][c] for c in CATS)
    ufs = sorted(UFS.values())
    rd = json.loads((HERE / "renda-uf-censo-pnadc.json").read_text(encoding="utf-8"))
    cl = {u: np.array([rd["classes_sm"][u][c] for c in ph.COD_CLASSE], float) for u in ufs}
    ir = json.loads((HERE / "irpf-uf-faixas-ac2024.json").read_text(encoding="utf-8"))["por_uf"]
    topo_ir = pd.Series({u: sum(ir[u][f]["renda_total"] for f in TOPO) for u in ufs})
    sh_ir = topo_ir / topo_ir.sum()
    massa = pd.Series({u: float((cl[u][7:10] * MEDIA_SM).sum()) for u in ufs})
    sh_cen = massa / massa.sum()
    gap = sh_ir / sh_cen
    npes = pd.Series({u: cl[u][7:10].sum() for u in ufs})
    f = gap / ((gap * npes).sum() / npes.sum())
    kn = m.groupby("cl", observed=False).apply(lambda x: np.average(x["base"] / x["pessoas"], weights=x["w"])).reindex(ph.CLASSES)

    def rota_c(fator):
        v = {}
        for u in ufs:
            c = cl[u].copy()
            mov = c[7:10] * (fator(u) - 1.0)
            c[7:10] += mov
            c[6] = max(c[6] - mov.sum(), 0)
            kr = m[m["reg"] == ph.REG[u]].groupby("cl", observed=False).apply(
                lambda x: np.average(x["base"] / x["pessoas"], weights=x["w"]) if x["w"].sum() > 0 else np.nan).reindex(ph.CLASSES).fillna(kn)
            v[u] = float(c @ (ph.LAMBDA * kr + (1 - ph.LAMBDA) * kn).values)
        return ph.sh(v)

    c0, cd = rota_c(lambda u: 1.0), rota_c(lambda u: float(f[u]))
    rb = json.loads((HERE / "phi-dest-robusto.json").read_text(encoding="utf-8"))["por_uf"]
    comp0 = ph.sh({u: (rb[u]["rota_A_pct"] + rb[u]["rota_B_pct"] + c0[u]) / 3 for u in ufs})
    compd = ph.sh({u: (rb[u]["rota_A_pct"] + rb[u]["rota_B_pct"] + cd[u]) / 3 for u in ufs})
    t2, t3 = ph.parse_comsefaz()
    phi = json.loads((HERE / "phi-dest-pof-censo.json").read_text(encoding="utf-8"))["por_uf"]
    ext = {"comsefaz_base_IBS_2025": ph.sh({u: t3[u][3] for u in ufs}), "gobetti_2023": {u: phi[u]["gobetti_tabela1_2023_pct"] for u in ufs},
           "comsefaz_base_TRU_2018": ph.sh({u: t2[u][3] for u in ufs})}
    rmse = lambda a, b: round(float(np.sqrt(np.mean([(a[u] - b[u]) ** 2 for u in ufs]))), 3)
    saida = {"_meta": "Sensibilidade à correção das rendas altas pelo IRPF (AC 2024); não altera o publicado",
             "fator_topo_por_uf": {u: round(float(f[u]), 3) for u in ufs},
             "rota_C": {"sem_IRPF": c0, "com_IRPF": cd}, "composto": {"sem_IRPF": comp0, "com_IRPF": compd},
             "rmse_pp_vs_externos": {n: {"composto_sem_IRPF": rmse(comp0, e), "composto_com_IRPF": rmse(compd, e)} for n, e in ext.items()},
             "participacao_na_renda_total_declarada_IRPF_pct": {u: round(100 * float(v), 3) for u, v in (pd.Series({u: sum(x["renda_total"] for x in ir[u].values()) for u in ufs}) / sum(sum(x["renda_total"] for x in ir[u].values()) for u in ufs)).items()}}
    (HERE / "phi-dest-robusto-irpf.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    for u in ("PR", "ES", "SP"):
        print(u, "fator %.2f" % f[u], "composto sem %.3f com %.3f" % (comp0[u], compd[u]))
    print(saida["rmse_pp_vs_externos"])


if __name__ == "__main__":
    main()
