"""
Seguro-Receita (ADCT art. 132; LC 227/2026, arts. 110 e 117): numerador e distribuição conforme a lei.

Numerador (art. 117, I): média dos 12 meses anteriores da receita mensal do IBS apurada com base nas
alíquotas de referência (art. 108), ou seja, o IBS total do ente pelo critério do destino, e não só a
parcela que o destino já distribui (1 - alfa). Aqui: ibs_bruto x (1 - ca) x phi_dest (líquido do CGIBS).

Média móvel (art. 117, I, e §2º): dentro de cada ano, o mês k tem k-1 meses do ano corrente e 13-k do
anterior. De 2029 a 2033 os meses do ano anterior são multiplicados pela razão entre as alíquotas de
referência do ano corrente e do anterior, o que equivale a levar o mês anterior à alíquota corrente; com a
base de consumo crescendo, o mês anterior vale bolo[a-1]/bolo[a] do corrente. Depois de 2033 a razão é 1
e o mesmo fator reflete só o crescimento da base. Receita mensal constante dentro do ano.

Distribuição mensal (art. 117, caput e §1º): cada mês, o fundo retido (art. 110) nivela, em ordem
crescente de razão, os entes até que todos os contemplados tenham a mesma razão entre (numerador mais valor
recebido) e a receita média de referência ajustada. Em unidades anuais equivalentes: pool anual a cada mês,
resultado = média dos 12 meses.
"""


def g_prev(nac_by_year, ano):
    """bolo[a-1]/bolo[a]; para o primeiro ano (2028 fora da base) extrapola pela taxa seguinte."""
    cur = nac_by_year[ano]['bolo_projetado']
    ant = nac_by_year.get(ano - 1)
    if ant:
        return ant['bolo_projetado'] / cur
    nxt = nac_by_year.get(ano + 1)
    return cur / nxt['bolo_projetado'] if nxt else 1.0


def fatores_mes(g):
    return [((k - 1) + (13 - k) * g) / 12 for k in range(1, 13)]


def seguro_ano(denoms, phis, nac_by_year, ano, water_fill, mensal=True):
    """Retorna (repasses_anuais, numeradores_medios). denoms: denom_capado por ente; phis: phi_dest."""
    nac = nac_by_year[ano]
    ibs_ref = nac['ibs_bruto'] * (1 - nac['ca'])
    pool = nac['ibs_seguro_receita']
    fat = fatores_mes(g_prev(nac_by_year, ano)) if mensal else [1.0]
    reps = [0.0] * len(denoms)
    for f in fat:
        pares = [(ibs_ref * f * p, d) for p, d in zip(phis, denoms)]
        r = water_fill(pares, pool)
        for i, x in enumerate(r):
            reps[i] += x / len(fat)
    fmed = sum(fat) / len(fat)
    return reps, [ibs_ref * fmed * p for p in phis]
