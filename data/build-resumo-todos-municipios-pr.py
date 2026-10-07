#!/usr/bin/env python3
"""
Resumo dos 399 municípios do Paraná (sem amostra): contagens de perdas e ganhos em 2033, medianas,
mudanças de sinal contra o uso direto da DCA, perdas e ganhos acumulados em 2029-2033 e rankings
(em R$ e em %). Lê municipios-pr-final-auditado-latest.csv; o contrafactual dos anos 2029-2032 é
a receita dividida por (1 + variação). Municípios com ISS incompleto (menos de cinco anos observados,
ISS de 2025 não observado diretamente ou pendência de validação) ficam marcados em "dado_iss_incompleto"
e só entram no teste de robustez.

Uso: python3 build-resumo-todos-municipios-pr.py -> auditoria-pr-validacao/resumo-todos-municipios-pr.json
"""
import csv, json, statistics
from pathlib import Path

OUT = Path(__file__).parent / "auditoria-pr-validacao"
ANOS = [2029, 2030, 2031, 2032, 2033]


def f(x):
    return None if x in ("", "None", None) else float(x)


def main():
    rows = list(csv.DictReader(open(OUT / "municipios-pr-final-auditado-latest.csv", encoding="utf-8-sig")))
    M = []
    for r in rows:
        rec = {y: float(r[f"receita_{y}_final"]) for y in ANOS}
        cf = {y: float(r["contrafactual_2033_final"]) if y == 2033 else rec[y] / (1 + float(r[f"variacao_{y}_final_pct"]) / 100) for y in ANOS}
        M.append({
            "municipio": r["municipio"], "codigo_ibge": r["codigo_ibge"], "rec": rec, "cf": cf,
            "var33": float(r["variacao_2033_final_pct"]), "orig33": f(r["variacao_2033_metodo_original_pct"]),
            "delta_met": f(r["delta_metodologia_2033_pp"]), "amostra_principal": r["qualificado_artigo"] == "True",
            "incompleto": not (int(r["iss_observado_anos"] or 0) >= 5 and r["iss_2025_direto"] == "True" and not r["iss_pendente_anos"]),
            "dif33": cf[2033] - rec[2033], "dif_acum": sum(cf[y] - rec[y] for y in ANOS),
        })

    def bloco(S):
        perd = [m for m in S if m["rec"][2033] < m["cf"][2033]]
        ganh = [m for m in S if m["rec"][2033] >= m["cf"][2033]]
        orig = [m["orig33"] for m in S if m["orig33"] is not None]
        flips = sum(1 for m in S if m["orig33"] is not None and ((m["orig33"] < 0) != (m["var33"] < 0)))
        dm = [abs(m["delta_met"]) for m in S if m["delta_met"] is not None]
        return {
            "n": len(S), "perdem_2033": len(perd), "ganham_2033": len(ganh),
            "mediana_var_2033_pct": statistics.median(m["var33"] for m in S),
            "perda_acum_2029_2033_dos_que_perdem_2033": sum(m["dif_acum"] for m in perd),
            "perda_por_ano_dos_que_perdem_2033": {str(y): sum(m["cf"][y] - m["rec"][y] for m in perd) for y in ANOS},
            "ganho_acum_2029_2033_dos_que_ganham_2033": -sum(m["dif_acum"] for m in ganh),
            "saldo_acum_2029_2033": -sum(m["dif_acum"] for m in S),
            "metodo_dca_direto": {"negativos": sum(1 for x in orig if x < 0), "positivos": sum(1 for x in orig if x > 0), "mediana_pct": statistics.median(orig)},
            "mudancas_de_sinal": flips, "media_abs_revisao_pp": statistics.mean(dm),
        }

    def rk(chave, rev, n=20):
        return [{"municipio": m["municipio"], "dif_2033_reais": m["dif33"], "var_2033_pct": m["var33"], "dado_iss_incompleto": m["incompleto"]}
                for m in sorted(M, key=lambda m: m[chave], reverse=rev)[:n]]

    res = {
        "_meta": "Paraná, 399 municípios, base final auditada, R$ constantes de 2025. dif = contrafactual − receita (positivo = perda).",
        "todos": bloco(M), "amostra_principal_10mil_iss": bloco([m for m in M if m["amostra_principal"]]),
        "dado_iss_incompleto": {"n": sum(m["incompleto"] for m in M), "peso_base_2025_pct": None},
        "maiores_perdas_reais": rk("dif33", True), "maiores_ganhos_reais": rk("dif33", False),
        "maiores_perdas_pct": rk("var33", False), "maiores_ganhos_pct": rk("var33", True),
    }
    base = {r["municipio"]: float(r["base_2025_final"]) for r in rows}
    res["dado_iss_incompleto"]["peso_base_2025_pct"] = 100 * sum(base[m["municipio"]] for m in M if m["incompleto"]) / sum(base.values())
    json.dump(res, open(OUT / "resumo-todos-municipios-pr.json", "w"), ensure_ascii=False, indent=1)
    t = res["todos"]
    print(t["n"], t["perdem_2033"], t["ganham_2033"], round(t["perda_acum_2029_2033_dos_que_perdem_2033"] / 1e6), round(t["saldo_acum_2029_2033"] / 1e6), t["mudancas_de_sinal"], round(t["media_abs_revisao_pp"], 2))


if __name__ == "__main__":
    main()
