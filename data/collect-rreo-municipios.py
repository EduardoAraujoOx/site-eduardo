#!/usr/bin/env python3
"""
Coleta, para cada município, o ISS e a cota-parte do ICMS no RREO Anexo 03 (Demonstrativo da Receita Corrente
Líquida), SICONFI/Tesouro Nacional: total dos últimos 12 meses e os 12 meses da janela.

Uso (a partir da raiz do repositório):
    python3 data/collect-rreo-municipios.py 2026:4 2025:4 2025:6 [--uf ES] [--workers 6]

Cada argumento ANO:BIMESTRE gera data/rreo-municipios/ANO-pBIMESTRE.json, com {código IBGE: {...}}.
- 2026:4  janela set/2025 a ago/2026 (o dado observado mais recente, base do tratamento de 2026 do coeficiente histórico);
- 2025:4  a mesma janela um ano antes (para a variação observada);
- 2025:6  janela de 2025 inteiro (jan a dez), comparável ao ano de 2025 da DCA, para validar RREO x DCA.

O script é retomável: municípios já gravados (inclusive os "ausentes", sem entrega no bimestre) são pulados.
"""
import json
import ssl
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "rreo-municipios"
BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo"
COD_ISS = "ISSLiquidoExcetoTransferenciasEFUNDEB"
COD_COTA = "RREO3CotaParteDoICMS"
MESES = ["<MR-11>", "<MR-10>", "<MR-9>", "<MR-8>", "<MR-7>", "<MR-6>", "<MR-5>", "<MR-4>", "<MR-3>", "<MR-2>", "<MR-1>", "<MR>"]
TOTAL12 = "TOTAL (ÚLTIMOS 12 MESES)"


def contexto_ssl():
    for p in ("/root/.ccr/ca-bundle.crt",):
        if Path(p).exists():
            return ssl.create_default_context(cafile=p)
    return ssl.create_default_context()


CTX = contexto_ssl()


def buscar(url, tentativas=5):
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(url, timeout=60, context=CTX) as r:
                return json.loads(r.read())
        except Exception:
            if i < tentativas - 1:
                time.sleep(2 ** i)
    return None


def extrair(itens, cod, nome):
    """Valores da conta: total de 12 meses e a lista dos 12 meses (None onde a coluna não veio)."""
    linhas = [x for x in itens if x.get("cod_conta") == cod]
    if not linhas:
        linhas = [x for x in itens if (x.get("conta") or "").strip() == nome and "Cota-Parte" not in (x.get("conta") or "")] if nome == "ISS" \
            else [x for x in itens if (x.get("conta") or "").strip() == nome]
    por_col = {x.get("coluna"): x.get("valor") for x in linhas}
    if TOTAL12 not in por_col:
        return None
    return {"total12": por_col[TOTAL12], "meses": [por_col.get(c) for c in MESES]}


def coletar(ano, bimestre, cod):
    url = (f"{BASE}?an_exercicio={ano}&nr_periodo={bimestre}&co_tipo_demonstrativo=RREO"
           f"&no_anexo=RREO-Anexo%2003&co_esfera=M&id_ente={cod}")
    d = buscar(url)
    if d is None:
        return {"erro": True}
    itens = d.get("items") or []
    if not itens:
        return {"ausente": True}
    return {"iss": extrair(itens, COD_ISS, "ISS"), "cota": extrair(itens, COD_COTA, "Cota-Parte do ICMS")}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    uf = None
    workers = 6
    for i, a in enumerate(sys.argv):
        if a == "--uf":
            uf = sys.argv[i + 1]
            args = [x for x in args if x != uf]
        if a == "--workers":
            workers = int(sys.argv[i + 1])
            args = [x for x in args if x != sys.argv[i + 1]]
    idx = json.load(open(HERE / "painel-municipios" / "index.json"))["municipios"]
    codigos = sorted(c for c, m in idx.items() if uf is None or m["uf"] == uf)
    OUT.mkdir(exist_ok=True)
    for arg in args:
        ano, bim = arg.split(":")
        arq = OUT / f"{ano}-p{bim}.json"
        dados = json.load(open(arq)) if arq.exists() else {}
        falta = [c for c in codigos if c not in dados or dados[c].get("erro")]
        print(f"{arg}: {len(codigos)} municípios, {len(falta)} a coletar", flush=True)
        t0 = time.time()
        feitos = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for c, r in zip(falta, ex.map(lambda c: coletar(ano, bim, c), falta)):
                dados[c] = r
                feitos += 1
                if feitos % 100 == 0:
                    json.dump(dados, open(arq, "w"), ensure_ascii=False, separators=(",", ":"))
                    print(f"  {feitos}/{len(falta)}  {time.time() - t0:.0f}s", flush=True)
        json.dump(dados, open(arq, "w"), ensure_ascii=False, separators=(",", ":"))
        ok = sum(1 for c in codigos if dados.get(c, {}).get("iss") and dados[c].get("cota"))
        aus = sum(1 for c in codigos if dados.get(c, {}).get("ausente"))
        err = sum(1 for c in codigos if dados.get(c, {}).get("erro"))
        print(f"{arg}: completos {ok}, ausentes {aus}, erros {err}, em {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
