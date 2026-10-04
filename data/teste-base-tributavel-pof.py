#!/usr/bin/env python3
"""
TESTE (rota alternativa, não altera nenhum resultado publicado): base tributável sintética do IBS
a partir dos microdados da POF 2017-18, no estilo da nota técnica do COMSEFAZ.

Ideia: em vez de ratear um IBS nacional por um coeficiente φ_UF (consumo), calcula-se uma base
tributável por UF = Σ (consumo da categoria × peso legal da categoria), onde o peso é o fator pelo
qual o regime da LC 214/2025 reduz a base efetiva (alíquota zero = 0; redução de 60% = 0,4; etc.).
A base de cada UF multiplicada por uma alíquota média daria a arrecadação; aqui só interessa a
DISTRIBUIÇÃO (participação de cada UF), que é o que a base muda em relação ao φ atual.

Cenários:
  S0   consumo total da POF, peso 1 em tudo (replica o conceito do φ bruto, com o aluguel imputado);
  S1   pesos derivados da LC 214 (com a alimentação em domicílio classificada item a item pelo
       Cadastro de Produtos: alíquota zero / redução de 60% / cheia); aluguel imputado fora da base;
  S1a  S1 com alimentação em domicílio toda a 0,4 (limite superior da base alimentar);
  S1b  S1 com alimentação em domicílio toda a zero (limite inferior);
  S2   pesos da Tabela 1 da nota técnica do COMSEFAZ (para replicar a Tabela 2 dela).

Comparações: φ atual do modelo (pof_censo_bruto_pct, Censo x POF), Gobetti 2023, e as colunas
"Consumo POF" e "Base POF" da Tabela 2 da nota (microdados puros).

Uso: python3 data/teste-base-tributavel-pof.py <pasta_pof> [--cache pasta]
Saída: data/teste-base-tributavel-pof.json
"""
import glob
import json
import pickle
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import importlib.util

spec = importlib.util.spec_from_file_location("elast", Path(__file__).parent / "estima-elasticidade-pof.py")
el = importlib.util.module_from_spec(spec)
spec.loader.exec_module(el)
KEY = el.KEY
DATA = Path(__file__).parent
OUT = DATA / "teste-base-tributavel-pof.json"

