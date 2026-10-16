"""
Tratamento de 2026 no coeficiente histórico (CPT). A lei (LC 227/2026, arts. 114 e 115) pede a média de 2019 a 2026; o DCA de 2026
só fecha em 2027. Opções (data/parametros-cpt-2026.json; a variável de ambiente CPT_2026 sobrepõe): omitir, repetir 2025 ou nowcast.
Em "nowcast": ICMS (receita líquida do estado e cota-parte municipal) = 2025 x exp(mu_UF) (mu_UF: sensibilidade-nowcast-2026.json,
RREO de jan-ago); ISS = 2025 (nenhuma fonte mensal confiável em escala); tudo renormalizado (fator r) para as participações somarem
o mesmo total de 2025. Os municípios herdam o fator da UF na cota-parte (sem nowcast municipal) e repetem o ISS de 2025.

Em "rreo" (tratamento adotado em out/2026): os totais por UF são os do nowcast (de modo que Σ dos municípios = agregado da UF e o painel
dos estados não muda); o RREO municipal (Anexo 03, SICONFI; data/collect-rreo-municipios.py) só redistribui o 2026 dentro de cada UF:
  - ISS = receita observada de set/2025 a ago/2026 (jan-ago de 2026 + set-dez de 2025, o "total dos últimos 12 meses" do 4º bimestre);
  - cota-parte do ICMS = valor de 2025 x crescimento observado de jan-ago de 2026 sobre jan-ago de 2025.
Município sem o Anexo 03 (ex.: quem usa o RREO simplificado) mantém a posição relativa de 2025 no estado: cresce à média dos municípios
observados da mesma UF. Backtest em 2024 e 2025 (data/teste-rreo-2026.py): erro mediano da participação cai de 6-7% (repetir o ano
anterior) para 2,0-2,4%.
"""
import json
import math
import os
from pathlib import Path

HERE = Path(__file__).parent
ANOS_OBS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def tratamento():
    t = os.environ.get("CPT_2026") or json.loads((HERE / "parametros-cpt-2026.json").read_text(encoding="utf-8"))["tratamento"]
    assert t in ("omitir", "repetir", "nowcast", "rreo"), t
    return t


def n_anos(t=None):
    return len(ANOS_OBS) + (0 if (t or tratamento()) == "omitir" else 1)


def mu_uf():
    return json.loads((HERE / "sensibilidade-nowcast-2026.json").read_text(encoding="utf-8"))["mu_uf"]


def fatores(componentes_2025):
    """componentes_2025: {uf: {"icms": valor 2025 sujeito ao fator do ICMS (estado líquido + cota-parte), "iss": ISS 2025}}.
    Devolve {uf: (fator_icms, fator_iss)}; para omitir devolve fatores nulos (2026 não entra)."""
    t = tratamento()
    if t == "omitir":
        return {u: (0.0, 0.0) for u in componentes_2025}, 0.0
    mu = mu_uf() if t in ("nowcast", "rreo") else {}
    pre = {u: math.exp(mu.get(u, 0.0)) for u in componentes_2025}
    antes = sum(c["icms"] + c["iss"] for c in componentes_2025.values())
    depois = sum(c["icms"] * pre[u] + c["iss"] for u, c in componentes_2025.items())
    r = antes / depois if t in ("nowcast", "rreo") else 1.0
    return {u: (pre[u] * r, r) for u in componentes_2025}, r


def componentes_2025(d):
    """componentes de 2025 por UF a partir de reforma-tributaria.json (já passado por fold): "icms" = ICMS líquido de outras deduções + FECOP
    (a parte que acompanha o ICMS do estado, inclusive a cota-parte municipal) e "iss" = ISS dos municípios da UF (DF: ISS integral)."""
    icms = (d.get("dca_icms_por_uf") or {}).get("2025") or {}
    outras = (d.get("dca_icms_outras_deducoes_por_uf") or {}).get("2025") or {}
    fecop = (d.get("dca_fecop_por_uf") or {}).get("2025") or {}
    iss = (d.get("dca_iss_por_uf") or {}).get("2025") or {}
    return {u: {"icms": (icms.get(u) or 0) - (outras.get(u, 0) or 0) + (fecop.get(u, 0) or 0), "iss": iss.get(u) or 0} for u in sorted(icms)}


