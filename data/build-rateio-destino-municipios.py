#!/usr/bin/env python3
"""
Rateio do coeficiente de destino (phi^dest) do IBS entre os municipios
individuais de cada UF, como preparacao para o estudo de repasses do
Seguro-Receita por ente (ADCT art. 132).

O Estudo 06 (estudos/ibs-projecao-arrecadacao-br.html) calcula phi^dest por
esfera (estado e agregado dos municipios) para cada UF: a fatia estadual
desloca phi^neutro pela variacao relativa real de Gobetti e Monteiro
(tabela4_esferas); a fatia municipal e, desde ago/2026, exatamente 25% da
fatia estadual da mesma UF -- fracao fixa e nacionalmente uniforme definida
em CF art. 158, IV, "b", e LC 227/2026 arts. 118, par. 3o, e 128 (ver
computeParams() no HTML). Esse numero, porem, so existe agregado por UF: nao
diz quanto do "conjunto dos municipios do ES" cabe a Vitoria, Serra, Vila
Velha etc. individualmente.

Metodo: repartir o phi^dest agregado da camada municipal de cada UF entre
seus municipios individuais pelo criterio do proprio art. 128 da LC
227/2026: 80% na proporcao da populacao, 10% por indicadores de
educacao-equidade, 5% por indicadores ambientais (ambos fixados por lei
estadual -- nenhum Estado regulamentou ainda, por isso aproximados aqui pelo
mesmo criterio populacional do inciso I) e 5% em montantes iguais entre os
municipios da UF. Na pratica, ate que os Estados regulamentem os
indicadores, o peso equivale a 95% populacao + 5% igualitario:

    phi_dest_m = phi_dest_agregado_UF x [0,95 x (pop_m / pop_UF) + 0,05 x (1/n_municipios_UF)]

Populacao: media aritmetica 2019-2026 (IBGE), a mesma serie ja usada para o
teto per capita do Seguro-Receita (LC 227/2026 art. 117, par. 3o-6o) em
data/populacao-municipios-media-2019-2026.json.

Por construcao, a soma dos phi_dest_m de uma UF reproduz exatamente o
phi_dest agregado dessa UF (os pesos somam 1), e portanto o agregado
nacional tambem se preserva -- verificado abaixo.

DF fica de fora (sem esfera municipal propria, art. 115 LC 227/2026).

Uso:
  python3 build-rateio-destino-municipios.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "rateio-destino-municipios.json"

UFS = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT',
       'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']


def compute_params(dca_icms_2025, dca_iss_2025, dca_fecop_2025, dca_cota_declarada_2025,
                    total_br_2025, coeficientes_uf, t4_by_uf):
    """Replica computeParams() de estudos/ibs-projecao-arrecadacao-br.html."""
    params = {}
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
        r_muni = None if is_df else (iss + cota)

        coef_neutro_estado = r_estado / total_br_2025 if total_br_2025 > 0 else 0
        coef_neutro_muni = (r_muni / total_br_2025) if (r_muni is not None and total_br_2025 > 0) else None

        vr_estado = (t4.get('estado_pct') or 0) / 100

        bruto_estado = coef_neutro_estado * (1 + vr_estado)
        # Cota-parte municipal do IBS-destino: 25% fixo e nacionalmente uniforme sobre o destino
        # do proprio Estado (CF art. 158, IV, "b"; LC 227/2026 arts. 118, par. 3o, e 128) -- nao a
        # variacao especifica por UF estimada por Gobetti e Monteiro (efeito de consumo, nao a
        # regra legal de partilha).
        bruto_muni = (bruto_estado / 3) if coef_neutro_muni is not None else None

        params[uf] = {
            'estado': {'coefNeutro': coef_neutro_estado, 'bruto': bruto_estado},
            'municipio': None if r_muni is None else {'coefNeutro': coef_neutro_muni, 'bruto': bruto_muni},
        }

    soma_bruto = sum(
        (params[uf]['estado']['bruto'] or 0) + ((params[uf]['municipio'] or {}).get('bruto') or 0)
        for uf in UFS
    )
    for uf in UFS:
        p = params[uf]
        p['estado']['coefPleno'] = (p['estado']['bruto'] / soma_bruto) if soma_bruto > 0 else 0
        if p['municipio']:
            p['municipio']['coefPleno'] = (p['municipio']['bruto'] / soma_bruto) if soma_bruto > 0 else 0
    return params


def main():
    with open(HERE / "reforma-tributaria.json") as f:
        ref_data = json.load(f)
    with open(HERE / "coeficientes-uf.json") as f:
        coeficientes_uf = json.load(f)
    with open(HERE / "gobetti-2023-perdas-ganhos-uf.json") as f:
        gobetti = json.load(f)
    with open(HERE / "coeficientes-municipios.json") as f:
        cpt_municipios = json.load(f)
    with open(HERE / "populacao-municipios-media-2019-2026.json") as f:
        pop_municipios = json.load(f)['municipios']

    dca_icms_2025 = ref_data.get('dca_icms_por_uf', {}).get('2025', {})
    dca_iss_2025 = ref_data.get('dca_iss_por_uf', {}).get('2025', {})
    dca_fecop_2025 = ref_data.get('dca_fecop_por_uf', {}).get('2025', {})
    dca_cota_declarada_2025 = ref_data.get('dca_transf_munis_por_uf', {}).get('2025', {})
    total_br_2025 = sum(
        (dca_icms_2025.get(uf, 0) or 0) + (dca_iss_2025.get(uf, 0) or 0) + (dca_fecop_2025.get(uf, 0) or 0)
        for uf in UFS
    )
    t4_by_uf = {u['uf']: u for u in gobetti['tabela4_esferas']['ufs']}

    params = compute_params(dca_icms_2025, dca_iss_2025, dca_fecop_2025, dca_cota_declarada_2025,
                             total_br_2025, coeficientes_uf, t4_by_uf)

    municipios_por_uf = {}
    for cod, r in cpt_municipios['municipios'].items():
        municipios_por_uf.setdefault(r['uf'], []).append((cod, r))

    resultado = {}
    validacao_uf = {}
    for uf, lst in municipios_por_uf.items():
        if uf == 'DF':
            continue
        n_municipios_uf = len(lst)
        total_pop_uf = sum(pop_municipios[cod]['pop_media'] for cod, r in lst if cod in pop_municipios)
        dest_agregado_uf = (params[uf]['municipio']['coefPleno'] * 100) if params[uf]['municipio'] else 0
        soma_verif = 0.0
        for cod, r in lst:
            pop_media = pop_municipios.get(cod, {}).get('pop_media', 0)
            peso_pop = (pop_media / total_pop_uf) if total_pop_uf > 0 else 0
            peso_igual = 1 / n_municipios_uf if n_municipios_uf > 0 else 0
            # Art. 128, LC 227/2026: 80% populacao + 5% igualitario, valores exatos da lei; os
            # 10% (educacao-equidade) + 5% (ambiental) restantes dependem de indicadores fixados
            # por lei estadual, que nenhum Estado regulamentou ainda -- aproximados aqui por
            # populacao (mesmo criterio do inciso I), o que da 95% populacao + 5% igualitario.
            peso = 0.95 * peso_pop + 0.05 * peso_igual
            phi_dest_m = dest_agregado_uf * peso
            soma_verif += phi_dest_m
            resultado[cod] = {
                'nome': r['nome'],
                'uf': uf,
                'pop_media': pop_media,
                'peso_intra_uf': peso,
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
            "Rateio derivado: phi_dest agregado por UF (25% fixo do destino do Estado, CF art. "
            "158, IV, 'b'; LC 227/2026 arts. 118 par. 3o e 128) repartido entre municipios pelo "
            "criterio do art. 128 da LC 227/2026: 80% populacao + 10% educacao-equidade + 5% "
            "ambiental + 5% igualitario. Populacao: data/populacao-municipios-media-2019-2026.json "
            "(IBGE, media 2019-2026)."
        ),
        'metodo': (
            "phi_dest_m = phi_dest_agregado_UF x [0,95 x (pop_m / pop_UF) + 0,05 x (1/n_municipios_UF)]. "
            "Os 80% de populacao e os 5% igualitarios do art. 128 sao aplicados exatamente como na "
            "lei; os 10% de educacao-equidade e 5% ambiental (art. 128, incisos II e III) dependem "
            "de indicadores ainda nao fixados por lei estadual em nenhuma UF, e por isso sao "
            "aproximados aqui pelo mesmo criterio populacional do inciso I -- ficando, na pratica, "
            "95% populacao + 5% igualitario. Ajustar quando os Estados regulamentarem esses "
            "indicadores."
        ),
        'total_br_2025': total_br_2025,
        'n_municipios': len(resultado),
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


if __name__ == "__main__":
    main()
