#!/usr/bin/env python3
"""
Trajetória de longo prazo do resultado de cada município, 2029-2097.

Estende o que o Painel de Municípios já mostra para 2029-2033
(build-painel-municipios.py) até o fim da transição federativa, SEM alterar
nenhum arquivo existente: grava arquivos novos em painel-municipios-longo-prazo/.

O que é reaproveitado, sem reescrever regra alguma:
  - project_municipio e a decomposição em 4 partes de build-painel-municipios.py
    (origem, IBS histórico, IBS destino, Seguro-Receita), com os mesmos
    coeficientes por município;
  - a trajetória nacional 2029-2077 de ibs-projecao-longo-prazo.json (ADCT art.
    131, §1º: peso do critério histórico cai 1/45 ao ano e zera em 2078);
  - o nivelamento do Seguro-Receita sobre as 5.596 entidades de
    build-seguro-receita-repasses-longo-prazo.py (mesma função water_fill, mesmo
    seguro_lei.seguro_ano), que ali só gravava o agregado por UF. Aqui o repasse
    é guardado município a município.

O que é novo, e só isto:
  - 2078-2097. O critério histórico já zerou (100% destino). O Seguro-Receita,
    pela LC 227/2026 (art. 110, II), é reduzido a 1/20 do percentual de 5% por
    ano a partir de 2078 (4,75% em 2078 ... 0,25% em 2096) e o ADCT art. 132,
    §3º, manda extingui-lo até 2097: em 2097, 0%. PIB real, razão bolo/PIB, CGIBS
    (0,2%) seguem as mesmas premissas de 2034-2077.

Premissas de longo prazo (cenário, não previsão): PIB real +2,2% a.a.; R$
constantes de 2025; receita de referência e participação no destino de cada
município FIXAS no dado de 2025. Ver _meta do index.json.

Conferência embutida: 2029-2033 precisa bater com painel-municipios/<UF>.json
(componentes_por_ano), e 2029-2077 com o agregado por UF de
seguro-receita-repasses-longo-prazo.json. O script falha se não bater.

Uso: python3 build-painel-municipios-longo-prazo.py
"""

import importlib.util
import json
from pathlib import Path

import seguro_lei
from fundos_art115b import fold

HERE = Path(__file__).parent
OUT_DIR = HERE / "painel-municipios-longo-prazo"

ANO_INI = 2029
ANO_FIM = 2097
ANO_FIM_MODELO_ATUAL = 2077          # até aqui, ibs-projecao-longo-prazo.json
PIB_REAL_LONGO_PRAZO = 0.022          # mesma premissa de 2034-2077
CA = 0.0020                           # CGIBS, teto permanente (art. 47, I, LC 227/2026)
RHO_BASE = 0.05                       # Seguro-Receita, art. 110, I
ANO_RHO_INICIO_QUEDA = 2078           # art. 110, II
ANO_RHO_ULTIMO = 2096                 # art. 110 / art. 117: retenção vai até 2096
ANO_RHO_ZERO = 2097                   # ADCT art. 132, §3º: extinção até 2097
PASSOS_RHO = 20                       # 1/20 por ano


