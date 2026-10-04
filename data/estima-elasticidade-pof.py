#!/usr/bin/env python3
"""
Estima a elasticidade-renda do consumo com os MICRODADOS da POF 2017-18.

Objetivo: substituir a hipótese implícita de elasticidade 1 (consumo do município
proporcional à renda total) por uma curva de consumo estimada. O resultado alimenta
o rateio da receita própria de IBS entre municípios (ver Estudo 17 e plano em
data/legislacao/reforma-tributaria-referencias.md).

Insumos (IBGE, https://ftp.ibge.gov.br/Orcamentos_Familiares/
Pesquisa_de_Orcamentos_Familiares_2017_2018/Microdados/):
  Dados_20230713.zip, Documentacao_20230713.zip, Tradutores_20230713.zip
  (descompactar numa pasta e passar como argumento).

Definições:
  - Unidade de consumo (UC) = (COD_UPA, NUM_DOM, NUM_UC); pessoas = nº de moradores da UC.
  - Renda per capita = RENDA_TOTAL / pessoas (RENDA_TOTAL mensal, já deflacionada).
  - Consumo mensal da UC = soma de V8000_DEFLA x FATOR_ANUALIZACAO / 12 nas despesas
    classificadas como "Despesas de Consumo" (Nivel_2 = 11 do Tradutor_Despesa_Geral).
    Variante "monetário" exclui o aluguel não monetário (aluguel imputado).
  - Estimadores: (a) MQO log-log domiciliar ponderado por pessoas; (b) log-log sobre
    médias ponderadas de 20 quantis de renda per capita (reduz o viés de atenuação
    por erro de medida na renda). Reportados para o Brasil, grandes regiões e
    urbano/rural.

Uso: python3 data/estima-elasticidade-pof.py <pasta_com_dados_doc_trad> [--cache pasta]
Saída: data/pof-elasticidade-consumo.json
"""
import glob
import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).parent / "pof-elasticidade-consumo.json"
KEY = ["COD_UPA", "NUM_DOM", "NUM_UC"]


def layout(xl, sheet):
    df = xl.parse(sheet, header=None, skiprows=5).iloc[:, :5]
    df.columns = ["pos", "tam", "dec", "cod", "desc"]
    df = df[df["pos"].notna() & df["cod"].notna()]
    pos = df["pos"].astype(int).tolist()
    tam = df["tam"].astype(int).tolist()
    return df["cod"].tolist(), [(p - 1, p - 1 + t) for p, t in zip(pos, tam)]


def le(base, xl, arq, sheet, cols):
    nomes, specs = layout(xl, sheet)
    sel = [(n, s) for n, s in zip(nomes, specs) if n in cols]
    df = pd.read_fwf(Path(base) / "dados" / arq, colspecs=[s for _, s in sel],
                     names=[n for n, _ in sel], header=None)
    return df


