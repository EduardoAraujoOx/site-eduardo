#!/usr/bin/env python3
"""
Estimativa independente do coeficiente de destino (phi^dest) do IBS por UF,
a partir de duas fontes publicas que nao sao Gobetti e Monteiro (IPEA, 2023):

  phi_dest_pof_censo_UF = [despesa de consumo media mensal familiar (POF
  2017-2018, por UF) x domicilios particulares ocupados (Censo 2022, por UF)]
  / soma nacional do mesmo produto

A POF fornece a "intensidade" de consumo por familia (nao ha pesquisa mais
recente); o Censo 2022 fornece o peso demografico atualizado (substitui a
propria ponderacao amostral da POF, de 2018). E o mesmo raciocinio de usar
"POF para o comportamento, Censo para a atualizacao do peso" descrito na
sessao em que este estudo foi encomendado.

Alem da versao bruta (despesa total), calcula uma versao ponderada por
tributabilidade: Alimentacao, Saude e Educacao com peso 0,4 (reducao geral
de 60%, EC 132/2023 art. 9, Sec. 1), demais categorias em peso cheio. Nao
se aplica peso zero (aliquota zero) a Alimentacao: a cesta basica nacional
de aliquota zero e uma lista especifica e restrita de produtos, nao toda a
categoria "Alimentacao" da POF (que inclui alimentacao fora do domicilio,
bebidas alcoolicas e itens fora da cesta basica) -- como a tabela da POF
usada aqui (1.1.13) nao separa essa fatia por UF, o peso 0,4 (regime geral
de alimentos, nao a excecao da cesta basica) e a aproximacao mais
defensavel disponivel. Ainda assim, e um teste de sensibilidade, nao um
mapeamento fino da legislacao por categoria.

A partir de ago/2026, phi_dest_pof_censo (bruto) passou a ser o INSUMO do
modelo em todo o site (Estudos 06, 03, 11, 12 e a extensao de longo prazo),
substituindo Gobetti e Monteiro. Este script tambem recalcula, so para
comparacao/auditoria (nao mais como fonte primaria):
  - "modelo_anterior": o phi^dest usado no site ANTES dessa mudanca
    (Gobetti e Monteiro 2023 + cota-parte municipal de 25% fixa), replicando
    a formula antiga de compute_params() -- mostra o tamanho da mudanca;
  - a participacao bruta de cada UF na propria Tabela 1 de Gobetti e
    Monteiro (2023, base 2022), sem qualquer ajuste nosso.

Uso:
  python3 build-phi-dest-pof-censo.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "phi-dest-pof-censo.json"

UFS = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT',
       'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']


def compute_modelo_anterior(dca_icms_2025, dca_iss_2025, dca_fecop_2025, dca_cota_declarada_2025,
                          total_br_2025, coeficientes_uf, t4_by_uf):
    """Replica computeParams() de estudos/ibs-projecao-arrecadacao-br.html: retorna
    o phi^dest TOTAL (estado + municipios) de cada UF, coeficiente pleno normalizado."""
    brutos_estado, brutos_muni = {}, {}
    for uf in UFS:
        icms = dca_icms_2025.get(uf, 0) or 0
        iss = dca_iss_2025.get(uf, 0) or 0
        fecop = dca_fecop_2025.get(uf, 0) or 0
        cuf = coeficientes_uf['por_uf'].get(uf, {})
        t4 = t4_by_uf.get(uf, {})
        is_df = bool(cuf.get('is_df'))

        cota_declarada = dca_cota_declarada_2025.get(uf)
        cota = 0 if is_df else (cota_declarada if cota_declarada is not None else icms * 0.25)

        r_estado = (icms + fecop) if is_df else (icms - cota + fecop)
        coef_neutro_estado = r_estado / total_br_2025 if total_br_2025 > 0 else 0
        vr_estado = (t4.get('estado_pct') or 0) / 100
        bruto_estado = coef_neutro_estado * (1 + vr_estado)
        brutos_estado[uf] = bruto_estado
        if not is_df:
            # 25% fixo do destino do proprio Estado (CF art. 158, IV, "b"; LC 227/2026 art. 118 par. 3o e 128)
            brutos_muni[uf] = bruto_estado / 3

    soma_bruto = sum(brutos_estado.values()) + sum(brutos_muni.values())
    resultado = {}
    for uf in UFS:
        total = brutos_estado[uf] + brutos_muni.get(uf, 0)
        resultado[uf] = total / soma_bruto * 100 if soma_bruto > 0 else 0
    return resultado


def compute_gobetti_tabela1(gobetti):
    t1 = gobetti['tabela1_static']
    total = t1['total_pos']
    return {u['uf']: u['pos'] / total * 100 for u in t1['ufs']}


def compute_pof_censo(pof, censo):
    despesa = pof['despesa_por_uf']
    domicilios = {uf: v['domicilios_particulares_ocupados'] for uf, v in censo['por_uf'].items()}

    def ponderada(cat, w_alim=0.4, w_saude=0.4, w_edu=0.4):
        outras = (cat['habitacao'] + cat['vestuario'] + cat['transporte'] + cat['higiene'] +
                  cat['recreacao'] + cat['fumo'] + cat['servicos_pessoais'] + cat['despesas_diversas'])
        return cat['alimentacao'] * w_alim + cat['saude'] * w_saude + cat['educacao'] * w_edu + outras

    brutos, ponderados = {}, {}
    for uf in UFS:
        cat = despesa[uf]
        dom = domicilios[uf]
        brutos[uf] = cat['total'] * dom
        ponderados[uf] = ponderada(cat) * dom

    soma_bruto = sum(brutos.values())
    soma_pond = sum(ponderados.values())
    bruto_pct = {uf: brutos[uf] / soma_bruto * 100 for uf in UFS}
    pond_pct = {uf: ponderados[uf] / soma_pond * 100 for uf in UFS}
    return bruto_pct, pond_pct


def main():
    with open(HERE / "reforma-tributaria.json") as f:
        ref_data = json.load(f)
    with open(HERE / "coeficientes-uf.json") as f:
        coeficientes_uf = json.load(f)
    with open(HERE / "gobetti-2023-perdas-ganhos-uf.json") as f:
        gobetti = json.load(f)
    with open(HERE / "pof-2017-2018-despesa-uf.json") as f:
        pof = json.load(f)
    with open(HERE / "censo-2022-domicilios-uf.json") as f:
        censo = json.load(f)

    dca_icms_2025 = ref_data.get('dca_icms_por_uf', {}).get('2025', {})
    dca_iss_2025 = ref_data.get('dca_iss_por_uf', {}).get('2025', {})
    dca_fecop_2025 = ref_data.get('dca_fecop_por_uf', {}).get('2025', {})
    dca_cota_declarada_2025 = ref_data.get('dca_transf_munis_por_uf', {}).get('2025', {})
    total_br_2025 = sum(
        (dca_icms_2025.get(uf, 0) or 0) + (dca_iss_2025.get(uf, 0) or 0) + (dca_fecop_2025.get(uf, 0) or 0)
        for uf in UFS
    )
    t4_by_uf = {u['uf']: u for u in gobetti['tabela4_esferas']['ufs']}

    modelo_anterior = compute_modelo_anterior(dca_icms_2025, dca_iss_2025, dca_fecop_2025,
                                         dca_cota_declarada_2025, total_br_2025, coeficientes_uf, t4_by_uf)
    gobetti_t1 = compute_gobetti_tabela1(gobetti)
    pof_bruto, pof_ponderado = compute_pof_censo(pof, censo)

    por_uf = {}
    for uf in UFS:
        ma = modelo_anterior[uf]
        pb = pof_bruto[uf]
        pp = pof_ponderado[uf]
        por_uf[uf] = {
            "modelo_anterior_pct": ma,
            "gobetti_tabela1_2023_pct": gobetti_t1[uf],
            "pof_censo_bruto_pct": pb,
            "pof_censo_ponderado_pct": pp,
            "despesa_pof_familiar": pof['despesa_por_uf'][uf]['total'],
            "domicilios_censo_2022": censo['por_uf'][uf]['domicilios_particulares_ocupados'],
            "delta_bruto_vs_modelo_pp": pb - ma,
            "delta_ponderado_vs_bruto_pp": pp - pb,
        }

    output = {
        "metodo": (
            "phi_dest_UF = despesa de consumo media mensal familiar (POF 2017-2018, "
            "Tabela 1.1.13) x domicilios particulares ocupados (Censo 2022, tabela SIDRA "
            "9922), normalizado pela soma nacional. Versao ponderada: mesma formula, "
            "substituindo a despesa total pela despesa ponderada por tributabilidade "
            "(Alimentacao, Saude e Educacao x 0,4 -- reducao geral de 60%, EC 132/2023 "
            "art. 9, Sec. 1 -- demais categorias x 1). Nao isola a cesta basica nacional "
            "(aliquota zero, lista especifica de produtos) porque a POF nao separa essa "
            "fatia por UF na tabela usada; e um teste de sensibilidade, nao um mapeamento "
            "fino da legislacao por categoria."
        ),
        "es_gobetti_2025_sefaz_referencia_pct": 1.88,
        "es_gobetti_2025_sefaz_nota": (
            "'IBS hipotetico 2025', apresentacao de Sergio Gobetti a SEFAZ-ES (2026) -- so "
            "disponivel para o ES; nao e um dado por UF, por isso fica fora da tabela "
            "principal, so como referencia de contexto."
        ),
        "por_uf": por_uf,
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {OUT}")
    soma_ma = sum(v["modelo_anterior_pct"] for v in por_uf.values())
    soma_pb = sum(v["pof_censo_bruto_pct"] for v in por_uf.values())
    print(f"Soma modelo anterior: {soma_ma:.4f}% | Soma POF x Censo bruto: {soma_pb:.4f}%")
    print(f"ES: modelo anterior={por_uf['ES']['modelo_anterior_pct']:.4f}% | "
          f"Gobetti Tabela 1={por_uf['ES']['gobetti_tabela1_2023_pct']:.4f}% | "
          f"POF x Censo bruto={por_uf['ES']['pof_censo_bruto_pct']:.4f}% | "
          f"ponderado={por_uf['ES']['pof_censo_ponderado_pct']:.4f}%")


if __name__ == "__main__":
    main()
