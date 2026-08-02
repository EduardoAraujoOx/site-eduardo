#!/usr/bin/env python3
"""
Rateio do coeficiente de destino (phi^dest) do IBS entre os municipios
individuais de cada UF, como preparacao para o estudo de repasses do
Seguro-Receita por ente (ADCT art. 132).

O Estudo 06 (estudos/ibs-projecao-arrecadacao-br.html) ja calcula phi^dest
por esfera (estado e agregado dos municipios) para cada UF, deslocando
phi^neutro pela variacao relativa (vr) do saldo real de Gobetti e Monteiro
(tabela4_esferas) e normalizando para conservar o total nacional (ver
computeParams() no HTML). Esse numero, porem, so existe agregado por UF: nao
diz quanto de "conjunto dos municipios do ES" cabe a Vitoria, Serra, Vila
Velha etc. individualmente -- e o proprio paper de Gobetti e Monteiro nao
publica essa granularidade (a Tabela 2 tras so o saldo somado dos
municipios de cada UF).

Metodo: repartir o phi^dest agregado da camada municipal de cada UF entre
seus municipios individuais, proporcionalmente ao peso de cada um no
phi^CPT (Coeficiente de Participacao de Transicao, media historica
2019-2025, ja validado em data/coeficientes-municipios.json). A escolha da
media historica como peso do rateio (em vez do resultado isolado de 2025)
foi checada empiricamente para o ES: correlacao de 0,996 entre os dois
pesos, mas 5 dos 78 municipios nao tem nenhuma declaracao em 2025 (entre
eles Cariacica, que nao e pequeno), e a divergencia relativa para
municipios menores chega a 20-50% num ano isolado -- a media de 7 anos e
mais robusta para um rateio entre milhares de entes.

    phi_dest_m = phi_dest_agregado_UF x (phi_cpt_m / soma(phi_cpt_m' em UF))

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
        vr_muni = (t4.get('muni_pct') / 100) if t4.get('muni_pct') is not None else None

        bruto_estado = coef_neutro_estado * (1 + vr_estado)
        bruto_muni = (coef_neutro_muni * (1 + vr_muni)) if (coef_neutro_muni is not None and vr_muni is not None) else None

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
        total_cpt_uf = sum(r['coeficiente_pct'] for cod, r in lst)
        dest_agregado_uf = (params[uf]['municipio']['coefPleno'] * 100) if params[uf]['municipio'] else 0
        soma_verif = 0.0
        for cod, r in lst:
            peso = (r['coeficiente_pct'] / total_cpt_uf) if total_cpt_uf > 0 else 0
            phi_dest_m = dest_agregado_uf * peso
            soma_verif += phi_dest_m
            resultado[cod] = {
                'nome': r['nome'],
                'uf': uf,
                'phi_cpt_pct': r['coeficiente_pct'],
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
            "Rateio derivado: phi_dest agregado por UF (estudos/ibs-projecao-arrecadacao-br.html, "
            "computeParams) repartido entre municipios pelo peso de cada um em "
            "data/coeficientes-municipios.json (phi^CPT, media historica 2019-2025)"
        ),
        'metodo': (
            "phi_dest_m = phi_dest_agregado_UF x (phi_cpt_m / soma(phi_cpt_m' na mesma UF)). "
            "Pressupoe que, dentro de uma UF, o efeito do criterio destino e proporcional ao peso "
            "historico do municipio (phi^CPT) -- simplificacao necessaria porque Gobetti e Monteiro "
            "(2023) so publicam o saldo do criterio destino agregado por UF, nao por municipio."
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
