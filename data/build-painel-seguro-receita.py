#!/usr/bin/env python3
"""Dados da aba Seguro-Receita do painel (painelufir): beneficiários por ano com numerador,
denominador, razão e nível de equalização, e a trajetória estadual até 2077.

Entradas: seguro-receita-repasses.json (2029-2033, por ente) e
seguro-receita-repasses-longo-prazo.json (2029-2077, agregado por UF e razão dos estados).
Saída: painelufir/data/painel-seguro-receita.json (e cópia em data/).
"""
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
S = json.load(open(D / "seguro-receita-repasses.json"))["anos"]
L = json.load(open(D / "seguro-receita-repasses-longo-prazo.json"))["anos"]
ANOS = sorted(int(a) for a in S)
LIM = 1.0  # R$ 1: abaixo disso é resíduo numérico do enchimento

niveis = {}
for a in ANOS:
    y = S[str(a)]
    ent = y["entidades"]
    ben = [e for e in ent if e["repasse"] > LIM]
    niveis[a] = {
        "nivel": L[str(a)]["nivel_equalizacao"], "fundo": y["pool"],
        "n_estados": sum(1 for e in ben if e["esfera"] == "estado"),
        "n_municipios": sum(1 for e in ben if e["esfera"] != "estado"),
        "soma": y["soma_repasses"],
    }

entes = {}
for a in ANOS:
    for e in S[str(a)]["entidades"]:
        r = entes.setdefault(e["id"], {
            "id": e["id"], "nome": e["nome"], "uf": e["uf"], "esfera": e["esfera"],
            "denom_ref": e["denom_ref"], "teto": e["teto"], "anos": {}})
        r["anos"][a] = {"num": e["numerador"], "den": e["denom_capado"], "razao": e["razao"], "rep": e["repasse"]}
lista = []
for r in entes.values():
    if any(v["rep"] > LIM for v in r["anos"].values()):
        r["teto_aplicado"] = r["teto"] < r["denom_ref"]
        r["acumulado"] = sum(v["rep"] for v in r["anos"].values())
        lista.append(r)
lista.sort(key=lambda r: -r["acumulado"])

# Trajetória dos estados até 2077: anos em que o fundo repassa algo ao governo estadual.
estados_longo = {}
for uf in L["2077"]["repasse_por_uf"]:
    anos = [int(a) for a in sorted(L, key=int) if L[a]["repasse_por_uf"][uf]["estado"] > LIM]
    estados_longo[uf] = {"anos": anos}

out = {
    "anos": ANOS, "horizonte": max(int(a) for a in L),
    "niveis": niveis, "entes": lista, "estados_longo": estados_longo,
}
for dest in (D / "painel-seguro-receita.json", ROOT / "painelufir/data/painel-seguro-receita.json"):
    json.dump(out, open(dest, "w"), ensure_ascii=False, separators=(",", ":"))
print(len(lista), "beneficiários;", {uf: (v["anos"][0] if v["anos"] else None) for uf, v in estados_longo.items() if v["anos"]})
