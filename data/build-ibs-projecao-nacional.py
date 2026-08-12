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
  - a trajetória de PIB real 2026-2033, construída a partir do PIB nominal
    de 2025 (BCB/SGS, ano-base, coincide com seu próprio valor real) e
    composta só pela taxa de crescimento REAL do Boletim Focus (2026-2030)
    e da IFI/RAF 107 (2031-2033) -- sem compor o IPCA projetado. A partir
    de ago/2026, todos os valores de "projecao" e "macro_path" estão em
    R$ constantes de 2025, não em R$ nominais de cada ano futuro: dado o
    horizonte de até 50 anos deste estudo (ver extensão de longo prazo),
    comparar R$ nominais entre anos distantes exigiria o leitor deflacionar
    mentalmente antes de interpretar qualquer variação. A série histórica
    (2013-2025) permanece nominal (é dado observado, não projeção) mas tem
    a coluna bolo_real_2025 para comparação na mesma base. O IPCA projetado
    (Focus/IFI) continua registrado em macro_path para referência, mas não
    é mais aplicado ao crescimento da base; ver data/macro-parametros.json;
  - a premissa de que o bolo ICMS+ISS cresce na mesma proporção do PIB
    a partir de 2027 (razão bolo/PIB constante na média de
    2024-2026) — o período de referência definido pelos arts. 361 a 365
    da LC 214/2025 (redação da LC 227/2026) para a fixação da alíquota
    de referência do IBS em cada ano da transição (2029-2033): a média
    da razão entre a receita de referência (ICMS+ISS) e o PIB nos anos
    de 2024 a 2026, não apenas o último ano fechado;
  - o cronograma constitucional de transição ICMS/ISS → IBS (ADCT arts.
    128 e 131, LC 227/2026), replicando exatamente os parâmetros fa/sa já
    usados no Estudo 06 (estudos/ibs-projecao-arrecadacao-br.html).

No agregado nacional, o valor TOTAL de IBS não depende dos coeficientes de
redistribuição por UF (φ^neutro, φ^CPT, φ^dest) usados no Estudo 06 —
esses parâmetros só determinam COMO o bolo é dividido entre entes, não o
seu tamanho total. Por isso a fórmula nacional se reduz a:

  ICMS+ISS residual(a) = bolo_projetado(a) × fa
  IBS bruto(a)          = bolo_projetado(a) × sa
  Total(a)               = bolo_projetado(a)          [fa + sa = 1, por construção]

"IBS bruto" aqui é a arrecadação total antes das deduções do CGIBS e do
Seguro-Receita. Diferente dos φ (que só redistribuem entre entes, sem
afetar o total nacional), a fração α_a (histórico vs. destino) e as taxas
de CGIBS/Seguro-Receita AFETAM o total nacional que efetivamente chega
aos entes, porque essas duas deduções incidem só sobre a parcela destino
— por isso são detalhadas à parte, na decomposição de IBS bruto em
quatro categorias (ver "ibs_historico"/"ibs_destino_liquido"/
"ibs_seguro_receita"/"ibs_cgibs" em cada ano de "projecao", e a Seção 4
da metodologia na página). Os parâmetros α_a e c_a (CGIBS) usados aqui
são os mesmos já publicados no Estudo 06
(estudos/ibs-projecao-arrecadacao-br.html).

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

