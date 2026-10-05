"""
Tratamento de 2026 no coeficiente histórico (CPT). A lei (LC 227/2026, arts. 114 e 115) pede a média de 2019 a 2026; o DCA de 2026
só fecha em 2027. Opções (data/parametros-cpt-2026.json; a variável de ambiente CPT_2026 sobrepõe): omitir, repetir 2025 ou nowcast.
Em "nowcast": ICMS (receita líquida do estado e cota-parte municipal) = 2025 x exp(mu_UF) (mu_UF: sensibilidade-nowcast-2026.json,
RREO de jan-ago); ISS = 2025 (nenhuma fonte mensal confiável em escala); tudo renormalizado (fator r) para as participações somarem
o mesmo total de 2025. Os municípios herdam o fator da UF na cota-parte (sem nowcast municipal) e repetem o ISS de 2025.
"""
import json
import math
import os
from pathlib import Path

HERE = Path(__file__).parent
ANOS_OBS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def tratamento():
    t = os.environ.get("CPT_2026") or json.loads((HERE / "parametros-cpt-2026.json").read_text(encoding="utf-8"))["tratamento"]
    assert t in ("omitir", "repetir", "nowcast"), t
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
    mu = mu_uf() if t == "nowcast" else {}
    pre = {u: math.exp(mu.get(u, 0.0)) for u in componentes_2025}
    antes = sum(c["icms"] + c["iss"] for c in componentes_2025.values())
    depois = sum(c["icms"] * pre[u] + c["iss"] for u, c in componentes_2025.items())
    r = antes / depois if t == "nowcast" else 1.0
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
