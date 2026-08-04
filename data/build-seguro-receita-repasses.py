#!/usr/bin/env python3
"""
Repasses do Seguro-Receita (ADCT art. 132, incluído pela EC 132/2023) por
ente -- estados, DF e cada um dos 5.569 municípios individualmente --,
2029-2033.

Base legal (texto integral conferido com o usuário): ADCT arts. 131-132 (EC
132/2023, mecanismo geral); LC 227/2026 arts. 114-116 (regra do critério
histórico, contexto) e, principalmente, art. 117 (o regulamento operacional
do Seguro-Receita em si -- "Da distribuição complementar para os entes
federativos com maior perda de participação relativa na receita").

  Art. 117, caput: o valor retido (5% do IBS-destino, art. 132 ADCT) é
  distribuído MENSALMENTE aos entes com as MENORES razões entre:
    I  - a média móvel dos 12 meses anteriores da receita mensal de IBS
         pelo critério destino; e
    II - a "receita média de referência AJUSTADA" (art. 117, §§3º-6º) --
         o MENOR valor entre (a) a receita média de referência do art. 115
         (histórica, fixa, mesma base do φ^CPT) e (b) 3x a média nacional
         per capita da respectiva esfera federativa.

  Art. 117, §1º: distribuição SEQUENCIAL e SUCESSIVA aos entes de menor
  razão, até que -- para quem recebeu -- todos atinjam a MESMA razão (não é
  proporcional ao déficit: é nivelamento por "enchimento de água" a partir
  de baixo, até o fundo acabar ou todos igualarem).

  Art. 117, §§5º-6º -- tratamento do DF: como o DF não tem camada municipal
  própria, sua receita média de referência soma ICMS e ISS (art. 115, §5º);
  o ICMS+população do DF entram na média per capita do grupo "Estados", e o
  ISS+população do DF entram na média per capita do grupo "Municípios" (sem
  o DF ganhar uma linha própria nesse segundo grupo); o teto do próprio DF
  soma as duas médias per capita, multiplicadas pela população do DF.

Simplificações explícitas desta implementação (a lei opera com mais
granularidade do que uma projeção anual permite):
  1. MENSAL -> ANUAL. Uso o ano-calendário inteiro como proxy da "média
     móvel de 12 meses" (não modelo a apuração mês a mês nem o ajuste do
     §2º para meses de alíquota diferente entre anos).
  2. POPULAÇÃO: era estimativa 2025 (ponto único) numa versão anterior; já
     corrigido para a média 2019-2026 exigida pelo art. 117, §§3º-6º -- ver
     data/build-populacao-municipios.py e build-populacao-uf-media.py.
     Cobertura real: 2019, 2020, 2021, 2024 e 2025 (5 dos 8 anos pedidos);
     2022-2023 não têm estimativa anual normal (Censo Demográfico 2022 a
     substituiu nesses dois anos) e 2026 ainda não foi publicado pelo IBGE.
  3. DF, numerador: o φ^dest do DF nesta página segue a convenção já
     estabelecida no Estudo 06 (baseada só no ICMS, sem ISS separado, já
     que o DF não tem φ^dest municipal próprio calculado em nenhum estudo
     do site) -- só o TETO (item II) foi corrigido para somar ICMS+ISS,
     como manda o art. 115, §5º; o numerador (item I) segue com o mesmo
     escopo (só ICMS) do restante do site, por consistência com o que já
     foi publicado e revisado.

Fórmulas:
  numerador_ente,a    = ibs_destino_liquido(a) × φ^dest_ente        (cresce)
  denom_ente           = receita_media_referencia_ente               (fixo)
  teto_ente             = 3 × média_percapita_da_esfera × pop_ente
  denom_capado_ente     = min(denom_ente, teto_ente)
  razão_ente,a          = numerador_ente,a / denom_capado_ente

  Nivelamento: acha L tal que Σ max(0, L×denom_capado − numerador) = pool_a
  (pool_a = ibs_seguro_receita do ano, Estudo 11); repasse_ente,a = essa
  parcela. Resolvido por busca binária (a função é monótona em L).

Uso:
  python3 build-seguro-receita-repasses.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "seguro-receita-repasses.json"

UFS = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT',
       'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']
ANOS = [2029, 2030, 2031, 2032, 2033]


def compute_params_estado(dca_icms_2025, dca_iss_2025, dca_fecop_2025, dca_cota_declarada_2025,
                           total_br_2025, coeficientes_uf, t4_by_uf):
    """Replica computeParams() de estudos/ibs-projecao-arrecadacao-br.html (φ^dest por esfera/UF)."""
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
    with open(HERE / "ibs-projecao-nacional.json") as f:
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

    # ── Monta lista de entidades (estados+DF, depois municípios) ───────────
    # denom = receita_media_referencia (R$, FIXA -- art. 115 LC 227/2026, mesma base do φ^CPT).
    # DF: usa coef_cpt_total (ICMS+FECOP+ISS), não coef_cpt_estado (só ICMS+FECOP) -- art. 115,
    # §5º, LC 227/2026 manda somar os dois para o DF, já que não tem camada municipal própria.
    entidades = []  # cada item: {id, nome, uf, esfera, denom, phi_dest, pop}
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

    # ── Teto de 3x a média nacional per capita, por esfera (art. 117, §§3º-§6º, LC 227/2026) ──
    # Grupo "estado": 27 UFs (inclui DF, com seu denom ICMS+FECOP -- não o total -- para não contar
    # o ISS duas vezes na média do grupo estadual). Grupo "município": 5.569 municípios + a
    # contribuição do ISS/população do DF (§5º, II), mesmo o DF não recebendo linha própria nesse
    # grupo -- ele conta na média nacional, mas quem recebe é só a linha "UF-DF" (esfera "estado").
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
            # Art. 117, §6º: teto do DF soma a média per capita das duas esferas.
            teto = 3 * (media_percapita_estado + media_percapita_muni) * e['pop']
        elif e['esfera'] == 'estado':
            teto = 3 * media_percapita_estado * e['pop']
        else:
            teto = 3 * media_percapita_muni * e['pop']
        e['denom_capado'] = min(e['denom'], teto) if e['pop'] > 0 else e['denom']

    # ── Para cada ano: só o numerador (IBS-destino recebido) muda; denom_capado é fixo ──
    resultado_por_ano = {}
    for a in ANOS:
        nac = nac_by_year[a]
        ibsd = nac['ibs_destino_liquido']
        pool = nac['ibs_seguro_receita']

        for e in entidades:
            e['numerador'] = ibsd * e['phi_dest']

        pares = [(e['numerador'], e['denom_capado']) for e in entidades]
        repasses = water_fill(pares, pool)

        soma_repasses = sum(repasses)
        n_beneficiarios = sum(1 for r in repasses if r > 1e-6)

        linhas = []
        for e, repasse in zip(entidades, repasses):
            razao = e['numerador'] / e['denom_capado'] if e['denom_capado'] > 0 else float('inf')
            linhas.append({
                'id': e['id'], 'nome': e['nome'], 'uf': e['uf'], 'esfera': e['esfera'],
                'numerador': e['numerador'], 'denom_capado': e['denom_capado'],
                'razao': razao, 'repasse': repasse,
            })

        resultado_por_ano[a] = {
            'pool': pool,
            'soma_repasses': soma_repasses,
            'diff_pool': soma_repasses - pool,
            'n_beneficiarios': n_beneficiarios,
            'entidades': linhas,
        }
        print(f"{a}: pool=R$ {pool/1e9:.3f}bi | distribuído=R$ {soma_repasses/1e9:.3f}bi "
              f"(diff={soma_repasses-pool:+.2f}) | beneficiários={n_beneficiarios}/{len(entidades)}")

    output = {
        'metodo': (
            "Art. 132 ADCT (EC 132/2023) e art. 117 LC 227/2026: 5% do IBS pelo critério destino "
            "(líquido de CGIBS, já deduzido no ibs_destino_liquido do Estudo 11) retido para "
            "nivelamento sequencial dos entes com menor razão entre (I) IBS-destino recebido no "
            "ano (cresce a cada ano) e (II) receita média de referência ajustada -- o menor valor "
            "entre a receita média histórica FIXA (art. 115 LC 227/2026, mesma base do φ^CPT) e 3x "
            "a média nacional per capita da esfera (estadual/municipal, separadamente; DF soma as "
            "duas médias, art. 117 §6º). População: média 2019-2026 (5 dos 8 anos pedidos "
            "disponíveis no IBGE -- ver docstring). Ver docstring do script para o texto legal "
            "completo e a simplificação restante (mensal->anual; numerador do DF restrito ao "
            "ICMS por consistência com o Estudo 06)."
        ),
        'anos': resultado_por_ano,
    }

    with open(OUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSalvo em {OUT}")


if __name__ == "__main__":
    main()
