#!/usr/bin/env python3
"""
Reconciliação DCA x RREO do ICMS estadual, por UF e ano.

Achado de metodologia (validado empiricamente contra o ES, onde há valor
oficial da SEFAZ-ES): a conta do RREO Anexo 3 `ICMSLiquidoExcetoTransferenciasEFUNDEB`
é ICMS BRUTO do estado, não líquido da cota-parte municipal, apesar do nome.
Comparando com o ICMS bruto implícito (cota-parte oficial do ES ÷ 25%), o
RREO bate com o bruto (diff < 1%), não com o líquido (que seria ~20% menor).
"Líquido" no nome da conta provavelmente se refere a líquido de restituições,
não de transferências constitucionais.

Por isso a reconciliação correta é bruto (RREO) contra bruto (DCA), não
bruto (RREO) contra líquido (DCA bruto − transferência a municípios) como
uma primeira tentativa fez — o que gerava divergências espúrias de 25-35%
em quase todas as UFs.

A cota-parte municipal só está disponível no lado DCA
(`dca_transf_munis_por_uf`, dedução declarada pelo próprio estado no Anexo
I-C); o RREO Anexo 3 não quebra a dedução por imposto, só no agregado da
Receita Corrente, então não há como validar o valor líquido por essa via.

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

    icms_rreo = d["icms_por_uf"]  # {uf: {ano: valor}} -- bruto, apesar do nome da conta
    icms_dca = d["dca_icms_por_uf"]  # {ano: {uf: valor}} -- bruto
    transf_dca = d["dca_transf_munis_por_uf"]  # {ano: {uf: valor}} -- só existe no lado DCA
    cota_dca_munis = d.get("dca_cota_icms_por_uf", {})  # {ano: {uf: valor}} -- lado municipal, checagem cruzada
    fecop_dca = d.get("dca_fecop_por_uf", {})

    anos = sorted(icms_dca.keys())
    ufs = sorted(icms_dca[anos[-1]].keys())  # inclui DF

    resultado = {}
    divergencias = []

    for uf in ufs:
        resultado[uf] = {}
        for ano in anos:
            bruto_dca = icms_dca.get(ano, {}).get(uf)
            bruto_rreo = icms_rreo.get(uf, {}).get(ano)
            transf = transf_dca.get(ano, {}).get(uf)
            cota_munis = cota_dca_munis.get(ano, {}).get(uf)
            fecop = fecop_dca.get(ano, {}).get(uf)

            if bruto_dca is None and bruto_rreo is None:
                continue

            entry = {
                "icms_bruto_dca": bruto_dca,
                "icms_bruto_rreo": bruto_rreo,
                "transf_munis_dca": transf,
                "icms_liquido_dca": (bruto_dca - transf) if (bruto_dca is not None and transf is not None) else None,
                "cota_parte_declarada_munis_dca": cota_munis,
                "fecop_dca": fecop,
            }

            if bruto_dca and bruto_rreo:
                diff_abs = bruto_dca - bruto_rreo
                diff_rel = diff_abs / bruto_rreo
                entry["diff_abs_bruto"] = diff_abs
                entry["diff_rel_bruto"] = diff_rel
                if abs(diff_rel) > LIMIAR_DIVERGENCIA:
                    divergencias.append({
                        "uf": uf, "ano": ano,
                        "diff_rel": diff_rel, "diff_abs": diff_abs,
                    })

            if cota_munis is not None and transf:
                entry["diff_transf_vs_cota_munis_rel"] = (cota_munis - transf) / transf

            resultado[uf][ano] = entry

    output = {
        "fonte_dca": "STN/DCA Anexo I-C — PCASP RO1.1.1.8.02.1.0 / RO1.1.1.4.50.1.0 (ICMS bruto, coluna Receitas Brutas Realizadas)",
        "fonte_rreo": "SICONFI RREO Anexo 3 — conta ICMSLiquidoExcetoTransferenciasEFUNDEB",
        "achado_metodologico": (
            "Apesar do nome, ICMSLiquidoExcetoTransferenciasEFUNDEB do RREO é ICMS BRUTO "
            "do estado, não líquido da cota-parte municipal. Validado contra o ICMS bruto "
            "implícito do ES (cota-parte oficial SEFAZ-ES ÷ 25%): RREO bate com o bruto "
            "(diff < 1% em 2023-2025), não com o líquido (que seria ~20% menor). "
            "A reconciliação correta é bruto (RREO) x bruto (DCA)."
        ),
        "metodo": "diff_rel_bruto = (icms_bruto_dca - icms_bruto_rreo) / icms_bruto_rreo",
        "limiar_divergencia": LIMIAR_DIVERGENCIA,
        "fonte_canonica_recomendada": "dca",
        "motivo_fonte_canonica": (
            "Art. 116 da LC 227/2026 cita o Siconfi como base do coeficiente; o DCA "
            "Anexo I-C separa ICMS bruto e transferência a municípios declarados pelo "
            "próprio estado, permitindo replicar a memória de cálculo linha a linha "
            "(bruto − transferência = líquido). O RREO Anexo 3 não quebra a dedução "
            "por imposto, só serve como validação cruzada do valor bruto."
        ),
        "por_uf_ano": resultado,
        "divergencias_acima_do_limiar": sorted(
            divergencias, key=lambda x: -abs(x["diff_rel"])
        ),
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {OUT}")
    print(f"\n{len(divergencias)} divergências (bruto x bruto) acima de {LIMIAR_DIVERGENCIA*100:.0f}%:")
    print(f"{'UF':<4}{'Ano':<6}{'Diff %':>10}{'Diff R$':>18}")
    for div in sorted(divergencias, key=lambda x: -abs(x["diff_rel"]))[:40]:
        print(f"{div['uf']:<4}{div['ano']:<6}{div['diff_rel']*100:>9.2f}%{div['diff_abs']:>18,.0f}")


if __name__ == "__main__":
    main()
