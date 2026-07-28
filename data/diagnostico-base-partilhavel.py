#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnostico-base-partilhavel.py

Diagnostica a divergência entre DCA e RREO no ICMS estadual e recalcula os
coeficientes de participação sob dois tratamentos alternativos da base.

Contexto
--------
A conta de ICMS da DCA, em algumas unidades da Federação, registra valor superior
ao do RREO. O teste abaixo mostra que a diferença é explicada pela razão entre a
cota-parte declarada e o ICMS bruto declarado. Onde essa razão cai abaixo dos 25%
constitucionais, a conta de ICMS da DCA está incorporando receita que não integra
a base de partilha municipal.

Identidade verificada (erro inferior a 1% em MT, TO, MS e RO):

    ICMS_DCA x (razao/25) ~= ICMS_RREO

o que implica

    base_partilhavel = cota_parte_declarada / 0,25

Uso
---
    python3 diagnostico-base-partilhavel.py

Entradas   : data/reforma-tributaria.json, data/reconciliacao-dca-rreo.json
Saídas     : data/diagnostico-base-partilhavel.json
             data/coeficientes-uf-cenarios.json
"""

import json
import os

ANOS = [str(a) for a in range(2019, 2026)]
COTA = 0.25
TOL_RAZAO = 0.245          # abaixo disso a razão é considerada anômala
DIR = os.path.join(os.path.dirname(__file__))


def carregar():
    with open(os.path.join(DIR, "reforma-tributaria.json"), encoding="utf-8") as f:
        d = json.load(f)
    rec_path = os.path.join(DIR, "reconciliacao-dca-rreo.json")
    rec = {}
    if os.path.exists(rec_path):
        with open(rec_path, encoding="utf-8") as f:
            rec = json.load(f).get("por_uf_ano", {})
    return d, rec


def get(bloco, ano, uf, padrao=0.0):
    return (bloco.get(ano) or {}).get(uf) or padrao


def diagnosticar(d, rec):
    """Razão cota-parte/ICMS por UF-ano, quebras estruturais e teste contra o RREO."""
    icms = d["dca_icms_por_uf"]
    tr = d.get("dca_transf_munis_por_uf", {})
    ufs = sorted(icms[ANOS[-1]])
    saida = {}

    for uf in ufs:
        linha = {"razao_por_ano": {}, "quebras": [], "teste_rreo": {}}
        anterior = None
        for a in ANOS:
            ic = get(icms, a, uf)
            cp = get(tr, a, uf)
            if not ic or not cp:
                linha["razao_por_ano"][a] = None
                continue
            r = cp / ic
            linha["razao_por_ano"][a] = round(r * 100, 2)

            # quebra estrutural: salto de mais de 2 p.p. na razão
            if anterior is not None and abs(r - anterior) > 0.02:
                linha["quebras"].append({"ano": a,
                                         "razao_anterior": round(anterior * 100, 2),
                                         "razao": round(r * 100, 2)})
            anterior = r

            # teste contra o RREO
            rr = (rec.get(uf, {}).get(a) or {}).get("icms_bruto_rreo")
            if rr:
                ajustado = ic * (r / COTA)
                linha["teste_rreo"][a] = {
                    "icms_dca": ic,
                    "icms_rreo": rr,
                    "icms_dca_ajustado": ajustado,
                    "erro_pct": round((ajustado / rr - 1) * 100, 2),
                    "divergencia_bruta_pct": round((ic / rr - 1) * 100, 2),
                }

        razoes = [v for v in linha["razao_por_ano"].values() if v]
        linha["razao_media"] = round(sum(razoes) / len(razoes), 2) if razoes else None
        linha["anomala"] = bool(linha["razao_media"] and linha["razao_media"] < TOL_RAZAO * 100)
        saida[uf] = linha

    return saida


def coeficientes(d, ajustar):
    """Coeficiente por UF. Se ajustar=True, substitui o ICMS pela base partilhável."""
    icms = d["dca_icms_por_uf"]
    iss = d.get("dca_iss_por_uf", {})
    fec = d.get("dca_fecop_por_uf", {})
    tr = d.get("dca_transf_munis_por_uf", {})
    ufs = sorted(icms[ANOS[-1]])
    acumulado = {uf: 0.0 for uf in ufs}

    for a in ANOS:
        valores, total = {}, 0.0
        for uf in ufs:
            ic = get(icms, a, uf)
            cp = get(tr, a, uf, None)
            if ajustar and cp and ic and 0 < cp / ic < TOL_RAZAO:
                ic = cp / COTA                      # base partilhável implícita
            receita = ic + get(fec, a, uf) + get(iss, a, uf)
            valores[uf] = receita
            total += receita
        for uf in ufs:
            acumulado[uf] += valores[uf] / total * 100 / len(ANOS)

    return acumulado


def main():
    d, rec = carregar()

    diag = diagnosticar(d, rec)
    anomalas = sorted([uf for uf, v in diag.items() if v["anomala"]])
    print("UFs com razao cota-parte/ICMS anomala: %s" % ", ".join(anomalas))

    a = coeficientes(d, ajustar=False)
    b = coeficientes(d, ajustar=True)
    cen = {uf: {"cenario_a_dca_integral": round(a[uf], 4),
                "cenario_b_base_partilhavel": round(b[uf], 4),
                "delta_pp": round(a[uf] - b[uf], 4),
                "anomala": diag[uf]["anomala"]}
           for uf in a}

    print("\nMaiores deltas entre cenarios:")
    for uf in sorted(cen, key=lambda u: -abs(cen[u]["delta_pp"]))[:8]:
        c = cen[uf]
        print("  %s  A=%8.4f  B=%8.4f  delta=%+7.4f" %
              (uf, c["cenario_a_dca_integral"], c["cenario_b_base_partilhavel"], c["delta_pp"]))
    print("\nsoma A = %.4f | soma B = %.4f" % (sum(a.values()), sum(b.values())))

    with open(os.path.join(DIR, "diagnostico-base-partilhavel.json"), "w", encoding="utf-8") as f:
        json.dump({"metodo": "razao cota-parte/ICMS; base partilhavel = cota_parte/0,25",
                   "tolerancia_razao": TOL_RAZAO, "por_uf": diag}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DIR, "coeficientes-uf-cenarios.json"), "w", encoding="utf-8") as f:
        json.dump({"cenario_a": "conta de ICMS da DCA como declarada",
                   "cenario_b": "ICMS substituido pela base partilhavel implicita onde a razao e anomala",
                   "por_uf": cen}, f, ensure_ascii=False, indent=2)
    print("\nArquivos gravados em data/.")


if __name__ == "__main__":
    main()