def main():
    base = Path(sys.argv[1])
    cache = Path(sys.argv[sys.argv.index("--cache") + 1]) if "--cache" in sys.argv else base
    pkl = cache / "pof_uc.pkl"
    if pkl.exists():
        uc = pickle.loads(pkl.read_bytes())
    else:
        xl = pd.ExcelFile(glob.glob(str(base / "doc" / "Dicion*"))[0])
        trad = pd.read_excel(glob.glob(str(base / "trad" / "Tradutor_Despesa_Geral*"))[0])
        trad = trad[trad["Nivel_2"] == 11].copy()
        trad["cod"] = trad["Codigo"].astype(int)
        # aluguel não monetário (imputado): Nivel_5 = 1102012
        imput = set(trad.loc[trad["Nivel_5"] == 1102012, "cod"])
        consumo = set(trad["cod"])

        # moradores: pessoas, renda e peso por UC
        mor = le(base, xl, "MORADOR.txt", "Morador",
                 KEY + ["UF", "ESTRATO_POF", "TIPO_SITUACAO_REG", "PESO_FINAL", "RENDA_TOTAL",
                        "V0306", "ANOS_ESTUDO"])
        g = mor.groupby(KEY).agg(pessoas=("UF", "size"), UF=("UF", "first"),
                                 estrato=("ESTRATO_POF", "first"),
                                 sit=("TIPO_SITUACAO_REG", "first"),
                                 peso=("PESO_FINAL", "first"),
                                 renda=("RENDA_TOTAL", "first")).reset_index()
        ref = mor[mor["V0306"] == 1].groupby(KEY)["ANOS_ESTUDO"].first().rename("anos_ref").reset_index()
        g = g.merge(ref, on=KEY, how="left")
        tot = {}
        mon = {}
        # Fórmula oficial do IBGE (Memoria_de_Calculo, "Tabela de Despesa Geral"):
        # valor mensal = V8000_DEFLA x FATOR_ANUALIZACAO / 12, multiplicado também por V9011
        # (nº de meses) nos itens mensais: quadros 10 e 19 (coletiva), 44, 47, 48, 49 e 50
        # (individual) e em todo o aluguel estimado.
        mensais = {"DESPESA_COLETIVA.txt": {10, 19}, "DESPESA_INDIVIDUAL.txt": {44, 47, 48, 49, 50}}
        for arq, sheet in [("DESPESA_COLETIVA.txt", "Despesa Coletiva"),
                           ("DESPESA_INDIVIDUAL.txt", "Despesa Individual"),
                           ("CADERNETA_COLETIVA.txt", "Caderneta Coletiva"),
                           ("ALUGUEL_ESTIMADO.txt", "Aluguel Estimado")]:
            cols = KEY + ["V9001", "V8000_DEFLA", "FATOR_ANUALIZACAO"]
            if arq != "CADERNETA_COLETIVA.txt":
                cols += ["V9011"]
            if arq in mensais:
                cols += ["QUADRO"]
            d = le(base, xl, arq, sheet, cols)
            d["cod"] = (d["V9001"] // 100).astype(int)
            d = d[d["cod"].isin(consumo)].copy()
            d["val"] = d["V8000_DEFLA"] * d["FATOR_ANUALIZACAO"] / 12.0
            if arq == "ALUGUEL_ESTIMADO.txt":
                d["val"] *= d["V9011"]
            elif arq in mensais:
                d.loc[d["QUADRO"].isin(mensais[arq]), "val"] *= d["V9011"]
            for k, v in d.groupby(KEY)["val"].sum().items():
                tot[k] = tot.get(k, 0.0) + v
            dm = d[~d["cod"].isin(imput)]
            for k, v in dm.groupby(KEY)["val"].sum().items():
                mon[k] = mon.get(k, 0.0) + v
            print(arq, len(d), flush=True)
        g["cons_total"] = [tot.get(tuple(r), 0.0) for r in g[KEY].itertuples(index=False)]
        g["cons_monet"] = [mon.get(tuple(r), 0.0) for r in g[KEY].itertuples(index=False)]
        uc = g
        pkl.write_bytes(pickle.dumps(uc))

    uc = uc[(uc["renda"] > 0) & (uc["cons_total"] > 0)].copy()
    uc["renda_pc"] = uc["renda"] / uc["pessoas"]
    uc["w"] = uc["peso"] * uc["pessoas"]
    uc["regiao"] = uc["UF"].astype(int) // 10
    nomes = {1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste"}

    def wols(x, y, w):
        X = np.column_stack([np.ones_like(x), x])
        W = np.sqrt(w)[:, None]
        b, *_ = np.linalg.lstsq(X * W, y * W[:, 0], rcond=None)
        res = y - X @ b
        # erro-padrão robusto (HC1) aproximado, ponderado
        XtWX_inv = np.linalg.inv((X * w[:, None]).T @ X)
        meat = (X * (w * res)[:, None]).T @ (X * (w * res)[:, None])
        cov = XtWX_inv @ meat @ XtWX_inv * len(y) / (len(y) - 2)
        return b[1], math.sqrt(cov[1, 1])

    def quantis(df, var, n=20):
        d = df.sort_values("renda_pc")
        cw = d["w"].cumsum() / d["w"].sum()
        d = d.assign(q=np.minimum((cw * n).astype(int), n - 1))
        r = d.groupby("q").apply(lambda s: pd.Series({
            "renda": np.average(s["renda_pc"], weights=s["w"]),
            "cons": np.average(s[var] / s["pessoas"], weights=s["w"]),
            "w": s["w"].sum()}), include_groups=False)
        return r

    def estima(df):
        res = {"n_uc": int(len(df)), "n_pessoas_exp": float(df["w"].sum())}
        for var in ["cons_total", "cons_monet"]:
            d = df[df[var] > 0]
            x = np.log(d["renda_pc"].values)
            y = np.log((d[var] / d["pessoas"]).values)
            b, se = wols(x, y, d["w"].values)
            q = quantis(d, var)
            bq, seq = wols(np.log(q["renda"].values), np.log(q["cons"].values), q["w"].values)
            res[var] = {"elasticidade_domiciliar": round(b, 4), "ep_domiciliar": round(se, 4),
                        "elasticidade_quantis20": round(bq, 4), "ep_quantis20": round(seq, 4)}
        return res

    saida = {"_meta": {
        "fonte": "POF 2017-18, microdados IBGE (MORADOR, DESPESA_*, CADERNETA_COLETIVA, ALUGUEL_ESTIMADO)",
        "consumo": "Despesas de Consumo (Tradutor_Despesa_Geral, Nivel_2=11), mensal, deflacionado",
        "cons_total": "inclui aluguel não monetário (imputado)",
        "cons_monet": "exclui o aluguel não monetário",
        "renda": "RENDA_TOTAL da UC por pessoa; ponderação por PESO_FINAL x pessoas",
        "estimadores": "elasticidade_domiciliar = MQO log-log (EP robusto HC1); "
                       "elasticidade_quantis20 = log-log nas médias de 20 quantis de renda per capita",
    }}
    saida["brasil"] = estima(uc)
    saida["regioes"] = {nomes[r]: estima(uc[uc["regiao"] == r]) for r in sorted(nomes)}
    saida["situacao"] = {"urbano": estima(uc[uc["sit"] == 1]), "rural": estima(uc[uc["sit"] == 2])}
    saida["regiao_x_situacao"] = {
        f"{nomes[r]}-{'urbano' if s == 1 else 'rural'}": estima(uc[(uc["regiao"] == r) & (uc["sit"] == s)])
        for r in sorted(nomes) for s in (1, 2)}
    # elasticidade ENTRE células UF x situação (médias de renda e consumo per capita):
    # captura a relação estrutural entre níveis médios de renda, mais próxima do que
    # importa na comparação entre municípios
    cel = uc.groupby(["UF", "sit"]).apply(lambda s: pd.Series({
        "renda": np.average(s["renda_pc"], weights=s["w"]),
        "cons": np.average(s["cons_monet"] / s["pessoas"], weights=s["w"]),
        "w": s["w"].sum()}), include_groups=False).reset_index()
    be, see = wols(np.log(cel["renda"].values), np.log(cel["cons"].values), cel["w"].values)
    saida["entre_uf_situacao"] = {"n_celulas": int(len(cel)), "elasticidade": round(be, 4),
                                  "ep": round(see, 4)}
    # elasticidade ENTRE estratos amostrais da POF (cada estrato reúne domicílios de uma mesma
    # área geográfica e socioeconômica, a analogia mais próxima de um conjunto de municípios)
    est = uc.groupby("estrato").apply(lambda s: pd.Series({
        "renda": np.average(s["renda_pc"], weights=s["w"]),
        "cons": np.average(s["cons_monet"] / s["pessoas"], weights=s["w"]),
        "w": s["w"].sum(), "n": len(s)}), include_groups=False).reset_index()
    est = est[est["n"] >= 30]
    bs, ses = wols(np.log(est["renda"].values), np.log(est["cons"].values), est["w"].values)
    saida["entre_estratos"] = {"n_estratos": int(len(est)), "elasticidade": round(bs, 4), "ep": round(ses, 4)}

    # variável instrumental: log da renda per capita instrumentada pela escolaridade da pessoa de
    # referência (corrige o viés de atenuação do erro de medida e da renda transitória; a hipótese
    # de exclusão é imperfeita, pois a escolaridade também molda preferências, por isso é um
    # limite superior plausível, não o valor central)
    d = uc.dropna(subset=["anos_ref"]).copy()
    d = d[d["cons_monet"] > 0]
    x = np.log(d["renda_pc"].values); y = np.log((d["cons_monet"] / d["pessoas"]).values)
    z = d["anos_ref"].values.astype(float); w = d["w"].values
    Z = np.column_stack([np.ones_like(z), z]); X = np.column_stack([np.ones_like(x), x])
    Wm = np.sqrt(w)[:, None]
    pi = np.linalg.lstsq(Z * Wm, x * Wm[:, 0], rcond=None)[0]
    xhat = Z @ pi
    Xh = np.column_stack([np.ones_like(x), xhat])
    b_iv = np.linalg.lstsq(Xh * Wm, y * Wm[:, 0], rcond=None)[0][1]
    r2_1 = 1 - np.sum(w * (x - xhat) ** 2) / np.sum(w * (x - np.average(x, weights=w)) ** 2)
    saida["variavel_instrumental"] = {"instrumento": "anos de estudo da pessoa de referência",
                                      "elasticidade": round(float(b_iv), 4), "r2_primeiro_estagio": round(float(r2_1), 4),
                                      "n_uc": int(len(d))}
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1))
    print(json.dumps(saida["brasil"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
