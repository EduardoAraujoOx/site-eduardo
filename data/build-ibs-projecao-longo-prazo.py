#!/usr/bin/env python3
"""
Estudo (novo): extensão da projeção nacional do IBS (Estudo 11) de 2033 até
2077, seguindo o cronograma real de transição do critério histórico->destino
do ADCT (EC 132/2023) -- não uma projeção inventada de crescimento por UF.

Não recalcula nada de 2013 a 2033: lê ibs-projecao-nacional.json (Estudo 11)
e usa esse "historico" e essa "projecao" 2029-2033 exatamente como estão, para
as duas páginas sempre baterem número a número no trecho em que se sobrepõem.
Só adiciona 2034-2077.

Duas peças mudam depois de 2033:

1. Trajetória de PIB nominal. Focus (BCB) só cobre 2026-2030 e a IFI (RAF
   107) só detalha até 2033 -- mas a própria nota da IFI diz que a taxa de
   2,2% a.a. real (IPCA convergindo a 3,0%) vale para todo o intervalo
   2027-2035 "por simplificação, já que a IFI não detalha ano a ano". Para
   2034-2077 esta extensão apenas continua essa MESMA taxa (nenhum número
   novo, nenhuma tentativa de simular ciclo econômico de 44 anos): PIB real
   +2,2% a.a., IPCA 3,0% a.a. (meta contínua do CMN), o que dá crescimento
   nominal de (1,022 x 1,03 - 1) = 5,266% a.a. constante. É premissa nossa,
   não é lei -- por isso fica destacada à parte na _meta.

2. Divisão histórico/destino do IBS bruto (alpha_a). Isso NÃO é premissa
   nossa: é o cronograma da própria EC 132/2023. ADCT art. 131, §1º: de 2029
   a 2033, os percentuais já usados no Estudo 11/06 (alpha_a: 80% em
   2029-2032, 90% em 2033); de 2034 a 2077, o percentual de 2033 (90%) é
   reduzido em 1/45 a cada ano, chegando a 0% (100% destino) em 2078 -- os
   "50 anos de transição" (2029-2078) citados de passagem em outras páginas
   do site, aqui finalmente modelados ano a ano. sa=1/fa=0 (a conversão
   ICMS/ISS->IBS já terminou em 2033, não muda mais). ca (taxa do CGIBS)
   mantida no piso de 0,50% já vigente em 2032-2033 (não há indicação de
   nova mudança na lei); rho (Seguro-Receita) continua 5% -- a lei só reduz
   esse percentual a partir de 2078, linearmente até 0% em 2097, fora do
   horizonte desta página.

Uso: python3 build-ibs-projecao-longo-prazo.py
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent
OUTPUT = DATA_DIR / "ibs-projecao-longo-prazo.json"

ANO_FIM = 2077

# Mesma taxa da IFI (RAF 107) já usada em 2031-2033, apenas continuada.
PIB_REAL_LONGO_PRAZO = 0.022
IPCA_LONGO_PRAZO = 0.03

# ADCT art. 131, §1º: de 2033 (90% histórico) a 2078 (0% histórico), reduz
# 1/45 do valor de 2033 a cada ano.
ALPHA_2033 = 0.90
ANO_ALPHA_BASE = 2033
ANO_ALPHA_ZERO = 2078
PASSOS_ALPHA = ANO_ALPHA_ZERO - ANO_ALPHA_BASE  # 45

CA_PISO = 0.0050  # taxa do CGIBS, piso já vigente em 2032-2033, mantida
RHO_SEGURO_RECEITA = 0.05  # ADCT art. 132: 5% flat até 2077 (só cai a partir de 2078)


def main():
    nacional = json.load(open(DATA_DIR / "ibs-projecao-nacional.json"))
    razao_referencia = nacional["_meta"]["razao_bolo_pib_base"] / 100

    projecao_2029_2033 = nacional["projecao"]
    pib_nom = {p["ano"]: p["pib_nominal"] for p in projecao_2029_2033}
    ultimo_ano = max(pib_nom)  # 2033

    projecao_2034_2077 = []
    for a in range(ultimo_ano + 1, ANO_FIM + 1):
        pib_nom[a] = pib_nom[a - 1] * (1 + PIB_REAL_LONGO_PRAZO) * (1 + IPCA_LONGO_PRAZO)
        bolo_a = razao_referencia * pib_nom[a]

        # fa=0, sa=1: conversão ICMS/ISS -> IBS já terminada em 2033.
        icms_iss_residual = 0.0
        ibs_bruto = bolo_a

        passos = min(a - ANO_ALPHA_BASE, PASSOS_ALPHA)
        alpha_a = ALPHA_2033 * (1 - passos / PASSOS_ALPHA)
        ca = CA_PISO

        ibs_historico = ibs_bruto * alpha_a
        ibs_destino_bruto = ibs_bruto * (1 - alpha_a)
        ibs_cgibs = ibs_destino_bruto * ca
        ibs_destino_liquido_cgibs = ibs_destino_bruto * (1 - ca)
        ibs_seguro_receita = ibs_destino_liquido_cgibs * RHO_SEGURO_RECEITA
        ibs_destino_liquido = ibs_destino_liquido_cgibs * (1 - RHO_SEGURO_RECEITA)

        projecao_2034_2077.append({
            "ano": a,
            "bolo_projetado": round(bolo_a, 2),
            "pib_nominal": round(pib_nom[a], 2),
            "bolo_pct_pib": round(bolo_a / pib_nom[a] * 100, 4),
            "fa": 0.0,
            "sa": 1.0,
            "icms_iss_residual": round(icms_iss_residual, 2),
            "ibs_bruto": round(ibs_bruto, 2),
            "alpha_a": round(alpha_a, 6),
            "ca": ca,
            "ibs_historico": round(ibs_historico, 2),
            "ibs_destino_liquido": round(ibs_destino_liquido, 2),
            "ibs_seguro_receita": round(ibs_seguro_receita, 2),
            "ibs_cgibs": round(ibs_cgibs, 2),
        })

    projecao = projecao_2029_2033 + projecao_2034_2077

    output = {
        "_meta": {
            "descricao": (
                f"Extensão do Estudo 11: série histórica (2013-2025) e projeção do IBS total "
                f"(Brasil), 2029-{ANO_FIM}. 2029-2033 é uma cópia exata do Estudo 11 "
                f"(mesma fonte, mesmo cálculo); 2034-{ANO_FIM} segue o cronograma real do "
                f"ADCT art. 131, §1º para a transição histórico->destino."
            ),
            "ano_base": nacional["_meta"]["ano_base"],
            "razao_bolo_pib_base": nacional["_meta"]["razao_bolo_pib_base"],
            "premissas_2034_em_diante": [
                f"PIB real: {PIB_REAL_LONGO_PRAZO*100:.1f}% a.a., IPCA: {IPCA_LONGO_PRAZO*100:.1f}% a.a. "
                "-- a MESMA taxa da IFI (RAF 107) já usada em 2031-2033 no Estudo 11, simplesmente "
                "continuada. A própria nota da IFI diz que essa taxa vale 'por simplificação' para "
                "todo o intervalo 2027-2035, sem detalhamento ano a ano; esta extensão não introduz "
                "nenhuma tentativa de prever ciclo econômico further além disso -- é estado "
                "estacionário na última taxa oficial disponível, não uma previsão de longo prazo.",
                "Razão bolo (ICMS+ISS+FECOP originais) / PIB mantida na mesma constante do Estudo 11 "
                "(média 2024-2026, art. 361-365 LC 214/2025). fa=0/sa=1 fixos: a conversão ICMS/ISS -> "
                "IBS já terminou em 2033, não é mais uma variável.",
                f"alpha_a (fração histórica do IBS bruto): NÃO é premissa -- é o cronograma do ADCT "
                f"art. 131, §1º. De 2034 a {ANO_FIM}, reduz o valor de 2033 ({ALPHA_2033*100:.0f}%) em "
                f"1/{PASSOS_ALPHA} a cada ano, chegando a 0% em {ANO_ALPHA_ZERO} (100% destino) -- os "
                "'50 anos de transição' (2029-2078) já mencionados em outras páginas do site.",
                "ca (taxa do CGIBS): mantida no piso de 0,50% já vigente em 2032-2033; a lei não "
                "detalha novo valor além disso.",
                f"rho (Seguro-Receita): 5% constante até {ANO_FIM} (ADCT art. 132; só reduz "
                f"linearmente a partir de 2078, até 0% em 2097 -- fora do horizonte desta página).",
            ],
            "fontes": {
                **nacional["_meta"]["fontes"],
                "cronograma_alpha_2034_2077": "ADCT art. 131, §1º (EC 132/2023): redução de 1/45 ao ano a partir do valor de 2033, chegando a 0% em 2078",
                "pib_ipca_2034_2077": "IFI (RAF 107, 18/dez/2025), mesma taxa de 2031-2033 (2,2% a.a. real, IPCA 3,0% a.a.), continuada sem alteração",
            },
        },
        "historico": nacional["historico"],
        "macro_path": nacional["macro_path"],
        "projecao": projecao,
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Gravado em {OUTPUT}")
    print(f"\n=== Projeção IBS {projecao[0]['ano']}-{ANO_FIM} (alpha_a e destino líquido) ===")
    for p in projecao:
        if p["ano"] in (2029, 2033, 2034, 2043, 2053, 2063, 2073, 2077):
            print(f"{p['ano']}: alpha_a={p['alpha_a']*100:6.2f}% | "
                  f"bolo R$ {p['bolo_projetado']/1e9:8.1f}B | "
                  f"IBS-destino líq. R$ {p['ibs_destino_liquido']/1e9:7.1f}B | "
                  f"Seguro-Receita R$ {p['ibs_seguro_receita']/1e9:6.2f}B")


if __name__ == "__main__":
    main()
