#!/usr/bin/env python3
"""
Completa dca_detalhes (ISS e cota-parte do ICMS por município e ano) onde o registro está ausente ou incompleto.

Por que existe: a coleta da DCA (workflow collect-dca-municipios) fotografa o SICONFI num dia; municípios que entregam depois, ou que lançam a conta
fora do lugar, ficam sem o ano. No modelo, "sem dado" conta como zero na média histórica (e, em 2025, tira o município da base do ano:
neutro_aproximado), então o coeficiente fica subestimado.

Para cada município x ano x componente ausente (DF fora), tenta nesta ordem, e fica com a primeira fonte plausível:
  1. DCA Anexo I-C consultada de novo (mesmas contas e coluna da coleta original);
  2. RREO Anexo 03, total de janeiro a dezembro (bimestre 6; data/rreo-municipios/ANO-p6.json, complementado aqui por collect-rreo-municipios.py),
     só se os 12 meses vieram preenchidos. Onde DCA e RREO existem, a razão RREO/DCA tem mediana 1,000: é a mesma série oficial;
  3. estimativa pela série do próprio município: média dos anos vizinhos observados (ano-1 e ano+1), cada um levado ao ano pelo crescimento do
     componente na UF entre os dois anos.

Plausibilidade (filtro contra dados aberrantes): o valor de 1 ou 2 só vale se ficar entre 0,5 e 2 vezes o esperado pela série do município
(item 3). Quem entregou poucos meses, ou lançou a conta no lugar errado, cai muito abaixo e passa para a fonte seguinte; o valor descartado fica
registrado em "descartado". Sem vizinho observado não há referência e vale a primeira fonte disponível. Esperados abaixo de R$ 50 mil não filtram
(séries muito pequenas oscilam além da faixa).

Cada componente preenchido leva em "origem" a fonte ("dca", "rreo" ou "estimativa_serie"). Valores já observados não são alterados. Os agregados
(dca_iss_br, dca_iss_es, dca_iss_por_uf, dca_cota_icms_por_uf) recebem apenas o acréscimo do que foi preenchido: os agregados dos anos 2022+ não
coincidem com a soma de dca_detalhes e a validação contra a Nota Técnica v22 depende deles como estão.

Uso (da raiz do repositório):
    python3 data/atualiza-dca-pendentes.py [ANO ...] [--dry]       # padrão: 2019 a 2025
Depois rodar: bash data/rodar-modelo.sh
Parte de reforma-tributaria.json como está; para repetir do zero, restaurar o arquivo (git checkout) antes.
"""
import copy
import importlib.util
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "reforma-tributaria.json"
LIM = (0.5, 2.0)        # faixa aceita para valor / esperado
PISO = 50_000.0         # esperado abaixo disso não filtra
ANOS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
CAMPOS = ("valor", "cota_parte_icms")
TARGET_COL = "Receitas Brutas Realizadas"
CONTAS = {"novo": ("RO1.1.1.4.51.1.0", "RO1.7.2.1.50.0.0"), "antigo": ("RO1.1.1.8.02.3.0", "RO1.7.2.8.01.1.0")}   # PCASP 2022+ / antes


