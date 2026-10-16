#!/usr/bin/env python3
"""
Completa o ano-base (padrão 2025) de dca_detalhes para os municípios que não têm ISS ou cota-parte do ICMS no registro.

Por que existe: a coleta da DCA (workflow collect-dca-municipios) fotografa o SICONFI num dia; municípios que entregam a DCA depois
ficam sem o ano. No modelo, "sem dado em 2025" conta como zero na média histórica e tira o município da base de 2025
(neutro_aproximado), então o coeficiente fica subestimado.

Para cada município pendente (portal: data/painel-municipios/index.json; DF fora), em ordem:
  1. DCA Anexo I-C reconsultada agora (mesma conta e coluna da coleta original);
  2. RREO Anexo 03, total de janeiro a dezembro (data/rreo-municipios/ANO-p6.json, de collect-rreo-municipios.py), só se os 12 meses vieram
     preenchidos. Onde DCA e RREO existem, a razão RREO/DCA tem mediana 1,000 (p10 0,996 no ISS; 1,000 na cota-parte): é a mesma série oficial;
  3. DCA do ano anterior x crescimento do estado entre os dois anos (média dos municípios com dado completo nos dois anos): estimativa, só
     onde nenhuma fonte de ANO existe.

Em 1 e 2, o valor só vale se ficar entre 0,5 e 2 vezes o do ano anterior corrigido pelo crescimento do estado (LIM): quem entregou poucos meses, ou
lançou a conta fora do lugar, cai muito abaixo disso e passa para a fonte seguinte.

Cada componente preenchido leva em "origem" a sua fonte ("dca", "rreo" ou "estimativa_ano_anterior"). Os agregados (dca_iss_br, dca_iss_es,
dca_iss_por_uf, dca_cota_icms_por_uf) recebem apenas o acréscimo do que foi preenchido, para não mexer em nada do que já estava (os agregados dos anos
2022+ não coincidem com a soma de dca_detalhes e a validação contra a Nota Técnica v22 depende deles como estão).

Uso (da raiz do repositório):
    python3 data/atualiza-dca-pendentes.py [ANO] [--dry]
Depois rodar: bash data/rodar-modelo.sh
"""
import json
import ssl
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "reforma-tributaria.json"
BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
TARGET_COL = "Receitas Brutas Realizadas"
LIM = (0.5, 2.0)   # faixa aceita para valor / (ano anterior x crescimento do estado)
ISS_COD_NEW, COTA_COD_NEW = "RO1.1.1.4.51.1.0", "RO1.7.2.1.50.0.0"   # PCASP 2022+ (como na coleta original)


def contexto_ssl():
    p = Path("/root/.ccr/ca-bundle.crt")
    return ssl.create_default_context(cafile=str(p)) if p.exists() else ssl.create_default_context()


CTX = contexto_ssl()


def buscar(url, tentativas=4):
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(url, timeout=60, context=CTX) as r:
                return json.loads(r.read())
        except Exception:
            if i < tentativas - 1:
                time.sleep(2 ** i)
    return None


