#!/usr/bin/env python3
"""
Exportação complementar ao Estudo 15 (build-resultados-consolidados.py),
para o Painel de Indicadores da Reforma Tributária.

Reaplica exatamente as mesmas funções já publicadas e citadas em
resultados-consolidados-ibs.json (project_municipio, compute_params_uf,
compute_neutro_municipal_2025) -- nenhuma lógica de projeção é reescrita ou
alterada aqui. A única diferença é o que é exportado: o Estudo 15 mantém só
os 20 maiores ganhos e as 20 maiores perdas de 2033 (destaques_municipios_2033);
este script exporta o resultado 2029-2033 completo, já computado
internamente por main() mas descartado antes de chegar ao JSON, para todos
os municípios com coeficiente de participação (coeficientes-municipios.json)
e coeficiente de destino (rateio-destino-municipios.json) disponíveis.

As mesmas sinalizações de qualidade do Estudo 15 (neutro_aproximado,
neutro_suspeito, cobertura_anos) são preservadas no output, para que o
front-end trate a incerteza dos dados exatamente como o próprio Estudo 15
já trata -- não como uma tabela "limpa" escondendo os casos frágeis.

Uso:
  python3 build-painel-municipios.py
"""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT_DIR = HERE / "painel-municipios"

spec = importlib.util.spec_from_file_location(
    "build_resultados_consolidados", HERE / "build-resultados-consolidados.py"
)
brc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brc)


