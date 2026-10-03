"""Soma ao FECOP, em memória, o ajuste dos fundos estaduais do art. 115, I, "b"
(LC 227/2026) e art. 350, II, "b" (LC 214/2025).

O ajuste mora na chave ``ajuste_fundos_art115b`` de data/reforma-tributaria.json,
gravada por data/build-fundos-art115-b.py. Fica em chave própria porque o fluxo
collect-dca-estados.yml reescreve ``dca_fecop_br`` e ``dca_fecop_por_uf`` por
inteiro a cada coleta, o que apagaria qualquer valor misturado ali.

Tratamento: como o FECOP, a contribuição pertence só ao Estado e não passa pela
cota-parte municipal do ICMS (art. 115, I, "b": "após a aplicação, quando
couber, do disposto na alínea 'a' do inciso IV do caput do art. 158 da CF").
"""


def fold(ref):
    """Devolve ``ref`` com o ajuste somado a dca_fecop_por_uf e dca_fecop_br.
    Idempotente: uma segunda chamada não soma de novo."""
    aj = ref.get("ajuste_fundos_art115b")
    if not aj or ref.get("_fundos_art115b_aplicado"):
        return ref
    por_uf = ref.setdefault("dca_fecop_por_uf", {})
    for ano, ufs in aj.get("fecop_por_uf", {}).items():
        d = por_uf.setdefault(ano, {})
        for uf, v in ufs.items():
            d[uf] = (d.get(uf) or 0) + v
    br = ref.setdefault("dca_fecop_br", {})
    for ano, v in aj.get("fecop_br", {}).items():
        br[ano] = (br.get(ano) or 0) + v
    ref["_fundos_art115b_aplicado"] = True
    return ref
