"""
Peças compartilhadas do rateio intramunicipal do destino próprio do IBS (ver
build-rateio-destino-municipios.py e simula-rateio-compras-consumo.py):

  - pesos_consumo(): consumo esperado do município com elasticidade-renda < 1
    (microdados da POF, estima-elasticidade-pof.py), a partir da média e da mediana
    de renda domiciliar per capita do Censo 2022 (lognormal).
  - compras_municipais(): base de compras de cada prefeitura (DCA Anexo I-D, 2024),
    com imputação para municípios sem dado e teto por habitante (Estudo 17).

Parâmetros (podem ser sobrescritos por variável de ambiente, para avaliar etapas):
  RATEIO_EPS        elasticidade-renda do consumo (padrão 0,80: ponto médio dos limites 0,75 e 0,87)
  RATEIO_THETA_M    peso das compras no IBS municipal próprio (padrão: calibrado em
                    data/calibra-peso-compras.py; 0 desliga)
  RATEIO_THETA_E    idem, no IBS estadual
  RATEIO_TETO_P     percentil nacional do teto de compras per capita (padrão 0,99; 1 = sem teto)
Justificativa de cada parâmetro: materiais/parametros-rateio-consumo-compras.md
"""
import json
import math
import os
from pathlib import Path

HERE = Path(__file__).parent

def _calibracao():
    """pesos das compras calibrados por data/calibra-peso-compras.py (neutralidade do art. 370)"""
    try:
        c = json.loads((HERE / "compras-calibracao.json").read_text())
        return c["theta_municipal"], c["theta_estadual"]
    except Exception:
        return 0.30, 0.027   # reserva, caso a calibração não exista


_TM, _TE = _calibracao()
EPS = float(os.environ.get("RATEIO_EPS", "0.80"))
THETA_M = float(os.environ.get("RATEIO_THETA_M", str(_TM)))
TETO_P = float(os.environ.get("RATEIO_TETO_P", "0.99"))
THETA_E = float(os.environ.get("RATEIO_THETA_E", str(_TE if "RATEIO_THETA_M" not in os.environ else round(THETA_M * 0.09, 6))))


def pesos_consumo(pops, rend, med, eps=EPS):
    """peso de consumo = pop x E[y^eps], y lognormal com a média e a mediana do município.

    sigma^2 = 2 ln(média/mediana); E[y^eps] = mediana^eps x exp(eps^2 sigma^2 / 2).
    Com eps = 1 reproduz pop x média. Municípios sem média ou com média < mediana
    (lognormal inválida) caem para pop x (média ou mediana)^eps. Sem dado algum:
    o chamador atribui a renda média da UF."""
    w = {}
    for c, pop in pops.items():
        mean = rend.get(c)
        md = med.get(c)
        if not mean or not md or md <= 0 or mean < md:
            base = mean or md or 0
            w[c] = pop * base ** eps if base else 0.0
        else:
            s2 = 2 * math.log(mean / md)
            w[c] = pop * (md ** eps) * math.exp(eps ** 2 * s2 / 2)
    return w


LIM_COMPRAS_DESPESA = 0.90


def _valido(d):
    return bool(d) and d["compras"] > 0 and d.get("populacao") and \
        d["compras"] <= LIM_COMPRAS_DESPESA * (d.get("despesa_total_liquidada") or float("inf"))


