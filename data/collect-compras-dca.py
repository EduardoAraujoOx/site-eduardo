#!/usr/bin/env python3
"""
Coleta as compras de bens e serviços de cada ente (Estado e municípios) na
DCA Anexo I-D (Despesas Orçamentárias por categoria econômica e grupo de
natureza), SICONFI/Tesouro Nacional.

Objetivo: medir a base de compras governamentais observada, que no regime do
art. 473 da LC 214/2025 gera IBS para o ente comprador (ver Estudo 17).

Compras = soma, nas despesas LIQUIDADAS, dos elementos de despesa abaixo
(aplicação direta, modalidade 90). Excluídos: pessoal (GND 1), juros e
amortização, transferências, serviços de pessoa física (36), sentenças e
despesas de exercícios anteriores (91, 92), obrigações tributárias (47).

  3.3.90.30 material de consumo           4.4.90.35 consultoria (investimento)
  3.3.90.32 material p/ distr. gratuita   4.4.90.39 serviços PJ (investimento)
  3.3.90.33 passagens e locomoção         4.4.90.40 TIC (investimento)
  3.3.90.34 terceirização (contab. pessoal) 4.4.90.51 obras e instalações
  3.3.90.35 consultoria                   4.4.90.52 equipamentos e mat. permanente
  3.3.90.37 locação de mão de obra        4.4.90.61 aquisição de imóveis
  3.3.90.39 serviços de terceiros PJ      3.3.90.40 TIC
Fora da proxy, por decisão documentada (materiais/parametros-rateio-consumo-compras.md): 3.3.50 e 3.3.60
(transferências sem contraprestação), 3.3.90.36 (pessoa física), 3.3.90.38 (sem registros relevantes).

Uso:
  python3 data/collect-compras-dca.py ES            # um ou mais UFs
  python3 data/collect-compras-dca.py ES PR --ano 2024
Saída: data/compras-governamentais-dca.json (mescla por UF; idempotente)
"""
import gzip
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{}/municipios"
OUT = Path(__file__).parent / "compras-governamentais-dca.json"
UF_COD = {"RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17,
          "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27,
          "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35, "PR": 41,
          "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53}
ELEMENTOS = {
    "3.3.90.30": "material de consumo",
    "3.3.90.32": "material para distribuição gratuita",
    "3.3.90.33": "passagens e despesas com locomoção",
    "3.3.90.34": "terceirização de mão de obra contabilizada como pessoal",
    "3.3.90.35": "serviços de consultoria",
    "3.3.90.37": "locação de mão de obra",
    "3.3.90.39": "outros serviços de terceiros PJ",
    "3.3.90.40": "TIC PJ",
    "4.4.90.35": "consultoria (investimento)",
    "4.4.90.39": "serviços PJ (investimento)",
    "4.4.90.40": "TIC PJ (investimento)",
    "4.4.90.51": "obras e instalações",
    "4.4.90.52": "equipamentos e material permanente",
    "4.4.90.61": "aquisição de imóveis",
}


def get(url, tentativas=4):
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                raw = r.read()
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except Exception:
            if i == tentativas - 1:
                return None
            time.sleep(2 ** i)


def ente(id_ente, ano):
    d = get(f"{BASE}?an_exercicio={ano}&no_anexo=DCA-Anexo%20I-D&id_ente={id_ente}")
    if not d or not d.get("items"):
        return None
    v = {}
    pop = None
    for x in d["items"]:
        pop = x.get("populacao") or pop
        if x["coluna"] == "Despesas Liquidadas":
            v[x["cod_conta"]] = x["valor"]
    det = {}
    for el, nome in ELEMENTOS.items():
        k = "DO" + el + ".00.00"
        if v.get(k):
            det[el] = round(v[k], 2)
    return {
        "populacao": pop,
        "despesa_total_liquidada": round(v.get("TotalDespesas", 0), 2),
        "compras": round(sum(det.values()), 2),
        "por_elemento": det,
    }


def main():
    args = sys.argv[1:]
    ano = 2024
    if "--ano" in args:
        i = args.index("--ano")
        ano = int(args[i + 1])
        del args[i:i + 2]
    ufs = args or ["ES"]
    saida = json.loads(OUT.read_text()) if OUT.exists() else {}
    saida.setdefault("_meta", {})
    saida["_meta"].update({
        "fonte": "SICONFI/Tesouro Nacional, DCA Anexo I-D, despesas liquidadas",
        "ano": ano,
        "elementos_incluidos": ELEMENTOS,
        "observacao": "Proxy da base de compras sujeita ao art. 473 da LC 214/2025; "
                      "não separa fornecedores do Simples/MEI nem dispensas presenciais.",
    })
    for uf in ufs:
        cod = UF_COD[uf]
        reg = {"estado": ente(cod, ano), "municipios": {}}
        muns = get(IBGE.format(cod)) or []
        with ThreadPoolExecutor(max_workers=8) as pool:
            resultados = list(pool.map(lambda m: ente(m["id"], ano), muns))
        for m, r in zip(muns, resultados):
            if r:
                r["nome"] = m["nome"]
                reg["municipios"][str(m["id"])] = r
        faltam = [m["nome"] for m in muns if str(m["id"]) not in reg["municipios"]]
        reg["sem_dado"] = faltam
        saida[uf] = reg
        print(f"{uf}: {len(reg['municipios'])}/{len(muns)} municípios; sem dado: {faltam}")
        OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
