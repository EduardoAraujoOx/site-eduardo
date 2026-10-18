#!/usr/bin/env python3
"""
Nota Municipal (protótipo): gera o HTML de impressão de um município a partir dos mesmos JSONs do portal
Municípios na Reforma (data/painel-municipios, ibs-projecao-nacional, sensibilidade-uf). Nenhum número é escrito à mão:
os textos são montados por regras sobre os dados. O PDF sai do HTML pelo Chromium (render_pdf.js).

Uso (da raiz do repositório):
    python3 materiais/nota-municipal/gerar_nota.py 3201308
"""
import json
import sys
from html import escape as esc
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATA = RAIZ / "data"
SAIDA = Path(__file__).resolve().parent
VERSAO = "outubro de 2026"
ANOS = ["2029", "2030", "2031", "2032", "2033"]
ANOS_HIST = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]
NOMES_UF = {"AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal",
            "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
            "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
            "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins"}
# preposição de cada UF ("do Espírito Santo", "de Minas Gerais", "da Bahia")
EM_UF = {"AC": "do Acre", "AL": "de Alagoas", "AM": "do Amazonas", "AP": "do Amapá", "BA": "da Bahia", "CE": "do Ceará", "DF": "do Distrito Federal",
         "ES": "do Espírito Santo", "GO": "de Goiás", "MA": "do Maranhão", "MG": "de Minas Gerais", "MS": "de Mato Grosso do Sul",
         "MT": "de Mato Grosso", "PA": "do Pará", "PB": "da Paraíba", "PE": "de Pernambuco", "PI": "do Piauí", "PR": "do Paraná",
         "RJ": "do Rio de Janeiro", "RN": "do Rio Grande do Norte", "RO": "de Rondônia", "RR": "de Roraima", "RS": "do Rio Grande do Sul",
         "SC": "de Santa Catarina", "SE": "de Sergipe", "SP": "de São Paulo", "TO": "do Tocantins"}

# paleta do portal (municipios-na-reforma/style.css): marinho e dourado como cromo; vermelho e azul só para perda e ganho
NAVY, GOLD, GOLD_DEEP, NEG, POS, CINZA, GRADE = "#1f2a55", "#b8922f", "#8f6f1c", "#a02525", "#1c5cab", "#858384", "#e2e0d8"
TITULO = "Reforma Tributária: projeções da receita e implicações para municípios"
SITE = "municipiosnareforma.com.br"


# ── formatação (mesmas regras do portal) ──
def num(v, d=0):
    s = f"{abs(v):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if v < 0 and round(abs(v), d) != 0 else "") + s


def pct(v, d=1, sinal=True):
    p = round(v * 100, d)
    return (("+" if p > 0 else "−" if p < 0 else "") if sinal else ("−" if p < 0 else "")) + num(abs(p), d) + "%"


def pct_plain(v, d=4):
    return num(v, d) + "%"


def pct_adapt(v):
    d = 5 if abs(v) < 0.01 else 4 if abs(v) < 0.1 else 3 if abs(v) < 1 else 2
    return num(v, d) + "%"


def dinheiro(v, fino=False):
    a, s = abs(v), ("−" if v < 0 else "")
    if a >= 1e9:
        return f"{s}R$ {num(a / 1e9, 2 if fino else 1)} bi"
    if a >= 1e6:
        return f"{s}R$ {num(a / 1e6, 1)} mi"
    if a >= 1e3:
        return f"{s}R$ {num(a / 1e3, 0)} mil"
    return f"{s}R$ {num(a, 0)}"


def mi(v, d=1):
    return num(v / 1e6, d)


def faixa_anos(anos):
    """['2019','2020','2021','2023'] -> '2019 a 2021 e 2023'"""
    grupos, ini, ant = [], None, None
    for a in [int(x) for x in anos]:
        if ini is None:
            ini = ant = a
        elif a == ant + 1:
            ant = a
        else:
            grupos.append((ini, ant)); ini = ant = a
    if ini is not None:
        grupos.append((ini, ant))
    txt = [str(i) if i == f else (f"{i} e {f}" if f == i + 1 else f"{i} a {f}") for i, f in grupos]
    return txt[0] if len(txt) == 1 else ", ".join(txt[:-1]) + " e " + txt[-1]


def carrega(p):
    return json.loads((DATA / p).read_text(encoding="utf-8"))


# ── gráficos em SVG ──
def eixo_ticks(lo, hi, n=5):
    """Ticks 'redondos' entre lo e hi."""
    import math
    span = hi - lo
    bruto = span / n
    mag = 10 ** math.floor(math.log10(bruto))
    for f in (1, 2, 2.5, 5, 10):
        if f * mag >= bruto:
            passo = f * mag
            break
    t0 = math.floor(lo / passo) * passo
    ticks, t = [], t0
    while True:
        ticks.append(t)
        if t >= hi - passo * 1e-9:
            break
        t += passo
    return ticks, passo