def compras_municipais(compras_json, pops_por_uf, teto_p=TETO_P):
    """compras por município e por UF. Retorna (compras, n_imputados, teto_pc).

    Município sem dado, com valor não positivo, sem população ou com compras acima de
    LIM_COMPRAS_DESPESA da despesa total (prefeitura sem folha de pessoal: classificação
    inconsistente na DCA, como Quinta do Sol/PR, 95%) recebe a mediana per capita da UF x
    população. O teto limita a compra per capita ao percentil teto_p nacional (1 = sem teto)."""
    out, imput = {}, 0
    for uf, pops in pops_por_uf.items():
        dados = compras_json.get(uf, {}).get("municipios", {})
        pcs = sorted(d["compras"] / d["populacao"] for d in dados.values() if _valido(d))
        med_pc = pcs[len(pcs) // 2] if pcs else 0.0
        for c, pop in pops.items():
            d = dados.get(c)
            if _valido(d):
                out[c] = d["compras"]
            else:
                out[c] = med_pc * pop
                imput += 1
    teto_pc = None
    if teto_p < 1:
        pcs = sorted(out[c] / pop for pops in pops_por_uf.values() for c, pop in pops.items() if pop)
        teto_pc = pcs[int(teto_p * (len(pcs) - 1))]
        out = {c: min(v, teto_pc * pops_por_uf_pop(pops_por_uf, c)) for c, v in out.items()}
    return out, imput, teto_pc


def pops_por_uf_pop(pops_por_uf, c):
    for pops in pops_por_uf.values():
        if c in pops:
            return pops[c]
    return 0.0


def carrega_entradas():
    j = lambda n: json.loads((HERE / n).read_text())
    rend = {c: v["renda_domiciliar_per_capita_2022"] for c, v in j("censo-2022-renda-municipios.json")["municipios"].items()}
    med = {c: v["renda_mediana_domiciliar_per_capita_2022"] for c, v in j("censo-2022-renda-mediana-municipios.json")["municipios"].items()}
    return rend, med, j("compras-governamentais-dca.json")


def phi_compras_por_uf(phi_fam, ufs, df_uf, frac_estado, frac_muni, compras_json, pops_por_uf, theta_m=None, theta_e=None):
    """Coeficiente de destino por UF com as compras (Estudo 17), por esfera.

    phi_fam: dict uf -> fração (POF x Censo). Retorna dict uf -> {phi_E, phi_M, ...} em fração:
      phi_E  = (1-thE) phi_fam + thE s_E     (esfera estadual; s_E = participação nas compras estaduais)
      phi_M  = (1-thM) phi_fam + thM s_M     (esfera municipal; s_M = participação nas compras municipais)
      coef_estado = frac_estado x phi_E                      (Estado, líquido da cota-parte)
      coef_muni   = alfa_M x phi_M + (frac_estado/3) x phi_E (municípios: IBS próprio + cota-parte)
      DF: coef_estado = alfa_E phi_E + alfa_M phi_M (soma das esferas; compras do DF na esfera estadual)
    com alfa_E = frac_estado/0,75 e alfa_M = frac_muni - frac_estado/3. A cota-parte incide sobre
    as compras estaduais (leitura literal do art. 118, par. 3o, LC 227/2026).
    """
    theta_m = THETA_M if theta_m is None else theta_m
    theta_e = THETA_E if theta_e is None else theta_e
    compras_mun, _, _ = compras_municipais(compras_json, pops_por_uf)
    s_M_raw = {uf: sum(compras_mun[c] for c in pops_por_uf.get(uf, {})) for uf in ufs}
    tm = sum(s_M_raw.values())
    s_M = {uf: v / tm for uf, v in s_M_raw.items()}
    est = {uf: ((compras_json.get(uf, {}) or {}).get("estado") or {}).get("compras", 0) for uf in ufs}
    te = sum(est.values())
    s_E = {uf: v / te for uf, v in est.items()}
    alfa_E = frac_estado / 0.75
    alfa_M = frac_muni - frac_estado / 3
    out = {}
    for uf in ufs:
        phi_E = (1 - theta_e) * phi_fam[uf] + theta_e * s_E[uf]
        phi_M = (1 - theta_m) * phi_fam[uf] + theta_m * s_M[uf]
        if uf in df_uf:
            out[uf] = {"phi_E": phi_E, "phi_M": phi_M, "coef_estado": alfa_E * phi_E + alfa_M * phi_M, "coef_muni": None}
        else:
            out[uf] = {"phi_E": phi_E, "phi_M": phi_M, "coef_estado": frac_estado * phi_E,
                       "coef_muni": alfa_M * phi_M + (frac_estado / 3) * phi_E}
    return out


def esferas_uf(entry, is_df, frac_estado, frac_muni):
    """(coef_pleno_estado, coef_pleno_muni) em fração, para a UF.

    Usa os coeficientes com compras gravados em phi-dest-pof-censo.json (se THETA_M > 0 e presentes);
    caso contrário, a fórmula original: phi_UF x frac_estado e phi_UF x frac_muni."""
    if THETA_M > 0 and entry.get("coef_estado_compras_pct") is not None:
        ce = entry["coef_estado_compras_pct"] / 100
        cm = entry.get("coef_muni_compras_pct")
        return ce, (None if cm is None else cm / 100)
    phi_uf = (entry.get("pof_censo_bruto_pct") or 0) / 100
    return (phi_uf if is_df else phi_uf * frac_estado), (None if is_df else phi_uf * frac_muni)