def fatores_uf(d, uf):
    """(fator_icms, fator_iss, n_anos) de uma UF para somar o termo estimado de 2026 a séries municipais próprias (ex.: Paraná auditado)."""
    fat, _ = fatores(componentes_2025(d))
    fi, fr = fat[uf]
    return fi, fr, n_anos()


# ── RREO municipal: distribuição do 2026 dentro de cada UF ──────────────────────────────────────────────
RREO_DIR = HERE / "rreo-municipios"


def rreo_municipal():
    """{cod: {"iss_12m": ISS set/25-ago/26, "g_cota": crescimento jan-ago/26 sobre jan-ago/25 da cota-parte}} só para quem tem o dado
    completo (ISS e cota-parte, 12 meses preenchidos e positivos); quem não tem fica de fora."""
    a26 = json.loads((RREO_DIR / "2026-p4.json").read_text(encoding="utf-8"))
    a25 = json.loads((RREO_DIR / "2025-p6.json").read_text(encoding="utf-8"))
    out = {}
    for cod, v in a26.items():
        w = a25.get(cod) or {}
        if not (v.get("iss") and v.get("cota") and w.get("cota")):
            continue
        m26, m25 = v["cota"]["meses"], w["cota"]["meses"]
        iss12 = v["iss"]["total12"]
        if None in m26[4:] or None in m25[:8] or iss12 is None:
            continue
        j26, j25 = sum(m26[4:]), sum(m25[:8])
        if iss12 > 0 and j26 > 0 and j25 > 0:
            out[cod] = {"iss_12m": iss12, "g_cota": j26 / j25}
    return out


def distribuir_2026(r25_por_uf, fat):
    """r25_por_uf: {uf: {cod: (iss_2025, cota_2025)}} (valores de 2025 já como entram no modelo); fat: {uf: (fator_icms, fator_iss)}.
    Devolve {cod: {"iss", "cota", "origem_iss", "origem_cota"}} com Σ por UF = fator_iss x Σ ISS 2025 e fator_icms x Σ cota 2025
    (os totais do nowcast); o RREO só decide a distribuição entre os municípios da UF."""
    obs = rreo_municipal()
    out = {}
    for uf, munis in r25_por_uf.items():
        fi, fr = fat.get(uf, (0.0, 0.0))
        # crescimento médio dos observados da UF (ponderado por 2025): é o que recebe quem não tem o Anexo 03
        o = [(c, obs[c]) for c in munis if c in obs]
        s_iss25 = sum(munis[c][0] for c, _ in o)
        s_cot25 = sum(munis[c][1] for c, _ in o)
        g_iss = (sum(x["iss_12m"] for _, x in o) / s_iss25) if s_iss25 > 0 else 1.0
        g_cota = (sum(munis[c][1] * x["g_cota"] for c, x in o) / s_cot25) if s_cot25 > 0 else 1.0
        w_iss, w_cota, orig = {}, {}, {}
        for c, (iss25, cota25) in munis.items():
            if c in obs and iss25 > 0 and cota25 > 0:
                w_iss[c], w_cota[c], orig[c] = obs[c]["iss_12m"], cota25 * obs[c]["g_cota"], "rreo"
            else:
                w_iss[c], w_cota[c], orig[c] = iss25 * g_iss, cota25 * g_cota, "repetido"
        t_iss = fr * sum(m[0] for m in munis.values())
        t_cota = fi * sum(m[1] for m in munis.values())
        s_i, s_c = sum(w_iss.values()), sum(w_cota.values())
        for c in munis:
            out[c] = {"iss": t_iss * w_iss[c] / s_i if s_i > 0 else 0.0, "cota": t_cota * w_cota[c] / s_c if s_c > 0 else 0.0,
                      "origem_iss": orig[c], "origem_cota": orig[c]}
    return out
