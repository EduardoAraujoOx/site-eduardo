#!/usr/bin/env python3
"""
Reconciliação DCA x RREO do ICMS estadual, por UF e ano.

O site já coleta ICMS por duas fontes que medem coisas diferentes:
- RREO Anexo 3 (`icms_por_uf`): conta ICMSLiquidoExcetoTransferenciasEFUNDEB,
  já líquida de transferências.
- DCA Anexo I-C, lado estadual (`dca_icms_por_uf` + `dca_transf_munis_por_uf`):
  ICMS bruto ("Receitas Brutas Realizadas") e a dedução de transferências
  constitucionais aos municípios ("Deduções - Transferências Constitucionais"),
  ambos declarados pelo próprio estado no mesmo Anexo I-C.

  Não confundir com `dca_cota_icms_por_uf`: esse campo vem do lado
  MUNICIPAL do DCA (cota-parte ICMS recebida, declarada pelos municípios),
  uma fonte independente da mesma transferência — útil como checagem
  cruzada adicional, mas não é o que a Nota v22 deduz do ICMS bruto.

ICMS líquido DCA = ICMS bruto DCA - transferências a municípios (DCA).
Comparado ao ICMS líquido RREO para achar UFs onde as duas fontes divergem.

*** STATUS: RASCUNHO, NÃO VALIDADO ***
A execução produz divergências sistemáticas de 25-35% em várias UFs (RJ,
MG, GO, MA, AL, PI, CE, SE), muito maiores que o esperado. Inspecionando a
API do Tesouro diretamente (RREO Anexo 3, RJ 2023), a conta
`ICMSLiquidoExcetoTransferenciasEFUNDEB` aparece dentro de "RECEITAS
CORRENTES (I)" -- a seção BRUTA -- e não em "DEDUÇÕES (II)", onde fica a
linha "Transferências Constitucionais e Legais" (a cota-parte municipal).
Isso sugere que essa conta do RREO pode ser ICMS BRUTO do estado (líquido
apenas de receitas de transferência que o estado RECEBE de terceiros, tipo
FPE/FUNDEB), e não líquido da cota-parte que o estado REPASSA aos
municípios -- ao contrário do que o levantamento original assumiu. Se for
esse o caso, comparar essa conta com "bruto DCA - transferência a
municípios" está comparando bruto com líquido, o que explicaria a
divergência sistemática observada. Precisa de confirmação antes de definir
fonte canônica ou usar isso em qualquer estatística publicada.

Uso:
  python3 build-reconciliacao-dca-rreo.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "reforma-tributaria.json"
OUT = HERE / "reconciliacao-dca-rreo.json"

LIMIAR_DIVERGENCIA = 0.02  # 2%


def main():
    with open(SRC) as f:
        d = json.load(f)

    icms_rreo = d["icms_por_uf"]  # {uf: {ano: valor}}
    icms_dca = d["dca_icms_por_uf"]  # {ano: {uf: valor}}
    transf_dca = d["dca_transf_munis_por_uf"]  # {ano: {uf: valor}} -- dedução declarada pelo estado
    cota_dca_munis = d.get("dca_cota_icms_por_uf", {})  # {ano: {uf: valor}} -- lado municipal, checagem cruzada
    fecop_dca = d.get("dca_fecop_por_uf", {})  # {ano: {uf: valor}}

    anos = sorted(icms_dca.keys())
    ufs = sorted(icms_dca[anos[-1]].keys())  # inclui DF

    resultado = {}
    divergencias = []

    for uf in ufs:
        resultado[uf] = {}
        for ano in anos:
            bruto = icms_dca.get(ano, {}).get(uf)
            transf = transf_dca.get(ano, {}).get(uf)
            cota_munis = cota_dca_munis.get(ano, {}).get(uf)
            fecop = fecop_dca.get(ano, {}).get(uf)
            liquido_rreo = icms_rreo.get(uf, {}).get(ano)

            if bruto is None or transf is None:
                continue

            liquido_dca = bruto - transf

            entry = {
                "icms_bruto_dca": bruto,
                "transf_munis_dca": transf,
                "cota_parte_declarada_munis_dca": cota_munis,
                "icms_liquido_dca": liquido_dca,
                "fecop_dca": fecop,
                "icms_liquido_rreo": liquido_rreo,
            }
            if cota_munis is not None and transf:
                entry["diff_transf_vs_cota_munis_rel"] = (cota_munis - transf) / transf

            if liquido_rreo:
                diff_abs = liquido_dca - liquido_rreo
                diff_rel = diff_abs / liquido_rreo
                entry["diff_abs"] = diff_abs
                entry["diff_rel"] = diff_rel
                if abs(diff_rel) > LIMIAR_DIVERGENCIA:
                    divergencias.append({
                        "uf": uf, "ano": ano,
                        "diff_rel": diff_rel, "diff_abs": diff_abs,
                    })

            resultado[uf][ano] = entry

    output = {
        "status": "RASCUNHO_NAO_VALIDADO",
        "aviso": (
            "Divergências sistemáticas de 25-35% em várias UFs indicam possível "
            "comparação bruto x líquido, não erro de dado -- ver docstring do "
            "script para a hipótese investigada. Não usar como fonte canônica "
            "até confirmar a definição exata de ICMSLiquidoExcetoTransferenciasEFUNDEB "
            "no RREO Anexo 3."
        ),
        "fonte_dca": "STN/DCA Anexo I-C — PCASP RO1.1.1.8.02.1.0 / RO1.1.1.4.50.1.0 (ICMS bruto)",
        "fonte_rreo": "SICONFI RREO Anexo 3 — ICMSLiquidoExcetoTransferenciasEFUNDEB",
        "metodo": "icms_liquido_dca = icms_bruto_dca - transf_munis_dca (dedução declarada pelo estado); comparado a icms_liquido_rreo",
        "limiar_divergencia": LIMIAR_DIVERGENCIA,
        "fonte_canonica_recomendada": None,
        "por_uf_ano": resultado,
        "divergencias_acima_do_limiar": sorted(
            divergencias, key=lambda x: -abs(x["diff_rel"])
        ),
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {OUT}")
    print(f"\n{len(divergencias)} divergências acima de {LIMIAR_DIVERGENCIA*100:.0f}%:")
    print(f"{'UF':<4}{'Ano':<6}{'Diff %':>10}{'Diff R$':>18}")
    for div in sorted(divergencias, key=lambda x: -abs(x["diff_rel"]))[:30]:
        print(f"{div['uf']:<4}{div['ano']:<6}{div['diff_rel']*100:>9.2f}%{div['diff_abs']:>18,.0f}")


if __name__ == "__main__":
    main()