def svg_serie(m, cor_neg_pos):
    """Gráfico da ficha do portal: realizado 2019-2025 e os dois cenários de 2029 a 2033, no mesmo eixo categórico
    (2026-2028 não são projetados, e a linha segue direto de 2025 para 2029). R$ milhões de 2025."""
    W, H = 690, 258
    L, R, T, B = 50, 118, 38, 40
    cats = ANOS_HIST + ANOS
    n = len(cats)
    X = lambda i: L + i * (W - L - R) / (n - 1)
    hist = [m["historico_por_ano"][a]["total_reais_2025"] / 1e6 if a in m["historico_por_ano"] else None for a in ANOS_HIST]
    p25 = m["pre_2025"] / 1e6
    cf = [p25] + [m["contrafactual_por_ano"][a] / 1e6 for a in ANOS]
    ps = [p25] + [m["pos_por_ano"][a] / 1e6 for a in ANOS]
    vals = [v for v in hist if v] + cf + ps
    ticks, _ = eixo_ticks(min(vals) * 0.88, max(vals) * 1.05, 5)
    lo, hi = ticks[0], ticks[-1]
    dec = 0 if hi >= 60 else 1 if hi >= 6 else 2
    Y = lambda v: T + (1 - (v - lo) / (hi - lo)) * (H - T - B)
    i25 = ANOS_HIST.index("2025")
    idx_proj = [i25] + [len(ANOS_HIST) + k for k in range(len(ANOS))]
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="graf" role="img" aria-label="Receita realizada de 2019 a 2025 e projeção de 2029 a 2033 com e sem a reforma">']
    for t in ticks:
        o.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{GRADE}"/>')
        o.append(f'<text x="{L - 8}" y="{Y(t) + 3.5:.1f}" text-anchor="end" class="eixo">{num(t, dec)}</text>')
    o.append(f'<text x="2" y="{T - 22}" class="eixo-tit">R$ milhões de 2025</text>')
    for i, a in enumerate(cats):
        o.append(f'<text x="{X(i):.1f}" y="{H - B + 18}" text-anchor="middle" class="eixo{" neg-eixo" if a == "2025" else ""}">{a}</text>')
    # separação entre o realizado e a projeção
    xs = (X(i25) + X(i25 + 1)) / 2
    o.append(f'<line x1="{xs:.1f}" x2="{xs:.1f}" y1="{T - 6}" y2="{H - B}" stroke="#c9c6bb" stroke-dasharray="2 3"/>')
    o.append(f'<text x="{xs - 6:.1f}" y="{T - 10}" text-anchor="end" class="rot-faixa">realizado</text>')
    o.append(f'<text x="{xs + 6:.1f}" y="{T - 10}" class="rot-faixa">projeção (2026 a 2028 não projetados)</text>')
    # área entre os cenários
    topo = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in zip(idx_proj, cf))
    base = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in reversed(list(zip(idx_proj, ps))))
    o.append(f'<polygon points="{topo} {base}" fill="{GOLD}" fill-opacity=".20"/>')
    # realizado
    pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(hist) if v)
    o.append(f'<polyline points="{pts}" fill="none" stroke="{NAVY}" stroke-width="2.4" stroke-linejoin="round"/>')
    for i, v in enumerate(hist):
        if v:
            o.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.4" fill="{NAVY}" stroke="#fff" stroke-width="1.6"/>')
    # cenários
    pc = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in zip(idx_proj, cf))
    pp = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in zip(idx_proj, ps))
    o.append(f'<polyline points="{pc}" fill="none" stroke="#6b6b6b" stroke-width="2.2" stroke-dasharray="6 4"/>')
    o.append(f'<polyline points="{pp}" fill="none" stroke="{GOLD}" stroke-width="2.8" stroke-linejoin="round"/>')
    for i, v in list(zip(idx_proj, cf))[1:]:
        o.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3" fill="#6b6b6b" stroke="#fff" stroke-width="1.5"/>')
    for i, v in list(zip(idx_proj, ps))[1:]:
        o.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.6" fill="{GOLD}" stroke="#fff" stroke-width="1.6"/>')
    # rótulos diretos
    prim = next((k for k, v in enumerate(hist) if v), None)
    if prim is not None:
        o.append(f'<text x="{X(prim):.1f}" y="{Y(hist[prim]) - 11:.1f}" text-anchor="middle" class="rot-pt">{num(hist[prim], dec)}</text>')
    o.append(f'<text x="{X(i25):.1f}" y="{Y(p25) - 12:.1f}" text-anchor="middle" class="rot-pt">{num(p25, dec)}</text>')
    xe = X(idx_proj[-1])
    yc, yp = Y(cf[-1]), Y(ps[-1])
    cima_cf = yc <= yp
    def rot(y, nome, v, cor, acima):
        yy = y - 22 if acima else y + 8
        return (f'<text x="{xe + 12:.1f}" y="{yy + 9:.1f}" class="rot-nome">{nome}</text>'
                f'<text x="{xe + 12:.1f}" y="{yy + 23:.1f}" class="rot-fim" fill="{cor}">{num(v, dec)}</text>')
    o.append(rot(yc, "Sem a reforma", cf[-1], "#4a4a4a", cima_cf))
    o.append(rot(yp, "Com a reforma", ps[-1], GOLD_DEEP, not cima_cf))
    # colchete da diferença
    if abs(yp - yc) > 26:
        ym = (yc + yp) / 2
        o.append(f'<path d="M{xe + 5:.1f},{min(yc, yp) + 2:.1f} h4 V{max(yc, yp) - 2:.1f} h-4" fill="none" stroke="{cor_neg_pos}" stroke-width="1.3"/>')
        o.append(f'<text x="{xe + 14:.1f}" y="{ym + 4:.1f}" class="rot-dif" fill="{cor_neg_pos}">{pct(m["variacao_por_ano"]["2033"])}</text>')
    o.append("</svg>")
    return "".join(o)


def svg_participacao(d, h):
    """Barras da participação nacional por ano (2019-2025, 2026 estimada) e linha da média (coeficiente histórico)."""
    W, Hh = 690, 228
    L, R, T, B = 50, 20, 24, 32
    rot = ANOS_HIST + ["2026"]
    vals = d["valores"] + [d["est"]]
    topo = max(v for v in vals if v is not None) * 1.16
    ticks, _ = eixo_ticks(0, topo, 4)
    topo = ticks[-1]
    dig = 5 if topo < 0.01 else 4 if topo < 1 else 3
    Y = lambda v: T + (1 - v / topo) * (Hh - T - B)
    bw = (W - L - R) / len(rot)
    o = [f'<svg viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg" class="graf" role="img">']
    for t in ticks:
        o.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{GRADE}"/>')
        o.append(f'<text x="{L - 8}" y="{Y(t) + 3.5:.1f}" text-anchor="end" class="eixo">{num(t, dig)}%</text>')
    for i, (a, v) in enumerate(zip(rot, vals)):
        if v is None:
            continue
        x = L + i * bw + bw * 0.2
        w = bw * 0.6
        est = a == "2026"
        fill = f'url(#hach)' if est else NAVY
        o.append(f'<rect x="{x:.1f}" y="{Y(v):.1f}" width="{w:.1f}" height="{Hh - B - Y(v):.1f}" fill="{fill}" stroke="{NAVY}" stroke-width="{1.4 if est else 0}"/>')
        o.append(f'<text x="{x + w / 2:.1f}" y="{Y(v) - 6:.1f}" text-anchor="middle" class="rot-pt">{num(v, dig)}%</text>')
        o.append(f'<text x="{x + w / 2:.1f}" y="{Hh - B + 17}" text-anchor="middle" class="eixo">{a}{" (est.)" if est else ""}</text>')
    yc = Y(d["coef"])
    o.append(f'<line x1="{L}" x2="{W - R}" y1="{yc:.1f}" y2="{yc:.1f}" stroke="{GOLD}" stroke-width="2.4" stroke-dasharray="7 5"/>')
    o.append(f'<text x="{L + 8}" y="{yc - 7:.1f}" class="rot-ouro">coeficiente de participação {num(d["coef"], dig)}%</text>')
    o.append(f'<defs><pattern id="hach" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="#fff"/><line x1="0" y1="0" x2="0" y2="6" stroke="{NAVY}" stroke-width="2.4"/></pattern></defs>')
    o.append("</svg>")
    return "".join(o)