def _coletor():
    spec = importlib.util.spec_from_file_location("collect_rreo", HERE / "collect-rreo-municipios.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


RREO = _coletor()


def dca(cod, ano):
    iss_c, cota_c = CONTAS["novo" if ano >= 2022 else "antigo"]
    d = RREO.buscar(f"https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca?an_exercicio={ano}&co_tipo_demonstrativo=DCA"
                    f"&no_anexo=DCA-Anexo%20I-C&co_esfera=M&id_ente={cod}")
    iss = cota = None
    for it in (d or {}).get("items", []):
        if it.get("coluna") == TARGET_COL:
            if it["cod_conta"] == iss_c:
                iss = it["valor"]
            elif it["cod_conta"] == cota_c:
                cota = it["valor"]
    return {"valor": iss, "cota_parte_icms": cota}


def main():
    dry = "--dry" in sys.argv
    anos = [int(a) for a in sys.argv[1:] if not a.startswith("--")] or ANOS

    ref = json.loads(SRC.read_text(encoding="utf-8"))
    det = ref["dca_detalhes"]
    idx = json.loads((HERE / "painel-municipios" / "index.json").read_text(encoding="utf-8"))["municipios"]
    obs = copy.deepcopy({str(a): det[str(a)] for a in ANOS})        # só o observado, para esperados e índices

    # índice de crescimento do componente: (Σ ano) / (Σ vizinho) nos municípios completos nos dois anos, por UF e no país
    cache = {}

    def indice(uf, campo, y, n):
        k = (uf, campo, y, n)
        if k not in cache:
            def razao(filtro):
                a = b = 0.0
                for c, v in obs[str(y)].items():
                    w = obs[str(n)].get(c)
                    if w and filtro(v) and (v.get(campo) or 0) > 0 and (w.get(campo) or 0) > 0:
                        a += v[campo]; b += w[campo]
                return a / b if b else None
            r = razao(lambda v: v.get("uf") == uf)
            nfloor = sum(1 for c, v in obs[str(y)].items() if v.get("uf") == uf and obs[str(n)].get(c))
            cache[k] = r if (r is not None and nfloor >= 3) else razao(lambda v: True)
        return cache[k]

    def esperado(cod, uf, campo, y):
        v = []
        for n in (y - 1, y + 1):
            if n in ANOS and (obs[str(n)].get(cod) or {}).get(campo):
                f = indice(uf, campo, y, n)
                if f:
                    v.append(obs[str(n)][cod][campo] * f)
        return sum(v) / len(v) if v else None

    relatorio = {}
    delta_iss, delta_cota = {}, {}
    por_ano = {}
    for y in anos:
        s = str(y)
        pend = [c for c in sorted(idx) if any((obs[s].get(c) or {}).get(k) is None for k in CAMPOS)]
        print(f"{y}: {len(pend)} municípios com ISS ou cota-parte ausente", flush=True)
        with ThreadPoolExecutor(max_workers=6) as ex:
            novos = dict(zip(pend, ex.map(lambda c: dca(c, y), pend)))
        # RREO anual dos pendentes (acrescenta ao arquivo ANO-p6.json sem refazer o que já está)
        arq = HERE / "rreo-municipios" / f"{y}-p6.json"
        rreo = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}
        falta = [c for c in pend if c not in rreo or rreo[c].get("erro")]
        if falta:
            with ThreadPoolExecutor(max_workers=6) as ex:
                for c, r in zip(falta, ex.map(lambda c: RREO.coletar(y, 6, c), falta)):
                    rreo[c] = r
            if not dry:
                arq.write_text(json.dumps(rreo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

        cont = {}
        for c in pend:
            uf = idx[c]["uf"]
            reg = det[s].get(c) or {"ente": idx[c]["nome"], "uf": uf}
            org, desc = dict(reg.get("origem") or {}), dict(reg.get("descartado") or {})
            r = rreo.get(c) or {}
            for campo, chave in (("valor", "iss"), ("cota_parte_icms", "cota")):
                if reg.get(campo) is not None:
                    continue
                esp = esperado(c, uf, campo, y)
                rr = r.get(chave) or {}
                rreo_ok = rr.get("total12") is not None and rr.get("meses") and None not in rr["meses"]
                cands = [("dca", novos[c][campo]), ("rreo", rr["total12"] if rreo_ok else None)]
                val = fonte = None
                for f, v in cands:
                    if v is None:
                        continue
                    if esp is None or esp < PISO or LIM[0] <= v / esp <= LIM[1]:
                        val, fonte = v, f
                        break
                    desc.setdefault(campo, []).append({"fonte": f, "valor": v, "esperado": round(esp, 2)})
                if val is None and esp is not None:
                    val, fonte = esp, "estimativa_serie"
                if val is None:
                    continue
                reg[campo] = val
                org[campo] = fonte
                (delta_iss if campo == "valor" else delta_cota).setdefault((s, uf), 0.0)
                (delta_iss if campo == "valor" else delta_cota)[(s, uf)] += val
            if org:
                reg["origem"] = org
            if desc:
                reg["descartado"] = desc
            det[s][c] = reg
            ainda = [k for k in CAMPOS if reg.get(k) is None]
            chave = "+".join(sorted(set(org.values()))) or "sem fonte"
            if ainda:
                chave += " (ainda falta " + "+".join(ainda) + ")"
            if desc:
                chave += " [descartou valor aberrante]"
            cont[chave] = cont.get(chave, 0) + 1
            relatorio.setdefault(s, {})[c] = {"nome": idx[c]["nome"], "uf": uf, "origem": org, "descartado": desc, "ainda_sem": ainda}
        por_ano[s] = cont
        for k, v in sorted(cont.items(), key=lambda kv: -kv[1]):
            print(f"  {v:4d}  {k}")

    # agregados: só o acréscimo do que foi preenchido
    for (s, uf), v in delta_iss.items():
        ref["dca_iss_br"][s] = (ref["dca_iss_br"].get(s) or 0.0) + v
        ref["dca_iss_por_uf"][s][uf] = (ref["dca_iss_por_uf"][s].get(uf) or 0.0) + v
        if uf == "ES":
            ref["dca_iss_es"][s] = (ref["dca_iss_es"].get(s) or 0.0) + v
    for (s, uf), v in delta_cota.items():
        ref["dca_cota_icms_por_uf"][s][uf] = (ref["dca_cota_icms_por_uf"][s].get(uf) or 0.0) + v
    for s in sorted({k[0] for k in list(delta_iss) + list(delta_cota)}):
        print(f"{s}: ISS +R$ {sum(v for (a, _), v in delta_iss.items() if a == s) / 1e6:,.1f} mi; "
              f"cota-parte +R$ {sum(v for (a, _), v in delta_cota.items() if a == s) / 1e6:,.1f} mi")
    if dry:
        return
    SRC.write_text(json.dumps(ref, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "dca-pendentes.json").write_text(json.dumps({"anos": anos, "resumo": por_ano, "municipios": relatorio}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
