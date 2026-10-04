#!/usr/bin/env python3
"""
Simulação (NÃO publicada) de duas melhorias no rateio municipal do coeficiente de
destino do IBS:

  (1) FUNÇÃO DE CONSUMO: o consumo do município deixa de ser proporcional à renda
      média (elasticidade 1, hipótese atual) e passa a seguir uma elasticidade-renda
      estimada nos microdados da POF 2017-18 (data/estima-elasticidade-pof.py).
      Aproxima-se a renda do município por uma lognormal com a média e a mediana do
      Censo 2022 (sigma^2 = 2 ln(média/mediana)); o consumo per capita esperado é
      proporcional a E[y^e] = mediana^e * exp(e^2 sigma^2 / 2). Com e = 1, E[y] é a
      própria média e o resultado reproduz o rateio atual.

  (2) COMPRAS GOVERNAMENTAIS: o IBS das compras da administração direta, autarquias
      e fundações vai ao ente comprador (CF art. 149-C; LC 214 arts. 472-473) e
      entra na receita inicial (LC 227 art. 106, III), sujeito às mesmas retenções e
      redistribuições do restante do IBS (arts. 107-111, 114-117). Logo, o ajuste é
      no coeficiente de destino: em cada esfera, o coeficiente da UF passa a ser uma
      mistura do coeficiente de consumo das famílias com a participação da UF nas
      compras da esfera:

         phi_E(u) = (1 - theta_E) phi_fam(u) + theta_E s_E(u)    (esfera estadual)
         phi_M(u) = (1 - theta_M) phi_fam(u) + theta_M s_M(u)    (esfera municipal)

      theta = peso das compras no IBS da esfera (nota Gobetti/COMSEFAZ, 2026: 30% no
      IBS municipal próprio, cerca de 3% no estadual). s_E(u), s_M(u) = participação
      da UF nas compras estaduais e municipais (DCA Anexo I-D 2024, liquidado,
      data/compras-governamentais-dca.json). DF: as compras do ente distrital entram
      na esfera estadual (a DCA não separa), como na nota.
      Dentro da UF, a parcela de compras do IBS municipal próprio é rateada entre os
      municípios pela compra observada de cada prefeitura; a parte de famílias, pelo
      consumo estimado em (1); a cota-parte, por população (art. 128), como hoje.

Cenários e a pergunta que cada um responde estão em CENARIOS. O resultado NÃO altera
nenhum número publicado: é insumo para decidir o que entra no modelo.

Uso: python3 data/simula-rateio-compras-consumo.py
Saída: data/rateio-destino-municipios-cenarios.json
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "rateio-destino-municipios-cenarios.json"

# theta_E guarda a mesma proporção de theta_M observada na nota (2,7% / 30% = 0,09)
CENARIOS = {
    "base": dict(desc="modelo atual (elasticidade 1, sem compras)", eps=1.0, thM=0.0, thE=0.0, cota_compras=True),
    "consumo": dict(desc="só função de consumo (e = 0,80)", eps=0.80, thM=0.0, thE=0.0, cota_compras=True),
    "compras": dict(desc="só compras (theta_M = 30%)", eps=1.0, thM=0.30, thE=0.027, cota_compras=True),
    "central": dict(desc="consumo + compras (e = 0,80; theta_M = 30%)", eps=0.80, thM=0.30, thE=0.027, cota_compras=True),
    "conservador": dict(desc="consumo + compras com theta_M = 20%", eps=0.80, thM=0.20, thE=0.018, cota_compras=True),
    "central_teto": dict(desc="central, compras per capita limitadas ao percentil 99 nacional", eps=0.80, thM=0.30, thE=0.027, cota_compras=True, teto=True),
    "central_sem_cota_compras": dict(desc="central, cota-parte NÃO incide sobre compras estaduais", eps=0.80, thM=0.30, thE=0.027, cota_compras=False),
}
SENSIBILIDADE_EPS = [0.75, 0.80, 0.87]
UFS = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT',
       'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']
CAPITAIS = {'AC': '1200401', 'AL': '2704302', 'AM': '1302603', 'AP': '1600303', 'BA': '2927408',
            'CE': '2304400', 'ES': '3205309', 'GO': '5208707', 'MA': '2111300', 'MG': '3106200',
            'MS': '5002704', 'MT': '5103403', 'PA': '1501402', 'PB': '2507507', 'PE': '2611606',
            'PI': '2211001', 'PR': '4106902', 'RJ': '3304557', 'RN': '2408102', 'RO': '1100205',
            'RR': '1400100', 'RS': '4314902', 'SC': '4205407', 'SE': '2800308', 'SP': '3550308',
            'TO': '1721000'}


def carrega():
    j = lambda n: json.loads((HERE / n).read_text())
    return (j("rateio-destino-municipios.json")["municipios"], j("phi-dest-pof-censo.json"),
            j("censo-2022-renda-municipios.json")["municipios"],
            j("censo-2022-renda-mediana-municipios.json")["municipios"],
            j("compras-governamentais-dca.json"))


def pesos_consumo(muns, rend, med, eps):
    """peso de consumo de cada município: pop * E[y^eps], lognormal média/mediana"""
    w = {}
    for c, pop in muns.items():
        mean = rend.get(c, {}).get("renda_domiciliar_per_capita_2022")
        md = med.get(c, {}).get("renda_mediana_domiciliar_per_capita_2022")
        if not mean or not md or md <= 0 or mean < md:
            # sem dado ou distribuição degenerada: cai para média (eps tratado como 1 e escala)
            w[c] = pop * (mean or md or 0) ** eps if (mean or md) else 0.0
            continue
        s2 = 2 * math.log(mean / md)
        w[c] = pop * (md ** eps) * math.exp(eps ** 2 * s2 / 2)
    return w


def compras_municipais(compras, ufs_munis):
    """compras por município; ausentes ou zeradas recebem a mediana per capita da UF x população"""
    out, imput = {}, 0
    for uf, cods in ufs_munis.items():
        dados = compras.get(uf, {}).get("municipios", {})
        pcs = sorted(d["compras"] / d["populacao"] for d in dados.values() if d.get("populacao") and d["compras"] > 0)
        med_pc = pcs[len(pcs) // 2] if pcs else 0
        for c, pop in cods.items():
            d = dados.get(c)
            if d and d["compras"] > 0:
                out[c] = d["compras"]
            else:
                out[c] = med_pc * pop
                imput += 1
    return out, imput


def main():
    rateio, phi, rend, med, compras = carrega()
    fE, fM = phi["frac_estado_pct"] / 100, phi["frac_muni_pct"] / 100
    phi_fam = {u: phi["por_uf"][u]["pof_censo_bruto_pct"] / 100 for u in UFS}
    alfa_E = fE / 0.75         # esfera estadual bruta (antes da cota-parte de 25%)
    alfa_M = fM - fE / 3       # IBS municipal próprio (sucessor do ISS)

    ufs_munis = {}
    for c, m in rateio.items():
        ufs_munis.setdefault(m["uf"], {})[c] = m["pop_media"]
    c_mun, n_imput = compras_municipais(compras, ufs_munis)
    pcs = sorted(c_mun[c] / pop for u in ufs_munis.values() for c, pop in u.items() if pop)
    teto_pc = pcs[int(0.99 * (len(pcs) - 1))]
    c_mun_teto = {c: min(v, teto_pc * pop) for u in ufs_munis.values() for c, pop in u.items() for v in [c_mun[c]]}
    s_M = {u: sum(c_mun[c] for c in ufs_munis.get(u, {})) for u in UFS}
    tot_M = sum(s_M.values())
    s_M = {u: v / tot_M for u, v in s_M.items()}
    s_Mt = {u: sum(c_mun_teto[c] for c in ufs_munis.get(u, {})) for u in UFS}
    tt = sum(s_Mt.values())
    s_Mt = {u: v / tt for u, v in s_Mt.items()}
    est = {u: (compras[u]["estado"] or {}).get("compras", 0) for u in UFS}
    tot_E = sum(est.values())
    s_E = {u: v / tot_E for u, v in est.items()}

    resultado = {"_meta": {
        "descricao": __doc__.strip().split("\n\n")[0],
        "cenarios": {k: v["desc"] for k, v in CENARIOS.items()},
        "n_municipios_compras_imputadas": n_imput,
        "teto_compras_per_capita_p99": round(teto_pc, 2),
        "aviso": "Simulação; não altera nenhum número publicado.",
    }, "uf": {}, "municipios": {}}
    base_phi = {}

    def roda(nome, par, extra_eps=None):
        eps = extra_eps if extra_eps is not None else par["eps"]
        uf_res, mun_res = {}, {}
        for u in UFS:
            phiE = (1 - par["thE"]) * phi_fam[u] + par["thE"] * s_E[u]
            sM = s_Mt if par.get("teto") else s_M
            phiM = (1 - par["thM"]) * phi_fam[u] + par["thM"] * sM[u]
            S = alfa_E * phiE  # esfera estadual da UF, bruta (antes da cota-parte)
            F = alfa_M * (1 - par["thM"]) * phi_fam[u]  # famílias no IBS municipal próprio
            C = alfa_M * par["thM"] * sM[u]             # compras no IBS municipal próprio
            if u == "DF":
                # DF: sem esfera municipal própria; fica com a soma das duas esferas
                uf_res[u] = {"phi_total_pct": 100 * (S + F + C)}
                continue
            # cota-parte = 25% da esfera estadual; se NÃO incide sobre compras estaduais, só a parte de famílias a financia
            base_cota = S if par["cota_compras"] else alfa_E * (1 - par["thE"]) * phi_fam[u]
            cota_uf = 0.25 * base_cota
            estado_uf = S - cota_uf
            muns = ufs_munis[u]
            n, popuf = len(muns), sum(muns.values())
            wc = pesos_consumo(muns, rend, med, eps)
            swc = sum(wc.values())
            cm = c_mun_teto if par.get("teto") else c_mun
            scm = sum(cm[c] for c in muns)
            tot_m = 0.0
            for c, pop in muns.items():
                cota_m = cota_uf * (0.95 * pop / popuf + 0.05 / n)
                prop_m = F * (wc[c] / swc) + C * (cm[c] / scm)
                mun_res[c] = 100 * (cota_m + prop_m)
                tot_m += mun_res[c]
            uf_res[u] = {"phi_total_pct": 100 * (S + F + C), "estado_pct": 100 * estado_uf,
                         "municipios_pct": tot_m}
        return uf_res, mun_res

    for nome, par in CENARIOS.items():
        uf_res, mun_res = roda(nome, par)
        resultado["uf"][nome] = uf_res
        for c, v in mun_res.items():
            resultado["municipios"].setdefault(c, {"nome": rateio[c]["nome"], "uf": rateio[c]["uf"]})[nome] = round(v, 6)
    for e in SENSIBILIDADE_EPS:
        _, mun_res = roda("central", CENARIOS["central"], extra_eps=e)
        for c, v in mun_res.items():
            resultado["municipios"][c][f"central_eps_{e}"] = round(v, 6)
    OUT.write_text(json.dumps(resultado, ensure_ascii=False))

    # --- resumo no terminal ---
    mun = resultado["municipios"]
    print("municípios:", len(mun), "| compras imputadas:", n_imput)
    for u in ["ES", "PR"]:
        print(f"\n{u}: phi total (% nacional) por cenário")
        for nome in CENARIOS:
            print(f"  {nome:26s} {resultado['uf'][nome][u]['phi_total_pct']:.4f}")
    # conferência: base reproduz o rateio publicado
    dif = max(abs(mun[c]["base"] - rateio[c]["phi_dest_pct"]) for c in mun)
    print("\nmax |base - rateio publicado| (pp do total nacional):", f"{dif:.2e}")
    soma_base = sum(v["base"] for v in mun.values()) + sum(100 * 0 for _ in [0])
    for nome in CENARIOS:
        s = sum(v[nome] for v in mun.values())
        print(f"soma municípios (sem DF) {nome:26s} {s:.4f}")


if __name__ == "__main__":
    main()
