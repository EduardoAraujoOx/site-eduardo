#!/usr/bin/env python3
"""
Fundos estaduais do art. 115, I, "b", da LC 227/2026 (e art. 350, II, "b", da
LC 214/2025): contribuições a fundos estaduais em funcionamento em 30/04/2023,
estabelecidas como condição para diferimento, regime especial ou outro
tratamento diferenciado de ICMS, que entram na receita média de referência dos
Estados (e no bolo da alíquota de referência).

Fonte dos valores: data/fundos-art115-b.json (séries 2021-2023 do DCA Anexo I-C,
SICONFI/STN). Só entram as UFs cujo valor é verificável no SICONFI (hoje, AM).
GO e MT ficam em "pendentes_informacao_oficial".

Método (art. 115, §3º, II, da LC 227/2026): média dos valores de 2021 a 2023,
cada ano corrigido (i) até 2023 pela variação nominal do ICMS da própria UF e
(ii) de 2023 em diante pela variação nominal do ICMS+ISS nacional. O modelo
trabalha a preços de 2025 (2026 ainda não consolidado), então a segunda etapa
vai até 2025.

O resultado grava, em data/reforma-tributaria.json, a chave
``ajuste_fundos_art115b`` com os valores já distribuídos pelos anos 2019-2025
no formato que o modelo espera (ver fundos_art115b.fold): o ajuste de cada ano
é ``valor_2025 * bolo[ano] / bolo[2025]``, de modo que, depois do deflator
usado em build-coeficientes-uf.py, cada ano contribui com o mesmo
``valor_2025`` e a média 2019-2025 é igual a ele.

Rodar depois de cada coleta DCA e antes dos demais build-*.py.

Uso:
  python3 build-fundos-art115-b.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
REF = HERE / "reforma-tributaria.json"
SRC = HERE / "fundos-art115-b.json"
ANOS = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]


def main():
    ref = json.loads(REF.read_text(encoding="utf-8"))
    src = json.loads(SRC.read_text(encoding="utf-8"))
    ref.pop("ajuste_fundos_art115b", None)

    # Bolo nacional como build-coeficientes-uf.py o monta: ICMS - outras + ISS + FECOP.
    outras = ref.get("dca_icms_outras_deducoes_por_uf", {})
    def bolo(y, com_fecop=True):
        v = ref["dca_icms_br"][y] - sum((outras.get(y) or {}).values()) + ref["dca_iss_br"][y]
        return v + (ref["dca_fecop_br"].get(y, 0) or 0) if com_fecop else v

    icms_iss = {y: bolo(y, com_fecop=False) for y in ANOS}   # variação do art. 115, §3º, II, 2
    bolo_ref = {y: bolo(y) for y in ANOS}                    # base do deflator do modelo

    valores = {}
    for uf, d in src["por_uf"].items():
        serie = {y: float(v) for y, v in d["serie_dca_rs"].items()}
        icms_uf = {y: ref["dca_icms_por_uf"][y][uf] for y in serie}
        fator_nac = icms_iss["2025"] / icms_iss["2023"]
        corrigidos = {y: serie[y] * (icms_uf["2023"] / icms_uf[y]) * fator_nac for y in serie}
        valor = sum(corrigidos.values()) / len(corrigidos)
        valores[uf] = valor
        d["valor_art115_rs_2025"] = round(valor, 2)
        d["calculo"] = {
            "fator_icms_iss_nacional_2023_2025": round(fator_nac, 6),
            "fatores_icms_uf_ate_2023": {y: round(icms_uf["2023"] / icms_uf[y], 6) for y in serie},
            "valores_corrigidos_rs_2025": {y: round(v, 2) for y, v in corrigidos.items()},
        }

    fecop_uf = {y: {uf: v * bolo_ref[y] / bolo_ref["2025"] for uf, v in valores.items()} for y in ANOS}
    fecop_br = {y: sum(fecop_uf[y].values()) for y in ANOS}
    ref["ajuste_fundos_art115b"] = {
        "descricao": ("Fundos estaduais do art. 115, I, 'b' (LC 227/2026): ajuste somado ao FECOP em memória "
                      "por fundos_art115b.fold. Gerado por data/build-fundos-art115-b.py a partir de "
                      "data/fundos-art115-b.json. Não editar à mão."),
        "valor_2025_por_uf": {uf: round(v, 2) for uf, v in valores.items()},
        "fecop_por_uf": {y: {uf: round(v, 2) for uf, v in d.items()} for y, d in fecop_uf.items()},
        "fecop_br": {y: round(v, 2) for y, v in fecop_br.items()},
    }
    REF.write_text(json.dumps(ref, ensure_ascii=False, indent=2), encoding="utf-8")
    SRC.write_text(json.dumps(src, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for uf, v in valores.items():
        print(f"{uf}: valor art. 115 (R$ de 2025) = R$ {v/1e9:.3f} bi")


if __name__ == "__main__":
    main()