UFS = {11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO", 21: "MA", 22: "PI", 23: "CE",
       24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
       41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF"}

# Quadros de alimentação em domicílio com alíquota zero (Anexo I e XV da LC 214: grãos, hortícolas,
# frutas, tubérculos, massas, carnes e pescados, aves, leite) e palavras-chave dos demais itens da
# cesta (pão francês, café, açúcar, óleos, margarina, sal, ovos)
QUADROS_ZERO = {63, 64, 65, 67, 68, 71, 72, 74, 76, 78, 79}
PALAVRAS_ZERO = ("PAO FRANCES", "CAFE", "ACUCAR", "OLEO", "MARGARINA", "SAL REFINADO", "SAL GROSSO",
                 "OVO", "FARINHA DE MANDIOCA", "FARINHA DE MILHO", "MANTEIGA", "QUEIJO")
PALAVRAS_CHEIA = ("CERVEJA", "CHOPP", "REFRIGERANTE", "VINHO", "CACHACA", "AGUARDENTE", "WHISKY", "VODKA",
                  "LICOR", "ENERGETICO", "CIGARRO")
CATS = ["alug_imput", "alug_mon", "condominio", "gas", "transp_urb", "gasolina", "viagens", "higiene",
        "saude", "educacao", "serv_pessoais", "apostas", "alim_fora", "alim_zero", "alim_reduz",
        "alim_cheia", "outros"]


def classifica(trad, cad):
    """Devolve dict codigo(5 dígitos) -> categoria."""
    desc = cad.groupby("k")["d"].first()
    cat = {}
    for r in trad.itertuples(index=False):
        c = int(r.Codigo)
        n3, n4, n5 = r.Nivel_3, r.Nivel_4, r.Nivel_5
        q = c // 1000
        d = str(desc.get(c, ""))
        if n5 == 1102012:
            k = "alug_imput"
        elif n4 == 110201:
            k = "alug_mon"
        elif n4 == 110202:
            k = "condominio"
        elif n4 == 110203 and ("GAS DE BOTIJ" in d or "GAS DE BUJ" in d or "GAS ENCANADO" in d):
            k = "gas"
        elif n4 == 110401:
            k = "transp_urb"
        elif n4 in (110402, 110403):
            k = "gasolina"
        elif n4 == 110406:
            k = "viagens"
        elif n3 == 1105:
            k = "higiene"
        elif n3 == 1106:
            k = "saude"
        elif n3 == 1107:
            k = "educacao"
        elif n3 == 1110:
            k = "serv_pessoais"
        elif n4 == 111101:
            k = "apostas"
        elif n3 == 1101:
            if q == 24 or q == 85:
                k = "alim_fora"
            elif any(p in d for p in PALAVRAS_CHEIA):
                k = "alim_cheia"
            elif q in QUADROS_ZERO or any(p in d for p in PALAVRAS_ZERO):
                k = "alim_zero"
            else:
                k = "alim_reduz"
        else:
            k = "outros"
        cat[c] = k
    return cat


def monta_uc(base):
    xl = pd.ExcelFile(glob.glob(str(base / "doc" / "Dicion*"))[0])
    trad = pd.read_excel(glob.glob(str(base / "trad" / "Tradutor_Despesa_Geral*"))[0])
    trad = trad[trad["Nivel_2"] == 11].copy()
    cad = pd.read_excel(glob.glob(str(base / "doc" / "Cadastro de Produtos.xls"))[0], dtype=str)
    cad.columns = ["q", "c", "d"]
    cad["k"] = cad["c"].str.strip().astype(int) // 100
    cat = classifica(trad, cad)
    mor = el.le(base, xl, "MORADOR.txt", "Morador", KEY + ["UF", "PESO_FINAL"])
    g = mor.groupby(KEY).agg(UF=("UF", "first"), peso=("PESO_FINAL", "first"),
                             pessoas=("UF", "size")).reset_index()
    acum = {c: {} for c in CATS}
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
        d = el.le(base, xl, arq, sheet, cols)
        d["cod"] = (d["V9001"] // 100).astype(int)
        d = d[d["cod"].isin(cat)].copy()
        d["val"] = d["V8000_DEFLA"] * d["FATOR_ANUALIZACAO"] / 12.0
        if arq == "ALUGUEL_ESTIMADO.txt":
            d["val"] *= d["V9011"]
        elif arq in mensais:
            d.loc[d["QUADRO"].isin(mensais[arq]), "val"] *= d["V9011"]
        d["cat"] = d["cod"].map(cat)
        s = d.groupby(KEY + ["cat"])["val"].sum().unstack(fill_value=0.0)
        for c in s.columns:
            for k, v in s[c].items():
                acum[c][k] = acum[c].get(k, 0.0) + v
        print(arq, len(d), flush=True)
    for c in CATS:
        g[c] = [acum[c].get(tuple(r), 0.0) for r in g[KEY].itertuples(index=False)]
    return g


def parse_tabela2():
    txt = (DATA / "referencias-externas" / "NT_COMSEFAZ_RefTributaria_v3.md").read_text(encoding="utf-8")
    sec = txt.split("Tabela 2 —")[1].split("Fonte:")[0]
    out = {}
    for ln in sec.splitlines():
        m = re.match(r"\|\s*([A-Z]{2})\s*\|(.*)\|\s*$", ln)
        if m:
            try:
                v = [float(x.replace("%", "").replace(",", ".")) for x in m.group(2).split("|")]
            except ValueError:
                continue
            out[m.group(1)] = {"renda": v[0], "consumo": v[1], "base": v[2], "tru": v[3]}
    return out


PESOS = {
    # alug_imput, alug_mon, cond, gas, transp_urb, gasolina, viagens, higiene, saude, educ, serv_pess,
    # apostas, alim_fora, zero, reduz, cheia, outros
    "S0": dict(alug_imput=1, alug_mon=1, condominio=1, gas=1, transp_urb=1, gasolina=1, viagens=1, higiene=1,
               saude=1, educacao=1, serv_pessoais=1, apostas=1, alim_fora=1, alim_zero=1, alim_reduz=1,
               alim_cheia=1, outros=1),
    "S1": dict(alug_imput=0, alug_mon=0.3, condominio=0.5, gas=1, transp_urb=0, gasolina=1, viagens=1,
               higiene=1, saude=0.4, educacao=0.4, serv_pessoais=1, apostas=0, alim_fora=0.6,
               alim_zero=0, alim_reduz=0.4, alim_cheia=1, outros=1),
    "S1a": dict(alug_imput=0, alug_mon=0.3, condominio=0.5, gas=1, transp_urb=0, gasolina=1, viagens=1,
                higiene=1, saude=0.4, educacao=0.4, serv_pessoais=1, apostas=0, alim_fora=0.6,
                alim_zero=0.4, alim_reduz=0.4, alim_cheia=1, outros=1),
    "S1b": dict(alug_imput=0, alug_mon=0.3, condominio=0.5, gas=1, transp_urb=0, gasolina=1, viagens=1,
                higiene=1, saude=0.4, educacao=0.4, serv_pessoais=1, apostas=0, alim_fora=0.6,
                alim_zero=0, alim_reduz=0, alim_cheia=1, outros=1),
    # Tabela 1 da nota: peso = 1 + ajuste (alimentação -0,60 vale para toda a alimentação)
    "S2": dict(alug_imput=0, alug_mon=0.3, condominio=0.5, gas=0.7, transp_urb=0.2, gasolina=1.5,
               viagens=0.5, higiene=0.9, saude=0.4, educacao=0.4, serv_pessoais=0.5, apostas=1,
               alim_fora=0.4, alim_zero=0.4, alim_reduz=0.4, alim_cheia=0.4, outros=1),
}


def main():
    base = Path(sys.argv[1])
    cache = Path(sys.argv[sys.argv.index("--cache") + 1]) if "--cache" in sys.argv else base
    pkl = cache / "pof_uc_cat.pkl"
    if pkl.exists():
        uc = pickle.loads(pkl.read_bytes())
    else:
        uc = monta_uc(base)
        pkl.write_bytes(pickle.dumps(uc))
    uc["uf"] = uc["UF"].astype(int).map(UFS)

    phi = json.loads((DATA / "phi-dest-pof-censo.json").read_text(encoding="utf-8"))["por_uf"]
    t2 = parse_tabela2()

    def part(serie):
        s = serie.groupby(uc["uf"]).sum()
        return (100 * s / s.sum())

    bases = {}
    for nome, w in PESOS.items():
        b = sum(uc[c] * w[c] for c in CATS)
        bases[nome] = b
    agg = {n: float((b * uc["peso"]).sum()) for n, b in bases.items()}
    shares = {n: part(b * uc["peso"]) for n, b in bases.items()}
    # versão "POF x Censo": base média por domicílio da UF x domicílios do Censo 2022 (mesmo desenho do φ atual)
    dom = pd.Series({u: phi[u]["domicilios_censo_2022"] for u in phi})
    shares_cens = {}
    for n, b in bases.items():
        med = (b * uc["peso"]).groupby(uc["uf"]).sum() / uc["peso"].groupby(uc["uf"]).sum()
        x = med * dom.reindex(med.index)
        shares_cens[n] = 100 * x / x.sum()

    ufs = sorted(phi)
    ref = {
        "phi_atual_bruto": pd.Series({u: phi[u]["pof_censo_bruto_pct"] for u in ufs}),
        "gobetti_2023": pd.Series({u: phi[u]["gobetti_tabela1_2023_pct"] for u in ufs}),
        "comsefaz_consumo_pof": pd.Series({u: t2[u]["consumo"] for u in ufs}),
        "comsefaz_base_pof": pd.Series({u: t2[u]["base"] for u in ufs}),
        "comsefaz_base_tru": pd.Series({u: t2[u]["tru"] for u in ufs}),
    }

    def dist(a, b):
        d = (a - b).reindex(ufs)
        return {"dif_abs_media_pp": round(float(d.abs().mean()), 4),
                "dif_abs_max_pp": round(float(d.abs().max()), 4),
                "uf_max": d.abs().idxmax(),
                "corr": round(float(np.corrcoef(a.reindex(ufs), b.reindex(ufs))[0, 1]), 5),
                "dif_rel_media_pct": round(float((d.abs() / b.reindex(ufs)).mean() * 100), 2)}

    comp = {}
    for n in PESOS:
        comp[n] = {"microdados_puros": {r: dist(shares[n], ref[r]) for r in ref},
                   "pof_x_censo": {r: dist(shares_cens[n], ref[r]) for r in ref}}
    # estabilidade entre cenários: quanto a base legal (S1) muda a distribuição vs consumo bruto (S0)
    estab = {f"{a}_vs_{b}": dist(shares_cens[a], shares_cens[b])
             for a, b in [("S1", "S0"), ("S1a", "S1"), ("S1b", "S1"), ("S2", "S1"), ("S1a", "S1b")]}
    # quanto da base é eliminada pelos regimes (agregado)
    razao = {n: round(agg[n] / agg["S0"], 4) for n in agg}
    comp_cats = {c: round(float((uc[c] * uc["peso"]).sum() / (uc[CATS].sum(axis=1) * uc["peso"]).sum()), 4)
                 for c in CATS}

    por_uf = {u: {n: {"microdados": round(float(shares[n][u]), 4), "pof_x_censo": round(float(shares_cens[n][u]), 4)}
                  for n in PESOS} | {"phi_atual_bruto": round(float(ref["phi_atual_bruto"][u]), 4),
                                     "comsefaz_base_pof": float(ref["comsefaz_base_pof"][u])}
              for u in ufs}
    saida = {"_meta": {
        "descricao": "Teste de base tributável sintética (POF 2017-18) - NAO alimenta nenhum resultado publicado",
        "pesos": PESOS,
        "classificacao_alimentos": {"quadros_zero": sorted(QUADROS_ZERO), "palavras_zero": PALAVRAS_ZERO,
                                    "palavras_cheia": PALAVRAS_CHEIA},
        "simplificacoes": "Fora da base: bens imóveis, reformas e serviços bancários (despesas não de consumo); "
                          "sem Simples/MEI, sem créditos, sem cashback, sem seletivo; pesos de categoria "
                          "aplicados à categoria inteira (sem distinguir itens dentro de saúde/educação).",
    },
        "base_agregada_rel_S0": razao, "composicao_consumo_pct": comp_cats,
        "comparacoes": comp, "estabilidade_entre_cenarios": estab, "por_uf": por_uf}
    OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"razao_base": razao, "composicao": comp_cats}, ensure_ascii=False, indent=1))
    for n in PESOS:
        print(n, "vs φ atual (POFxCenso):", comp[n]["pof_x_censo"]["phi_atual_bruto"])
        print(n, "vs Gobetti:", comp[n]["pof_x_censo"]["gobetti_2023"])
        print(n, "micro vs COMSEFAZ base POF:", comp[n]["microdados_puros"]["comsefaz_base_pof"])
    print(json.dumps(estab, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
