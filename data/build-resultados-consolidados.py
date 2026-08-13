#!/usr/bin/env python3
"""
Resultados consolidados da transição ICMS/ISS -> IBS (Estudo 15).

Reaplica a mesma lógica de projeção já usada em
estudos/ibs-projecao-arrecadacao-br.html (funções project()/accumulate(),
cenário único de destino pleno) para produzir, num único JSON:

  1. Receita estadual projetada por UF, 2029-2033 (pré-IBS / pós-IBS / variação).
  2. Receita por município, 2029-2033, usada para o mapa (agregado por UF) e
     para a tabela de destaques (municípios que mais ganham/perdem).
  3. Receita das 27 capitais (26 municípios + Distrito Federal, que não tem
     esfera municipal própria -- art. 115, LC 227/2026).
  4. Receita per capita por UF, pré-reforma (2025) x pós-reforma em 2033 e em
     2077 (extensão de longo prazo, Estudo 09), população fixada na média
     2019-2025 nos três pontos para isolar o efeito da redistribuição do
     efeito do crescimento populacional.

O "pré-IBS" de cada ente, em qualquer ano, é sempre o mesmo contrafactual já
usado nas demais páginas do site: a receita de referência nacional do ano
(Estudo 11/09) aplicada à participação neutra (ICMS/ISS, 2025) do ente -- não
um valor fixo de 2025. Ver nota-metodologica-ibs.html, Seção 8.

Uso:
  python3 build-resultados-consolidados.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "resultados-consolidados-ibs.json"

ANOS = [2029, 2030, 2031, 2032, 2033]
ANO_LONGO = 2077

UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
]

NOMES_UF = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal",
    "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí",
    "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins",
}

CAPITAIS = {
    "AC": ("1200401", "Rio Branco"), "AL": ("2704302", "Maceió"),
    "AP": ("1600303", "Macapá"), "AM": ("1302603", "Manaus"),
    "BA": ("2927408", "Salvador"), "CE": ("2304400", "Fortaleza"),
    "DF": (None, "Brasília"), "ES": ("3205309", "Vitória"),
    "GO": ("5208707", "Goiânia"), "MA": ("2111300", "São Luís"),
    "MT": ("5103403", "Cuiabá"), "MS": ("5002704", "Campo Grande"),
    "MG": ("3106200", "Belo Horizonte"), "PA": ("1501402", "Belém"),
    "PB": ("2507507", "João Pessoa"), "PR": ("4106902", "Curitiba"),
    "PE": ("2611606", "Recife"), "PI": ("2211001", "Teresina"),
    "RJ": ("3304557", "Rio de Janeiro"), "RN": ("2408102", "Natal"),
    "RS": ("4314902", "Porto Alegre"), "RO": ("1100205", "Porto Velho"),
    "RR": ("1400100", "Boa Vista"), "SC": ("4205407", "Florianópolis"),
    "SP": ("3550308", "São Paulo"), "SE": ("2800308", "Aracaju"),
    "TO": ("1721000", "Palmas"),
}

# Floor de cobertura/porte para a tabela de destaques municipais: variação
# percentual sobre uma base de dados incompleta ou uma população muito
# pequena produz oscilações sem sentido substantivo. Mesmo critério de boa
# cobertura já usado em build-coeficientes-municipios.py (>=5 dos 7 anos).
COBERTURA_MIN = 5
POP_MIN = 10000


def load(name):
    with open(HERE / name, encoding="utf-8") as f:
        return json.load(f)


def compute_params_uf(ref_data, coef_uf, phi_dest):
    """Réplica de computeParams() em ibs-projecao-arrecadacao-br.html."""
    dca_icms = ref_data.get("dca_icms_por_uf", {}).get("2025", {})
    dca_iss = ref_data.get("dca_iss_por_uf", {}).get("2025", {})
    dca_fecop = ref_data.get("dca_fecop_por_uf", {}).get("2025", {})
    dca_cota_decl = ref_data.get("dca_transf_munis_por_uf", {}).get("2025", {})

    total_br_2025 = sum(
        (dca_icms.get(uf, 0) or 0) + (dca_iss.get(uf, 0) or 0) + (dca_fecop.get(uf, 0) or 0)
        for uf in UFS
    )

    frac_estado = (phi_dest.get("frac_estado_pct", 0) or 0) / 100
    frac_muni = (phi_dest.get("frac_muni_pct", 0) or 0) / 100
    phi_by_uf = phi_dest.get("por_uf", {})

    params = {}
    for uf in UFS:
        icms = dca_icms.get(uf, 0) or 0
        iss = dca_iss.get(uf, 0) or 0
        fecop = dca_fecop.get(uf, 0) or 0
        cuf = coef_uf.get("por_uf", {}).get(uf, {})
        is_df = bool(cuf.get("is_df"))

        cota_decl = dca_cota_decl.get(uf)
        cota = 0.0 if is_df else (cota_decl if cota_decl is not None else icms * 0.25)

        r_estado = (icms + fecop) if is_df else (icms - cota + fecop)
        r_muni = None if is_df else (iss + cota)

        coef_neutro_estado = r_estado / total_br_2025 if total_br_2025 else 0
        coef_neutro_muni = (r_muni / total_br_2025) if (r_muni is not None and total_br_2025) else None

        coef_cpt_estado = (cuf.get("coeficiente_estado_pct") or 0) / 100
        coef_cpt_muni = (cuf.get("coeficiente_municipios_pct") / 100
                          if cuf.get("coeficiente_municipios_pct") is not None else None)

        phi_uf = ((phi_by_uf.get(uf) or {}).get("pof_censo_bruto_pct") or 0) / 100
        coef_pleno_estado = phi_uf if is_df else phi_uf * frac_estado
        coef_pleno_muni = None if is_df else phi_uf * frac_muni

        params[uf] = {
            "estado": {
                "r0_2025": r_estado, "coefNeutro": coef_neutro_estado,
                "coefCPT": coef_cpt_estado, "coefPleno": coef_pleno_estado,
            },
            "municipio": None if r_muni is None else {
                "r0_2025": r_muni, "coefNeutro": coef_neutro_muni,
                "coefCPT": coef_cpt_muni, "coefPleno": coef_pleno_muni,
            },
        }
    return params, total_br_2025


def build_repasse_index(seguro_data, anos):
    idx = {}
    for a in anos:
        ano_data = (seguro_data.get("anos") or {}).get(str(a))
        if not ano_data:
            continue
        for e in ano_data.get("entidades", []):
            uf = e.get("uf")
            if uf not in idx:
                idx[uf] = {"estado": {}, "municipio": {}}
            esfera = e.get("esfera")
            idx[uf][esfera][a] = idx[uf][esfera].get(a, 0) + (e.get("repasse") or 0)
    return idx


def project_uf(uf, params, nacional_by_year, repasse_idx, anos, esfera="total"):
    """
    esfera="total": soma o ente estadual com o agregado municipal da UF (sem
    dupla contagem -- a cota-parte é subtraída de um lado e somada do outro).
    esfera="estado": só o ente estadual, líquido da cota-parte devida aos
    municípios -- o análogo direto da "receita estadual" na acepção de
    Gobetti e Monteiro (75% do ICMS bruto), usado na Tabela 1.
    """
    p = params[uf]
    if esfera == "estado":
        parts = [p["estado"]]
    else:
        parts = [p["estado"]] + ([p["municipio"]] if p["municipio"] else [])
    r0_2025 = sum(x["r0_2025"] for x in parts)
    res = {}
    for a in anos:
        nac = nacional_by_year[a]
        ref_a = nac["icms_iss_residual"] + nac["ibs_bruto"]
        total = 0.0
        contra = 0.0
        for part in parts:
            total += (nac["icms_iss_residual"] * part["coefNeutro"]
                      + nac["ibs_historico"] * part["coefCPT"]
                      + nac["ibs_destino_liquido"] * part["coefPleno"])
            contra += ref_a * part["coefNeutro"]
        repasse = 0.0
        ridx = repasse_idx.get(uf)
        if ridx:
            repasse += ridx["estado"].get(a, 0)
            if esfera == "total" and p["municipio"]:
                repasse += ridx["municipio"].get(a, 0)
        total += repasse
        dpct = (total - contra) / contra if contra > 0 else 0.0
        res[a] = {"total": total, "contrafactual": contra, "repasse": repasse, "dpct": dpct}
    return {"res": res, "r0_2025": r0_2025}


def compute_neutro_municipal_2025(ref_data):
    """
    Participação neutra (2025) de cada município: ISS bruto 2025 + cota-parte
    (proporcionalizada ao valor declarado pelo estado, mesma lógica de
    build-coeficientes-municipios.py, mas para um único ano em vez da média
    2019-2025 -- é o dado que falta em coeficientes-municipios.json, que só
    guarda o CPT de 7 anos, não a participação neutra do ano-base isolada).
    """
    dca_det_2025 = ref_data.get("dca_detalhes", {}).get("2025", {})
    dca_icms_uf_2025 = ref_data.get("dca_icms_por_uf", {}).get("2025", {})
    dca_cota_decl_2025 = ref_data.get("dca_transf_munis_por_uf", {}).get("2025", {})
    dca_cota_total_dca_2025 = ref_data.get("dca_cota_icms_por_uf", {}).get("2025", {})

    cota_alvo_uf = {}
    for uf, icms_val in dca_icms_uf_2025.items():
        real = dca_cota_decl_2025.get(uf)
        cota_alvo_uf[uf] = real if real is not None else (icms_val or 0) * 0.25

    r0_por_municipio = {}
    for cod, v in dca_det_2025.items():
        uf = v.get("uf")
        if not uf or uf == "DF":
            continue
        # Registro parcial: falta "valor" (ISS) ou "cota_parte_icms" para
        # 2025 especificamente, embora outros anos existam (5-15 municípios
        # de 5.569 -- não sistemático). Tratar a ausência como zero, como
        # antes, subestima o ente (ex.: Água Boa/MG perdia os ~74% da sua
        # receita que vêm da cota-parte, por essa faltar só em 2025). Melhor
        # não usar o dado de 2025 nesses casos: cai no fallback por CPT
        # (neutro_aproximado), que reflete a média de 7 anos do próprio ente.
        if v.get("valor") is None or v.get("cota_parte_icms") is None:
            continue
        cota_total = dca_cota_total_dca_2025.get(uf)
        cota_alvo = cota_alvo_uf.get(uf)
        cota_dca = v["cota_parte_icms"]
        if cota_alvo is not None and cota_total:
            cota_muni = cota_alvo * (cota_dca / cota_total)
        else:
            cota_muni = cota_dca
        r0_por_municipio[cod] = v["valor"] + cota_muni
    return r0_por_municipio


def project_municipio(cod, r0_2025, coef_cpt, coef_pleno, uf, total_br_2025,
                       nacional_by_year, repasse_muni_idx, anos):
    coef_neutro = r0_2025 / total_br_2025 if total_br_2025 else 0
    res = {}
    for a in anos:
        nac = nacional_by_year[a]
        ref_a = nac["icms_iss_residual"] + nac["ibs_bruto"]
        total = (nac["icms_iss_residual"] * coef_neutro
                 + nac["ibs_historico"] * coef_cpt
                 + nac["ibs_destino_liquido"] * coef_pleno)
        repasse = repasse_muni_idx.get(f"MUN-{cod}", {}).get(a, 0)
        total += repasse
        contra = ref_a * coef_neutro
        dpct = (total - contra) / contra if contra > 0 else 0.0
        res[a] = {"total": total, "contrafactual": contra, "repasse": repasse, "dpct": dpct}
    return res


def main():
    ref_data = load("reforma-tributaria.json")
    coef_uf = load("coeficientes-uf.json")
    phi_dest = load("phi-dest-pof-censo.json")
    nac_data = load("ibs-projecao-nacional.json")
    lp_data = load("ibs-projecao-longo-prazo.json")
    seguro_data = load("seguro-receita-repasses.json")
    seguro_lp_data = load("seguro-receita-repasses-longo-prazo.json")
    coef_muni = load("coeficientes-municipios.json")["municipios"]
    rateio_muni = load("rateio-destino-municipios.json")["municipios"]
    pop_uf = load("populacao-uf-media-2019-2026.json")["ufs"]
    pop_muni = load("populacao-municipios-media-2019-2026.json")["municipios"]

    nacional_by_year = {r["ano"]: r for r in nac_data["projecao"]}
    lp_by_year = {r["ano"]: r for r in lp_data["projecao"]}

    params_uf, total_br_2025 = compute_params_uf(ref_data, coef_uf, phi_dest)
    repasse_idx = build_repasse_index(seguro_data, ANOS)

    # ── 1a. Receita do ente estadual por UF, 2029-2033 (Tabela 1) ───────────
    # Só a esfera estadual, líquida da cota-parte devida aos municípios -- o
    # análogo direto da "receita estadual" de Gobetti e Monteiro (75% do
    # ICMS bruto), não o agregado UF (que seria a soma com os municípios).
    por_uf_estado = {}
    for uf in UFS:
        proj = project_uf(uf, params_uf, nacional_by_year, repasse_idx, ANOS, esfera="estado")
        sum_total = sum(proj["res"][a]["total"] for a in ANOS)
        sum_contra = sum(proj["res"][a]["contrafactual"] for a in ANOS)
        por_uf_estado[uf] = {
            "nome": NOMES_UF[uf],
            "pre_2025": proj["r0_2025"],
            "pos_por_ano": {a: proj["res"][a]["total"] for a in ANOS},
            "contrafactual_por_ano": {a: proj["res"][a]["contrafactual"] for a in ANOS},
            "variacao_por_ano": {a: proj["res"][a]["dpct"] for a in ANOS},
            "acumulado_dpct": (sum_total - sum_contra) / sum_contra if sum_contra > 0 else 0.0,
        }

    # ── 1b. Receita total por UF (estado + municípios), 2029-2033 (mapa) ────
    por_uf = {}
    for uf in UFS:
        proj = project_uf(uf, params_uf, nacional_by_year, repasse_idx, ANOS, esfera="total")
        sum_total = sum(proj["res"][a]["total"] for a in ANOS)
        sum_contra = sum(proj["res"][a]["contrafactual"] for a in ANOS)
        por_uf[uf] = {
            "nome": NOMES_UF[uf],
            "pre_2025": proj["r0_2025"],
            "pos_por_ano": {a: proj["res"][a]["total"] for a in ANOS},
            "contrafactual_por_ano": {a: proj["res"][a]["contrafactual"] for a in ANOS},
            "variacao_por_ano": {a: proj["res"][a]["dpct"] for a in ANOS},
            "acumulado_dpct": (sum_total - sum_contra) / sum_contra if sum_contra > 0 else 0.0,
        }

    # ── 2 e 3. Receita por município, 2029-2033 (para mapa/destaques/capitais) ─
    r0_neutro_muni = compute_neutro_municipal_2025(ref_data)
    repasse_muni_idx = {}
    for a in ANOS:
        ano_data = (seguro_data.get("anos") or {}).get(str(a))
        if not ano_data:
            continue
        for e in ano_data.get("entidades", []):
            if e.get("esfera") != "municipio":
                continue
            repasse_muni_idx.setdefault(e["id"], {})[a] = e.get("repasse") or 0

    municipios_resultado = {}
    for cod, cm in coef_muni.items():
        rd = rateio_muni.get(cod)
        if rd is None:
            continue
        coef_cpt = (cm.get("coeficiente_pct") or 0) / 100
        coef_pleno = (rd.get("phi_dest_pct") or 0) / 100
        uf = cm["uf"]

        # 401/5569 municípios não têm registro DCA especificamente para 2025
        # (apesar de teren cobertura suficiente nos outros anos para compor o
        # CPT): nesses casos, aproxima-se a participação neutra pela própria
        # CPT (média 2019-2025) -- não entram no ranking de destaques (abaixo),
        # só nas tabelas onde a granularidade individual é indispensável
        # (capitais).
        r0 = r0_neutro_muni.get(cod)
        neutro_aproximado = r0 is None
        if neutro_aproximado:
            r0 = coef_cpt * total_br_2025

        # Mesmo com um registro de 2025 presente, ele pode ser um dado
        # parcial ou mal declarado (ex.: Confins/MG reportou R$76 mil de ISS
        # em 2025, contra R$24 milhões em 2024 -- não uma queda real, uma
        # falha de preenchimento). Comparado contra o que a própria série de
        # 7 anos do município (CPT) implicaria para 2025, um desvio de mais
        # de 5x para cima ou para baixo de 0,2x é tratado como suspeito, não
        # como resultado real -- mesmo critério de robustez usado para
        # neutro_aproximado, aplicado aqui à consistência interna do dado.
        implied_pelo_cpt = coef_cpt * total_br_2025
        neutro_suspeito = (not neutro_aproximado and implied_pelo_cpt > 0
                            and not (0.2 <= r0 / implied_pelo_cpt <= 5))

        res = project_municipio(cod, r0, coef_cpt, coef_pleno, uf, total_br_2025,
                                 nacional_by_year, repasse_muni_idx, ANOS)
        pop = (pop_muni.get(cod) or {}).get("pop_media")
        municipios_resultado[cod] = {
            "nome": cm["nome"], "uf": uf,
            "cobertura_anos": cm.get("cobertura_anos", 0),
            "neutro_aproximado": neutro_aproximado,
            "neutro_suspeito": neutro_suspeito,
            "pop_media": pop,
            "pre_2025": r0,
            "pos_2033": res[2033]["total"],
            "contrafactual_2033": res[2033]["contrafactual"],
            "variacao_2033": res[2033]["dpct"],
        }

    elegiveis = [
        m for m in municipios_resultado.values()
        if m["cobertura_anos"] >= COBERTURA_MIN and (m["pop_media"] or 0) >= POP_MIN
        and not m["neutro_aproximado"] and not m["neutro_suspeito"]
    ]
    maiores_ganhos = sorted(elegiveis, key=lambda m: -m["variacao_2033"])[:20]
    maiores_perdas = sorted(elegiveis, key=lambda m: m["variacao_2033"])[:20]

    # ── Dispersão intramunicipal de receita per capita, antes x depois ──────
    # Mesmo exercício da Tabela 9 de Gobetti e Monteiro: por UF, a razão entre
    # a receita per capita do município mais rico e a do mais pobre, antes e
    # depois da reforma. Sem o piso de população usado acima (POP_MIN) -- aqui
    # os municípios pequenos e atípicos são o próprio objeto da pergunta, não
    # ruído a excluir -- mas mantendo o filtro de cobertura de dados e
    # excluindo aproximações de participação neutra, pelo mesmo motivo do
    # ranking de destaques.
    elegiveis_percapita = [
        m for m in municipios_resultado.values()
        if m["cobertura_anos"] >= COBERTURA_MIN and not m["neutro_aproximado"]
        and not m["neutro_suspeito"] and (m["pop_media"] or 0) > 0
    ]
    for m in elegiveis_percapita:
        m["percapita_pre"] = m["pre_2025"] / m["pop_media"]
        m["percapita_pos"] = m["pos_2033"] / m["pop_media"]

    dispersao_intramunicipal = {}
    for uf in UFS:
        muni_uf = [m for m in elegiveis_percapita if m["uf"] == uf]
        if not muni_uf:
            continue  # DF: sem municípios próprios
        richest = max(muni_uf, key=lambda m: m["percapita_pre"])
        poorest = min(muni_uf, key=lambda m: m["percapita_pre"])
        max_pos = max(m["percapita_pos"] for m in muni_uf)
        min_pos = min(m["percapita_pos"] for m in muni_uf)
        dispersao_intramunicipal[uf] = {
            "n_municipios": len(muni_uf),
            "municipio_mais_rico": richest["nome"],
            "receita_pc_mais_rico_pre": richest["percapita_pre"],
            "municipio_mais_pobre": poorest["nome"],
            "receita_pc_mais_pobre_pre": poorest["percapita_pre"],
            "max_min_pre": (richest["percapita_pre"] / poorest["percapita_pre"]
                             if poorest["percapita_pre"] > 0 else None),
            "max_min_pos": max_pos / min_pos if min_pos > 0 else None,
        }

    richest_br = max(elegiveis_percapita, key=lambda m: m["percapita_pre"])
    poorest_br = min(elegiveis_percapita, key=lambda m: m["percapita_pre"])
    max_pos_br = max(m["percapita_pos"] for m in elegiveis_percapita)
    min_pos_br = min(m["percapita_pos"] for m in elegiveis_percapita)
    dispersao_brasil = {
        "municipio_mais_rico": richest_br["nome"], "uf_mais_rico": richest_br["uf"],
        "receita_pc_mais_rico_pre": richest_br["percapita_pre"],
        "municipio_mais_pobre": poorest_br["nome"], "uf_mais_pobre": poorest_br["uf"],
        "receita_pc_mais_pobre_pre": poorest_br["percapita_pre"],
        "max_min_pre": richest_br["percapita_pre"] / poorest_br["percapita_pre"],
        "max_min_pos": max_pos_br / min_pos_br,
    }

    # Agregado por UF da variação municipal (média ponderada pela receita pré,
    # 2033), para colorir o mapa junto com a variação estadual.
    variacao_municipal_por_uf = {}
    for uf in UFS:
        muni_uf = [m for m in municipios_resultado.values() if m["uf"] == uf]
        soma_pre = sum(m["contrafactual_2033"] for m in muni_uf)
        soma_pos = sum(m["pos_2033"] for m in muni_uf)
        variacao_municipal_por_uf[uf] = (soma_pos - soma_pre) / soma_pre if soma_pre > 0 else None

    capitais_resultado = {}
    for uf, (cod, nome) in CAPITAIS.items():
        if cod is None:  # DF: sem esfera municipal própria (art. 115, LC 227/2026)
            proj = project_uf(uf, params_uf, nacional_by_year, repasse_idx, ANOS)
            capitais_resultado[uf] = {
                "codigo_ibge": None, "nome": nome, "uf": uf, "sem_municipio_proprio": True,
                "pre_2025": proj["r0_2025"],
                "pos_por_ano": {a: proj["res"][a]["total"] for a in ANOS},
                "variacao_por_ano": {a: proj["res"][a]["dpct"] for a in ANOS},
            }
        else:
            m = municipios_resultado.get(cod)
            if m is None:
                continue
            cm = coef_muni[cod]
            rd = rateio_muni[cod]
            coef_cpt = (cm.get("coeficiente_pct") or 0) / 100
            coef_pleno = (rd.get("phi_dest_pct") or 0) / 100
            r0 = m["pre_2025"]
            res = project_municipio(cod, r0, coef_cpt, coef_pleno, uf, total_br_2025,
                                     nacional_by_year, repasse_muni_idx, ANOS)
            capitais_resultado[uf] = {
                "codigo_ibge": cod, "nome": nome, "uf": uf, "sem_municipio_proprio": False,
                "neutro_aproximado": m["neutro_aproximado"],
                "pre_2025": r0,
                "pos_por_ano": {a: res[a]["total"] for a in ANOS},
                "variacao_por_ano": {a: res[a]["dpct"] for a in ANOS},
            }

    # ── 4. Per capita por UF, 2025 x 2033 x 2077 (população fixa 2019-2025) ─
    repasse_por_uf_lp = {}
    lp_2077 = (seguro_lp_data.get("anos") or {}).get(str(ANO_LONGO), {}).get("repasse_por_uf", {})
    for uf, v in lp_2077.items():
        repasse_por_uf_lp[uf] = (v.get("estado") or 0) + (v.get("municipio") or 0)

    per_capita_uf = {}
    for uf in UFS:
        pop = (pop_uf.get(uf) or {}).get("pop_media")
        if not pop:
            continue
        p = params_uf[uf]
        parts = [p["estado"]] + ([p["municipio"]] if p["municipio"] else [])

        pre_2025 = sum(x["r0_2025"] for x in parts)

        proj_2033 = por_uf[uf]["pos_por_ano"][2033]

        nac_2077 = lp_by_year[ANO_LONGO]
        total_2077 = 0.0
        for part in parts:
            total_2077 += (nac_2077["icms_iss_residual"] * part["coefNeutro"]
                           + nac_2077["ibs_historico"] * part["coefCPT"]
                           + nac_2077["ibs_destino_liquido"] * part["coefPleno"])
        total_2077 += repasse_por_uf_lp.get(uf, 0)

        per_capita_uf[uf] = {
            "nome": NOMES_UF[uf],
            "pop_media_2019_2025": pop,
            "per_capita_2025": pre_2025 / pop,
            "per_capita_2033": proj_2033 / pop,
            "per_capita_2077": total_2077 / pop,
        }

    output = {
        "fonte": "Estudos 02, 06, 09, 10, 11, 12, 13 deste site (data/*.json); ver nota-metodologica-ibs.html",
        "cenario": "destino pleno",
        "anos": ANOS,
        "ano_longo_prazo": ANO_LONGO,
        "criterios_destaque_municipal": {
            "cobertura_anos_min": COBERTURA_MIN, "populacao_min": POP_MIN,
        },
        "por_uf_estado": por_uf_estado,
        "por_uf": por_uf,
        "variacao_municipal_por_uf_2033": variacao_municipal_por_uf,
        "destaques_municipios_2033": {
            "maiores_ganhos": maiores_ganhos,
            "maiores_perdas": maiores_perdas,
        },
        "capitais": capitais_resultado,
        "per_capita_uf": per_capita_uf,
        "dispersao_intramunicipal": {
            "por_uf": dispersao_intramunicipal,
            "brasil": dispersao_brasil,
        },
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {OUT}")
    print(f"UFs: {len(por_uf)} | municípios computados: {len(municipios_resultado)} | "
          f"elegíveis p/ destaque: {len(elegiveis)}")
    print(f"Capitais: {len(capitais_resultado)} | per capita UF: {len(per_capita_uf)}")
    print()
    print("Maior ganho 2033:", maiores_ganhos[0]["nome"], maiores_ganhos[0]["uf"],
          f"{maiores_ganhos[0]['variacao_2033']*100:+.1f}%")
    print("Maior perda 2033:", maiores_perdas[0]["nome"], maiores_perdas[0]["uf"],
          f"{maiores_perdas[0]['variacao_2033']*100:+.1f}%")


if __name__ == "__main__":
    main()
