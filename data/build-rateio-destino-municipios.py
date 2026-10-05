#!/usr/bin/env python3
"""
ATUALIZACAO (out/2026): o peso do destino proprio deixou de ser renda x populacao e passou a
combinar (i) consumo esperado com elasticidade-renda < 1 (microdados da POF; media e mediana de
renda do Censo 2022) e (ii) compras observadas de cada prefeitura (DCA I-D 2024), conforme
data/rateio_consumo_compras.py e Estudo 17. Com RATEIO_EPS=1 e RATEIO_THETA_M=0 o script reproduz
exatamente a versao anterior. O texto abaixo descreve o desenho original.

Rateio do coeficiente de destino (phi^dest) do IBS entre os municipios
individuais de cada UF, como preparacao para o estudo de repasses do
Seguro-Receita por ente (ADCT art. 132).

O Estudo 06 (estudos/ibs-projecao-arrecadacao-br.html) calcula phi^dest por
esfera (estado e agregado dos municipios) para cada UF a partir de uma
estimativa propria (POF 2017-2018 x Censo 2022, Estudo 13,
data/phi-dest-pof-censo.json): phi_UF (participacao da UF no consumo
nacional) e dividido entre estado e municipios pela proporcao entre as
aliquotas de referencia estadual e municipal do IBS (LC 214/2025 art. 361),
aproximada pela razao ICMS/ISS nacional 2025 e combinada com a cota-parte
municipal de 25% (CF art. 158, IV, "b"; LC 227/2026 arts. 118, par. 3o, e
128) -- ver computeParams() no HTML. Gobetti e Monteiro (IPEA, 2023) deixou
de ser insumo do modelo, mantido so como comparacao (Estudos 07 e 13). Esse
numero, porem, so existe agregado por UF: nao diz quanto do "conjunto dos
municipios do ES" cabe a Vitoria, Serra, Vila Velha etc. individualmente.

O numero agregado por UF, porem, mistura DUAS fontes de receita municipal
que a lei trata de forma diferente:

  (a) COTA-PARTE (25% do IBS estadual, CF art. 158, IV, "b"; LC 227/2026
      arts. 118 par. 3o e 128): resolvida por criterio de RATEIO entre os
      municipios da UF -- 80% populacao + 10% educacao-equidade + 5%
      ambiental + 5% igualitario (art. 128).
  (b) DESTINO PROPRIO do IBS municipal (sucessor do ISS, LC 227/2026 art.
      106): nao e uma cota-parte de nada -- pertence diretamente ao
      municipio onde o consumo ocorreu, resolvida por CRITERIO DE DESTINO,
      nao por rateio populacional.

Ate a correcao desta versao, o script tratava as duas fontes como um bolo
unico, repartido so pelo criterio de rateio (a) -- correto para a
cota-parte, mas uma aproximacao grosseira para o destino proprio, que por
lei deveria seguir o consumo de cada cidade, nao sua populacao.

Decomposicao (nenhum dado novo necessario -- so reorganiza o que ja e
calculado): como fracMuni_UF = (r_M + 0,25 r_E)/(r_E+r_M) e fracEstado_UF =
0,75 r_E/(r_E+r_M) (ver data/build-phi-dest-pof-censo.py), a fatia de
cota-parte e exatamente 1/3 da fatia estadual (0,25/0,75 = 1/3):

    cota_parte_UF  = Estado_UF / 3
    propria_UF     = Municipio_UF - cota_parte_UF

Metodo do rateio intra-UF, agora em duas contas separadas:

  cota_parte_m = cota_parte_UF x [0,95 x (pop_m / pop_UF) + 0,05 x (1/n_municipios_UF)]
      -- criterio do art. 128 (80% populacao + 5% igualitario; os 10%
      educacao-equidade + 5% ambiental dependem de indicadores nao
      fixados por nenhum Estado, aproximados aqui pelo criterio
      populacional do inciso I).

  propria_m = propria_UF x [(renda_m x pop_m) / soma_UF(renda x pop)]
      -- proxy de intensidade de consumo por municipio: renda domiciliar
      per capita media (Censo 2022, SIDRA tabela 10295,
      data/collect-censo-2022-renda-municipios.py) x populacao, no mesmo
      espirito da formula POF x Censo usada em nivel de UF (Estudo 13),
      ja que a POF nao abre por municipio. LIMITACAO CONHECIDA: consumo e
      uma funcao concava da renda (familias mais pobres consomem quase
      100% do que ganham; mais ricas poupam uma fracao maior) -- este
      proxy tende a superestimar a fatia de municipios mais ricos. Sem
      dado publico de propensao a consumir por municipio para corrigir
      isso; documentado, nao escondido.

  phi_dest_m = cota_parte_m + propria_m

Populacao: media aritmetica 2019-2026 (IBGE), a mesma serie ja usada para o
teto per capita do Seguro-Receita (LC 227/2026 art. 117, par. 3o-6o) em
data/populacao-municipios-media-2019-2026.json.

Por construcao, a soma dos phi_dest_m de uma UF reproduz exatamente o
phi_dest agregado dessa UF (os pesos de cada conta somam 1 dentro da UF), e
portanto o agregado nacional tambem se preserva -- verificado abaixo.

DF fica de fora (sem esfera municipal propria, art. 115 LC 227/2026).

Uso:
  python3 build-rateio-destino-municipios.py
"""

