#!/usr/bin/env python3
"""
TESTE (não altera nenhum resultado publicado): a participação de cada UF no consumo muda se a POF 2017-18 for
atualizada pela renda do Censo 2022? O φ atual usa despesa familiar média da POF 2017-18 x domicílios do Censo 2022
(atualiza o peso demográfico, mas não a renda). A nota técnica do COMSEFAZ usa a renda municipal do Censo 2022 por
faixa, aplicada a propensões a consumir da POF. Aqui, uma versão simples e verificável da mesma ideia:
  consumo_UF(2022) ∝ consumo_POF(UF, 2018) x (massa de renda Censo 2022 / renda POF 2018)^ε
com ε = 0,5; 0,8 (elasticidade-renda estimada no repositório) e 1,0.
Massa de renda do Censo 2022 = rendimento médio domiciliar per capita (SIDRA 10295, var. 13431) x moradores (var. 13604).
Comparações: φ atual (pof_censo_bruto_pct), Gobetti 2023 (Tabela 1), nota COMSEFAZ (Tabelas 2 e 3; base IBS 2025).
Saída: data/teste-atualizacao-renda-censo2022.json
"""
import json
import re
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
COD = {"RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17, "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27,
       "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35, "PR": 41, "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53}
INV = {str(v): k for k, v in COD.items()}


def sh(x):
    s = sum(x.values())
    return {k: 100 * v / s for k, v in x.items()}


def tabela(linhas, ini, fim):
    out = {}
    for ln in linhas[ini:fim]:
        m = re.match(r"\| ([A-Z]{2}) \| ([\d,]+)% \| ([\d,]+)% \| ([\d,]+)% \| ([\d,]+)% \|", ln)
        if m:
            out[m.group(1)] = [float(x.replace(",", ".")) for x in m.groups()[1:]]
    return out


def main():
    d = json.loads(urllib.request.urlopen("https://apisidra.ibge.gov.br/values/t/10295/n3/all/p/last/v/all?formato=json", timeout=60).read())[1:]
    pop, inc = {}, {}
    for r in d:
        if r["D3C"] == "13604":
            pop[INV[r["D1C"]]] = float(r["V"])
        if r["D3C"] == "13431":
            inc[INV[r["D1C"]]] = float(r["V"])
    ufs = sorted(pop)
    L = (HERE / "referencias-externas" / "NT_COMSEFAZ_RefTributaria_v3.md").read_text(encoding="utf-8").split("\n")
    i2 = next(i for i, x in enumerate(L) if x.startswith("Tabela 2 —"))
    i3 = next(i for i, x in enumerate(L) if x.startswith("Tabela 3 —"))
    t2, t3 = tabela(L, i2, i2 + 40), tabela(L, i3, i3 + 40)
    phi = json.loads((HERE / "phi-dest-pof-censo.json").read_text(encoding="utf-8"))["por_uf"]
    massa = sh({u: pop[u] * inc[u] for u in ufs})
    renda18 = {u: t2[u][0] for u in ufs}
    cons18 = {u: t2[u][1] for u in ufs}
    ref = sh({u: t3[u][3] for u in ufs})
    nosso = {u: phi[u]["pof_censo_bruto_pct"] for u in ufs}
    gob = {u: phi[u]["gobetti_tabela1_2023_pct"] for u in ufs}

    def rmse(a):
        return float(np.sqrt(np.mean([(a[u] - ref[u]) ** 2 for u in ufs])))

    res = {"referencia_COMSEFAZ_base_IBS_2025": {"PR": round(ref["PR"], 3)},
           "phi_atual_POFxCenso": {"PR": round(nosso["PR"], 3), "rmse_pp": round(rmse(nosso), 3)},
           "gobetti_2023_T1": {"PR": round(gob["PR"], 3), "rmse_pp": round(rmse(gob), 3)},
           "consumo_POF_2018_puro": {"PR": cons18["PR"], "rmse_pp": round(rmse(cons18), 3)},
           "massa_renda_censo_2022": {"PR": round(massa["PR"], 3), "rmse_pp": round(rmse(massa), 3)}}
    for e in (0.5, 0.8, 1.0):
        upd = sh({u: cons18[u] * (massa[u] / renda18[u]) ** e for u in ufs})
        res[f"POF2018_atualizada_renda_eps{e}"] = {"PR": round(upd["PR"], 3), "rmse_pp": round(rmse(upd), 3),
                                                   "delta_vs_POF2018_pp": {u: round(upd[u] - cons18[u], 2) for u in ("PR", "SP", "RJ", "SC", "RS", "MG", "DF")}}
    for k, v in res.items():
        print(k, v if k.startswith("POF2018") is False else {a: b for a, b in v.items() if a != "delta_vs_POF2018_pp"})
    (HERE / "teste-atualizacao-renda-censo2022.json").write_text(json.dumps({"_meta": "Participações em % do total nacional; rmse_pp contra a base IBS 2025 da nota COMSEFAZ (27 UFs)", "resultados": res}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
