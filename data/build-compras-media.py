#!/usr/bin/env python3
"""
Compras governamentais usadas pelo modelo: média de 2024 e 2025, a preços de 2025.

Por quê. As compras de cada ente na DCA I-D variam bastante de um ano para o outro (investimento e obras
vêm em ondas): a correlação de postos das compras per capita entre 2024 e 2025 é de 0,88 nos municípios.
Um único ano carregaria esse ruído para o rateio. Além disso, nenhum dos dois anos cobre todos os entes
(2025: 74 municípios sem dado, entregas atrasadas; 2024: 24). A média dos anos disponíveis de cada ente
reduz o ruído e preenche as lacunas, sem usar nenhum dado de terceiros.

Como. 2024 é levado a preços de 2025 pelo crescimento do PIB nominal (ibs-projecao-nacional.json). Para cada
ente, valor = média dos anos com dado válido (compras > 0); se só um ano é válido, usa-se esse ano.
Os campos compras, despesa_total_liquidada e por_elemento são médias; população é a mais recente.

Entradas: compras-governamentais-dca-2024.json e -2025.json (collect-compras-dca.py).
Saída: compras-governamentais-dca.json (lido por rateio_consumo_compras.py, calibra-peso-compras.py etc.).
"""
import json
from pathlib import Path

D = Path(__file__).parent
a24 = json.loads((D / "compras-governamentais-dca-2024.json").read_text())
a25 = json.loads((D / "compras-governamentais-dca-2025.json").read_text())
nac = {r["ano"]: r["pib_nominal"] for r in json.loads((D / "ibs-projecao-nacional.json").read_text())["historico"]}
G = nac[2025] / nac[2024]


def media(m24, m25):
    v = []
    if m24 and (m24.get("compras") or 0) > 0:
        v.append((m24, G))
    if m25 and (m25.get("compras") or 0) > 0:
        v.append((m25, 1.0))
    if not v:
        return None
    n = len(v)
    out = {"populacao": (m25 or m24 or {}).get("populacao") or (m24 or {}).get("populacao"),
           "despesa_total_liquidada": round(sum(m["despesa_total_liquidada"] * k for m, k in v) / n, 2),
           "compras": round(sum(m["compras"] * k for m, k in v) / n, 2),
           "anos_usados": [2024 if k != 1.0 else 2025 for m, k in v]}
    el = {}
    for m, k in v:
        for e, x in m["por_elemento"].items():
            el[e] = el.get(e, 0) + x * k / n
    out["por_elemento"] = {e: round(x, 2) for e, x in el.items()}
    if "nome" in (m25 or {}):
        out["nome"] = m25["nome"]
    elif "nome" in (m24 or {}):
        out["nome"] = m24["nome"]
    return out


saida = {"_meta": {
    "fonte": "SICONFI/Tesouro Nacional, DCA Anexo I-D, despesas liquidadas",
    "anos": [2024, 2025], "precos": 2025, "fator_2024_para_2025": G,
    "regra": "média dos anos com dado válido; 2024 a preços de 2025 pelo PIB nominal",
    "elementos_incluidos": a25["_meta"]["elementos_incluidos"],
    "observacao": a25["_meta"].get("observacao", ""),
}}
n_um_ano = 0
for uf in a25:
    if uf == "_meta":
        continue
    r24, r25 = a24.get(uf, {}), a25[uf]
    est = media(r24.get("estado"), r25.get("estado"))
    muns, sem = {}, []
    codigos = set(r24.get("municipios", {})) | set(r25.get("municipios", {}))
    for c in sorted(codigos):
        m = media(r24.get("municipios", {}).get(c), r25.get("municipios", {}).get(c))
        if m:
            muns[c] = m
            n_um_ano += len(m["anos_usados"]) == 1
        else:
            sem.append(c)
    saida[uf] = {"estado": est, "municipios": muns, "sem_dado": sem}
saida["_meta"]["municipios_com_um_so_ano"] = n_um_ano
(D / "compras-governamentais-dca.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1))
print("ok; fator", round(G, 4), "; municípios com um só ano:", n_um_ano)