import json
from pathlib import Path
from fundos_art115b import fold
import rateio_consumo_compras as rcc

HERE = Path(__file__).parent
OUT = HERE / "rateio-destino-municipios.json"

UFS = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT',
       'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']


def compute_params(dca_icms_2025, dca_iss_2025, dca_fecop_2025, dca_cota_declarada_2025,
                    total_br_2025, coeficientes_uf, phi_dest_data, dca_outras_deducoes_2025=None):
    """Replica computeParams() de estudos/ibs-projecao-arrecadacao-br.html."""
    dca_outras_deducoes_2025 = dca_outras_deducoes_2025 or {}
    phi_dest_por_uf = phi_dest_data['por_uf']
    # Fracao estadual/municipal (art. 361 LC 214/2025: media 2024-2025 da razao receita de
    # referencia/PIB por esfera), calculada uma unica vez em build-phi-dest-pof-censo.py.
    frac_estado = phi_dest_data['frac_estado_pct'] / 100
    frac_muni = phi_dest_data['frac_muni_pct'] / 100

    params = {}
    for uf in UFS:
        icms = dca_icms_2025.get(uf, 0) or 0
        iss = dca_iss_2025.get(uf, 0) or 0
        fecop = dca_fecop_2025.get(uf, 0) or 0
        outras = dca_outras_deducoes_2025.get(uf, 0) or 0
        cuf = coeficientes_uf['por_uf'].get(uf, {})
        is_df = bool(cuf.get('is_df'))

        cota_declarada = dca_cota_declarada_2025.get(uf)
        cota = 0 if is_df else (cota_declarada if cota_declarada is not None else icms * 0.25)

        # DF não tem esfera municipal própria: soma-se +iss à sua receita "estadual".
        r_estado = (icms - outras + iss + fecop) if is_df else (icms - outras - cota + fecop)
        r_muni = None if is_df else (iss + cota)

        coef_neutro_estado = r_estado / total_br_2025 if total_br_2025 > 0 else 0
        coef_neutro_muni = (r_muni / total_br_2025) if (r_muni is not None and total_br_2025 > 0) else None

        # phi^dest: estimativa propria (POF x Censo, Estudo 13) -- Gobetti e Monteiro deixou de
        # ser insumo do modelo (fica so como comparacao, Estudos 07/13).
        # Coeficientes por esfera; com compras governamentais ativas (rcc.THETA_M > 0) vêm de
        # phi-dest-pof-censo.json (coef_*_compras_pct), senão da fórmula original phi_UF x frac.
        coef_pleno_estado, coef_pleno_muni = rcc.esferas_uf(phi_dest_por_uf.get(uf, {}), is_df, frac_estado, frac_muni)

        # Decomposicao da fatia municipal: cota-parte (1/3 da fatia estadual, ja que
        # 0,25/0,75 = 1/3) vs. destino proprio (o resto) -- ver docstring do modulo.
        cota_parte_uf = None if is_df else coef_pleno_estado / 3
        propria_uf = None if is_df else coef_pleno_muni - cota_parte_uf

        params[uf] = {
            'estado': {'coefNeutro': coef_neutro_estado, 'coefPleno': coef_pleno_estado},
            'municipio': None if r_muni is None else {
                'coefNeutro': coef_neutro_muni, 'coefPleno': coef_pleno_muni,
                'cotaParte': cota_parte_uf, 'propria': propria_uf,
            },
        }
    return params


