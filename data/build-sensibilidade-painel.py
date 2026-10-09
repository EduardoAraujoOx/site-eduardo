#!/usr/bin/env python3
"""Dados da análise de sensibilidade do painel (aba Sensibilidade).

Para cada UF: a participação do governo estadual na receita nacional de referência em cada ano de 2019 a
2026 (o cenário sem reforma mantém a participação de um desses anos) e a incerteza relativa do coeficiente
de destino (dispersão entre as três rotas combinada com o erro de previsão do método, em validação que
exclui cada UF; ver phi-dest-robusto.json). A variação de cada ano é calculada no navegador com a fórmula
fechada do modelo, que reproduz a variação central do painel.

Entradas: painelufir/data/painel-estados.json, coeficientes-uf.json, phi-dest-robusto.json.
Saída: sensibilidade-uf.json (e cópia em painelufir/data/).
"""
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
EST = json.load(open(D / "painel-estados.json"))["estados"]
CF = json.load(open(D / "coeficientes-uf.json"))
ROB = json.load(open(D / "phi-dest-robusto.json"))["por_uf"]

ANOS = list(range(2019, 2026))
base = {y: sum(e["historico_por_ano"][str(y)]["icms_reais_2025"] - e["historico_por_ano"][str(y)]["outras_deducoes_reais_2025"]
               + e["historico_por_ano"][str(y)]["iss_reais_2025"] + e["historico_por_ano"][str(y)]["fecop_reais_2025"]
               for e in EST.values()) for y in ANOS}
out = {}
for uf, e in EST.items():
    ref = {str(y): e["historico_por_ano"][str(y)]["estado_reais_2025"] / base[y] for y in ANOS}
    ref["2026"] = e["estimativa_2026"]["estado_reais_2025"] / CF["total_br_2025"]
    # 2025 é o coeficiente central do painel
    assert abs(ref["2025"] - e["coef_neutro_estado_pct"] / 100) < 1e-6, uf
    out[uf] = {"ref": {k: round(v, 8) for k, v in ref.items()}, "incerteza_rel": round(ROB[uf]["incerteza_rel"], 4)}

res = {
    "anos_referencia": list(range(2019, 2027)),
    "nota": "ref: participação do governo estadual na receita nacional de referência (fração); 2026 é estimada. "
            "incerteza_rel: incerteza relativa do coeficiente de destino da UF (um desvio-padrão).",
    "por_uf": out,
}
for dest in (D / "sensibilidade-uf.json", ROOT / "painelufir/data/sensibilidade-uf.json"):
    json.dump(res, open(dest, "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "UFs; incerteza de", min(v["incerteza_rel"] for v in out.values()), "a", max(v["incerteza_rel"] for v in out.values()))
