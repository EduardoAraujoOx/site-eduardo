#!/usr/bin/env python3
"""
População média de 2019 a 2026 de cada município e de cada UF, completa nos oito anos (LC 227/2026,
art. 117, §§3º a 6º, e §7º: estimativas mais recentes do IBGE).

Fontes (API SIDRA/IBGE): estimativas da população residente (tabela 6579, variável 9324) para 2019, 2020,
2021, 2024, 2025 e 2026; Censo Demográfico 2022 (tabela 4714, variável 93) para 2022. O IBGE não publica
estimativa em 2022 (ano do Censo) nem em 2023; 2022 usa o Censo e 2023 a média entre o Censo de 2022 e a
estimativa de 2024 (interpolação linear). Substitui, para o Seguro-Receita, a média de cinco anos que
build-populacao-municipios.py e build-populacao-uf-media.py calculavam a partir dos arquivos do DOU.

Uso: python3 build-populacao-sidra.py
Saídas: populacao-municipios-media-2019-2026.json e populacao-uf-media-2019-2026.json (mesmo formato).
"""
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
EST = [2019, 2020, 2021, 2024, 2025, 2026]


def sidra(tab, var, nivel, anos):
    url = f"https://apisidra.ibge.gov.br/values/t/{tab}/{nivel}/all/v/{var}/p/{','.join(map(str, anos))}"
    for _ in range(4):
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=180).read())
            return d[1:]
        except Exception:
            pass
    raise SystemExit(f"falha ao ler {url}")


def serie(nivel):
    pop = {}   # cod -> {ano: pop}
    nome = {}
    for r in sidra(6579, 9324, nivel, EST):
        if not r["V"].isdigit():
            continue
        pop.setdefault(r["D1C"], {})[int(r["D3C"])] = int(r["V"])
        nome[r["D1C"]] = r["D1N"]
    for r in sidra(4714, 93, nivel, [2022]):
        if r["V"] not in ("-", "..."):
            pop.setdefault(r["D1C"], {})[2022] = int(r["V"])
    for cod, v in pop.items():
        if 2022 in v and 2024 in v:
            v[2023] = (v[2022] + v[2024]) / 2
    return pop, nome


def main():
    meta = {
        "fonte": "IBGE, API SIDRA: Estimativas da População Residente (tabela 6579) e Censo Demográfico 2022 (tabela 4714)",
        "metodo": ("Média aritmética simples dos oito anos de 2019 a 2026 (LC 227/2026, art. 117, §§3º-6º). 2022: Censo; "
                   "2023: média entre o Censo de 2022 e a estimativa de 2024, porque o IBGE não publica estimativa nesse ano."),
        "anos_considerados": list(range(2019, 2027)),
        "anos_interpolados": [2023],
    }
    pop_m, nome_m = serie("n6")
    res = {}
    for cod, v in pop_m.items():
        if 2022 not in v:
            continue
        nm, uf = nome_m[cod].rsplit(" - ", 1)
        res[cod] = {"nome": nm, "uf": uf, "pop_media": sum(v.values()) / len(v), "anos_com_dado": sorted(v), "pop_por_ano": {str(a): v[a] for a in sorted(v)}}
    out = dict(meta, n_municipios=len(res), total_pop_media=sum(m["pop_media"] for m in res.values()), municipios=res)
    (HERE / "populacao-municipios-media-2019-2026.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    pop_u, nome_u = serie("n3")
    SIG = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN",
           "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR", "42": "SC",
           "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}
    ufs = {SIG[c]: {"pop_media": sum(v.values()) / len(v), "anos_com_dado": sorted(v), "pop_por_ano": {str(a): v[a] for a in sorted(v)}}
           for c, v in pop_u.items() if c in SIG and len(v) == 8}
    outu = dict(meta, ufs=ufs, total_pop_media=sum(u["pop_media"] for u in ufs.values()))
    (HERE / "populacao-uf-media-2019-2026.json").write_text(json.dumps(outu, ensure_ascii=False, indent=2))
    inc = sum(1 for m in res.values() if len(m["anos_com_dado"]) < 8)
    print("municípios com menos de 8 anos:", inc)
    print(len(res), "municípios;", len(ufs), "UFs; população média nacional", round(out["total_pop_media"]), round(outu["total_pop_media"]))


if __name__ == "__main__":
    main()