def svg_composicao(m):
    """Colunas empilhadas 2029-2033: ICMS/ISS residual, IBS pelo critério histórico, IBS pelo destino, Seguro-Receita (R$ milhões de 2025)."""
    W, Hh = 690, 235
    L, R, T, B = 50, 14, 22, 28
    comp = m["componentes_por_ano"]
    cats = [("origem", "ICMS e ISS remanescentes", CINZA), ("cpt", "IBS retido, pelo coeficiente de participação", NAVY), ("destino", "IBS pelo critério de destino", "#cfad56"), ("seguro", "Distribuição complementar (Seguro-Receita)", "#2f7f7a")]
    tot = {a: sum(comp[a][k] for k, _, _ in cats) / 1e6 for a in ANOS}
    ticks, _ = eixo_ticks(0, max(tot.values()) * 1.1, 4)
    topo = ticks[-1]
    Y = lambda v: T + (1 - v / topo) * (Hh - T - B)
    bw = (W - L - R) / len(ANOS)
    o = [f'<svg viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg" class="graf" role="img">']
    for t in ticks:
        o.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{GRADE}"/>')
        o.append(f'<text x="{L - 6}" y="{Y(t) + 3.5:.1f}" text-anchor="end" class="eixo">{num(t, 0)}</text>')
    for i, a in enumerate(ANOS):
        x, w, acc = L + i * bw + bw * 0.16, bw * 0.68, 0.0
        for k, _, cor in cats:
            v = comp[a][k] / 1e6
            if v <= 0:
                continue
            o.append(f'<rect x="{x:.1f}" y="{Y(acc + v):.1f}" width="{w:.1f}" height="{Y(acc) - Y(acc + v):.1f}" fill="{cor}"/>')
            acc += v
        o.append(f'<text x="{x + w / 2:.1f}" y="{Y(acc) - 6:.1f}" text-anchor="middle" class="rot-pt">{num(acc, 0)}</text>')
        o.append(f'<text x="{x + w / 2:.1f}" y="{Hh - B + 16}" text-anchor="middle" class="eixo">{a}</text>')
    o.append("</svg>")
    leg = "".join(f'<span><i style="background:{c}"></i>{esc(r)}</span>' for _, r, c in cats)
    return "".join(o), leg


def svg_pares(lista, cod):
    """Todos os municípios da UF ordenados da maior variação à menor; o município da nota em destaque."""
    W, Hh = 690, 160
    L, R, T, B = 50, 14, 14, 22
    vs = [x["v"] * 100 for x in lista]
    lo_d, hi_d = min(vs), max(vs)
    ticks, _ = eixo_ticks(min(lo_d, -1) * 1.05, max(hi_d, 1) * 1.05, 5)
    lo, hi = ticks[0], ticks[-1]
    Y = lambda v: T + (1 - (v - lo) / (hi - lo)) * (Hh - T - B)
    n = len(lista)
    bw = (W - L - R) / n
    o = [f'<svg viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg" class="graf" role="img">']
    for t in ticks:
        o.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{GRADE if t else "#9aa3b2"}" stroke-width="{1 if t else 1.3}"/>')
        o.append(f'<text x="{L - 6}" y="{Y(t) + 3.5:.1f}" text-anchor="end" class="eixo">{num(t, 0)}%</text>')
    y0 = Y(0)
    alvo = None
    for i, x in enumerate(lista):
        v = x["v"] * 100
        xx = L + i * bw
        if x["cod"] == cod:
            alvo = (i, xx + bw / 2, v)
        cor = POS if v >= 0 else NEG
        op = 1 if x["cod"] == cod else 0.42
        o.append(f'<rect x="{xx + 0.25:.2f}" y="{min(Y(v), y0):.1f}" width="{max(bw - 0.5, 0.6):.2f}" height="{abs(Y(v) - y0):.1f}" fill="{cor}" fill-opacity="{op}"/>')
    if alvo:
        i, xc, v = alvo
        yb = Y(v)
        o.append(f'<line x1="{xc:.1f}" x2="{xc:.1f}" y1="{yb:.1f}" y2="{yb + 22:.1f}" stroke="{NAVY}" stroke-width="1.2"/>')
        anc = "end" if xc > W * 0.62 else "start"
        o.append(f'<text x="{xc + (-3 if anc == "end" else 3):.1f}" y="{yb + 33:.1f}" text-anchor="{anc}" class="rot-pt" fill="{NAVY}">{esc(x_nome(lista, cod))} {pct(v / 100)}</text>')
    o.append(f'<text x="{L}" y="{Hh - 8}" class="eixo">maior ganho</text><text x="{W - R}" y="{Hh - 8}" text-anchor="end" class="eixo">maior perda</text>')
    o.append("</svg>")
    return "".join(o)


def x_nome(lista, cod):
    return next(x["nome"] for x in lista if x["cod"] == cod)


# ── sensibilidade (mesma conta da ficha: sensVar em app.js) ──
def sens_refs(m):
    h = m["historico_por_ano"]
    h25 = h["2025"]["total_reais_2025"]
    c0 = m["coef_neutro_pct"] / 100
    ref = {a: c0 * h[a]["total_reais_2025"] / h25 for a in ANOS_HIST if a in h}
    if m.get("estimativa_2026"):
        ref["2026"] = c0 * m["estimativa_2026"]["total_reais_2025"] / h25
    return ref


def sens_var(m, nac, ref, mult, ano="2033"):
    s = nac[ano]
    pos = (s["icms_iss_residual"] * ref + s["ibs_historico"] * (m["coef_cpt_pct"] / 100) * (1 - s["ca"])
           + s["ibs_destino_liquido"] * (m["coef_pleno_pct"] / 100) * (1 + mult)
           + (m["repasse_seguro_receita_por_ano"].get(ano, 0)) * (1 - s["ca"]))
    return pos / (ref * s["bolo_projetado"]) - 1


# ── textos por regra ──
# ── textos por regra (v3): a redação segue a revisão editorial; cada frase depende dos dados do município ──
def lista_anos(anos):
    anos = [str(a) for a in anos]
    return anos[0] if len(anos) == 1 else ", ".join(anos[:-1]) + " e " + anos[-1]


def em_anos(anos):
    """'em 2029 e 2030' ou 'de 2029 a 2033', conforme o agrupamento."""
    t = faixa_anos(anos)
    return ("de " if " a " in t and "," not in t and " e " not in t else "em ") + t


def comp(rel, lim=0.05):
    """Classifica uma razão relativa: abaixo, acima ou próxima."""
    return "abaixo" if rel < -lim else "acima" if rel > lim else "proxima"


