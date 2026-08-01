#!/usr/bin/env python3
"""
Estudo 11: série histórica e projeção do IBS total (Brasil), 2029-2033.

Combina:
  - o "bolo" histórico ICMS+ISS+FECOP (SICONFI), todo em base DCA Anexo I-C:
    dca_icms_por_uf (2019-2025, já coletado) mesclado com
    data/icms-dca-2013-2018.json (2013-2018, ver
    data/collect-icms-dca-2013-2018.py — substitui o RREO Anexo 3 usado
    antes para 2015-2018, validado como equivalente, diff < 1%, ver
    data/build-reconciliacao-dca-rreo.py); dca_iss_por_uf (2015-2025)
    mesclado com data/iss-dca-2013-2014.json (2013-2014, ver
    data/collect-iss-dca-2013-2014.py). SICONFI não tem cobertura DCA
    antes de 2013. FECOP (Fundo de Combate à Pobreza) usa DCA
    (dca_fecop_br) para 2019-2025 — mesma fonte e mesma base usada em
    data/build-coeficientes-uf.py para o coeficiente estadual validado
    contra a Nota Técnica nº 02/2026; não há FECOP coletado para
    2013-2018, tratado como zero nesses anos;
  - a trajetória de PIB nominal 2026-2033, construída a partir do PIB
    nominal de 2025 (BCB/SGS) composto pelas medianas do Boletim Focus
    (2026-2030) e pelas projeções da IFI/RAF 107 (2031-2033), ver
    data/macro-parametros.json;
  - a premissa de que o bolo ICMS+ISS cresce na mesma proporção do PIB
    nominal a partir de 2027 (razão bolo/PIB constante na média de
    2024-2026) — o período de referência definido pelos arts. 361 a 365
    da LC 214/2025 (redação da LC 227/2026) para a fixação da alíquota
    de referência do IBS em cada ano da transição (2029-2033): a média
    da razão entre a receita de referência (ICMS+ISS) e o PIB nos anos
    de 2024 a 2026, não apenas o último ano fechado;
  - o cronograma constitucional de transição ICMS/ISS → IBS (ADCT arts.
    128 e 131, LC 227/2026), replicando exatamente os parâmetros fa/sa já
    usados no Estudo 06 (estudos/ibs-projecao-arrecadacao-br.html).

No agregado nacional, o valor TOTAL de IBS não depende dos coeficientes de
redistribuição por UF (φ^neutro, φ^CPT, φ^dest) nem da fração α_a
(histórico vs. destino) usados no Estudo 06 — esses parâmetros só
determinam COMO o bolo é dividido entre entes, não o seu tamanho total.
Por isso a fórmula nacional se reduz a:

  ICMS+ISS residual(a) = bolo_projetado(a) × fa
  IBS bruto(a)          = bolo_projetado(a) × sa
  Total(a)               = bolo_projetado(a)          [fa + sa = 1, por construção]

"IBS bruto" aqui é a arrecadação total antes das deduções do CGIBS e do
Seguro-Receita (ADCT arts. 51 LC 227/2026 e 132 ADCT), que incidem sobre a
parcela distribuída aos entes pelo critério destino — não reduzem o total
nacional, apenas a fatia que cada estado/município recebe líquida (ver
Estudo 06 para a decomposição por UF).

Uso: python3 build-ibs-projecao-nacional.py
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent
OUTPUT = DATA_DIR / "ibs-projecao-nacional.json"

ANO_HIST_INICIO = 2013
ANO_HIST_FIM = 2025
ANO_BASE = 2025

# Mesmo cronograma do Estudo 06 (estudos/ibs-projecao-arrecadacao-br.html),
# derivado do ADCT arts. 128 e 131 (EC 132/2023) e LC 227/2026.
ADCT = {
    2029: {"fa": 0.9, "sa": 0.10},
    2030: {"fa": 0.8, "sa": 0.20},
    2031: {"fa": 0.7, "sa": 0.30},
    2032: {"fa": 0.6, "sa": 0.40},
    2033: {"fa": 0.0, "sa": 1.00},
}
ANOS_PROJ = [2029, 2030, 2031, 2032, 2033]


def main():
    ref = json.load(open(DATA_DIR / "reforma-tributaria.json"))
    macro = json.load(open(DATA_DIR / "macro-parametros.json"))

    dca_icms_por_uf = dict(ref["dca_icms_por_uf"])
    dca_iss_por_uf = dict(ref["dca_iss_por_uf"])
    dca_fecop_br = ref.get("dca_fecop_br", {})

    icms_dca_2013_2018 = json.load(open(DATA_DIR / "icms-dca-2013-2018.json"))
    iss_dca_2013_2014 = json.load(open(DATA_DIR / "iss-dca-2013-2014.json"))["dca_iss_por_uf"]
    dca_icms_por_uf.update(icms_dca_2013_2018)
    dca_iss_por_uf.update(iss_dca_2013_2014)

    # ── Bolo histórico ICMS+ISS+FECOP, 2013-2025 (100% base DCA Anexo I-C) ──
    historico = []
    for y in range(ANO_HIST_INICIO, ANO_HIST_FIM + 1):
        ys = str(y)
        icms = sum(dca_icms_por_uf[ys].values())
        fonte_icms = "DCA"
        iss = sum(dca_iss_por_uf.get(ys, {}).values())
        fecop = dca_fecop_br.get(ys, 0) or 0
        bolo = icms + iss + fecop
        pib = macro["pib_nominal_historico"][ys]
        deflator = macro["deflator_ipca_para_2025"][ys]
        historico.append({
            "ano": y,
            "icms": round(icms, 2),
            "iss": round(iss, 2),
            "fecop": round(fecop, 2),
            "bolo_nominal": round(bolo, 2),
            "bolo_real_2025": round(bolo * deflator, 2),
            "pib_nominal": round(pib, 2),
            "bolo_pct_pib": round(bolo / pib * 100, 4),
            "fonte_icms": fonte_icms,
        })

    bolo_2025 = next(h["bolo_nominal"] for h in historico if h["ano"] == ANO_BASE)
    pib_2025 = macro["pib_nominal_historico"][str(ANO_BASE)]

    ratios = [h["bolo_pct_pib"] for h in historico if h["ano"] >= 2019]
    faixa_historica = {"min": round(min(ratios), 4), "max": round(max(ratios), 4)}

    # ── Trajetória de PIB nominal, 2026-2033 (Focus + IFI) ──
    focus = macro["projecao_2026_2030_focus"]
    ifi = macro["projecao_2031_2033_ifi"]

    pib_nom = {ANO_BASE: pib_2025}
    macro_path = []
    for y in range(2026, 2034):
        ys = str(y)
        if ys in focus:
            g = focus[ys]["pib_real_pct"]
            infl = focus[ys]["ipca_pct"]
            fonte = "Focus (BCB), mediana"
        else:
            g = ifi[ys]["pib_real_pct"]
            infl = ifi[ys]["ipca_pct"]
            fonte = "IFI, RAF 107 (dez/2025)"
        pib_nom[y] = pib_nom[y - 1] * (1 + g) * (1 + infl)
        macro_path.append({
            "ano": y,
            "pib_real_pct": round(g, 4),
            "ipca_pct": round(infl, 4),
            "pib_nominal_pct_crescimento": round((1 + g) * (1 + infl) - 1, 4),
            "pib_nominal": round(pib_nom[y], 2),
            "fonte": fonte,
        })

    # ── Receita de referência: média da razão bolo/PIB em 2024-2026 ──
    # Arts. 361 a 365 da LC 214/2025 (redação da LC 227/2026) fixam a
    # alíquota de referência do IBS, em cada ano da transição, de forma a
    # equivaler à média da razão entre a receita de referência (ICMS+ISS)
    # e o PIB nos anos de 2024 a 2026 — não apenas o último ano fechado.
    # 2026 ainda não fechou: usa-se o bolo RREO (últimos 12 meses até
    # abr/2026, ref.py) sobre o PIB projetado de 2026 (Focus) como
    # estimativa preliminar, a ser substituída pelo dado fechado (DCA)
    # quando disponível.
    bolo_2024 = next(h["bolo_nominal"] for h in historico if h["ano"] == 2024)
    pib_2024 = macro["pib_nominal_historico"]["2024"]
    # FECOP de 2026 ainda não fechou na DCA; usa-se o valor de 2025 como estimativa
    # preliminar (mesma lógica de "carregar o último dado fechado" já aplicada ao
    # ICMS/ISS de 2026 via RREO). Repor por dado fechado quando a DCA de 2026 sair.
    fecop_2026_est = dca_fecop_br.get(str(ANO_BASE), 0) or 0
    bolo_2026_est = ref["icms_br"]["2026"] + ref["iss_br"]["2026"] + fecop_2026_est
    pib_2026_est = pib_nom[2026]

    ratio_2024 = bolo_2024 / pib_2024
    ratio_2025 = bolo_2025 / pib_2025
    ratio_2026 = bolo_2026_est / pib_2026_est
    razao_referencia = (ratio_2024 + ratio_2025 + ratio_2026) / 3

    receita_referencia = {
        "anos": [
            {"ano": 2024, "bolo": round(bolo_2024, 2), "pib": round(pib_2024, 2), "razao_pct": round(ratio_2024 * 100, 4), "status": "fechado (DCA)"},
            {"ano": 2025, "bolo": round(bolo_2025, 2), "pib": round(pib_2025, 2), "razao_pct": round(ratio_2025 * 100, 4), "status": "fechado (DCA)"},
            {"ano": 2026, "bolo": round(bolo_2026_est, 2), "pib": round(pib_2026_est, 2), "razao_pct": round(ratio_2026 * 100, 4), "status": "estimativa preliminar (RREO 12m + PIB Focus)"},
        ],
        "razao_media_pct": round(razao_referencia * 100, 4),
    }

    # ── Bolo projetado (razão bolo/PIB constante na média 2024-2026) e decomposição ADCT ──
    projecao = []
    for a in ANOS_PROJ:
        bolo_a = razao_referencia * pib_nom[a]
        fa, sa = ADCT[a]["fa"], ADCT[a]["sa"]
        icms_iss_residual = bolo_a * fa
        ibs_bruto = bolo_a * sa
        projecao.append({
            "ano": a,
            "bolo_projetado": round(bolo_a, 2),
            "pib_nominal": round(pib_nom[a], 2),
            "bolo_pct_pib": round(bolo_a / pib_nom[a] * 100, 4),
            "fa": fa,
            "sa": sa,
            "icms_iss_residual": round(icms_iss_residual, 2),
            "ibs_bruto": round(ibs_bruto, 2),
        })

    output = {
        "_meta": {
            "descricao": "Estudo 11: série histórica (2013-2025) e projeção do IBS total (Brasil), 2029-2033.",
            "ano_base": ANO_BASE,
            "razao_bolo_pib_base": round(razao_referencia * 100, 4),
            "receita_referencia": receita_referencia,
            "faixa_historica_razao_2019_2025": faixa_historica,
            "fontes": {
                "icms_2013_2025": "SICONFI/STN, DCA Anexo I-C, todos os estados e o DF",
                "iss_2013_2025": "SICONFI/STN, DCA Anexo I-C, todos os municípios",
                "fecop_2019_2025": "SICONFI/STN, DCA Anexo I-C (dca_fecop_br); zero em 2013-2018 (sem coleta); 2026 usa o valor de 2025 como estimativa preliminar",
                "pib_ipca_historico": "BCB/SGS séries 1207 (PIB nominal) e 433 (IPCA)",
                "projecao_macro_2026_2030": "BCB, Boletim Focus (Sistema de Expectativas de Mercado), mediana",
                "projecao_macro_2031_2033": "IFI (Instituição Fiscal Independente, Senado Federal), RAF 107, 18/dez/2025",
                "cronograma_adct": "ADCT art. 128 (extinção do ICMS/ISS) e art. 131 (implementação do IBS), EC 132/2023, e LC 227/2026",
                "periodo_referencia_aliquota": "LC 214/2025, arts. 361 a 365 (redação da LC 227/2026): média da razão receita de referência/PIB nos anos de 2024 a 2026",
            },
            "data_pesquisa_focus": macro["_meta"]["data_pesquisa_focus"],
            "premissas": [
                "Razão bolo (ICMS+ISS+FECOP) / PIB nominal mantida constante na média de 2024-2026 a partir de 2027. Esse período de referência não é uma escolha de modelagem: é o que os arts. 361 a 365 da LC 214/2025 (redação da LC 227/2026) usam para calibrar a alíquota de referência do IBS em cada ano da transição (2029-2033), a média da razão entre a receita de referência e o PIB nos anos de 2024 a 2026, fixada por resolução do Senado Federal. O FECOP (Fundo de Combate à Pobreza) é incluído na receita de referência porque a legislação da reforma o trata como parte da base de receita substituída pelo IBS nos estados que o cobram; sem essa parcela, a receita de referência ficaria subestimada em cerca de R$ 14 bi em 2025 (~1,4% do total) frente ao dataset validado de coeficientes por UF (data/coeficientes-uf.json, conferido contra a Nota Técnica nº 02/2026).",
                "O art. 130, §4º e §5º, do ADCT define um mecanismo distinto: o 'Teto de Referência', que compara a média 2029-2033 de CBS+Imposto Seletivo+IBS com a média 2012-2021 de IPI+ICMS+ISS+PIS/Cofins+IOF-seguros. Não altera os valores projetados aqui: mesmo se ultrapassado, a redução da alíquota só vale a partir de 2035 (fora desta projeção), e o teto exige dados federais (CBS, PIS/Cofins, IPI, IOF-seguros) fora do escopo deste estudo, que modela só o lado subnacional (ICMS/ISS/IBS).",
                "2026 ainda não fechou: a razão desse ano usa o bolo do RREO (últimos 12 meses até abr/2026) sobre o PIB projetado pelo Focus, uma estimativa preliminar a ser substituída pelo dado fechado (DCA) quando disponível.",
                "IBS bruto = bolo projetado × sa (fração já migrada para IBS no ADCT). Não inclui a dedução do CGIBS nem a retenção do Seguro-Receita (ADCT art. 132), que incidem sobre a parcela distribuída aos entes pelo critério destino, não sobre o total nacional arrecadado.",
                "Para 2031-2033, fora do horizonte do Boletim Focus (~5 anos), usa-se a projeção da IFI (2,2% a.a. real, IPCA convergindo a 3,0%), constante para os três anos por simplificação, já que a IFI não detalha ano a ano dentro do intervalo 2027-2035.",
            ],
        },
        "historico": historico,
        "macro_path": macro_path,
        "projecao": projecao,
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Gravado em {OUTPUT}")
    print(f"\nReceita de referência (média 2024-2026): {razao_referencia*100:.2f}% do PIB")
    print(f"  2024: {ratio_2024*100:.2f}% | 2025: {ratio_2025*100:.2f}% | 2026 (est.): {ratio_2026*100:.2f}%")
    print("\n=== Projeção IBS 2029-2033 ===")
    for p in projecao:
        print(f"{p['ano']}: bolo R$ {p['bolo_projetado']/1e9:.1f}B | "
              f"ICMS+ISS residual R$ {p['icms_iss_residual']/1e9:.1f}B | "
              f"IBS bruto R$ {p['ibs_bruto']/1e9:.1f}B")


if __name__ == "__main__":
    main()
