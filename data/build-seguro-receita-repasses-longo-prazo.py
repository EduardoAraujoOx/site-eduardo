#!/usr/bin/env python3
"""
Repasses do Seguro-Receita (ADCT art. 132, EC 132/2023), 2029-2077 -- extensão
do Estudo 12 (build-seguro-receita-repasses.py, 2029-2033) para todo o
cronograma de transição histórico->destino (ADCT art. 131, §1º), usando o
bolo/IBS-destino estendido em ibs-projecao-longo-prazo.json.

Só o horizonte de anos muda em relação ao Estudo 12: entidades, denom_capado
(receita de referência ajustada, teto per capita) e phi_dest de cada ente são
os MESMOS, fixos, calculados uma única vez a partir do mesmo dado 2025 -- ver
build-seguro-receita-repasses.py para o texto legal completo (art. 117 LC
227/2026) e as simplificações já documentadas lá (mensal->anual, população
média 2019-2026, etc.), que valem igualmente aqui.

O único número que cresce ano a ano é o numerador (IBS-destino recebido pelo
ente, que cresce com o bolo nacional projetado); o pool do Seguro-Receita
(5% do IBS-destino líquido de CGIBS) também vem de ibs-projecao-longo-prazo.json,
ano a ano, até 2077 (a lei só reduz esse percentual a partir de 2078).

Diferença de formato em relação ao Estudo 12: o nivelamento ainda roda
sobre as 5.596 entidades individuais (todos os municípios competem pelo
mesmo fundo, exatamente como na lei), mas a SAÍDA grava só o agregado por
UF/esfera (estado, municípios somados) -- que é tudo que a página
ibs-projecao-longo-prazo.html consome (buildRepasseIndex agrega por UF de
qualquer forma). Gravar as 5.596 linhas × 49 anos individualmente geraria
um JSON de ~80&nbsp;MB só para ser somado no navegador; o Estudo 12
(estudos/seguro-receita-repasses.html), que mostra o repasse por
município, continua com o detalhe completo em
data/seguro-receita-repasses.json -- não alterado por este script.

Uso: python3 build-seguro-receita-repasses-longo-prazo.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "seguro-receita-repasses-longo-prazo.json"

UFS = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT',
       'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']
ANO_FIM = 2077


def compute_params_estado(dca_icms_2025, dca_iss_2025, dca_fecop_2025, dca_cota_declarada_2025,
                           total_br_2025, coeficientes_uf, t4_by_uf):
    """Idêntico a build-seguro-receita-repasses.py -- replica computeParams() do Estudo 06."""
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
        # do proprio Estado (CF art. 158, IV, "b"; LC 227/2026 arts. 118, par. 3o, e 128).
        bruto_muni = (bruto_estado / 3) if coef_neutro_muni is not None else None

        params[uf] = {
            'is_df': is_df,
            'coef_cpt_estado': (cuf.get('coeficiente_estado_pct') or 0) / 100,
            'coef_cpt_total': (cuf.get('coeficiente_total_pct') or 0) / 100,
            'iss_2025': iss,
            'bruto_estado': bruto_estado,
            'bruto_muni': bruto_muni,
        }

    soma_bruto = sum(
        (params[uf]['bruto_estado'] or 0) + (params[uf]['bruto_muni'] or 0)
        for uf in UFS
    )
    for uf in UFS:
        p = params[uf]
        p['phi_dest_estado'] = (p['bruto_estado'] / soma_bruto) if soma_bruto > 0 else 0
        p['phi_dest_muni_agregado'] = (p['bruto_muni'] / soma_bruto) if (soma_bruto > 0 and p['bruto_muni'] is not None) else None
    return params


def water_fill(entidades, pool):
    """entidades: lista de (numerador, denom_capado). Retorna lista de repasses na mesma ordem."""
    if pool <= 0 or not entidades:
        return [0.0] * len(entidades)

    def total_pago(L):
        return sum(max(0.0, L * d - n) for n, d in entidades)

    lo = min(n / d for n, d in entidades if d > 0)
    hi = lo + 1.0
    total_denom = sum(d for _, d in entidades)
    while total_pago(hi) < pool:
        hi = lo + (hi - lo) * 2 if hi > lo else hi + pool / total_denom + 1
    for _ in range(100):
        mid = (lo + hi) / 2
        if total_pago(mid) < pool:
            lo = mid
        else:
            hi = mid
    L = (lo + hi) / 2
    return [max(0.0, L * d - n) for n, d in entidades]


def main():
    with open(HERE / "reforma-tributaria.json") as f:
        ref_data = json.load(f)
    with open(HERE / "coeficientes-uf.json") as f:
        coeficientes_uf = json.load(f)
    with open(HERE / "coeficientes-municipios.json") as f:
        coeficientes_municipios = json.load(f)
    with open(HERE / "gobetti-2023-perdas-ganhos-uf.json") as f:
        gobetti = json.load(f)
    with open(HERE / "rateio-destino-municipios.json") as f:
        rateio_muni = json.load(f)
    with open(HERE / "ibs-projecao-longo-prazo.json") as f:
        nacional = json.load(f)
    with open(HERE / "populacao-uf-media-2019-2026.json") as f:
        pop_uf = json.load(f)
    with open(HERE / "populacao-municipios-media-2019-2026.json") as f:
        pop_muni = json.load(f)

    dca_icms_2025 = ref_data.get('dca_icms_por_uf', {}).get('2025', {})
    dca_iss_2025 = ref_data.get('dca_iss_por_uf', {}).get('2025', {})
    dca_fecop_2025 = ref_data.get('dca_fecop_por_uf', {}).get('2025', {})
    dca_cota_declarada_2025 = ref_data.get('dca_transf_munis_por_uf', {}).get('2025', {})
    total_br_2025 = sum(
        (dca_icms_2025.get(uf, 0) or 0) + (dca_iss_2025.get(uf, 0) or 0) + (dca_fecop_2025.get(uf, 0) or 0)
        for uf in UFS
    )
    t4_by_uf = {u['uf']: u for u in gobetti['tabela4_esferas']['ufs']}
    params_estado = compute_params_estado(dca_icms_2025, dca_iss_2025, dca_fecop_2025,
                                           dca_cota_declarada_2025, total_br_2025, coeficientes_uf, t4_by_uf)

    pop_by_uf = {uf: v['pop_media'] for uf, v in pop_uf['ufs'].items()}

    nac_by_year = {r['ano']: r for r in nacional['projecao']}
    anos = sorted(a for a in nac_by_year if a <= ANO_FIM)

    entidades = []
    for uf in UFS:
        p = params_estado[uf]
        denom = (p['coef_cpt_total'] if p['is_df'] else p['coef_cpt_estado']) * total_br_2025
        entidades.append({
            'id': f'UF-{uf}', 'nome': uf, 'uf': uf, 'esfera': 'estado', 'is_df': p['is_df'],
            'denom': denom, 'phi_dest': p['phi_dest_estado'],
            'pop': pop_by_uf.get(uf, 0),
        })

    for cod, r in coeficientes_municipios['municipios'].items():
        rd = rateio_muni['municipios'].get(cod)
        pm = pop_muni['municipios'].get(cod)
        if rd is None or pm is None:
            continue
        entidades.append({
            'id': f'MUN-{cod}', 'nome': r['nome'], 'uf': r['uf'], 'esfera': 'municipio', 'is_df': False,
            'denom': r['receita_media_referencia'], 'phi_dest': rd['phi_dest_pct'] / 100,
            'pop': pm['pop_media'],
        })

    print(f"Total de entidades: {len(entidades)} "
          f"({sum(1 for e in entidades if e['esfera']=='estado')} estados+DF, "
          f"{sum(1 for e in entidades if e['esfera']=='municipio')} municípios)")

    grupo_estado = [e for e in entidades if e['esfera'] == 'estado']
    denom_df_icms = next(p['coef_cpt_estado'] * total_br_2025 for uf, p in params_estado.items() if p['is_df'])
    soma_denom_estado = sum((denom_df_icms if e['is_df'] else e['denom']) for e in grupo_estado)
    soma_pop_estado = sum(e['pop'] for e in grupo_estado)
    media_percapita_estado = (soma_denom_estado / soma_pop_estado) if soma_pop_estado > 0 else 0

    grupo_muni = [e for e in entidades if e['esfera'] == 'municipio']
    denom_df_iss = next(p['iss_2025'] for uf, p in params_estado.items() if p['is_df'])
    pop_df = next(e['pop'] for e in grupo_estado if e['is_df'])
    soma_denom_muni = sum(e['denom'] for e in grupo_muni) + denom_df_iss
    soma_pop_muni = sum(e['pop'] for e in grupo_muni) + pop_df
    media_percapita_muni = (soma_denom_muni / soma_pop_muni) if soma_pop_muni > 0 else 0

    for e in entidades:
        if e['is_df']:
            teto = 3 * (media_percapita_estado + media_percapita_muni) * e['pop']
        elif e['esfera'] == 'estado':
            teto = 3 * media_percapita_estado * e['pop']
        else:
            teto = 3 * media_percapita_muni * e['pop']
        e['denom_capado'] = min(e['denom'], teto) if e['pop'] > 0 else e['denom']

    resultado_por_ano = {}
    for a in anos:
        nac = nac_by_year[a]
        ibsd = nac['ibs_destino_liquido']
        pool = nac['ibs_seguro_receita']

        for e in entidades:
            e['numerador'] = ibsd * e['phi_dest']

        pares = [(e['numerador'], e['denom_capado']) for e in entidades]
        repasses = water_fill(pares, pool)

        soma_repasses = sum(repasses)
        n_beneficiarios = sum(1 for r in repasses if r > 1e-6)

        # Agrega por UF/esfera (estado; municípios somados) -- é só isso que
        # a página consome (buildRepasseIndex agregaria de qualquer forma).
        # O nivelamento acima já rodou sobre as 5.596 entidades individuais;
        # só a saída é agregada, para não gravar ~80 MB por ano de detalhe
        # município a município que ninguém lê nesta página.
        agregado_uf = {uf: {'estado': 0.0, 'municipio': 0.0} for uf in UFS}
        for e, repasse in zip(entidades, repasses):
            agregado_uf[e['uf']][e['esfera']] += repasse

        resultado_por_ano[a] = {
            'pool': pool,
            'soma_repasses': soma_repasses,
            'diff_pool': soma_repasses - pool,
            'n_beneficiarios': n_beneficiarios,
            'repasse_por_uf': agregado_uf,
        }
        if a in (2029, 2033, 2034, 2043, 2053, 2063, 2073, 2077):
            print(f"{a}: pool=R$ {pool/1e9:.3f}bi | distribuído=R$ {soma_repasses/1e9:.3f}bi "
                  f"(diff={soma_repasses-pool:+.2f}) | beneficiários={n_beneficiarios}/{len(entidades)}")

    output = {
        'metodo': (
            "Extensão do Estudo 12 (build-seguro-receita-repasses.py) de 2033 até 2077, seguindo "
            "o cronograma real do ADCT art. 131, §1º para a transição histórico->destino "
            "(ibs-projecao-longo-prazo.json). Entidades, receita de referência (denom_capado) e "
            "phi_dest de cada ente são os MESMOS do Estudo 12, fixos, calculados uma única vez a "
            "partir do dado 2025 -- só o numerador (IBS-destino recebido) e o pool cresce ano a "
            "ano. Ver build-seguro-receita-repasses.py para o texto legal completo (art. 132 ADCT, "
            "art. 117 LC 227/2026) e as simplificações documentadas lá."
        ),
        'anos': resultado_por_ano,
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSalvo em {OUT}")


if __name__ == "__main__":
    main()