def monta_textos(c):
    """c: contexto do município. Devolve os parágrafos variáveis da nota."""
    nome, v33 = c["nome"], c["v33"]
    perde, ganha = c["perde"], c["ganha"]
    cpt, neu, ple = c["cpt"], c["neu"], c["ple"]
    t = {}
    cr = c["cresc"]
    tend = ""
    if cr is not None:
        tend = (f"Entre 2019 e 2025, a participação do município na arrecadação nacional de ICMS e ISS {'aumentou' if cr > 0 else 'diminuiu'} {num(abs(cr) * 100, 0)}%"
                f" (de {pct_adapt(c['val0'])} para {pct_adapt(neu)}).")
    h_rel, d_rel = c["h_rel"], c["d_rel"]
    ch, cd = comp(h_rel), comp(d_rel)

    # 1. regra de transição (capa)
    t["s1"] = ("A transição para o IBS preserva temporariamente parte da distribuição histórica das receitas. De 2029 a 2032, 80% do IBS destinado a cada ente é retido e redistribuído pelos "
               "coeficientes de participação; em 2033, 90%, percentual que diminui até 2077. O restante é distribuído principalmente pelo critério de destino, que considera o consumo e as "
               "compras públicas locais (LC 227/2026, arts. 109, 114 e 115).")

    # 2. por que o resultado é este (capa)
    adverbio = {True: "perda", False: "ganho"}
    if c["sem_2025"]:
        t["s2"] = (f"<b>Resultado com ressalva.</b> {esc(nome)} não tem ISS e cota-parte de 2025 individualizados no Siconfi, e a participação de 2025 foi aproximada pelo próprio coeficiente de participação "
                   f"({pct_adapt(cpt)}). O resultado deve ser lido como ordem de grandeza e não entra nas posições.")
    elif ch == "abaixo":
        fim = (f"Essa diferença contribui para que a receita projetada em 2033 fique {pct(abs(v33), 1, False)} abaixo do cenário sem reforma." if perde else
               f"Mesmo assim, o resultado de 2033 é de {pct(v33)}, porque as demais parcelas compensam: " + ("o município recebe repasse do Seguro-Receita" if c["recebe"] else
               f"o coeficiente de destino ({pct_adapt(ple)}) é {'superior' if cd == 'acima' else 'próximo'} à participação de 2025") + ".")
        t["s2"] = (f"<b>O coeficiente de participação de {esc(nome)} é inferior à participação de 2025.</b> {tend} O coeficiente considera a média de 2019 a 2026 ({pct_adapt(cpt)}), "
                   f"{num(abs(h_rel) * 100, 0)}% abaixo da participação alcançada em 2025 ({pct_adapt(neu)}), que é o ponto de partida do cenário sem reforma. {fim}")
    elif ch == "acima":
        fim = (f"Essa diferença contribui para que a receita projetada em 2033 fique {pct(abs(v33), 1, False)} acima do cenário sem reforma." if ganha else
               f"Ainda assim, o resultado de 2033 é de {pct(v33)}, porque o coeficiente de destino ({pct_adapt(ple)}) é {'inferior' if cd == 'abaixo' else 'próximo'} à participação de 2025.")
        t["s2"] = (f"<b>O coeficiente de participação de {esc(nome)} é superior à participação de 2025.</b> {tend} O coeficiente considera a média de 2019 a 2026 ({pct_adapt(cpt)}), "
                   f"{num(abs(h_rel) * 100, 0)}% acima da participação de 2025 ({pct_adapt(neu)}), ponto de partida do cenário sem reforma. {fim}")
    else:
        rd = lambda r: f"{num(abs(r) * 100, 0)}% {'abaixo' if r < 0 else 'acima'}"
        comb = (f"O resultado de 2033 ({pct(v33)}) combina os dois coeficientes: o de participação, {rd(h_rel)} da participação de 2025 e responsável por 90% do IBS retido, "
                f"e o de destino ({pct_adapt(ple)}), {rd(d_rel)}.")
        t["s2"] = (f"<b>O critério histórico quase não altera o ponto de partida.</b> {tend} A média de 2019 a 2026 ({pct_adapt(cpt)}) é próxima da participação de 2025 ({pct_adapt(neu)}). " + comb)

    # 3. Seguro-Receita e incerteza (capa)
    if c["recebe"]:
        anos = em_anos(c["anos_seg"])
        v = f" Em 2033, o repasse é de {dinheiro(c['seg33'])}." if c["seg33"] > 1 else " Em 2033, o município deixa de receber, pois a receita pelo critério de destino alcança o nível de nivelamento."
        t["s3"] = (f"<b>Seguro-Receita.</b> As simulações indicam que {esc(nome)} deve receber recursos da distribuição complementar prevista no art. 117 da LC 227/2026 {anos}.{v} "
                   + ("Esse repasse reduz a perda estimada." if perde else "Esse repasse contribui para o resultado estimado."))
    else:
        t["s3"] = (f"<b>Seguro-Receita.</b> As simulações indicam que {esc(nome)} não deve receber recursos da distribuição complementar prevista no art. 117 da LC 227/2026, "
                   f"pois sua receita pelo critério de destino permanece acima do nível de nivelamento entre 2029 e 2033.")
    t["s4"] = ("<b>Incerteza das estimativas.</b> O resultado depende da participação utilizada como referência no cenário sem reforma. "
               "A seção 5 apresenta como as projeções variam conforme essa escolha.")

    # 5. trajetória
    vs = c["vars"]
    mesmo_sinal = all(v < -0.0005 for v in vs) or all(v > 0.0005 for v in vs)
    if mesmo_sinal and abs(vs[-1]) > abs(vs[0]):
        t["traj"] = (f"{'A perda' if perde else 'O ganho'} estimada{'' if perde else 'o'} aumenta ao longo da transição, passando de {pct(abs(vs[0]), 1, False)} em 2029 para "
                     f"{pct(abs(vs[3]), 1, False)} em 2032 e {pct(abs(vs[4]), 1, False)} em 2033. ").replace("estimadao", "estimado")
    else:
        t["traj"] = f"A diferença entre os cenários é de {pct(vs[0])} em 2029, {pct(vs[3])} em 2032 e {pct(vs[4])} em 2033. "
    if c["salto"] and abs(vs[4]) > abs(vs[3]) * 1.3:
        t["traj"] += (f"A mudança mais acentuada ocorre em 2033, quando ICMS e ISS são extintos (ADCT, art. 128). Até 2032, a arrecadação remanescente desses impostos, ainda distribuída segundo "
                      f"a participação de 2025, atenua {'as perdas' if perde else 'os ganhos' if ganha else 'a diferença'}. Com sua extinção, a receita passa a depender integralmente do IBS, "
                      f"cuja distribuição ainda é determinada principalmente pelo coeficiente de participação.")
    t["traj"] += " A comparação relevante é entre os dois cenários no mesmo ano; a variação em relação a 2025 aparece nos indicadores acima."

    # 9. coeficiente (p3)
    lvl = {"abaixo": "inferior", "acima": "superior", "proxima": "próximo"}[ch]
    if c["sem_2025"]:
        t["coef"] = (f"{esc(nome)} não tem o dado de 2025 no Siconfi, o que impede comparar o coeficiente de participação com a participação atual. O modelo adota o próprio coeficiente "
                     f"({pct_adapt(cpt)}) como aproximação da participação de 2025; por isso, o critério histórico quase não altera o ponto de partida.")
    else:
        p1 = f"{tend} Seu coeficiente de participação, calculado pela média de 2019 a 2026, é de {pct_adapt(cpt)}, " + (
            f"aproximadamente {num(abs(h_rel) * 100, 0)}% {'inferior' if h_rel < 0 else 'superior'} à participação de 2025." if ch != "proxima" else "próximo da participação de 2025.")
        p2 = ("Essa diferença é relevante porque, em 2033, 90% do IBS retido é distribuído pelo coeficiente de participação (LC 227/2026, arts. 109 e 114), enquanto o cenário sem reforma "
              "preserva a participação de 2025. ")
        if ch == "abaixo":
            p2 += ("Assim, a participação alcançada em 2025 não se reflete integralmente no coeficiente, contribuindo para a perda projetada. Se a arrecadação de 2025 representar um novo patamar, "
                   "o impacto tende a ser maior; se tiver sido um aumento temporário, menor.")
        elif ch == "acima":
            p2 += ("Assim, a média histórica reconhece uma participação maior do que a atual, contribuindo para o ganho projetado. Se a queda recente for permanente, o ganho tende a ser maior; "
                   "se for passageira, menor.")
        else:
            p2 += "Como o coeficiente é próximo da participação de 2025, o critério histórico pouco altera o ponto de partida do município."
        t["coef"] = p1 + "</p><p class=\"leit\">" + p2

    # 11. distribuição complementar (p4)
    base = ("O Seguro-Receita reserva uma parcela adicional de 5% do IBS entre 2029 e 2077, retida após a retenção do art. 109, para os entes com as menores razões entre a receita do IBS e a receita "
            "média de referência ajustada, limitada a três vezes a média per capita do conjunto dos Municípios (LC 227/2026, arts. 110 e 117, §4º). ")
    if c["recebe"]:
        base += f"Nas simulações, {esc(nome)} recebe repasse {em_anos(c['anos_seg'])}" + (f", com {dinheiro(c['seg33'])} em 2033." if c["seg33"] > 1 else ", e deixa de receber em 2033.")
    else:
        base += f"Nas simulações, {esc(nome)} permanece acima do patamar de nivelamento entre 2029 e 2033 e, por isso, não recebe recursos dessa distribuição complementar."
    t["compl"] = base

    # 13. sensibilidade
    pos_a, neg_a = c["pos_anos"], c["neg_anos"]
    ss = "Os resultados são sensíveis ao ano usado como referência do cenário sem reforma, que adotamos como 2025 por ser o último ano fechado. "
    if pos_a and neg_a:
        ss += f"Com a participação de {faixa_anos(pos_a)}, a projeção indica ganhos de receita em 2033; com a de {faixa_anos(neg_a)}, o resultado é negativo. "
    elif neg_a:
        ss += f"Em todos os anos de referência o resultado de 2033 é negativo, entre {pct(c['sens_min'])} e {pct(c['sens_max'])}. "
    elif pos_a:
        ss += f"Em todos os anos de referência o resultado de 2033 é positivo, entre {pct(c['sens_min'])} e {pct(c['sens_max'])}. "
    ss += ("Essa diferença reflete a evolução da participação do município na arrecadação nacional: quanto maior a participação tomada como referência, maior a receita do cenário sem reforma "
           "e, portanto, a perda relativa estimada. ")
    ss += f"A última coluna incorpora a incerteza do consumo estimado pelo critério de destino ({num(c['erro'] * 100, 1)}% {c['em_uf_curto']}), cujo efeito é menor do que o da escolha do ano-base."
    t["sens"] = ss

    # 17. critério de destino (p5)
    if c["sem_2025"]:
        t["dest"] = ("A parcela do consumo na distribuição do IBS aumenta gradualmente até 2078 e dependerá da atividade econômica, da renda, do consumo e das compras públicas locais.")
    else:
        if cd == "acima":
            efeito = (f"O coeficiente de destino ({pct_adapt(ple)}) supera a participação de 2025 ({pct_adapt(neu)}); por isso, a transição para o destino tende a favorecer o município no longo prazo.")
        elif cd == "abaixo":
            efeito = (f"O coeficiente de destino ({pct_adapt(ple)}) é {num(abs(d_rel) * 100, 0)}% inferior à participação de 2025 ({pct_adapt(neu)}); por isso, a transição para o destino "
                      f"não reverte a perda estimada e tende a mantê-la no longo prazo.")
        else:
            efeito = (f"O coeficiente de destino ({pct_adapt(ple)}) é próximo da participação de 2025 ({pct_adapt(neu)}); a transição para o destino tende a ser neutra no longo prazo.")
        t["dest"] = ("O peso do consumo na distribuição do IBS aumenta gradualmente até 2078 e dependerá da atividade econômica, da renda, do consumo e das compras públicas locais. " + efeito)
    return t


