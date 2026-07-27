#!/usr/bin/env python3
"""
Coeficiente de participação de transição do IBS por UF (estado + componente
municipal agregado), replicando em Python a mesma lógica já implementada em
JS na Tabela 3 de estudos/reforma-tributaria-coeficiente.html.

Estado: (ICMS bruto DCA - cota-parte declarada/25% teórico + FECOP) × deflator,
média 2019-2025, dividida pelo agregado nacional A_2025.
Municípios (agregado por UF): (ISS bruto DCA + cota-parte) × deflator, mesma
média e mesmo denominador.
DF: ICMS + FECOP + ISS integrais, sem dedução, sem componente municipal
separado (art. 115, LC 227/2026).

Uso:
  python3 build-coeficientes-uf.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "reforma-tributaria.json"
OUT = HERE / "coeficientes-uf.json"

ANOS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def main():
    with open(SRC) as f:
        d = json.load(f)

    dca_icms_br = d.get("dca_icms_br", {})
    dca_iss_br = d.get("dca_iss_br", {})
    dca_fecop_br = d.get("dca_fecop_br", {})
    dca_transf_uf = d.get("dca_transf_munis_por_uf", {})
    dca_icms_uf = d.get("dca_icms_por_uf", {})
    dca_fecop_uf = d.get("dca_fecop_por_uf", {})
    dca_iss_uf_by_ano = {ano: (d.get("dca_iss_por_uf", {}).get(str(ano)) or {}) for ano in ANOS}

    total_br = {}
    for ano in ANOS:
        s = str(ano)
        icms = dca_icms_br.get(s)
        iss = dca_iss_br.get(s)
        fecop = dca_fecop_br.get(s, 0) or 0
        total_br[ano] = (icms + iss + fecop) if (icms is not None and iss is not None) else None

    total_b = total_br[2025]
    deflators = {ano: (1.0 if ano == 2025 else (total_b / total_br[ano] if total_br[ano] else None))
                 for ano in ANOS}

    ufs = sorted((dca_icms_uf.get("2025") or {}).keys())

    resultado = {}
    for uf in ufs:
        is_df = uf == "DF"
        soma_icms = soma_iss = soma_fecop = soma_cota = 0.0
        n_icms = n_iss = 0
        for ano in ANOS:
            s = str(ano)
            defl = deflators[ano]
            if defl is None:
                continue
            icms_val = (dca_icms_uf.get(s) or {}).get(uf)
            iss_val = dca_iss_uf_by_ano[ano].get(uf)
            fecop_val = (dca_fecop_uf.get(s) or {}).get(uf, 0) or 0
            if icms_val is not None:
                soma_icms += icms_val * defl
                n_icms += 1
            if iss_val is not None:
                soma_iss += iss_val * defl
                n_iss += 1
            soma_fecop += fecop_val * defl
            if not is_df:
                cota_declarada = (dca_transf_uf.get(s) or {}).get(uf)
                cota_val = cota_declarada if cota_declarada is not None else (
                    icms_val * 0.25 if icms_val is not None else None)
                if cota_val is not None:
                    soma_cota += cota_val * defl

        media_icms = soma_icms / len(ANOS) if n_icms else None
        media_iss = soma_iss / len(ANOS) if n_iss else None
        media_fecop = soma_fecop / len(ANOS)
        media_cota = soma_cota / len(ANOS) if not is_df else None

        if is_df:
            media_estado = (media_icms + media_fecop) if media_icms is not None else None
            media_munis = None
            media_total = (media_estado + (media_iss or 0)) if media_estado is not None else None
        else:
            media_estado = (media_icms - media_cota + media_fecop) if (
                media_icms is not None and media_cota is not None) else None
            media_munis = ((media_iss or 0) + (media_cota or 0)) if (
                media_iss is not None or media_cota is not None) else None
            media_total = (media_estado + media_munis) if (
                media_estado is not None and media_munis is not None) else None

        resultado[uf] = {
            "is_df": is_df,
            "coeficiente_estado_pct": (media_estado / total_b * 100) if media_estado is not None else None,
            "coeficiente_municipios_pct": (media_munis / total_b * 100) if media_munis is not None else None,
            "coeficiente_total_pct": (media_total / total_b * 100) if media_total is not None else None,
        }
        if is_df:
            resultado[uf]["nota"] = (
                "DF é ente único (art. 115, II, LC 227/2026): coeficiente_estado_pct aqui é só a "
                "parcela ICMS+FECOP, NÃO o coeficiente unificado do DF -- use coeficiente_total_pct "
                "(ICMS+FECOP+ISS) para fechamento nacional e qualquer comparação com as demais UFs. "
                "coeficiente_municipios_pct é null porque o DF não tem repasse municipal separado."
            )

    output = {
        "fonte": "DCA Anexo I-C, agregado por UF",
        "anos": ANOS,
        "total_br_2025": total_b,
        "por_uf": resultado,
        "soma_coeficiente_total_pct": sum(
            r["coeficiente_total_pct"] for r in resultado.values() if r["coeficiente_total_pct"] is not None
        ),
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {OUT}")
    print(f"Soma coeficiente total (deve ~100%): {output['soma_coeficiente_total_pct']:.4f}%")


if __name__ == "__main__":
    main()