def main():
    with open(HERE / "reforma-tributaria.json") as f:
        ref_data = fold(json.load(f))
    with open(HERE / "coeficientes-uf.json") as f:
        coeficientes_uf = json.load(f)
    with open(HERE / "phi-dest-pof-censo.json") as f:
        phi_dest_data = json.load(f)
    with open(HERE / "coeficientes-municipios.json") as f:
        cpt_municipios = json.load(f)
    with open(HERE / "populacao-municipios-media-2019-2026.json") as f:
        pop_municipios = json.load(f)['municipios']
    with open(HERE / "censo-2022-renda-municipios.json") as f:
        renda_municipios = json.load(f)['municipios']
    rend_medias, rend_medianas, compras_json = rcc.carrega_entradas()

    dca_icms_2025 = ref_data.get('dca_icms_por_uf', {}).get('2025', {})
    dca_iss_2025 = ref_data.get('dca_iss_por_uf', {}).get('2025', {})
    dca_fecop_2025 = ref_data.get('dca_fecop_por_uf', {}).get('2025', {})
    dca_cota_declarada_2025 = ref_data.get('dca_transf_munis_por_uf', {}).get('2025', {})
    dca_outras_deducoes_2025 = ref_data.get('dca_icms_outras_deducoes_por_uf', {}).get('2025', {})
    total_br_2025 = sum(
        (dca_icms_2025.get(uf, 0) or 0) - (dca_outras_deducoes_2025.get(uf, 0) or 0)
        + (dca_iss_2025.get(uf, 0) or 0) + (dca_fecop_2025.get(uf, 0) or 0)
        for uf in UFS
    )
    params = compute_params(dca_icms_2025, dca_iss_2025, dca_fecop_2025, dca_cota_declarada_2025,
                             total_br_2025, coeficientes_uf, phi_dest_data, dca_outras_deducoes_2025)

    municipios_por_uf = {}
    for cod, r in cpt_municipios['municipios'].items():
        municipios_por_uf.setdefault(r['uf'], []).append((cod, r))

    # Compras governamentais (Estudo 17): base por município e participação de cada UF nas
    # compras municipais; usadas só se THETA_M > 0.
    pops_por_uf = {uf: {cod: pop_municipios[cod]['pop_media'] for cod, r in lst if cod in pop_municipios}
                   for uf, lst in municipios_por_uf.items() if uf != 'DF'}
    compras_mun, n_compras_imputadas, teto_pc = rcc.compras_municipais(compras_json, pops_por_uf)
    compras_uf = {uf: sum(compras_mun[c] for c in pops) for uf, pops in pops_por_uf.items()}
    compras_br = sum(compras_uf.values())
    phi_fam_uf = {uf: ((phi_dest_data['por_uf'].get(uf, {}).get('phi_fam_pct', phi_dest_data['por_uf'].get(uf, {}).get('pof_censo_bruto_pct'))) or 0) / 100 for uf in UFS}

    resultado = {}
    validacao_uf = {}
    municipios_sem_renda = []
    for uf, lst in municipios_por_uf.items():
        if uf == 'DF':
            continue
        n_municipios_uf = len(lst)
        total_pop_uf = sum(pop_municipios[cod]['pop_media'] for cod, r in lst if cod in pop_municipios)

        # Fallback para o(s) municipio(s) sem dado de renda no Censo 2022 (amostra insuficiente
        # em municipios muito pequenos): usa a media de renda per capita dos demais municipios
        # da mesma UF que tem dado.
        rendas_uf = [renda_municipios[cod]['renda_domiciliar_per_capita_2022'] for cod, r in lst if cod in renda_municipios]
        renda_media_uf = sum(rendas_uf) / len(rendas_uf) if rendas_uf else 0

        # Peso de consumo (microdados da POF): populacao x E[y^eps] com a media e a mediana
        # de renda do Censo 2022 (lognormal); municipio sem renda no Censo recebe a media da UF.
        pops_uf = {cod: pop_municipios.get(cod, {}).get('pop_media', 0) for cod, r in lst}
        medias_uf, medianas_uf = {}, {}
        for cod, r in lst:
            if cod in renda_municipios:
                medias_uf[cod] = rend_medias[cod]
                medianas_uf[cod] = rend_medianas.get(cod)
            else:
                medias_uf[cod] = renda_media_uf
                medianas_uf[cod] = None
                municipios_sem_renda.append(cod)
        pesos_cons_uf = rcc.pesos_consumo(pops_uf, medias_uf, medianas_uf)
        total_cons_uf = sum(pesos_cons_uf.values())
        # Peso de compras (Estudo 17): despesa de compras da prefeitura (DCA I-D 2024)
        total_compras_uf = sum(compras_mun.get(cod, 0) for cod, r in lst) or 1.0
        s_M_uf = (compras_uf.get(uf, 0) / compras_br) if compras_br else 0.0
        phi_f = phi_fam_uf.get(uf, 0)
        denom = (1 - rcc.THETA_M) * phi_f + rcc.THETA_M * s_M_uf
        theta_uf = (rcc.THETA_M * s_M_uf / denom) if denom > 0 else 0.0

        muni_agregado = params[uf]['municipio']
        cota_parte_agregado_uf = (muni_agregado['cotaParte'] * 100) if muni_agregado else 0
        propria_agregado_uf = (muni_agregado['propria'] * 100) if muni_agregado else 0
        dest_agregado_uf = (muni_agregado['coefPleno'] * 100) if muni_agregado else 0

        soma_verif = 0.0
        for cod, r in lst:
            pop_media = pop_municipios.get(cod, {}).get('pop_media', 0)
            renda_pc = medias_uf[cod]

            peso_pop = (pop_media / total_pop_uf) if total_pop_uf > 0 else 0
            peso_igual = 1 / n_municipios_uf if n_municipios_uf > 0 else 0
            # Art. 128, LC 227/2026: 80% populacao + 5% igualitario, valores exatos da lei; os
            # 10% (educacao-equidade) + 5% (ambiental) restantes dependem de indicadores fixados
            # por lei estadual, que nenhum Estado regulamentou ainda -- aproximados aqui por
            # populacao (mesmo criterio do inciso I), o que da 95% populacao + 5% igualitario.
            peso_cota_parte = 0.95 * peso_pop + 0.05 * peso_igual

            # Destino proprio: proxy de intensidade de consumo (renda per capita x populacao),
            # analogo a formula POF x Censo do Estudo 13 -- ver docstring do modulo.
            peso_cons = (pesos_cons_uf[cod] / total_cons_uf) if total_cons_uf > 0 else 0
            peso_compras = compras_mun.get(cod, 0) / total_compras_uf
            peso_propria = (1 - theta_uf) * peso_cons + theta_uf * peso_compras

            cota_parte_m = cota_parte_agregado_uf * peso_cota_parte
            propria_m = propria_agregado_uf * peso_propria
            phi_dest_m = cota_parte_m + propria_m
            soma_verif += phi_dest_m
            resultado[cod] = {
                'nome': r['nome'],
                'uf': uf,
                'pop_media': pop_media,
                'renda_domiciliar_per_capita_2022': renda_pc,
                'peso_intra_uf_cota_parte': peso_cota_parte,
                'peso_intra_uf_propria': peso_propria,
                'renda_mediana_domiciliar_per_capita_2022': medianas_uf[cod],
                'peso_consumo_bruto': pesos_cons_uf[cod],
                'compras_base_reais': compras_mun.get(cod, 0),
                'peso_intra_uf_propria_consumo': peso_cons,
                'peso_intra_uf_propria_compras': peso_compras,
                'theta_compras_uf': theta_uf,
                'cota_parte_pct': cota_parte_m,
                'propria_pct': propria_m,
                'phi_dest_pct': phi_dest_m,
            }
        validacao_uf[uf] = {
            'phi_dest_agregado_uf': dest_agregado_uf,
            'soma_phi_dest_individuais': soma_verif,
            'diff': soma_verif - dest_agregado_uf,
        }

    soma_nacional = sum(r['phi_dest_pct'] for r in resultado.values())
    soma_nacional_esperada = sum(
        params[uf]['municipio']['coefPleno'] * 100 for uf in UFS if params[uf]['municipio']
    )

    output = {
        'fonte': (
            "Versao com funcao de consumo (microdados da POF) e compras governamentais -- ver "
            "data/rateio_consumo_compras.py e Estudo 17. Rateio derivado, em duas contas separadas: (a) cota-parte (25% do destino do "
            "Estado, CF art. 158, IV, 'b'; LC 227/2026 arts. 118 par. 3o e 128), repartida entre "
            "municipios pelo criterio do art. 128 da LC 227/2026 (80% populacao + 10% "
            "educacao-equidade + 5% ambiental + 5% igualitario); (b) destino proprio do IBS "
            "municipal (sucessor do ISS, LC 227/2026 art. 106), repartido por um proxy de "
            "intensidade de consumo (populacao x consumo esperado com elasticidade-renda < 1, a partir "
            "da media e da mediana de renda do Censo 2022, SIDRA 10295) combinada com as compras "
            "observadas de cada prefeitura (DCA I-D 2024). Populacao: data/populacao-municipios-media-2019-2026.json "
            "(IBGE, media 2019-2026). Renda: data/censo-2022-renda-municipios.json."
        ),
        'metodo': (
            "cota_parte_m = cota_parte_UF x [0,95 x (pop_m/pop_UF) + 0,05 x (1/n_municipios_UF)] "
            "-- os 80% populacao + 5% igualitario do art. 128 aplicados exatamente como na lei; os "
            "10% educacao-equidade + 5% ambiental (art. 128, incisos II e III) dependem de "
            "indicadores ainda nao fixados por lei estadual em nenhuma UF, aproximados pelo "
            "criterio populacional do inciso I (95% populacao + 5% igualitario, na pratica). "
            "propria_m = propria_UF x [(1 - theta_UF) x peso_consumo_m + theta_UF x peso_compras_m]; "
            "peso_consumo_m = pop_m x E[y^e] / soma_UF (y lognormal com a media e a mediana de renda do "
            "municipio; e = elasticidade-renda do consumo, POF 2017-18 microdados); peso_compras_m = "
            "compras_m / soma_UF(compras); theta_UF = parte das compras no IBS municipal proprio da UF. "
            "phi_dest_m = cota_parte_m + propria_m. cota_parte_UF e "
            "propria_UF vem da decomposicao de Municipio_UF em build-rateio-destino-municipios.py "
            "(cota_parte_UF = Estado_UF/3; propria_UF = Municipio_UF - cota_parte_UF)."
        ),
        'limitacao_proxy_renda': (
            "A elasticidade-renda do consumo (e = 0,80) vem dos microdados da POF por familia e e "
            "aplicada a distribuicao de renda de cada municipio aproximada por uma lognormal com a "
            "media e a mediana do Censo 2022; a curva real nao e de elasticidade constante (0,47 nos 20% "
            "mais pobres a 0,89 na faixa de 50% a 80%). As compras sao uma proxy bruta (DCA I-D, soma de "
            "elementos de despesa), sem descontar fornecedores do Simples/MEI nem dispensas presenciais, "
            "e limitadas ao percentil 99 nacional por habitante; ver Estudo 17."
        ),
        'parametros': {
            'elasticidade_consumo': rcc.EPS, 'theta_compras_municipal': rcc.THETA_M,
            'theta_compras_estadual': rcc.THETA_E, 'teto_compras_per_capita_percentil': rcc.TETO_P,
            'teto_compras_per_capita_reais': teto_pc, 'n_municipios_compras_imputadas': n_compras_imputadas,
            'cota_parte_incide_sobre_compras_estaduais': True,
        },
        'total_br_2025': total_br_2025,
        'n_municipios': len(resultado),
        'n_municipios_sem_renda_censo': len(set(municipios_sem_renda)),
        'municipios_sem_renda_censo': sorted(set(municipios_sem_renda)),
        'municipios': resultado,
        'validacao_soma_por_uf': validacao_uf,
        'validacao_soma_nacional': {
            'soma_individuais': soma_nacional,
            'soma_esperada_agregados_uf': soma_nacional_esperada,
            'diff': soma_nacional - soma_nacional_esperada,
        },
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Salvo em {OUT}")
    print(f"Municipios: {len(resultado)}")
    print(f"Soma nacional phi_dest individual: {soma_nacional:.4f}% | esperado: {soma_nacional_esperada:.4f}% | "
          f"diff: {soma_nacional - soma_nacional_esperada:+.8f}pp")
    maior_diff_uf = max(validacao_uf.items(), key=lambda kv: abs(kv[1]['diff']))
    print(f"Maior divergencia soma-individual vs. agregado por UF: {maior_diff_uf[0]} "
          f"({maior_diff_uf[1]['diff']:+.8f}pp)")
    print(f"Municipios sem dado de renda no Censo 2022 (fallback = media da UF): "
          f"{len(set(municipios_sem_renda))} -> {sorted(set(municipios_sem_renda))}")


if __name__ == "__main__":
    main()