# Como o IBS bruto de cada ano se divide entre os critérios de distribuição
# e as duas retenções que incidem só sobre a parcela destino. Mesmos valores
# já publicados no Estudo 06 (estudos/ibs-projecao-arrecadacao-br.html):
# alpha_a = fração do IBS distribuída pelo critério histórico (IBSt); a
# parcela (1-alpha_a) vai pelo critério destino (IBSd). Base legal: ADCT
# arts. 131-132 e LC 227/2026 arts. 114-116. ca = taxa de financiamento do
# CGIBS (Comitê Gestor do IBS, art. 51 LC 227/2026), incide só sobre o IBSd,
# antes da redistribuição por destino.
ADCT_IBS = {
    2029: {"alpha_a": 0.80, "ca": 0.0200},
    2030: {"alpha_a": 0.80, "ca": 0.0100},
    2031: {"alpha_a": 0.80, "ca": 0.0067},
    2032: {"alpha_a": 0.80, "ca": 0.0050},
    2033: {"alpha_a": 0.90, "ca": 0.0050},
}
# Seguro-Receita (ADCT art. 132): retenção de 5% sobre o IBSd líquido de
# CGIBS, também antes da redistribuição por destino.
RHO_SEGURO_RECEITA = 0.05


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

    # ── Trajetória de PIB real, 2026-2033 (Focus + IFI, sem compor IPCA) ──
    focus = macro["projecao_2026_2030_focus"]
    ifi = macro["projecao_2031_2033_ifi"]

    pib_real = {ANO_BASE: pib_2025}
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
        pib_real[y] = pib_real[y - 1] * (1 + g)
        macro_path.append({
            "ano": y,
            "pib_real_pct": round(g, 4),
            "ipca_pct": round(infl, 4),
            "pib_real": round(pib_real[y], 2),
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
    pib_2026_est = pib_real[2026]

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
        bolo_a = razao_referencia * pib_real[a]
        fa, sa = ADCT[a]["fa"], ADCT[a]["sa"]
        icms_iss_residual = bolo_a * fa
        ibs_bruto = bolo_a * sa

        # Decomposição do IBS bruto em quatro fatias: histórico, destino
        # líquido, Seguro-Receita e CGIBS (ver ADCT_IBS acima).
        alpha_a, ca = ADCT_IBS[a]["alpha_a"], ADCT_IBS[a]["ca"]
        ibs_historico = ibs_bruto * alpha_a
        ibs_destino_bruto = ibs_bruto * (1 - alpha_a)
        ibs_cgibs = ibs_destino_bruto * ca
        ibs_destino_liquido_cgibs = ibs_destino_bruto * (1 - ca)
        ibs_seguro_receita = ibs_destino_liquido_cgibs * RHO_SEGURO_RECEITA
        ibs_destino_liquido = ibs_destino_liquido_cgibs * (1 - RHO_SEGURO_RECEITA)

        projecao.append({
            "ano": a,
            "bolo_projetado": round(bolo_a, 2),
            "pib_real": round(pib_real[a], 2),
            "bolo_pct_pib": round(bolo_a / pib_real[a] * 100, 4),
            "fa": fa,
            "sa": sa,
            "icms_iss_residual": round(icms_iss_residual, 2),
            "ibs_bruto": round(ibs_bruto, 2),
            "alpha_a": alpha_a,
            "ca": ca,
            "ibs_historico": round(ibs_historico, 2),
            "ibs_destino_liquido": round(ibs_destino_liquido, 2),
            "ibs_seguro_receita": round(ibs_seguro_receita, 2),
            "ibs_cgibs": round(ibs_cgibs, 2),
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
                "divisao_ibs_bruto": "ADCT arts. 131-132 e LC 227/2026 arts. 51 e 114-116 (critério histórico/destino, CGIBS e Seguro-Receita); mesmos parâmetros do Estudo 06",
            },
            "data_pesquisa_focus": macro["_meta"]["data_pesquisa_focus"],
            "premissas": [
                "Razão bolo (ICMS+ISS+FECOP) / PIB mantida constante na média de 2024-2026 a partir de 2027. Esse período de referência não é uma escolha de modelagem: é o que os arts. 361 a 365 da LC 214/2025 (redação da LC 227/2026) usam para calibrar a alíquota de referência do IBS em cada ano da transição (2029-2033), a média da razão entre a receita de referência e o PIB nos anos de 2024 a 2026, fixada por resolução do Senado Federal. O FECOP (Fundo de Combate à Pobreza) é incluído na receita de referência porque a legislação da reforma o trata como parte da base de receita substituída pelo IBS nos estados que o cobram; sem essa parcela, a receita de referência ficaria subestimada em cerca de R$ 14 bi em 2025 (~1,4% do total) frente ao dataset validado de coeficientes por UF (data/coeficientes-uf.json, conferido contra a Nota Técnica nº 02/2026).",
                "O art. 130, §4º e §5º, do ADCT define um mecanismo distinto: o 'Teto de Referência', que compara a média 2029-2033 de CBS+Imposto Seletivo+IBS com a média 2012-2021 de IPI+ICMS+ISS+PIS/Cofins+IOF-seguros. Não altera os valores projetados aqui: mesmo se ultrapassado, a redução da alíquota só vale a partir de 2035 (fora desta projeção), e o teto exige dados federais (CBS, PIS/Cofins, IPI, IOF-seguros) fora do escopo deste estudo, que modela só o lado subnacional (ICMS/ISS/IBS).",
                "2026 ainda não fechou: a razão desse ano usa o bolo do RREO (últimos 12 meses até abr/2026) sobre o PIB projetado pelo Focus, uma estimativa preliminar a ser substituída pelo dado fechado (DCA) quando disponível.",
                "IBS bruto = bolo projetado × sa (fração já migrada para IBS no ADCT). Esse total se divide em quatro fatias: a fração alpha_a distribuída pelo critério histórico, e a fração (1-alpha_a) distribuída pelo critério destino, da qual se deduzem o CGIBS (art. 51 LC 227/2026) e o Seguro-Receita (5%, ADCT art. 132) antes de chegar aos entes. alpha_a e a taxa do CGIBS variam a cada ano da transição (2029-2033) e são os mesmos parâmetros já publicados no Estudo 06.",
                "Para 2031-2033, fora do horizonte do Boletim Focus (~5 anos), usa-se a projeção da IFI (2,2% a.a. real), constante para os três anos por simplificação, já que a IFI não detalha ano a ano dentro do intervalo 2027-2035.",
                "A partir de ago/2026, este estudo projeta em R$ constantes de 2025 (sem IPCA): a trajetória de PIB usada para escalar o bolo projetado soma só a taxa de crescimento REAL de cada ano (Focus/IFI), sem compor a inflação projetada. O IPCA de cada ano (Focus/IFI) continua listado em macro_path para referência, mas não entra na conta. A série histórica (2013-2025) é nominal, por ser dado observado, não projeção; a coluna bolo_real_2025 converte para a mesma base de 2025 quando for necessário comparar com a projeção.",
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
    print("\n=== Divisão do IBS bruto: histórico / destino líquido / seguro-receita / CGIBS ===")
    for p in projecao:
        soma = p["ibs_historico"] + p["ibs_destino_liquido"] + p["ibs_seguro_receita"] + p["ibs_cgibs"]
        print(f"{p['ano']}: hist R$ {p['ibs_historico']/1e9:.1f}B | "
              f"dest R$ {p['ibs_destino_liquido']/1e9:.1f}B | "
              f"seg-receita R$ {p['ibs_seguro_receita']/1e9:.1f}B | "
              f"CGIBS R$ {p['ibs_cgibs']/1e9:.1f}B | "
              f"soma R$ {soma/1e9:.1f}B (IBS bruto R$ {p['ibs_bruto']/1e9:.1f}B)")


if __name__ == "__main__":
    main()
