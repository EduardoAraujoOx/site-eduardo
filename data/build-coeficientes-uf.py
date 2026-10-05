#!/usr/bin/env python3
"""
Coeficiente de participação de transição do IBS por UF (estado + componente
municipal agregado), replicando em Python a mesma lógica já implementada em
JS na Tabela 3 de estudos/reforma-tributaria-coeficiente.html.

Estado: (ICMS bruto DCA - cota-parte declarada/25% teórico + FECOP) × deflator,
média 2019-2026 (2026 ainda não fechado no DCA: tratamento em data/parametros-cpt-2026.json e data/cpt2026.py;
o campo *_obs_2019_2025 traz a média só dos sete anos observados, igual à Nota Técnica nº 02/2026 da SEFAZ-ES),
dividida pelo agregado nacional A_2025.
Municípios (agregado por UF): (ISS bruto DCA + cota-parte) × deflator, mesma
média e mesmo denominador.
DF: ICMS + FECOP + ISS integrais, sem dedução, sem componente municipal
separado (art. 115, LC 227/2026).

Uso:
  python3 build-coeficientes-uf.py
"""

import json
from pathlib import Path
from fundos_art115b import fold
import cpt2026

HERE = Path(__file__).parent
SRC = HERE / "reforma-tributaria.json"
OUT = HERE / "coeficientes-uf.json"

ANOS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def main():
    with open(SRC) as f:
        d = fold(json.load(f))

    dca_icms_br = d.get("dca_icms_br", {})
    dca_iss_br = d.get("dca_iss_br", {})
    dca_fecop_br = d.get("dca_fecop_br", {})
    dca_transf_uf = d.get("dca_transf_munis_por_uf", {})
    dca_icms_uf = d.get("dca_icms_por_uf", {})
    dca_fecop_uf = d.get("dca_fecop_por_uf", {})
    dca_outras_deducoes_uf = d.get("dca_icms_outras_deducoes_por_uf", {})
    dca_iss_uf_by_ano = {ano: (d.get("dca_iss_por_uf", {}).get(str(ano)) or {}) for ano in ANOS}

    # "Outras Deduções da Receita" do ICMS (DCA Anexo I-C): dedução oficial que o
    # SICONFI já reporta na conta do ICMS, além da cota-parte municipal e do
    # FUNDEB, mas que este pipeline não extraía. Desprezível (<1%) para a
    # maioria das UFs; grande (9%-37% do bruto) para MT/TO/MS/RO/GO, ligada a
    # mecanismos de diferimento/incentivo fiscal do ICMS sobre o agronegócio
    # (ex.: FETHAB/MT, FUNDERSUL/MS). Ver data/collect-dca-outras-deducoes.py.
    outras_ded_total_por_ano = {
        ano: sum((dca_outras_deducoes_uf.get(str(ano), {}) or {}).values())
        for ano in ANOS
    }

    total_br = {}
    for ano in ANOS:
        s = str(ano)
        icms = dca_icms_br.get(s)
        iss = dca_iss_br.get(s)
        fecop = dca_fecop_br.get(s, 0) or 0
        total_br[ano] = (icms - outras_ded_total_por_ano[ano] + iss + fecop) if (
            icms is not None and iss is not None) else None

    total_b = total_br[2025]
    deflators = {ano: (1.0 if ano == 2025 else (total_b / total_br[ano] if total_br[ano] else None))
                 for ano in ANOS}

    ufs = sorted((dca_icms_uf.get("2025") or {}).keys())

    # 2026 (ver cpt2026.py): componentes de 2025 em R$ de 2025 (deflator 1) e fatores por UF
    comp25 = cpt2026.componentes_2025(d)
    fat26, r_renorm = cpt2026.fatores(comp25)
    n_anos = cpt2026.n_anos()

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
            outras_val = (dca_outras_deducoes_uf.get(s) or {}).get(uf, 0) or 0
            if icms_val is not None:
                soma_icms += (icms_val - outras_val) * defl
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

        def medias(div, fi=0.0, fr=0.0, com_2026=False):
            """médias por componente; com_2026 acrescenta o termo estimado de 2026 (fatores fi para ICMS, fr para ISS)."""
            a26 = comp25[uf]
            icms_x = (soma_icms + (((dca_icms_uf.get("2025") or {}).get(uf) or 0) - ((dca_outras_deducoes_uf.get("2025") or {}).get(uf, 0) or 0)) * fi) if com_2026 else soma_icms
            fecop_x = (soma_fecop + ((dca_fecop_uf.get("2025") or {}).get(uf, 0) or 0) * fi) if com_2026 else soma_fecop
            iss_x = (soma_iss + a26["iss"] * fr) if com_2026 else soma_iss
            cota25_alvo = 0.0
            if not is_df:
                cd = (dca_transf_uf.get("2025") or {}).get(uf)
                iu = (dca_icms_uf.get("2025") or {}).get(uf)
                cota25_alvo = cd if cd is not None else (iu * 0.25 if iu is not None else 0.0)
            cota_x = (soma_cota + cota25_alvo * fi) if com_2026 else soma_cota
            m_icms = icms_x / div if n_icms else None
            m_iss = iss_x / div if n_iss else None
            m_fecop = fecop_x / div
            m_cota = cota_x / div if not is_df else None
            if is_df:
                m_estado = (m_icms + m_fecop) if m_icms is not None else None
                m_munis = None
                m_total = (m_estado + (m_iss or 0)) if m_estado is not None else None
            else:
                m_estado = (m_icms - m_cota + m_fecop) if (m_icms is not None and m_cota is not None) else None
                m_munis = ((m_iss or 0) + (m_cota or 0)) if (m_iss is not None or m_cota is not None) else None
                m_total = (m_estado + m_munis) if (m_estado is not None and m_munis is not None) else None
            return m_estado, m_munis, m_total

        fi, fr = fat26[uf]
        media_estado, media_munis, media_total = medias(n_anos, fi, fr, com_2026=(n_anos > len(ANOS)))
        obs_estado, obs_munis, obs_total = medias(len(ANOS))

        pct = lambda x: (x / total_b * 100) if x is not None else None
        resultado[uf] = {
            "is_df": is_df,
            "coeficiente_estado_pct": pct(media_estado),
            "coeficiente_municipios_pct": pct(media_munis),
            "coeficiente_total_pct": pct(media_total),
            "coeficiente_estado_obs_2019_2025_pct": pct(obs_estado),
            "coeficiente_municipios_obs_2019_2025_pct": pct(obs_munis),
            "coeficiente_total_obs_2019_2025_pct": pct(obs_total),
        }

    output = {
        "fonte": "DCA Anexo I-C, agregado por UF",
        "anos": ANOS,
        "tratamento_2026": cpt2026.tratamento(),
        "n_anos_media": n_anos,
        "r_renorm_2026": r_renorm,
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