def dca(cod, ano):
    d = buscar(f"{BASE}/dca?an_exercicio={ano}&co_tipo_demonstrativo=DCA&no_anexo=DCA-Anexo%20I-C&co_esfera=M&id_ente={cod}")
    iss = cota = None
    for it in (d or {}).get("items", []):
        if it.get("coluna") == TARGET_COL:
            if it["cod_conta"] == ISS_COD_NEW:
                iss = it["valor"]
            elif it["cod_conta"] == COTA_COD_NEW:
                cota = it["valor"]
    return iss, cota


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    ano = int(args[0]) if args else 2025
    s, s0 = str(ano), str(ano - 1)

    ref = json.loads(SRC.read_text(encoding="utf-8"))
    det, det0 = ref["dca_detalhes"][s], ref["dca_detalhes"][s0]
    idx = json.loads((HERE / "painel-municipios" / "index.json").read_text(encoding="utf-8"))["municipios"]
    rreo_arq = HERE / "rreo-municipios" / f"{ano}-p6.json"
    rreo = json.loads(rreo_arq.read_text(encoding="utf-8")) if rreo_arq.exists() else {}

    pend = [c for c in sorted(idx) if (det.get(c) or {}).get("valor") is None or (det.get(c) or {}).get("cota_parte_icms") is None]
    print(f"{ano}: {len(pend)} municípios com ISS ou cota-parte ausente em dca_detalhes", flush=True)
    with ThreadPoolExecutor(max_workers=6) as ex:
        novos = dict(zip(pend, ex.map(lambda c: dca(c, ano), pend)))

    # crescimento por UF (ano-1 -> ano) com os municípios completos nos dois anos, antes de qualquer preenchimento
    cresc = {}
    for c, v in det.items():
        w = det0.get(c)
        if w and None not in (v.get("valor"), v.get("cota_parte_icms"), w.get("valor"), w.get("cota_parte_icms")) and w["valor"] > 0 and w["cota_parte_icms"] > 0:
            a = cresc.setdefault(v["uf"], [0.0, 0.0, 0.0, 0.0])
            a[0] += v["valor"]; a[1] += w["valor"]; a[2] += v["cota_parte_icms"]; a[3] += w["cota_parte_icms"]
    g = {u: (a[0] / a[1], a[2] / a[3]) for u, a in cresc.items()}

    delta_iss, delta_cota = {}, {}
    rel = {}
    for c in pend:
        uf = idx[c]["uf"]
        reg = det.get(c) or {"ente": idx[c]["nome"], "uf": uf}
        ant = det0.get(c) or {}
        r = rreo.get(c) or {}
        org = dict(reg.get("origem") or {})
        iss_d, cota_d = novos[c]
        for campo, d_novo, chave_r, gi in (("valor", iss_d, "iss", 0), ("cota_parte_icms", cota_d, "cota", 1)):
            if reg.get(campo) is not None:
                continue
            esperado = ant[campo] * g[uf][gi] if (ant.get(campo) and uf in g) else None
            rr = r.get(chave_r) or {}
            rreo_ok = rr.get("total12") is not None and rr.get("meses") and None not in rr["meses"]   # só RREO com os 12 meses entregues

            def plausivel(v):
                # valor parcial (poucos meses, ou conta fora do lugar) cai muito abaixo do ano anterior corrigido pelo estado
                return esperado is None or (v is not None and LIM[0] <= v / esperado <= LIM[1])
            if d_novo is not None and plausivel(d_novo):
                val, o = d_novo, "dca"
            elif rreo_ok and plausivel(rr["total12"]):
                val, o = rr["total12"], "rreo"
            elif esperado is not None:
                val, o = esperado, "estimativa_ano_anterior"
            else:
                continue
            reg[campo] = val
            org[campo] = o
            if campo == "valor":
                delta_iss[uf] = delta_iss.get(uf, 0.0) + val
            else:
                delta_cota[uf] = delta_cota.get(uf, 0.0) + val
        if org:
            reg["origem"] = org
        det[c] = reg
        rel[c] = {"nome": idx[c]["nome"], "uf": uf, "origem": org, "ainda_sem": [k for k in ("valor", "cota_parte_icms") if reg.get(k) is None]}

    # agregados: só o acréscimo do que foi preenchido
    tot_iss = sum(delta_iss.values())
    ref["dca_iss_br"][s] = (ref["dca_iss_br"].get(s) or 0.0) + tot_iss
    for uf, v in delta_iss.items():
        ref["dca_iss_por_uf"][s][uf] = (ref["dca_iss_por_uf"][s].get(uf) or 0.0) + v
    if "ES" in delta_iss:
        ref["dca_iss_es"][s] = (ref["dca_iss_es"].get(s) or 0.0) + delta_iss["ES"]
    for uf, v in delta_cota.items():
        ref["dca_cota_icms_por_uf"][s][uf] = (ref["dca_cota_icms_por_uf"][s].get(uf) or 0.0) + v

    cont = {}
    for c, x in rel.items():
        if not x["origem"]:
            k = "sem fonte"
        else:
            k = "+".join(sorted(set(x["origem"].values())))
        if x["ainda_sem"]:
            k += " (ainda falta " + "+".join(x["ainda_sem"]) + ")"
        cont[k] = cont.get(k, 0) + 1
    for k, v in sorted(cont.items(), key=lambda kv: -kv[1]):
        print(f"  {v:4d}  {k}")
    print(f"acréscimo ao ISS nacional de {ano}: R$ {tot_iss / 1e6:,.1f} mi; à cota-parte: R$ {sum(delta_cota.values()) / 1e6:,.1f} mi")
    if dry:
        return
    SRC.write_text(json.dumps(ref, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / f"dca-pendentes-{ano}.json").write_text(json.dumps(
        {"ano": ano, "resumo": cont, "acrescimo_iss": tot_iss, "acrescimo_cota": sum(delta_cota.values()), "municipios": rel},
        ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