def _carrega(nome, arquivo):
    spec = importlib.util.spec_from_file_location(nome, HERE / arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


slp = _carrega("slp", "build-seguro-receita-repasses-longo-prazo.py")
brc = _carrega("brc", "build-resultados-consolidados.py")
UFS = slp.UFS


def rho_seguro(ano):
    """Percentual retido para o Seguro-Receita (LC 227/2026, art. 110)."""
    if ano <= ANO_FIM_MODELO_ATUAL:
        return RHO_BASE
    if ano <= ANO_RHO_ULTIMO:
        return RHO_BASE * (1 - (ano - ANO_FIM_MODELO_ATUAL) / PASSOS_RHO)
    return 0.0


def nacional_ate_2097(nacional):
    """2029-2077 vem do arquivo existente; 2078-2097 segue a mesma conta de
    build-ibs-projecao-longo-prazo.py com alpha_a = 0 e rho decrescente."""
    por_ano = {r["ano"]: dict(r) for r in nacional["projecao"]}
    razao = nacional["_meta"]["razao_bolo_pib_base"] / 100
    pib = por_ano[ANO_FIM_MODELO_ATUAL]["pib_real"]
    for a in range(ANO_FIM_MODELO_ATUAL + 1, ANO_FIM + 1):
        pib *= (1 + PIB_REAL_LONGO_PRAZO)
        bolo = razao * pib
        ibs_bruto = bolo
        alpha = 0.0
        rho = rho_seguro(a)
        ibs_historico = ibs_bruto * alpha
        ibs_destino_bruto = ibs_bruto * (1 - alpha)
        seguro = ibs_destino_bruto * rho
        destino_liq_seguro = ibs_destino_bruto * (1 - rho)
        cgibs = destino_liq_seguro * CA
        destino_liq = destino_liq_seguro * (1 - CA)
        por_ano[a] = {
            "ano": a, "bolo_projetado": bolo, "pib_real": pib,
            "bolo_pct_pib": bolo / pib * 100, "fa": 0.0, "sa": 1.0,
            "icms_iss_residual": 0.0, "ibs_bruto": ibs_bruto, "alpha_a": alpha,
            "ca": CA, "ibs_historico": ibs_historico,
            "ibs_destino_liquido": destino_liq, "ibs_seguro_receita": seguro,
            "ibs_cgibs": cgibs,
        }
    return por_ano


def entidades_nivelamento(ref_data, coeficientes_uf, coef_muni_data, phi_dest_data,
                          rateio_muni, pop_uf, pop_muni):
    """Mesma montagem de build-seguro-receita-repasses-longo-prazo.py (main())."""
    dca_icms_2025 = ref_data.get("dca_icms_por_uf", {}).get("2025", {})
    dca_iss_2025 = ref_data.get("dca_iss_por_uf", {}).get("2025", {})
    dca_fecop_2025 = ref_data.get("dca_fecop_por_uf", {}).get("2025", {})
    dca_cota_decl_2025 = ref_data.get("dca_transf_munis_por_uf", {}).get("2025", {})
    dca_outras_2025 = ref_data.get("dca_icms_outras_deducoes_por_uf", {}).get("2025", {})
    total_br_2025 = sum(
        (dca_icms_2025.get(uf, 0) or 0) - (dca_outras_2025.get(uf, 0) or 0)
        + (dca_iss_2025.get(uf, 0) or 0) + (dca_fecop_2025.get(uf, 0) or 0)
        for uf in UFS
    )
    params_estado = slp.compute_params_estado(
        dca_icms_2025, dca_iss_2025, dca_fecop_2025, dca_cota_decl_2025,
        total_br_2025, coeficientes_uf, phi_dest_data)
    pop_by_uf = {uf: v["pop_media"] for uf, v in pop_uf["ufs"].items()}

    entidades = []
    for uf in UFS:
        p = params_estado[uf]
        denom = (p["coef_cpt_total"] if p["is_df"] else p["coef_cpt_estado"]) * total_br_2025
        entidades.append({"id": f"UF-{uf}", "uf": uf, "esfera": "estado", "is_df": p["is_df"],
                          "denom": denom, "phi_dest": p["phi_dest_estado"],
                          "pop": pop_by_uf.get(uf, 0)})
    for cod, r in coef_muni_data["municipios"].items():
        rd = rateio_muni["municipios"].get(cod)
        pm = pop_muni["municipios"].get(cod)
        if rd is None or pm is None:
            continue
        entidades.append({"id": f"MUN-{cod}", "uf": r["uf"], "esfera": "municipio", "is_df": False,
                          "denom": r["receita_media_referencia"], "phi_dest": rd["phi_dest_pct"] / 100,
                          "pop": pm["pop_media"]})

    grupo_estado = [e for e in entidades if e["esfera"] == "estado"]
    denom_df_icms = next(p["coef_cpt_estado"] * total_br_2025 for p in params_estado.values() if p["is_df"])
    soma_denom_estado = sum((denom_df_icms if e["is_df"] else e["denom"]) for e in grupo_estado)
    soma_pop_estado = sum(e["pop"] for e in grupo_estado)
    media_pc_estado = soma_denom_estado / soma_pop_estado if soma_pop_estado > 0 else 0

    grupo_muni = [e for e in entidades if e["esfera"] == "municipio"]
    denom_df_iss = next(p["iss_2025"] for p in params_estado.values() if p["is_df"])
    pop_df = next(e["pop"] for e in grupo_estado if e["is_df"])
    soma_denom_muni = sum(e["denom"] for e in grupo_muni) + denom_df_iss
    soma_pop_muni = sum(e["pop"] for e in grupo_muni) + pop_df
    media_pc_muni = soma_denom_muni / soma_pop_muni if soma_pop_muni > 0 else 0

    for e in entidades:
        if e["is_df"]:
            teto = 3 * (media_pc_estado + media_pc_muni) * e["pop"]
        elif e["esfera"] == "estado":
            teto = 3 * media_pc_estado * e["pop"]
        else:
            teto = 3 * media_pc_muni * e["pop"]
        e["denom_capado"] = min(e["denom"], teto) if e["pop"] > 0 else e["denom"]
    return entidades


def main():
    ref_data = fold(brc.load("reforma-tributaria.json"))
    coef_uf = brc.load("coeficientes-uf.json")
    phi_dest = brc.load("phi-dest-pof-censo.json")
    coef_muni_data = brc.load("coeficientes-municipios.json")
    rateio_muni_data = brc.load("rateio-destino-municipios.json")
    pop_uf = brc.load("populacao-uf-media-2019-2026.json")
    pop_muni_data = brc.load("populacao-municipios-media-2019-2026.json")
    nacional_arq = brc.load("ibs-projecao-longo-prazo.json")
    seguro_lp_arq = brc.load("seguro-receita-repasses-longo-prazo.json")

    coef_muni = coef_muni_data["municipios"]
    rateio_muni = rateio_muni_data["municipios"]
    _, total_br_2025 = brc.compute_params_uf(ref_data, coef_uf, phi_dest)
    r0_neutro_muni = brc.compute_neutro_municipal_2025(ref_data)

    nac = nacional_ate_2097(nacional_arq)
    anos = list(range(ANO_INI, ANO_FIM + 1))

    entidades = entidades_nivelamento(ref_data, coef_uf, coef_muni_data, phi_dest,
                                      rateio_muni_data, pop_uf, pop_muni_data)
    print(f"Entidades no nivelamento: {len(entidades)} | anos: {anos[0]}-{anos[-1]}")
    idx_mun = {e["id"]: i for i, e in enumerate(entidades) if e["esfera"] == "municipio"}

    # ── Nivelamento do Seguro-Receita, ano a ano, guardando o repasse por município ──
    repasse = {}                      # {ano: lista de repasses alinhada a entidades}
    resumo_ano = {}
    agregado_uf_calc = {}             # só para a conferência com o arquivo existente
    for a in anos:
        reps, nums = seguro_lei.seguro_ano(
            [e["denom_capado"] for e in entidades], [e["phi_dest"] for e in entidades],
            nac, a, slp.water_fill)
        repasse[a] = reps
        benef = [r for r in reps if r > 1e-6]
        mun_benef = sum(1 for e, r in zip(entidades, reps) if e["esfera"] == "municipio" and r > 1e-6)
        resumo_ano[a] = {"n_beneficiarios": len(benef), "n_municipios_beneficiarios": mun_benef,
                         "soma_repasses": sum(reps)}
        agg = {uf: {"estado": 0.0, "municipio": 0.0} for uf in UFS}
        for e, r in zip(entidades, reps):
            agg[e["uf"]][e["esfera"]] += r
        agregado_uf_calc[a] = agg
        if a % 10 == 9 or a in (2033, 2034, 2077, 2078, 2096, 2097):
            print(f"  {a}: pool R$ {nac[a]['ibs_seguro_receita']/1e9:7.2f} bi | "
                  f"beneficiários {len(benef)} ({mun_benef} municípios)", flush=True)

    # ── Conferência 1: 2029-2077 contra o agregado por UF já publicado ──
    maior = 0.0
    for a in range(ANO_INI, ANO_FIM_MODELO_ATUAL + 1):
        pub = seguro_lp_arq["anos"][str(a)]["repasse_por_uf"]
        for uf in UFS:
            for esfera in ("estado", "municipio"):
                v_pub, v_calc = pub[uf][esfera], agregado_uf_calc[a][uf][esfera]
                dif = abs(v_pub - v_calc) / max(1.0, abs(v_pub), abs(v_calc))
                maior = max(maior, dif)
    print(f"Conferência 1 (agregado por UF vs seguro-receita-repasses-longo-prazo.json): "
          f"maior diferença relativa = {maior:.2e}")
    assert maior < 1e-6, "O nivelamento não reproduz o agregado já publicado."

    # ── Série por município ──
    municipios = {}
    for cod, cm in coef_muni.items():
        rd = rateio_muni.get(cod)
        if rd is None:
            continue
        coef_cpt = (cm.get("coeficiente_pct") or 0) / 100
        coef_pleno = (rd.get("phi_dest_pct") or 0) / 100
        r0 = r0_neutro_muni.get(cod)
        if r0 is None:
            r0 = coef_cpt * total_br_2025
        coef_neutro = r0 / total_br_2025 if total_br_2025 else 0
        i_ent = idx_mun.get(f"MUN-{cod}")
        serie = {"origem": [], "cpt": [], "destino": [], "seguro": [], "contra": []}
        for a in anos:
            n = nac[a]
            ca = n.get("ca", 0.0)
            rep = repasse[a][i_ent] if i_ent is not None else 0.0
            serie["origem"].append(round(n["icms_iss_residual"] * coef_neutro))
            serie["cpt"].append(round((1 - ca) * n["ibs_historico"] * coef_cpt))
            serie["destino"].append(round(n["ibs_destino_liquido"] * coef_pleno))
            serie["seguro"].append(round((1 - ca) * rep))
            serie["contra"].append(round((n["icms_iss_residual"] + n["ibs_bruto"]) * coef_neutro))
        municipios[cod] = {"uf": cm["uf"], "serie": serie}

    # ── Conferência 2: 2029-2033 contra painel-municipios/<UF>.json ──
    # A saída é arredondada ao real; por isso a diferença absoluta admitida é de 1 real
    # (meio real de arredondamento, com folga). Em valores grandes, vale também o relativo.
    max_abs, max_rel_grandes, n_comp = 0.0, 0.0, 0
    for uf in UFS:
        arq = HERE / "painel-municipios" / f"{uf}.json"
        if not arq.exists():
            continue
        existente = json.load(open(arq, encoding="utf-8"))["municipios"]
        for cod, m in existente.items():
            novo = municipios.get(cod)
            if novo is None:
                continue
            for j, a in enumerate(range(2029, 2034)):
                comp = m["componentes_por_ano"][str(a)]
                for k in ("origem", "cpt", "destino", "seguro"):
                    v_old, v_new = comp[k], novo["serie"][k][j]
                    d = abs(v_old - v_new)
                    max_abs = max(max_abs, d)
                    if abs(v_old) > 1e4:
                        max_rel_grandes = max(max_rel_grandes, d / abs(v_old))
                    n_comp += 1
    print(f"Conferência 2 ({n_comp} valores 2029-2033 vs painel-municipios): "
          f"maior diferença absoluta = R$ {max_abs:.2f} | maior relativa (valores > R$ 10 mil) = {max_rel_grandes:.2e}")
    assert n_comp > 0 and max_abs <= 1.0, "A decomposição 2029-2033 não reproduz o painel atual."

    # ── Saída ──
    OUT_DIR.mkdir(exist_ok=True)
    por_uf = {}
    for cod, m in municipios.items():
        por_uf.setdefault(m["uf"], {})[cod] = m["serie"]
    meta_curta = {"ano_inicial": ANO_INI, "ano_final": ANO_FIM,
                  "unidade": "R$ de 2025 (constantes), arredondado ao real",
                  "partes": ["origem", "cpt", "destino", "seguro", "contra"],
                  "resultado": "origem + cpt + destino + seguro",
                  "contra": "receita sem a reforma (ICMS+ISS crescendo com o bolo nacional)"}
    for uf, muns in por_uf.items():
        with open(OUT_DIR / f"{uf}.json", "w", encoding="utf-8") as f:
            json.dump({"_meta": meta_curta, "uf": uf, "municipios": muns}, f,
                      ensure_ascii=False, separators=(",", ":"))

    caminho_nacional = []
    for a in anos:
        n = nac[a]
        caminho_nacional.append({
            "ano": a,
            "alpha_historico": round(n["alpha_a"], 6),
            "rho_seguro": round(rho_seguro(a), 6),
            "bolo": round(n["bolo_projetado"]), "ibs_bruto": round(n["ibs_bruto"]),
            "ibs_historico": round(n["ibs_historico"]),
            "ibs_destino_liquido": round(n["ibs_destino_liquido"]),
            "pool_seguro_receita": round(n["ibs_seguro_receita"]),
            "n_beneficiarios": resumo_ano[a]["n_beneficiarios"],
            "n_municipios_beneficiarios": resumo_ano[a]["n_municipios_beneficiarios"],
        })
    meta = {
        "descricao": ("Trajetória do resultado de cada município de 2029 a 2097, em quatro partes "
                      "(ICMS/ISS residual, IBS pelo critério histórico, IBS pelo destino, "
                      "Seguro-Receita) e a receita sem a reforma. Extensão de painel-municipios/ "
                      "(2029-2033), mesma fórmula de project_municipio."),
        **meta_curta,
        "cronograma_legal": {
            "peso_historico": "ADCT art. 131, §1º e LC 227/2026 art. 109: 80% (2029-2032), 90% (2033), cai 1/45 ao ano e zera em 2078.",
            "seguro_receita": ("ADCT art. 132 e LC 227/2026 art. 110: 5% do IBS de destino de 2029 a 2077; de 2078 a 2096 o "
                               "percentual cai 1/20 ao ano (4,75% em 2078, 0,25% em 2096); ADCT art. 132, §3º: extinção até 2097. "
                               "Modelado com 0% em 2097."),
            "cgibs": "0,2% do IBS de destino (art. 47, I, LC 227/2026), mantido de 2033 em diante.",
        },
        "premissas": [
            "PIB real de +2,2% ao ano, a mesma taxa da IFI usada até 2033, apenas continuada (estado estacionário, sem ciclo econômico).",
            "Valores em R$ constantes de 2025, sem IPCA.",
            "Receita média de referência e participação no destino de cada município ficam FIXAS no dado de 2025: a projeção não prevê migração de base, crescimento diferencial nem mudanças de população.",
            "Cenário de destino pleno, mesma metodologia do Estudo 15.",
        ],
        "aviso": ("Ele é construído a partir das regras da lei e de premissas simples. "
                  "Quanto mais longe o ano, maior a incerteza: use a forma da trajetória (quando o ganho começa a cair, "
                  "quanto depende do Seguro-Receita) mais do que o valor de um ano isolado."),
        "conferencias": {
            "agregado_uf_2029_2077": "idêntico a seguro-receita-repasses-longo-prazo.json",
            "decomposicao_2029_2033": "idêntica a painel-municipios/<UF>.json (componentes_por_ano)",
        },
    }
    with open(OUT_DIR / "index.json", "w", encoding="utf-8") as f:
        json.dump({"_meta": meta, "caminho_nacional": caminho_nacional,
                   "n_municipios": len(municipios)}, f, ensure_ascii=False, separators=(",", ":"))

    tam = sum(p.stat().st_size for p in OUT_DIR.glob("*.json"))
    print(f"Salvo em {OUT_DIR}/ ({len(por_uf)} arquivos por UF + index.json) | {tam/1e6:.1f} MB no total")
    print(f"Municípios: {len(municipios)}")


if __name__ == "__main__":
    main()
