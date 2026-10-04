#!/usr/bin/env python3
"""
Calibra o peso das compras governamentais no IBS subnacional (theta_M, municipal; theta_E,
estadual) com dados do próprio acervo e do SICONFI, sem estimativas de terceiros.

Raciocínio (Estudo 17):
  1. O IBS/CBS das compras da administração direta, autarquias e fundações vai ao ente comprador
     (CF art. 149-C; LC 214, art. 473) e é reduzido por um redutor uniforme calibrado para que a
     receita seja NEUTRA em relação aos tributos que as mesmas operações pagavam antes (art. 370,
     inc. I-III e par. 3o). Portanto, o IBS que o comprador recebe sobre uma compra equivale aos
     tributos antigos embutidos nela: ICMS e ISS (subnacionais) e PIS, Cofins e IPI (federais, que
     o art. 473 também direciona ao comprador).
  2. Carga média dos tributos antigos sobre o gasto final (tax-inclusive):
         tau = (R + F) / (C_fam + f x C_gov)
     R = ICMS (líquido de outras deduções) + ISS + FECOP, DCA 2025 (bolo do modelo);
     F = PIS/PASEP + Cofins + IPI, DCA da União 2024, levados a 2025 pelo crescimento do PIB nominal;
     C_fam = consumo das famílias 2025 (Contas Nacionais/IBGE);
     C_gov = compras estaduais e municipais da DCA I-D 2024 (soma bruta dos elementos de despesa,
     levada a 2025 pelo PIB nominal), e f = fração da proxy que carrega a carga média.
  3. Receita de compras: X_M = tau x f x C_M (municípios) e X_E = tau x f x C_E (Estados e DF).
     A parte de famílias do IBS subnacional é R - X_M - X_E, dividida entre as esferas pelas
     alíquotas de referência (alfa_E, alfa_M, de phi-dest-pof-censo.json). Logo
         theta_M = X_M / (X_M + alfa_M (R - X)),   theta_E = X_E / (X_E + alfa_E (R - X)).
  4. f é estimado em data/estima-fracao-compras-carga.py com as Tabelas de Recursos e Usos 2023 do
     IBGE (carga de impostos sobre produtos, composição das compras da administração pública e do
     consumo das famílias) e a cobertura da proxy frente ao consumo intermediário das Contas Nacionais:
     f entre 1,05 e 1,09. Como f é uma fração, adota-se f = 1,0 (valor central) e publica-se a faixa
     de 0,8 a 1,0. O limite inferior cobre a incerteza que a estimativa por produto não resolve (a
     cascata de tributos nos insumos e a classificação das despesas na DCA); o superior é o teto de uma
     fração. O redutor oficial do art. 370, quando divulgado, substitui a estimativa.

Saída: data/compras-calibracao.json (lida por data/rateio_consumo_compras.py).
"""
import json
from pathlib import Path

from fundos_art115b import fold

HERE = Path(__file__).parent
F_CENTRAL = 1.00
F_GRADE = [0.8, 0.85, 0.9, 0.95, 1.0]


def main():
    j = lambda n: json.loads((HERE / n).read_text())
    ref = fold(j("reforma-tributaria.json"))
    ufs = list(ref["dca_icms_por_uf"]["2025"].keys())

    def bolo(ano):
        a, i = ref["dca_icms_por_uf"][str(ano)], ref["dca_iss_por_uf"][str(ano)]
        f = ref["dca_fecop_por_uf"][str(ano)]
        o = ref["dca_icms_outras_deducoes_por_uf"].get(str(ano), {})
        return sum((a.get(u, 0) or 0) - (o.get(u, 0) or 0) + (i.get(u, 0) or 0) + (f.get(u, 0) or 0) for u in ufs)

    R = bolo(2025)
    pib = j("macro-parametros.json")["pib_nominal_historico"]
    g = pib["2025"] / pib["2024"]
    fed = j("tributos-federais-dca-uniao.json")
    F = fed["total_reais"] * g
    c_fam = j("aliquota-base-referencia.json")["_meta"]["consumo_familias_2025_rs"]
    dca = j("compras-governamentais-dca.json")
    cod = [u for u in dca if u != "_meta"]
    C_M = sum(x["compras"] for u in cod for x in dca[u]["municipios"].values()) * g
    C_E = sum((dca[u]["estado"] or {}).get("compras", 0) for u in cod) * g
    phi = j("phi-dest-pof-censo.json")
    fE, fM = phi["frac_estado_pct"] / 100, phi["frac_muni_pct"] / 100
    alfa_E, alfa_M = fE / 0.75, fM - fE / 3

    def calc(f, com_federal=True):
        tau = (R + (F if com_federal else 0)) / (c_fam + f * (C_M + C_E))
        X_M, X_E = tau * f * C_M, tau * f * C_E
        fam = R - X_M - X_E
        return {"f": f, "tau": tau, "X_municipal": X_M, "X_estadual": X_E,
                "theta_M": X_M / (X_M + alfa_M * fam), "theta_E": X_E / (X_E + alfa_E * fam)}

    grade = {"com_federal": [calc(f) for f in F_GRADE], "so_subnacional": [calc(f, False) for f in F_GRADE]}
    central = calc(F_CENTRAL)
    saida = {
        "_meta": {
            "descricao": __doc__.strip().split("\n\n")[0],
            "entradas": {
                "R_bolo_2025_reais": R, "F_federal_2025_reais": F, "consumo_familias_2025_reais": c_fam,
                "compras_municipais_2025_reais": C_M, "compras_estaduais_2025_reais": C_E,
                "crescimento_pib_nominal_2024_2025": g, "alfa_E": alfa_E, "alfa_M": alfa_M,
                "fontes": ["SICONFI DCA I-C (ICMS, ISS, FECOP, União)", "SICONFI DCA I-D (compras)",
                           "IBGE Contas Nacionais (consumo das famílias, PIB)"],
            },
            "f_central": F_CENTRAL, "intervalo_f": [min(F_GRADE), max(F_GRADE)],
            "leitura_legal": "IBS extinto destinado ao ente contratante inclui a parte equivalente a CBS "
                             "(art. 473, par. 1o: a alíquota do ente comprador é fixada na soma das alíquotas "
                             "de IBS e CBS); 'so_subnacional' é a leitura restritiva, mostrada como limite inferior.",
        },
        "central": central, "grade": grade,
        "theta_municipal": round(central["theta_M"], 4), "theta_estadual": round(central["theta_E"], 4),
    }
    (HERE / "compras-calibracao.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1))
    print("R=%.0f bi F=%.0f bi C_fam=%.0f bi C_M=%.0f bi C_E=%.0f bi g=%.4f" % (R / 1e9, F / 1e9, c_fam / 1e9, C_M / 1e9, C_E / 1e9, g))
    for rotulo, lst in grade.items():
        for r in lst:
            print("%-15s f=%.1f tau=%.1f%% X=%.0f bi theta_M=%.1f%% theta_E=%.1f%%" % (
                rotulo, r["f"], r["tau"] * 100, (r["X_municipal"] + r["X_estadual"]) / 1e9, r["theta_M"] * 100, r["theta_E"] * 100))
    print("CENTRAL: theta_M=%.4f theta_E=%.4f" % (saida["theta_municipal"], saida["theta_estadual"]))


if __name__ == "__main__":
    main()