def qr_svg(url, cor=NAVY):
    import segno
    return segno.make(url, error="m").svg_inline(scale=3, border=0, dark=cor, light=None, omitsize=True).replace("<svg ", '<svg class="qr" ', 1)


def main(cod, saida_dir=None):
    idx = carrega("painel-municipios/index.json")
    uf = next(m["uf"] for c_, m in idx["municipios"].items() if c_ == cod)
    m = carrega(f"painel-municipios/{uf}.json")["municipios"][cod]
    nome = m["nome"]
    nac = {str(r["ano"]): r for r in carrega("ibs-projecao-nacional.json")["projecao"]}
    tb, fat = idx["referencia_nacional"]["total_br_2025"], idx["referencia_nacional"]["fatores_ajuste"]

    todos = [{"cod": c_, "nome": x["nome"], "uf": x["uf"], "v": x["v"], "r": bool(x.get("r"))} for c_, x in idx["municipios"].items()]
    ok = sorted([x for x in todos if not x["r"]], key=lambda x: -x["v"])
    uf_lista = [x for x in ok if x["uf"] == uf]
    ressalva = bool(m.get("neutro_aproximado") or m.get("neutro_suspeito"))
    pos_br = next((i for i, x in enumerate(ok) if x["cod"] == cod), -1) + 1
    pos_uf = next((i for i, x in enumerate(uf_lista) if x["cod"] == cod), -1) + 1
    perdem_uf, perdem_br = sum(1 for x in uf_lista if x["v"] < 0), sum(1 for x in ok if x["v"] < 0)

    v33 = m["variacao_por_ano"]["2033"]
    pos33, cf33 = m["pos_por_ano"]["2033"], m["contrafactual_por_ano"]["2033"]
    dif33 = pos33 - cf33
    perde, ganha = v33 < -0.0005, v33 > 0.0005
    cor = NEG if perde else POS if ganha else CINZA
    rep = m.get("repasse_seguro_receita_por_ano") or {}
    anos_seg = [a for a in ANOS if (rep.get(a) or 0) > 1]
    h = m["historico_por_ano"]
    valores = [h[a]["total_reais_2025"] / tb * 100 if a in h else None for a in ANOS_HIST]
    e26 = m.get("estimativa_2026")
    est26 = e26["total_reais_2025"] / tb * 100 if e26 else None
    s25 = valores[-1]
    d = {"valores": valores, "est": est26, "coef": m["coef_cpt_pct"], "s25": s25}
    neu = m["coef_neutro_pct"]
    val0 = next((v for v in valores if v), None)
    cresc = (s25 / val0 - 1) if (s25 and val0 and not ressalva) else None
    pop = round(m["pop_media"])
    nome_uf = NOMES_UF[uf]
    url_ficha = f"https://{SITE}/?m={cod}"
    erro = carrega("sensibilidade-uf.json")["por_uf"].get(uf, {}).get("incerteza_rel", 0.0)
    refs = sens_refs(m) if (h.get("2025") or {}).get("total_reais_2025") else {}
    sens_linhas = [(a, refs[a], sens_var(m, nac, refs[a], 0), sens_var(m, nac, refs[a], -erro), sens_var(m, nac, refs[a], erro)) for a in sorted(refs)]
    pos_anos = [l[0] for l in sens_linhas if l[2] > 0]
    neg_anos = [l[0] for l in sens_linhas if l[2] < 0]
    todos_v = [l[2] for l in sens_linhas] or [v33]
    vs = [m["variacao_por_ano"][a] for a in ANOS]
    comp_ = m["componentes_por_ano"]
    ctx = dict(nome=nome, v33=v33, perde=perde, ganha=ganha, cpt=m["coef_cpt_pct"], neu=neu, ple=m["coef_pleno_pct"], cresc=cresc, val0=val0,
               h_rel=m["coef_cpt_pct"] / neu - 1, d_rel=m["coef_pleno_pct"] / neu - 1, sem_2025=bool(m.get("neutro_aproximado")),
               recebe=bool(anos_seg), anos_seg=anos_seg, seg33=rep.get("2033") or 0, vars=vs,
               salto=comp_["2033"]["origem"] == 0 and comp_["2032"]["origem"] > 0, pos_anos=pos_anos, neg_anos=neg_anos,
               sens_min=min(todos_v), sens_max=max(todos_v), erro=erro, em_uf_curto=f"para {nome_uf}")
    T = monta_textos(ctx)

    def cab(n):
        return (f'<div class="cab"><span class="marca"><img src="../../municipios-na-reforma/images/vertex-simbolo.png" alt="">MUNICÍPIOS NA REFORMA</span><span class="url">{SITE}</span></div>'
                f'<div class="rod"><span>{esc(TITULO)} · {esc(nome)} ({uf})</span><span>{n} / 5</span></div>')

    if perde:
        manchete = f"Em 2033, a receita de <b>{esc(nome)}</b> fica <b>{dinheiro(abs(dif33))} abaixo</b> do que seria sem a reforma"
    elif ganha:
        manchete = f"Em 2033, a receita de <b>{esc(nome)}</b> fica <b>{dinheiro(abs(dif33))} acima</b> do que seria sem a reforma"
    else:
        manchete = f"Em 2033, a receita de <b>{esc(nome)}</b> fica praticamente igual à que seria sem a reforma"
    selo = "Perda estimada" if perde else "Ganho estimado" if ganha else "Efeito neutro"
    aviso = ""
    if m.get("neutro_suspeito"):
        aviso = f'<div class="aviso-dado"><b>Dado a conferir.</b> O valor declarado ao Siconfi para 2025 diverge de forma incompatível da série histórica do município, o que sugere falha de preenchimento na fonte. Os números são apresentados com cautela e não entram nas posições.</div>'
    elif m.get("neutro_aproximado"):
        aviso = f'<div class="aviso-dado"><b>Estimativa aproximada.</b> {esc(nome)} não tem ISS e cota-parte de 2025 individualizados no Siconfi, e a participação de 2025 foi aproximada pela média do período. Leia os números como ordem de grandeza.</div>'

    posicoes = ("" if ressalva else
                f'<div><b>{pos_uf}º</b><span>entre {len(uf_lista)} municípios {EM_UF[uf]}, do maior ganho à maior perda. {perdem_uf} têm perda estimada em 2033.</span></div>'
                f'<div><b>{num(pos_br)}º</b><span>entre {num(len(ok))} municípios do Brasil. {num(perdem_br)} têm perda estimada em 2033.</span></div>')
    if ressalva:
        posicoes = '<div class="semrank"><span>Município com ressalva de dados: fica fora das posições e dos rankings do portal.</span></div>'

    p1 = f"""
<section class="page capa">
  <div class="banda">
    <div class="lockup"><img src="../../municipios-na-reforma/images/vertex-simbolo-branco.png" alt=""><div><b>MUNICÍPIOS NA REFORMA</b><span>{SITE}</span></div></div>
    <h1>{esc(TITULO)}</h1>
    <div class="alvo"><b>Município de {esc(nome)}</b><span>{esc(nome_uf)} · {num(pop)} habitantes · código IBGE {cod}</span></div>
  </div>
  <div class="narr">
    <div class="narr-top">
      <div class="hn" style="--c:{cor}"><em>{selo}</em><b>{pct(v33)}</b></div>
      <p class="manchete">{manchete}<span>Efeito da reforma sobre a receita de ISS e cota-parte do ICMS, em 2033, comparado ao cenário sem reforma, em R$ de 2025.</span></p>
    </div>
    <div class="fig">{svg_serie(m, cor)}
      <div class="leg"><span><i class="l" style="background:{NAVY}"></i>Realizado (2019–2025)</span><span><i class="l" style="background:{GOLD}"></i>Projeção com a reforma</span><span><i class="l tr" style="border-color:#6b6b6b"></i>Cenário sem reforma</span></div>
    </div>
  </div>
  {aviso}
  <h2 class="sec">Síntese dos resultados</h2>
  <div class="resumo"><p>{T['s1']}</p><p>{T['s2']}</p><p>{T['s3']} {T['s4']}</p></div>
  <div class="posicoes">{posicoes}<div class="qrbox">{qr_svg(url_ficha)}<span>Ficha interativa e memória de cálculo</span></div></div>
  {cab(1)}
</section>"""

    cls = lambda v: "neg" if v < -0.0005 else "pos" if v > 0.0005 else ""
    linhas = "".join(
        f'<tr><td>{a}</td><td class="n">{mi(m["contrafactual_por_ano"][a])}</td><td class="n">{mi(m["pos_por_ano"][a])}</td>'
        f'<td class="n {cls(m["variacao_por_ano"][a])}">{mi(m["pos_por_ano"][a] - m["contrafactual_por_ano"][a])}</td>'
        f'<td class="n {cls(m["variacao_por_ano"][a])}"><b>{pct(m["variacao_por_ano"][a])}</b></td></tr>' for a in ANOS)
    acum = sum(m["pos_por_ano"][a] - m["contrafactual_por_ano"][a] for a in ANOS)
    real_c, real_s = pos33 / m["pre_2025"] - 1, cf33 / m["pre_2025"] - 1
    svg_c, leg_c = svg_composicao(m)
    p2 = f"""
<section class="page">
  {cab(2)}
  <h2 class="sec first"><i>1.</i> Projeção da receita municipal, 2029 a 2033</h2>
  <p class="sub">A tabela compara as receitas projetadas de {esc(nome)} com e sem a reforma tributária, em R$ milhões de 2025. No cenário sem reforma, o município mantém a participação de 2025 na arrecadação nacional projetada de ICMS e ISS, que evolui conforme as projeções do PIB (Focus e IFI). O cenário com reforma aplica as regras de transição do ADCT e da LC 227/2026.</p>
  <table class="tab"><thead><tr><th>Ano</th><th class="n">Sem a reforma<br><small>R$ mi</small></th><th class="n">Com a reforma<br><small>R$ mi</small></th><th class="n">Diferença<br><small>R$ mi</small></th><th class="n">Variação</th></tr></thead><tbody>{linhas}</tbody></table>
  <div class="mini">
    <div><span>Diferença acumulada, 2029–2033</span><b class="{cls(acum)}">{dinheiro(acum)}</b><small>soma das diferenças anuais, em R$ de 2025</small></div>
    <div><span>Com a reforma, 2033 vs. 2025</span><b class="{cls(real_c)}">{pct(real_c)}</b><small>variação real da receita entre os dois anos</small></div>
    <div><span>Sem a reforma, 2033 vs. 2025</span><b class="{cls(real_s)}">{pct(real_s)}</b><small>variação real mantendo a participação de 2025</small></div>
  </div>
  <p class="leit">{T['traj']}</p>
  <h2 class="sec"><i>2.</i> Composição da receita projetada</h2>
  <p class="sub">O gráfico mostra a substituição gradual do ICMS e do ISS pelo IBS e a composição da receita municipal segundo os diferentes critérios de distribuição. Valores em R$ milhões de 2025.</p>
  <div class="fig">{svg_c}<div class="leg">{leg_c}</div></div>
  <p class="nota">A parcela histórica incorpora a cota-parte do ICMS que o município já recebia. A parcela de destino inclui os 25% do IBS dos Estados repassados aos Municípios. A distribuição complementar (art. 117) só aparece quando há repasse ao município.</p>
</section>"""

    linhas_b1, soma = "", 0.0
    for a in ANOS_HIST:
        if a not in h:
            continue
        f = fat.get(a, 1.0)
        soma += h[a]["total_reais_2025"]
        orig = h[a].get("origem") or {}
        sel = [x for x in (orig.get("iss"), orig.get("cota")) if x and x != "dca"]
        marca = "" if not sel else (" <small>(RREO)</small>" if all(x == "rreo" for x in sel) else " <small>(est.)</small>")
        linhas_b1 += (f'<tr><td>{a}{marca}</td><td class="n">{num(h[a]["iss_reais_2025"] / f)}</td><td class="n">{num(h[a]["cota_parte_reais_2025"] / f)}</td><td class="n">{num(h[a]["total_reais_2025"] / f)}</td><td class="n">{num(f, 4)}</td>'
                      f'<td class="n"><b>{num(h[a]["total_reais_2025"])}</b></td><td class="n">{pct_adapt(h[a]["total_reais_2025"] / tb * 100)}</td></tr>')
    n_anos = len(ANOS_HIST) + (1 if e26 else 0)
    rreo26 = bool(e26 and (e26.get("origem") == "rreo" or e26.get("tratamento") == "rreo"))
    if e26:
        soma += e26["total_reais_2025"]
        linhas_b1 += (f'<tr class="est"><td>2026 <small>({"RREO" if rreo26 else "est."})</small></td><td class="n">{num(e26["iss_reais_2025"])}</td><td class="n">{num(e26["cota_parte_reais_2025"])}</td><td class="n">{num(e26["total_reais_2025"])}</td>'
                      f'<td class="n">n.a.</td><td class="n"><b>{num(e26["total_reais_2025"])}</b></td><td class="n">{pct_adapt(e26["total_reais_2025"] / tb * 100)}</td></tr>')
    media = soma / n_anos
    n26 = ("Para 2026, ainda sem DCA, utiliza-se o ISS informado no RREO de setembro de 2025 a agosto de 2026 e a cota-parte do ICMS de 2025, ajustada pelo crescimento observado entre janeiro e agosto." if rreo26 else
           "Para 2026, ainda sem DCA, o município não publica o Anexo 3 do RREO, e o valor repete a posição relativa de 2025 no estado." if e26 else "")
    anos_comp = [a for a in ANOS_HIST if (h.get(a) or {}).get("origem")]
    ntxt_orig = f" Os anos marcados (RREO ou est.) foram completados fora da DCA, pelo RREO anual ou pela série do próprio município." if anos_comp else ""
    p3 = f"""
<section class="page">
  {cab(3)}
  <h2 class="sec first"><i>3.</i> Receita média de referência e coeficiente de participação</h2>
  <p class="sub">O coeficiente de participação determina a parcela do IBS retido que cabe a cada ente federativo. Corresponde à razão entre a receita média de referência do município e a do conjunto de Estados, Distrito Federal e Municípios (LC 227/2026, arts. 114 e 115). Para os municípios, essa receita é a média do ISS e da cota-parte do ICMS entre 2019 e 2026, corrigida pela variação nominal da arrecadação nacional desses impostos.</p>
  <div class="fig">{svg_participacao(d, h)}</div>
  <p class="leit">{T['coef']}</p>
  <h3>Cálculo da receita média de referência e do coeficiente (art. 115, III e §2º)</h3>
  <table class="tab b1"><thead><tr><th>Ano</th><th class="n">ISS<br><small>(corrente)</small></th><th class="n">+ Cota-parte do ICMS<br><small>(CF, art. 158, IV, a)</small></th><th class="n">= Receita<br><small>(corrente)</small></th><th class="n">× Fator de<br>correção</th><th class="n">= Receita corrigida<br><small>(R$ de 2025)</small></th><th class="n">Participação no<br>total nacional</th></tr></thead>
  <tbody>{linhas_b1}</tbody>
  <tfoot><tr><td colspan="5">Soma da receita corrigida</td><td class="n">{num(soma)}</td><td class="n"></td></tr>
  <tr><td colspan="5">Receita média de referência (soma ÷ {n_anos})</td><td class="n"><b>{num(media)}</b></td><td class="n"></td></tr>
  <tr><td colspan="5">Total nacional de ICMS e ISS corrigido (receita média de referência do conjunto)</td><td class="n">{num(tb)}</td><td class="n"></td></tr>
  <tr class="res"><td colspan="5">Coeficiente de participação = receita média de referência ÷ conjunto</td><td class="n" colspan="2"><b>{pct_plain(m["coef_cpt_pct"], 6)}</b></td></tr></tfoot></table>
  <p class="nota">Valores em R$. As receitas são corrigidas pela variação nominal da arrecadação nacional de ICMS e ISS (art. 115, §2º, II, que corrige até 2026); aqui são expressas em reais de 2025, o que não altera o coeficiente, por ser uma razão. {n26}{ntxt_orig}</p>
</section>"""

    sens_rows = ""
    for a, rf, vc, vlo, vhi in sens_linhas:
        central = a == "2025"
        sens_rows += (f'<tr{" class=cent" if central else ""}><td>{a}{" (estimado)" if a == "2026" else ""}{" <small>· cenário central</small>" if central else ""}</td><td class="n">{pct_adapt(rf * 100)}</td>'
                      f'<td class="n {"neg" if vc < 0 else "pos"}"><b>{pct(vc)}</b></td><td class="n">{pct(min(vlo, vhi))} a {pct(max(vlo, vhi))}</td></tr>')
    if sens_linhas:
        bloco_sens = f"""<h3>Sensibilidade ao ano-base do cenário sem reforma</h3>
  <table class="tab sens"><thead><tr><th>Participação mantida do ano</th><th class="n">Participação</th><th class="n">Efeito em 2033</th><th class="n">Com margem de erro do destino</th></tr></thead><tbody>{sens_rows}</tbody></table>
  <p class="leit">{T['sens']}</p>"""
    else:
        bloco_sens = '<p class="leit">A análise de sensibilidade ao ano-base não se aplica a este município, que não tem a participação de 2025 individualizada.</p>'
    bloco_pos = "" if ressalva or not uf_lista else f"""<h3>{esc(nome)} entre os {len(uf_lista)} municípios {EM_UF[uf]}</h3>
  <p class="sub">Posição dos municípios com base de 2025 segundo a variação estimada da receita em 2033, em relação ao cenário sem reforma, do maior ganho (esquerda) à maior perda (direita).</p>
  <div class="fig">{svg_pares(uf_lista, cod)}</div>"""
    p4 = f"""
<section class="page">
  {cab(4)}
  <h2 class="sec first"><i>4.</i> Critério de destino e distribuição complementar</h2>
  <div class="coefs">
    <div><span>Participação em 2025</span><b>{pct_adapt(neu)}</b><small>Ponto de partida do cenário sem reforma: a participação do município hoje.</small></div>
    <div><span>Coeficiente de participação</span><b>{pct_adapt(m["coef_cpt_pct"])}</b><small>Receita média de referência de 2019 a 2026. Distribui o IBS retido: 90% do IBS em 2033.</small></div>
    <div><span>Coeficiente de destino</span><b>{pct_adapt(m["coef_pleno_pct"])}</b><small>{pct_adapt(m["cota_parte_pct"])} pela cota-parte dos Estados e {pct_adapt(m["propria_pct"])} pelo IBS próprio (consumo e compras públicas). Vale por inteiro em 2078.</small></div>
  </div>
  <p class="leit">{T['compl']}</p>
  <h2 class="sec"><i>5.</i> Posição relativa e análise de sensibilidade</h2>
  {bloco_pos}
  {bloco_sens}
</section>"""

    p5 = f"""
<section class="page densa">
  {cab(5)}
  <h2 class="sec first"><i>6.</i> Considerações para a gestão fiscal municipal</h2>
  <div class="atencao">
    <p><b>Revisar os dados fiscais antes da divulgação dos coeficientes.</b> O Comitê Gestor do IBS (CGIBS) deverá divulgar o coeficiente de participação de cada ente até 31 de agosto de 2027, com os valores e as fontes utilizados no cálculo, extraídos do Siconfi (LC 227/2026, art. 116, §§ 1º e 2º). Informações ausentes, duplicadas ou classificadas incorretamente podem alterar a receita média de referência. Por isso, é importante conferir a série de {esc(nome)}, apresentada na seção 3, e retificar eventuais inconsistências.</p>
    <p><b>Preparar-se para eventual contestação.</b> Caso identifique divergências no coeficiente divulgado, o município poderá apresentar contestação fundamentada no prazo de 30 dias após sua publicação no Diário Oficial da União. O CGIBS terá até 90 dias para responder, sem possibilidade de nova contestação ou recurso administrativo (art. 116, §§ 7º e 8º).</p>
    <p><b>Planejar com faixas, e não com valores únicos.</b> As projeções podem subsidiar o PPA e a LDO, considerando a sensibilidade dos resultados apresentada na seção 5. Recomenda-se acompanhar a atualização dos dados e a regulamentação do CGIBS.</p>
    <p><b>Acompanhar a transição para o critério de destino.</b> {T['dest']}</p>
  </div>
  <h2 class="sec"><i>7.</i> Metodologia e base legal</h2>
  <div class="met">
    <p><b>Receita média de referência (art. 115).</b> Considera a arrecadação municipal de ISS e a cota-parte do ICMS (CF, art. 158, IV, a) entre 2019 e 2026, corrigidas pela variação nominal da arrecadação nacional desses impostos. As informações vêm do Siconfi, com dados da DCA até 2025 e do RREO até agosto de 2026. Na ausência de registros, o modelo usa o RREO anual ou estimativas baseadas na série do município, e exclui valores fora da faixa entre metade e o dobro do esperado.</p>
    <p><b>Coeficiente de participação (art. 114, §1º).</b> Corresponde à razão entre a receita média de referência do município e a do conjunto dos entes federativos, equivalente a {dinheiro(tb, True)} em valores de 2025.</p>
    <p><b>Cenário sem reforma.</b> Projeta a receita municipal mantendo a participação de 2025 na arrecadação nacional de ICMS e ISS. A arrecadação evolui conforme o PIB nominal projetado pelo Focus (até 2030) e pela IFI (2031 a 2033), com a razão média entre receita de referência e PIB de 2024 a 2026 (LC 214/2025, arts. 361 a 365, com redação da LC 227/2026).</p>
    <p><b>Cenário com reforma.</b> A receita resulta da soma do ICMS e do ISS remanescentes, repartidos pela participação de 2025; do IBS retido (80% entre 2029 e 2032 e 90% em 2033, art. 109), distribuído pelo coeficiente de participação; do IBS pelo critério de destino, descontada a parcela do CGIBS; e dos eventuais repasses da distribuição complementar (art. 117). O peso do ICMS e do ISS cai de 90% em 2029 a zero em 2033 (ADCT, art. 128).</p>
    <p><b>Coeficiente de destino.</b> Combina a participação municipal na receita estadual do IBS com a estimativa do consumo (renda per capita do Censo 2022 e POF) e das compras públicas locais (DCA). Os critérios de educação e meio ambiente da cota-parte são aproximados pela distribuição populacional.</p>
    <p><b>Distribuição complementar (arts. 110 e 117).</b> Reserva adicional de 5% do IBS para os entes com menor razão entre o IBS e a receita média de referência ajustada, limitada a três vezes a média per capita, de modo a igualar essa razão entre os beneficiários.</p>
  </div>
  <h2 class="sec"><i>8.</i> Limitações</h2>
  <p class="leit peq">As projeções são estimativas e não representam previsões definitivas de arrecadação. Seus resultados dependem das hipóteses de crescimento econômico, da participação de 2025 adotada no cenário sem reforma e da regulamentação do IBS. Os dados fiscais são declarados pelos municípios ao Siconfi, sem auditoria independente, e o horizonte vai de 2029 a 2033. Os coeficientes definitivos serão divulgados pelo CGIBS, que poderá utilizar outras fontes e procedimentos previstos em lei (art. 116, §§ 3º e 4º).</p>
  <div class="citar">
    <div><b>Como citar.</b> Vertex Advisory. <i>{esc(TITULO)}: Município de {esc(nome)} ({uf})</i>. Municípios na Reforma, {VERSAO}. Disponível em {SITE}/?m={cod}.<br>
    <span>Fontes: STN/Siconfi (DCA e RREO), IBGE (Censo 2022, POF e estimativas populacionais), BCB (Focus), IFI, EC 132/2023, LC 214/2025 e LC 227/2026.</span></div>
    <div class="qrbox">{qr_svg(url_ficha)}<span>Ficha interativa e memória de cálculo em<br><b>{SITE}</b></span></div>
  </div>
</section>"""

    css = (Path(__file__).resolve().parent / "nota.css").read_text(encoding="utf-8")
    html = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{esc(TITULO)} · {esc(nome)} ({uf})</title><style>{css}</style></head><body>{p1}{p2}{p3}{p4}{p5}</body></html>'
    saida = (Path(saida_dir) if saida_dir else SAIDA) / f"nota-{cod}.html"
    saida.write_text(html, encoding="utf-8")
    print(saida)
    return saida


if __name__ == "__main__":
    for c_ in (sys.argv[1:] or ["3201308"]):
        main(c_)