def main():
    ref_data = brc.load("reforma-tributaria.json")
    coef_uf = brc.load("coeficientes-uf.json")
    phi_dest = brc.load("phi-dest-pof-censo.json")
    nac_data = brc.load("ibs-projecao-nacional.json")
    seguro_data = brc.load("seguro-receita-repasses.json")
    coef_muni = brc.load("coeficientes-municipios.json")["municipios"]
    rateio_muni = brc.load("rateio-destino-municipios.json")["municipios"]
    pop_muni = brc.load("populacao-municipios-media-2019-2026.json")["municipios"]

    nacional_by_year = {r["ano"]: r for r in nac_data["projecao"]}
    params_uf, total_br_2025 = brc.compute_params_uf(ref_data, coef_uf, phi_dest)
    r0_neutro_muni = brc.compute_neutro_municipal_2025(ref_data)

    repasse_muni_idx = {}
    for a in brc.ANOS:
        ano_data = (seguro_data.get("anos") or {}).get(str(a))
        if not ano_data:
            continue
        for e in ano_data.get("entidades", []):
            if e.get("esfera") != "municipio":
                continue
            repasse_muni_idx.setdefault(e["id"], {})[a] = e.get("repasse") or 0

    # ── Série histórica por município, 2019-2025 (mesmos insumos e mesma
    # proporcionalização de cota-parte de build-coeficientes-municipios.py,
    # não recalculados de outra forma -- só expostos ano a ano em vez de só
    # a média de 7 anos que vira coeficiente_pct). ──
    HIST_ANOS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    dca_icms_br = ref_data.get("dca_icms_br", {})
    dca_iss_br = ref_data.get("dca_iss_br", {})
    dca_fecop_br = ref_data.get("dca_fecop_br", {})
    dca_outras_uf = ref_data.get("dca_icms_outras_deducoes_por_uf", {})
    dca_icms_uf = ref_data.get("dca_icms_por_uf", {})
    dca_transf_uf = ref_data.get("dca_transf_munis_por_uf", {})
    dca_cota_uf = ref_data.get("dca_cota_icms_por_uf", {})
    dca_det = ref_data.get("dca_detalhes", {})

    total_br_hist = {}
    for ano in HIST_ANOS:
        s = str(ano)
        icms, iss = dca_icms_br.get(s), dca_iss_br.get(s)
        fecop = dca_fecop_br.get(s, 0) or 0
        outras = sum((dca_outras_uf.get(s, {}) or {}).values())
        total_br_hist[ano] = (icms - outras + iss + fecop) if (icms is not None and iss is not None) else None
    deflators_hist = {ano: (1.0 if ano == 2025 else
                             (total_br_hist[2025] / total_br_hist[ano] if total_br_hist.get(ano) else None))
                       for ano in HIST_ANOS}
    cota_alvo_uf_hist = {}
    for ano in HIST_ANOS:
        s = str(ano)
        cota_alvo_uf_hist[ano] = {
            uf: ((dca_transf_uf.get(s) or {}).get(uf) if (dca_transf_uf.get(s) or {}).get(uf) is not None
                 else icms_val * 0.25)
            for uf, icms_val in (dca_icms_uf.get(s) or {}).items()
        }
    cota_total_dca_uf_hist = {ano: (dca_cota_uf.get(str(ano)) or {}) for ano in HIST_ANOS}

    municipios = {}
    for cod, cm in coef_muni.items():
        rd = rateio_muni.get(cod)
        if rd is None:
            continue
        coef_cpt = (cm.get("coeficiente_pct") or 0) / 100
        coef_pleno = (rd.get("phi_dest_pct") or 0) / 100
        uf = cm["uf"]

        r0 = r0_neutro_muni.get(cod)
        neutro_aproximado = r0 is None
        if neutro_aproximado:
            r0 = coef_cpt * total_br_2025

        implied_pelo_cpt = coef_cpt * total_br_2025
        neutro_suspeito = (
            not neutro_aproximado and implied_pelo_cpt > 0
            and not (0.2 <= r0 / implied_pelo_cpt <= 5)
        )

        res = brc.project_municipio(
            cod, r0, coef_cpt, coef_pleno, uf, total_br_2025,
            nacional_by_year, repasse_muni_idx, brc.ANOS,
        )
        pop = (pop_muni.get(cod) or {}).get("pop_media")

        historico_por_ano = {}
        for ano in HIST_ANOS:
            s = str(ano)
            det = (dca_det.get(s) or {}).get(cod)
            defl = deflators_hist.get(ano)
            if det is None or defl is None:
                continue
            # mesmo tratamento de build-coeficientes-municipios.py: valor
            # ausente vira 0, não descarta o ano (ISS e cota-parte são
            # reportados em registros separados do DCA Anexo I-C).
            iss_v = det.get("valor") or 0
            cota_dca_v = det.get("cota_parte_icms") or 0
            cota_total = cota_total_dca_uf_hist.get(ano, {}).get(uf)
            cota_alvo = cota_alvo_uf_hist.get(ano, {}).get(uf)
            cota_v = (cota_alvo * (cota_dca_v / cota_total)) if (cota_alvo is not None and cota_total) else cota_dca_v
            historico_por_ano[ano] = {
                "iss_reais_2025": iss_v * defl,
                "cota_parte_reais_2025": cota_v * defl,
                "total_reais_2025": (iss_v + cota_v) * defl,
            }

        # Decomposição em 4 categorias, mesma fórmula de project_municipio
        # (não reescrita, só exposta por parte em vez de só o total): quanto
        # da receita projetada vem do ICMS/ISS residual (origem), do IBS pelo
        # critério histórico (φCPT), do IBS por destino (φdest) e do
        # Seguro-Receita. As quatro somam exatamente res[a]["total"].
        coef_neutro = r0 / total_br_2025 if total_br_2025 else 0
        componentes_por_ano = {}
        for a in brc.ANOS:
            nac = nacional_by_year[a]
            ca = nac.get("ca", 0.0)
            repasse = res[a]["repasse"]
            componentes_por_ano[a] = {
                "origem": nac["icms_iss_residual"] * coef_neutro,
                "cpt": (1 - ca) * nac["ibs_historico"] * coef_cpt,
                "destino": nac["ibs_destino_liquido"] * coef_pleno,
                "seguro": (1 - ca) * repasse,
            }

        municipios[cod] = {
            "nome": cm["nome"],
            "uf": uf,
            "cobertura_anos": cm.get("cobertura_anos", 0),
            "neutro_aproximado": neutro_aproximado,
            "neutro_suspeito": neutro_suspeito,
            "pop_media": pop,
            "pre_2025": r0,
            "receita_media_referencia_7anos": cm.get("receita_media_referencia"),
            "coef_neutro_pct": coef_neutro * 100,
            "coef_cpt_pct": coef_cpt * 100,
            "coef_pleno_pct": coef_pleno * 100,
            "cota_parte_pct": rd.get("cota_parte_pct"),
            "propria_pct": rd.get("propria_pct"),
            "renda_domiciliar_per_capita_2022": rd.get("renda_domiciliar_per_capita_2022"),
            "pos_por_ano": {a: res[a]["total"] for a in brc.ANOS},
            "contrafactual_por_ano": {a: res[a]["contrafactual"] for a in brc.ANOS},
            "variacao_por_ano": {a: res[a]["dpct"] for a in brc.ANOS},
            "repasse_seguro_receita_por_ano": {a: res[a]["repasse"] for a in brc.ANOS},
            "componentes_por_ano": componentes_por_ano,
            "historico_por_ano": historico_por_ano,
        }

    # Fatiado por UF (em vez de um único arquivo de ~17 MB): a navegação do
    # painel sempre passa por selecionar um estado antes, então cada visita
    # só precisa baixar os municípios daquela UF. Um índice leve (só
    # cod/nome/uf, sem os anos) cobre a busca nacional por nome.
    meta = {
        "descricao": (
            "Projeção de receita municipal 2029-2033, cenário de destino pleno "
            "(mesma metodologia do Estudo 15 -- resultados-consolidados-ibs.json "
            "-- aqui exportada para todos os municípios computados, não só os "
            "20 maiores ganhos/perdas), com os insumos do coeficiente de "
            "participação (coeficientes-municipios.json) e do rateio de destino "
            "(rateio-destino-municipios.json) reunidos no mesmo registro. Inclui "
            "também: decomposição da projeção em 4 categorias (origem/ICMS-ISS "
            "residual, IBS histórico, IBS destino, Seguro-Receita, mesma fórmula "
            "de project_municipio, só exposta por parte); repasse do "
            "Seguro-Receita por ano; e série histórica 2019-2025 (ISS + cota-parte "
            "do ICMS, real R$ 2025, mesma proporcionalização de "
            "build-coeficientes-municipios.py)."
        ),
        "fonte": "Estudos 02, 06, 09, 10, 11, 12, 13, 15 deste site; ver nota-metodologica-ibs.html",
        "cobertura_anos_min_recomendada": brc.COBERTURA_MIN,
        "populacao_min_recomendada": brc.POP_MIN,
        "aviso_qualidade": (
            "Municípios com neutro_aproximado=true ou neutro_suspeito=true têm "
            "participação neutra (2025) estimada de forma menos direta; o "
            "Estudo 15 os exclui do ranking de destaques por esse motivo. Exibir "
            "com indicação de incerteza, não como valor definitivo."
        ),
        "anos": brc.ANOS,
    }

    OUT_DIR.mkdir(exist_ok=True)
    por_uf = {}
    for cod, m in municipios.items():
        por_uf.setdefault(m["uf"], {})[cod] = m
    for uf, muns in por_uf.items():
        with open(OUT_DIR / f"{uf}.json", "w", encoding="utf-8") as f:
            json.dump({"_meta": meta, "uf": uf, "municipios": muns}, f, ensure_ascii=False, indent=1)

    # O índice carrega, além de nome e UF, a variação de 2033 e a marca de
    # ressalva de qualidade. Isso é o suficiente para o mapa nacional pintar
    # os 5.569 municípios sem baixar nenhum fragmento por UF; os valores
    # completos continuam vindo do fragmento quando a ficha é aberta.
    indice = {
        cod: {
            "nome": m["nome"],
            "uf": m["uf"],
            # Cinco casas dão precisão de 0,001 ponto percentual, bem além do
            # que o mapa pinta e do que a tela mostra. A ficha continua lendo
            # o valor cheio do fragmento da UF.
            "v": round(m["variacao_por_ano"][2033], 5),
            "r": 1 if (m["neutro_aproximado"] or m["neutro_suspeito"]) else 0,
        }
        for cod, m in municipios.items()
    }
    # Compacto, sem indentação: este arquivo é lido em toda visita à página e
    # nunca por uma pessoa. Os fragmentos por UF seguem indentados.
    with open(OUT_DIR / "index.json", "w", encoding="utf-8") as f:
        json.dump({"_meta": meta, "n_municipios": len(indice), "municipios": indice},
                  f, ensure_ascii=False, separators=(",", ":"))

    n_ok = sum(1 for m in municipios.values() if not m["neutro_aproximado"] and not m["neutro_suspeito"])
    print(f"Salvo em {OUT_DIR}/ ({len(por_uf)} arquivos por UF + index.json)")
    print(f"Municípios: {len(municipios)} | sem ressalva de qualidade: {n_ok}")


if __name__ == "__main__":
    main()
