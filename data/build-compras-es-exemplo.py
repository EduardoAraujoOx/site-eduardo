#!/usr/bin/env python3
"""
Exemplo do Estudo 17 (compras governamentais) com dados do ES: o rateio do IBS municipal próprio
entre os 78 municípios capixabas antes e depois da incorporação do consumo estimado com
elasticidade-renda e das compras.

  anterior = renda média x população (elasticidade 1, sem compras), calculado aqui com
             rateio_consumo_compras.pesos_consumo(eps=1);
  atual    = peso do rateio vigente (data/rateio-destino-municipios.json): mistura de consumo
             esperado (eps = 0,80) e compras observadas, com o peso theta da UF.

Entradas: compras-governamentais-dca.json, rateio-destino-municipios.json, painel-municipios/ES.json,
censo-2022-renda-municipios.json e censo-2022-renda-mediana-municipios.json.
Saída: data/compras-governamentais-es-exemplo.json
"""
import json
from pathlib import Path

import rateio_consumo_compras as rcc

D = Path(__file__).parent
_CAL = json.loads((D / "compras-calibracao.json").read_text())["central"]
ALIQ_EFETIVA = _CAL["tau"] * _CAL["f"]   # carga média x f: imposto sobre o gasto bruto (valores ilustrativos do estudo)
COTA = 0.25

c = json.loads((D / "compras-governamentais-dca.json").read_text())["ES"]
R = json.loads((D / "rateio-destino-municipios.json").read_text())["municipios"]
P = json.loads((D / "painel-municipios" / "ES.json").read_text())["municipios"]
rend, med, _ = rcc.carrega_entradas()

ids = list(P)
pops = {k: R[k]["pop_media"] for k in ids}
w_ant = rcc.pesos_consumo(pops, {k: R[k]["renda_domiciliar_per_capita_2022"] for k in ids},
                          {k: med.get(k) for k in ids}, eps=1.0)
tot_ant = sum(w_ant.values())
tot_c = sum(c["municipios"][k]["compras"] for k in ids)
pop_uf = sum(pops.values())
n = len(ids)

linhas = []
for k in ids:
    m = c["municipios"][k]
    s0 = w_ant[k] / tot_ant
    s1 = R[k]["peso_intra_uf_propria"]
    sc = m["compras"] / tot_c
    linhas.append({
        "id": k, "nome": P[k]["nome"], "populacao": m["populacao"],
        "renda_per_capita_2022": R[k]["renda_domiciliar_per_capita_2022"],
        "despesa_total": m["despesa_total_liquidada"], "compras": m["compras"],
        "compras_pct_despesa": m["compras"] / m["despesa_total_liquidada"],
        "compras_per_capita": m["compras"] / m["populacao"],
        "part_atual": s0, "part_compras": sc, "part_nova": s1,
        "var_relativa": s1 / s0 - 1,
        "var_por_100mi": (s1 - s0) * 100.0,
        "part_cota_parte_populacao": 0.95 * m["populacao"] / pop_uf + 0.05 / n,
    })

est = c["estado"]
saida = {
    "_meta": {
        "descricao": __doc__.strip().split("\n\n")[0],
        "theta_uf": R[ids[0]]["theta_compras_uf"], "elasticidade": rcc.EPS,
        "aliquota_efetiva_ilustrativa": ALIQ_EFETIVA,
        "cota_parte": COTA,
        "aviso": "Compras brutas (teto); a tabela compara o modelo anterior com o vigente.",
    },
    "totais": {
        "compras_municipios": tot_c, "compras_estado": est["compras"],
        "populacao_municipios": pop_uf, "n_municipios": n,
        "ibs_compras_municipios_aliq_efetiva": tot_c * ALIQ_EFETIVA,
        "ibs_compras_estado_aliq_efetiva": est["compras"] * ALIQ_EFETIVA,
        "cota_parte_se_incidir": est["compras"] * ALIQ_EFETIVA * COTA,
        "ganham": sum(1 for x in linhas if x["var_relativa"] > 0),
        "perdem": sum(1 for x in linhas if x["var_relativa"] < 0),
        "media_abs_var_relativa": sum(abs(x["var_relativa"]) for x in linhas) / n,
    },
    "municipios": sorted(linhas, key=lambda x: -x["compras"]),
}
(D / "compras-governamentais-es-exemplo.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1))
print("ok", saida["totais"], saida["_meta"]["theta_uf"])
