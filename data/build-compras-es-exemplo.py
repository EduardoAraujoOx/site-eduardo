#!/usr/bin/env python3
"""
Exemplo ilustrativo do Estudo 17 (compras governamentais) com dados do ES.

Entradas:
  data/compras-governamentais-dca.json  (collect-compras-dca.py ES)
  data/rateio-destino-municipios.json   (rateio atual: receita própria por renda x população)
  data/painel-municipios/ES.json        (lista de municípios e nomes)

Cenário ilustrativo: uma fração THETA do IBS municipal próprio (a parte que não
é cota-parte) provém de compras e é rateada pela despesa de compras observada de
cada prefeitura, em vez de renda x população. THETA = 30%, a participação das
compras no IBS municipal na estimativa nacional de Gobetti/COMSEFAZ (2026).

A base de compras é a soma bruta de elementos de despesa (DCA Anexo I-D, 2024,
liquidado), SEM descontar fornecedores do Simples/MEI ou dispensas presenciais;
por isso os valores absolutos são um teto e só as participações relativas devem
ser lidas como resultado.

Saída: data/compras-governamentais-es-exemplo.json
"""
import json
from pathlib import Path

D = Path(__file__).parent
THETA = 0.30
ALIQ_EFETIVA = 0.159   # alíquota efetiva com redutor (Gobetti/COMSEFAZ, 2026)
ALIQ_REFERENCIA = 0.284  # alíquota de referência IBS+CBS na mesma nota
COTA = 0.25

c = json.loads((D / "compras-governamentais-dca.json").read_text())["ES"]
R = json.loads((D / "rateio-destino-municipios.json").read_text())["municipios"]
P = json.loads((D / "painel-municipios" / "ES.json").read_text())["municipios"]

ids = list(P)
tot_c = sum(c["municipios"][k]["compras"] for k in ids)
tot_p = sum(R[k]["propria_pct"] for k in ids)
pop_uf = sum(c["municipios"][k]["populacao"] for k in ids)
n = len(ids)

linhas = []
for k in ids:
    m = c["municipios"][k]
    s0 = R[k]["propria_pct"] / tot_p
    sc = m["compras"] / tot_c
    s1 = (1 - THETA) * s0 + THETA * sc
    cota = 0.95 * m["populacao"] / pop_uf + 0.05 / n
    linhas.append({
        "id": k, "nome": P[k]["nome"], "populacao": m["populacao"],
        "renda_per_capita_2022": R[k]["renda_domiciliar_per_capita_2022"],
        "despesa_total": m["despesa_total_liquidada"], "compras": m["compras"],
        "compras_pct_despesa": m["compras"] / m["despesa_total_liquidada"],
        "compras_per_capita": m["compras"] / m["populacao"],
        "part_atual": s0, "part_compras": sc, "part_nova": s1,
        "var_relativa": s1 / s0 - 1,
        "var_por_100mi": (s1 - s0) * 100.0,       # R$ milhões por cada R$ 100 mi de IBS próprio
        "part_cota_parte_populacao": cota,
    })

est = c["estado"]
saida = {
    "_meta": {
        "descricao": __doc__.strip().split("\n\n")[0],
        "theta_compras_no_ibs_proprio": THETA,
        "aliquota_efetiva_compras": ALIQ_EFETIVA,
        "aliquota_referencia": ALIQ_REFERENCIA,
        "cota_parte": COTA,
        "aviso": "Base de compras bruta (teto). Ilustração, não resultado do modelo.",
    },
    "totais": {
        "compras_municipios": tot_c, "compras_estado": est["compras"],
        "populacao_municipios": pop_uf, "n_municipios": n,
        "ibs_compras_municipios_aliq_efetiva": tot_c * ALIQ_EFETIVA,
        "ibs_compras_estado_aliq_efetiva": est["compras"] * ALIQ_EFETIVA,
        "cota_parte_se_incidir": est["compras"] * ALIQ_EFETIVA * COTA,
        "ganham": sum(1 for x in linhas if x["var_relativa"] > 0),
        "perdem": sum(1 for x in linhas if x["var_relativa"] < 0),
    },
    "municipios": sorted(linhas, key=lambda x: -x["compras"]),
}
(D / "compras-governamentais-es-exemplo.json").write_text(
    json.dumps(saida, ensure_ascii=False, indent=1))
print("ok", saida["totais"])
