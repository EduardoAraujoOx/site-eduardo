#!/usr/bin/env python3
"""
Coleta, na DCA Anexo I-D (SICONFI, despesas liquidadas, 2024), elementos de despesa que NÃO compõem a
proxy de compras vigente (collect-compras-dca.py), para medir a sensibilidade da proxy (Estudo 17):

  3.3.90.33 passagens e despesas com locomoção      3.3.90.38 arrendamento mercantil
  3.3.90.34 outras despesas de pessoal decorrentes de contratos de terceirização
  3.3.90.36 outros serviços de terceiros, pessoa física (fora da base: PF não é contribuinte em regra)
  3.3.50    transferências a instituições privadas sem fins lucrativos (subvenções; tratamento incerto)
  3.3.60    transferências a instituições privadas com fins lucrativos

Uso: python3 data/collect-compras-complementares-dca.py ES PR ...   (retoma: pula UFs já feitas)
Saída: data/compras-complementares-dca.json
"""
import gzip, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{}/municipios"
OUT = Path(__file__).parent / "compras-complementares-dca.json"
UF_COD = {"RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17, "MA": 21, "PI": 22,
          "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27, "SE": 28, "BA": 29, "MG": 31, "ES": 32,
          "RJ": 33, "SP": 35, "PR": 41, "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53}
CONTAS = {"3.3.90.33": "DO3.3.90.33.00.00", "3.3.90.34": "DO3.3.90.34.00.00", "3.3.90.38": "DO3.3.90.38.00.00",
          "3.3.90.36": "DO3.3.90.36.00.00", "3.3.50": "DO3.3.50.00.00.00", "3.3.60": "DO3.3.60.00.00.00"}


def get(url, n=4):
    for i in range(n):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                raw = r.read()
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except Exception:
            if i == n - 1:
                return None
            time.sleep(2 ** i)


def ente(id_ente, ano):
    d = get(f"{BASE}?an_exercicio={ano}&no_anexo=DCA-Anexo%20I-D&id_ente={id_ente}")
    if not d or not d.get("items"):
        return None
    v = {x["cod_conta"]: x["valor"] for x in d["items"] if x["coluna"] == "Despesas Liquidadas"}
    out = {k: round(v[c], 2) for k, c in CONTAS.items() if v.get(c)}
    out["_total"] = round(v.get("TotalDespesas", 0), 2)
    return out


def main():
    ano = 2024
    ufs = sys.argv[1:]
    saida = json.loads(OUT.read_text()) if OUT.exists() else {}
    saida["_meta"] = {"fonte": "SICONFI/Tesouro Nacional, DCA Anexo I-D, despesas liquidadas", "ano": ano,
                      "contas": CONTAS}
    for uf in ufs:
        if uf in saida:
            continue
        cod = UF_COD[uf]
        muns = get(IBGE.format(cod)) or []
        with ThreadPoolExecutor(max_workers=16) as pool:
            res = list(pool.map(lambda m: ente(m["id"], ano), muns))
            est = ente(cod, ano)
        saida[uf] = {"estado": est, "municipios": {str(m["id"]): r for m, r in zip(muns, res) if r}}
        OUT.write_text(json.dumps(saida, ensure_ascii=False))
        print(uf, len(saida[uf]["municipios"]), "/", len(muns), flush=True)


if __name__ == "__main__":
    main()
