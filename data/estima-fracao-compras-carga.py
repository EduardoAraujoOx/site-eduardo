#!/usr/bin/env python3
"""
Estima, com dados oficiais, a fração f das compras governamentais que carrega a carga média de tributos
(parâmetro de data/calibra-peso-compras.py), por dois testes independentes:

  1. Carga relativa. Tabelas de Recursos e Usos 2023 (IBGE, Contas Nacionais): carga de impostos sobre
     produtos (IPI, ICMS, outros impostos: ISS, PIS/Cofins etc.) por grupo de produtos; composição do que a
     administração pública compra (consumo intermediário da atividade 12) e do consumo das famílias.
     r = carga das compras do governo / carga do consumo das famílias (a mesma medida nas duas pontas,
     o que neutraliza o que a medida não capta, como a cascata de tributos nos insumos).
     Variantes: com e sem o grupo financeiro (cujos "outros impostos" incluem IOF, que a reforma não substitui).
  2. Cobertura da proxy. Consumo intermediário da administração pública (TRU 2023, levado a 2025 pelo PIB
     nominal) contra o custeio da proxy de compras (DCA I-D média 2024-2025 a preços de 2025, elementos
     3.3.90.*, Estados, municípios e União 2025): g = CI / proxy. g próximo de 1 indica que a proxy não superestima nem subestima as compras.

  f = g x r (compras da proxy que efetivamente carregam a carga média).
Saída: data/fracao-compras-carga.json
"""
import json
import urllib.request
from pathlib import Path

import pandas as pd

D = Path(__file__).parent
TRU = "https://ftp.ibge.gov.br/Contas_Nacionais/Sistema_de_Contas_Nacionais/2023/tabelas_xls/tabelas_de_recursos_e_usos/"
CACHE = D / "cache-tru"
n = lambda s: pd.to_numeric(s, errors="coerce")


def baixa(nome):
    CACHE.mkdir(exist_ok=True)
    p = CACHE / nome
    if not p.exists():
        with urllib.request.urlopen(TRU + nome, timeout=90) as r:
            p.write_bytes(r.read())
    return p


def main():
    o = pd.read_excel(baixa("12_tab1_2023.xls"), "oferta", header=None).iloc[5:17]
    carga = (n(o[9]) / n(o[2])).values          # impostos líquidos / oferta a preço de consumidor
    nomes = [str(x) for x in o[1]]
    x = pd.ExcelFile(baixa("12_tab2_2023.xls"))
    ci = n(x.parse("CI", header=None).iloc[5:17][13]).values       # consumo intermediário da adm. pública
    dm = x.parse("demanda", header=None).iloc[5:17]
    fam = n(dm[5]).values                                           # consumo das famílias
    peso = lambda v, m=1: (v * m) / (v * m).sum()
    mask_fin = pd.Series([i != 8 for i in range(12)]).astype(float).values
    res = {}
    for nome, m in [("todos_os_grupos", 1.0), ("sem_financeiro_iof", mask_fin)]:
        cf = (carga * peso(fam, m)).sum()
        cg = (carga * peso(ci, m)).sum()
        res[nome] = {"carga_familias": cf, "carga_compras_governo": cg, "r": cg / cf}
    # cobertura da proxy
    d = json.loads((D / "compras-governamentais-dca.json").read_text())
    cust = lambda pe: sum(v for k, v in pe.items() if k.startswith("3.3.90"))
    sub = sum(cust(m["por_elemento"]) for u, r in d.items() if u != "_meta"
              for m in list(r["municipios"].values()) + [r["estado"]] if m)
    uniao = json.loads((D / "compras-uniao-dca.json").read_text())
    un = cust(uniao["2025"]["por_elemento"])
    nac = {r["ano"]: r["pib_nominal"] for r in json.loads((D / "ibs-projecao-nacional.json").read_text())["historico"]}
    ci24 = ci.sum() * 1e6 * nac[2025] / nac[2023]
    g = ci24 / (sub + un)
    # mistura da proxy completa (custeio com a carga das compras do governo; obras = construção; equipamentos = transformação)
    tot = {}
    for u, r in d.items():
        if u == "_meta":
            continue
        for m in list(r["municipios"].values()) + [r["estado"]]:
            for k, v in ((m or {}).get("por_elemento") or {}).items():
                tot[k] = tot.get(k, 0) + v
    S = sum(tot.values())
    s_ob, s_eq, s_im = tot["4.4.90.51"] / S, tot["4.4.90.52"] / S, tot["4.4.90.61"] / S
    s_cu = 1 - s_ob - s_eq - s_im
    for nome, m in [("todos_os_grupos", 1.0), ("sem_financeiro_iof", mask_fin)]:
        cg = res[nome]["carga_compras_governo"]
        carga_mix = s_cu * cg + s_ob * carga[4] + s_eq * carga[2] + s_im * carga[9]
        res[nome]["carga_mix_proxy"] = carga_mix
        res[nome]["r_mix_proxy"] = carga_mix / res[nome]["carga_familias"]
        res[nome]["f_estimado"] = g * res[nome]["r_mix_proxy"]
    saida = {
        "_meta": {"descricao": __doc__.strip().split("\n\n")[0], "fonte_tru": TRU,
                  "custeio_proxy_subnacional_reais": sub, "custeio_proxy_uniao_reais": un,
                  "consumo_intermediario_adm_publica_2025_reais": ci24, "cobertura_g": g,
                  "mistura_proxy": {"custeio": s_cu, "obras": s_ob, "equipamentos": s_eq, "imoveis": s_im}},
        "carga_por_grupo": dict(zip(nomes, carga.tolist())),
        "resultado": res,
    }
    (D / "fracao-compras-carga.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1))
    print(json.dumps({"g": g, **{k: round(v["f_estimado"], 3) for k, v in res.items()}}, indent=1))


if __name__ == "__main__":
    main()
