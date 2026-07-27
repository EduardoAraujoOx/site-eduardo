#!/usr/bin/env python3
"""
Coeficiente de participação de transição do IBS por município (art. 115, III,
LC 227/2026), replicando nacionalmente a metodologia já implementada para o
ES em estudos/reforma-tributaria-coeficiente.html (Tabela 4).

Receita de referência do município = ISS bruto + cota-parte ICMS recebida,
ambos DCA Anexo I-C (`dca_detalhes`, ~93-99% de cobertura nacional dos
municípios, 2019-2025 -- muito mais completo que a coleta municipal via
RREO Anexo 3, que serve só de validação cruzada em outros arquivos).

Como a cota-parte somada pelos próprios municípios diverge do valor que o
Estado declara ter deduzido do ICMS (a partir de 2022, ~11% abaixo no ES;
ver nota da Tabela 4 do HTML), a cota-parte de cada município é
proporcionalizada pela distribuição relativa real do DCA municipal, mas
reescalada para o total declarado pelo Estado (ou, na ausência, 25% teórico
do ICMS bruto). Isso garante Σ cpt_município = cpt_municipal da UF (Tabela 3),
por construção.

Cada ano é deflacionado por Índice_t = TotalBR_2025 / TotalBR_t, onde
TotalBR = ICMS_BR + ISS_BR + FECOP_BR (DCA), igual à Tabela 3. A receita
média de referência divide sempre por 7 (2019-2025) -- anos sem declaração
contam como zero, mesma convenção do HTML, não são excluídos do denominador.

Uso:
  python3 build-coeficientes-municipios.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "reforma-tributaria.json"
OUT = HERE / "coeficientes-municipios.json"

ANOS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def main():
    with open(SRC) as f:
        d = json.load(f)

    dca_icms_br = d.get("dca_icms_br", {})
    dca_iss_br = d.get("dca_iss_br", {})
    dca_fecop_br = d.get("dca_fecop_br", {})
    dca_transf_uf = d.get("dca_transf_munis_por_uf", {})  # {ano: {uf: valor}} -- declarado pelo estado
    dca_icms_uf = d.get("dca_icms_por_uf", {})
    dca_cota_uf = d.get("dca_cota_icms_por_uf", {})  # {ano: {uf: valor}} -- soma municipal declarada
    dca_det = d.get("dca_detalhes", {})  # {ano: {cod: {ente, uf, valor, cota_parte_icms}}}

    # ── Agregado nacional e deflatores ──────────────────────────────────────
    total_br = {}
    for ano in ANOS:
        s = str(ano)
        icms = dca_icms_br.get(s)
        iss = dca_iss_br.get(s)
        fecop = dca_fecop_br.get(s, 0) or 0
        total_br[ano] = (icms + iss + fecop) if (icms is not None and iss is not None) else None

    total_b = total_br[2025]
    if total_b is None:
        raise SystemExit("TotalBR_2025 ausente -- não é possível calcular coeficientes.")

    deflators = {ano: (1.0 if ano == 2025 else (total_b / total_br[ano] if total_br[ano] else None))
                 for ano in ANOS}

    # ── Cota-parte alvo por UF (declarada pelo estado, ou 25% teórico) ─────
    cota_alvo_uf = {}  # {ano: {uf: valor}}
    for ano in ANOS:
        s = str(ano)
        cota_alvo_uf[ano] = {}
        for uf, icms_val in (dca_icms_uf.get(s) or {}).items():
            real = (dca_transf_uf.get(s) or {}).get(uf)
            cota_alvo_uf[ano][uf] = real if real is not None else icms_val * 0.25

    cota_total_dca_uf = {ano: (dca_cota_uf.get(str(ano)) or {}) for ano in ANOS}

    # ── Por município ────────────────────────────────────────────────────
    # DF não tem coeficiente municipal separado (art. 115, LC 227/2026): é ente
    # único, com ICMS+FECOP+ISS integrais sem dedução de 25%. Seu registro no
    # DCA municipal (Brasília) participa do coeficiente estadual do DF, não
    # deste arquivo.
    municipios = {}  # {cod: {nome, uf, dados: {ano: {iss, cota_dca}}}}
    for ano in ANOS:
        for cod, v in (dca_det.get(str(ano)) or {}).items():
            uf = v.get("uf")
            if not uf or uf == "DF":
                continue
            m = municipios.setdefault(cod, {"nome": v.get("ente"), "uf": uf, "dados": {}})
            m["dados"][ano] = {"iss": v.get("valor") or 0, "cota_dca": v.get("cota_parte_icms") or 0}

    resultado = {}
    soma_cpt_por_uf = {}
    for cod, m in municipios.items():
        uf = m["uf"]
        soma = 0.0
        anos_com_dado = 0
        for ano in ANOS:
            dado = m["dados"].get(ano)
            defl = deflators[ano]
            if not dado or defl is None:
                continue
            anos_com_dado += 1
            cota_total = cota_total_dca_uf[ano].get(uf)
            cota_alvo = cota_alvo_uf[ano].get(uf)
            if cota_alvo is not None and cota_total:
                cota_muni = cota_alvo * (dado["cota_dca"] / cota_total)
            else:
                cota_muni = dado["cota_dca"]
            soma += (dado["iss"] + cota_muni) * defl

        receita_media = soma / len(ANOS)
        cpt = (receita_media / total_b) * 100

        resultado[cod] = {
            "nome": m["nome"],
            "uf": uf,
            "cobertura_anos": anos_com_dado,
            "receita_media_referencia": receita_media,
            "coeficiente_pct": cpt,
        }
        soma_cpt_por_uf[uf] = soma_cpt_por_uf.get(uf, 0.0) + cpt

    # ── Validação: Σ cpt_município por UF == cpt municipal da UF (Tabela 3) ─
    validacao_uf = {}
    for uf in cota_alvo_uf[2025].keys():
        if uf == "DF":
            continue
        soma_iss = 0.0
        soma_cota = 0.0
        n_iss = 0
        for ano in ANOS:
            defl = deflators[ano]
            if defl is None:
                continue
            iss_uf_ano = sum(
                (v.get("valor") or 0) for v in (dca_det.get(str(ano)) or {}).values() if v.get("uf") == uf
            )
            cota_ano = cota_alvo_uf[ano].get(uf)
            soma_iss += iss_uf_ano * defl
            if cota_ano is not None:
                soma_cota += cota_ano * defl
            n_iss += 1
        media_munis_uf = (soma_iss + soma_cota) / len(ANOS)
        cpt_munis_uf_tabela3 = (media_munis_uf / total_b) * 100
        cpt_munis_uf_soma_individual = soma_cpt_por_uf.get(uf, 0.0)
        diff = cpt_munis_uf_soma_individual - cpt_munis_uf_tabela3
        validacao_uf[uf] = {
            "cpt_municipal_agregado_uf": cpt_munis_uf_tabela3,
            "cpt_municipal_soma_individual": cpt_munis_uf_soma_individual,
            "diff": diff,
        }

    # ── Duplicidade de código IBGE ────────────────────────────────────────
    duplicados = [cod for cod in resultado if list(resultado.keys()).count(cod) > 1]

    output = {
        "fonte": "DCA Anexo I-C (dca_detalhes) — ISS bruto + cota-parte ICMS declarada, por município",
        "metodo": (
            "receita_media_referencia = média_7anos[(ISS_muni,t + cota_muni,t) × deflator_t]; "
            "cota_muni,t = cota_alvo_UF,t × (cota_dca_muni,t / cota_total_dca_UF,t); "
            "coeficiente_pct = receita_media_referencia / TotalBR_2025 × 100"
        ),
        "anos": ANOS,
        "total_br_2025": total_b,
        "n_municipios": len(resultado),
        "n_duplicados_ibge": len(duplicados),
        "municipios": resultado,
        "validacao_soma_por_uf": validacao_uf,
        "pendencias": [
            "Comparação ente a ente contra a Nota Técnica v22 feita em "
            "data/build-divergencia-vs-nota-v22.py: 27/27 UFs e 78/78 municípios do ES "
            "batem exatamente (diff = 0,0000pp) -- ver data/divergencia-vs-nota-v22.json.",
            "MT segue como divergência conhecida não investigada -- confirmada por três "
            "sinais independentes (DCA x RREO, Nota v22 x Sefaz-BA, e já citada no "
            "briefing original); ver data/reconciliacao-dca-rreo.json e "
            "data/raw/nota-v22/comparacao_sefaz_es_ba_ufs.csv.",
        ],
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    soma_total_cpt = sum(r["coeficiente_pct"] for r in resultado.values())
    print(f"Salvo em {OUT}")
    print(f"Municípios: {len(resultado)} | duplicados: {len(duplicados)}")
    print(f"Soma dos coeficientes municipais (Brasil): {soma_total_cpt:.4f}%")
    print()
    maiores_diff = sorted(validacao_uf.items(), key=lambda kv: -abs(kv[1]["diff"]))[:10]
    print("Maiores divergências soma-individual vs. agregado-UF (deveriam ser ~0):")
    for uf, v in maiores_diff:
        print(f"  {uf}: agregado={v['cpt_municipal_agregado_uf']:.5f}%  "
              f"soma_ind={v['cpt_municipal_soma_individual']:.5f}%  diff={v['diff']:+.6f}pp")

    cobertura_baixa = sorted(
        ((cod, r) for cod, r in resultado.items() if r["cobertura_anos"] < 5),
        key=lambda kv: kv[1]["cobertura_anos"]
    )
    print(f"\nMunicípios com cobertura < 5/7 anos: {len(cobertura_baixa)}")


if __name__ == "__main__":
    main()
