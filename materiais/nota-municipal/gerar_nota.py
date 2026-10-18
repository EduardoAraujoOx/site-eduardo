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
    W, H = 690, 282
    L, R, T, B = 50, 118, 40, 42
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
    Y = lambda v: T + (1 - (v - lo) / (hi - lo)) * (H - T - B)
    i25 = ANOS_HIST.index("2025")
    idx_proj = [i25] + [len(ANOS_HIST) + k for k in range(len(ANOS))]
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="graf" role="img" aria-label="Receita realizada de 2019 a 2025 e projeção de 2029 a 2033 com e sem a reforma">']
    for t in ticks:
        o.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{GRADE}"/>')
        o.append(f'<text x="{L - 8}" y="{Y(t) + 3.5:.1f}" text-anchor="end" class="eixo">{num(t, 0)}</text>')
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
    o.append(f'<text x="{X(0):.1f}" y="{Y(hist[0]) - 11:.1f}" text-anchor="middle" class="rot-pt">{num(hist[0], 0)}</text>')
    o.append(f'<text x="{X(i25):.1f}" y="{Y(p25) - 12:.1f}" text-anchor="middle" class="rot-pt">{num(p25, 0)}</text>')
    xe = X(idx_proj[-1])
    yc, yp = Y(cf[-1]), Y(ps[-1])
    cima_cf = yc <= yp
    def rot(y, nome, v, cor, acima):
        yy = y - 22 if acima else y + 8
        return (f'<text x="{xe + 12:.1f}" y="{yy + 9:.1f}" class="rot-nome">{nome}</text>'
                f'<text x="{xe + 12:.1f}" y="{yy + 23:.1f}" class="rot-fim" fill="{cor}">{num(v, 0)}</text>')
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
    W, Hh = 690, 180
    L, R, T, B = 50, 14, 16, 24
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
def texto_participacao(nome, d):
    r = d["coef"] / d["s25"]
    cresc = d["s25"] / d["valores"][0] - 1 if d["valores"][0] else None
    if r < 0.87:
        sent = ("Por isso a reforma devolve uma fatia menor do que o município tem hoje, e o critério histórico puxa o resultado para baixo. "
                "Se o nível de 2025 se mostrar um novo patamar, o município perde parte do que já arrecada; se tiver sido um pico passageiro, o efeito é menor.")
    elif r > 1.15:
        sent = ("Por isso a reforma preserva uma fatia maior do que o município tem hoje, e o critério histórico puxa o resultado para cima. "
                "Se a queda for permanente, o município ganha em relação a continuar como está; se a receita voltar ao patamar anterior, o ganho diminui ou desaparece.")
    else:
        sent = "Por isso o critério histórico quase não altera o ponto de partida do município."
    cr = (f" A fatia {'cresceu' if cresc > 0 else 'caiu'} {num(abs(cresc) * 100, 0)}% entre 2019 e 2025 (de {pct_adapt(d['valores'][0])} para {pct_adapt(d['s25'])})." if cresc is not None else "")
    return (f"Em 2025, a fatia de {nome} na arrecadação nacional de ICMS e ISS foi de {pct_adapt(d['s25'])}.{cr} A média de 2019 a 2026 é de "
            f"{pct_adapt(d['coef'])}, {num(abs(1 - r) * 100, 0)}% {'abaixo' if r < 1 else 'acima'} da fatia de 2025. É essa média, e não o valor de 2025, que vira o "
            f"coeficiente histórico, e em 2033 cerca de 90% do IBS ainda é repartido por ele. O cenário sem a reforma, ao contrário, mantém a fatia de 2025. {sent}")


def qr_svg(url, cor=NAVY):
    import segno
    return segno.make(url, error="m").svg_inline(scale=3, border=0, dark=cor, light=None, omitsize=True).replace("<svg ", '<svg class="qr" ', 1)


def texto_participacao(nome, d):
    r = d["coef"] / d["s25"]
    cresc = d["s25"] / d["valores"][0] - 1 if d["valores"][0] else None
    if r < 0.87:
        sent = ("Por isso o critério histórico devolve ao município uma fatia menor do que a de hoje e puxa o resultado para baixo. "
                "Se o nível de 2025 se mostrar um novo patamar, o município perde parte do que já arrecada; se tiver sido um pico passageiro, o efeito é menor.")
    elif r > 1.15:
        sent = ("Por isso o critério histórico preserva uma fatia maior do que a de hoje e puxa o resultado para cima. "
                "Se a queda for permanente, o município ganha em relação a continuar como está; se a receita voltar ao patamar anterior, o ganho diminui ou desaparece.")
    else:
        sent = "Por isso o critério histórico quase não altera o ponto de partida do município."
    cr = (f" A participação {'cresceu' if cresc > 0 else 'caiu'} {num(abs(cresc) * 100, 0)}% entre 2019 e 2025, de {pct_adapt(d['valores'][0])} para {pct_adapt(d['s25'])}." if cresc is not None else "")
    return (f"Em 2025, a participação de {nome} na arrecadação nacional de ICMS e ISS foi de {pct_adapt(d['s25'])}.{cr} A receita média de referência, que considera os "
            f"anos de 2019 a 2026 (art. 115, §2º, I), corresponde a {pct_adapt(d['coef'])} do total nacional, {num(abs(1 - r) * 100, 0)}% {'abaixo' if r < 1 else 'acima'} da participação de 2025. "
            f"É esse coeficiente, e não o valor de 2025, que distribui a parcela retida do IBS (art. 114, §1º), em 2033 correspondente a 90% da arrecadação (art. 109, II). "
            f"O cenário contrafactual, ao contrário, mantém a participação de 2025. {sent}")


def main(cod):
    idx = carrega("painel-municipios/index.json")
    uf = next(m["uf"] for c, m in idx["municipios"].items() if c == cod)
    m = carrega(f"painel-municipios/{uf}.json")["municipios"][cod]
    nome = m["nome"]
    nac_j = carrega("ibs-projecao-nacional.json")
    nac = {str(r["ano"]): r for r in nac_j["projecao"]}
    ref_nac = idx["referencia_nacional"]
    tb, fat = ref_nac["total_br_2025"], ref_nac["fatores_ajuste"]

    todos = [{"cod": c, "nome": x["nome"], "uf": x["uf"], "v": x["v"], "r": bool(x.get("r"))} for c, x in idx["municipios"].items()]
    ok = sorted([x for x in todos if not x["r"]], key=lambda x: -x["v"])
    uf_lista = [x for x in ok if x["uf"] == uf]
    pos_br = next(i for i, x in enumerate(ok) if x["cod"] == cod) + 1
    pos_uf = next(i for i, x in enumerate(uf_lista) if x["cod"] == cod) + 1
    perdem_uf = sum(1 for x in uf_lista if x["v"] < 0)
    perdem_br = sum(1 for x in ok if x["v"] < 0)

    v33 = m["variacao_por_ano"]["2033"]
    pos33, cf33 = m["pos_por_ano"]["2033"], m["contrafactual_por_ano"]["2033"]
    dif33 = pos33 - cf33
    perde, ganha = v33 < -0.0005, v33 > 0.0005
    cor = NEG if perde else POS if ganha else CINZA
    recebe_seguro = any((m["repasse_seguro_receita_por_ano"].get(a) or 0) > 1 for a in ANOS)
    h = m["historico_por_ano"]
    valores = [h[a]["total_reais_2025"] / tb * 100 if a in h else None for a in ANOS_HIST]
    est26 = m["estimativa_2026"]["total_reais_2025"] / tb * 100 if m.get("estimativa_2026") else None
    d = {"valores": valores, "est": est26, "coef": m["coef_cpt_pct"], "s25": valores[-1]}
    pop = round(m["pop_media"])
    nome_uf = NOMES_UF[uf]
    url_ficha = f"https://{SITE}/?m={cod}"
    cresc = d["s25"] / d["valores"][0] - 1
    r_ = d["coef"] / d["s25"]

    def cab(n):
        return (f'<div class="cab"><span class="marca"><img src="../../municipios-na-reforma/images/vertex-simbolo.png" alt="">MUNICÍPIOS NA REFORMA</span><span class="url">{SITE}</span></div>'
                f'<div class="rod"><span>{esc(TITULO)} · {esc(nome)} ({uf})</span><span>{n} / 5</span></div>')

    # ── p1: abertura com o gráfico narrativo ──
    if perde:
        manchete = f"Em 2033, a receita de <b>{esc(nome)}</b> fica <b>{dinheiro(abs(dif33))} abaixo</b> do que seria sem a reforma"
    elif ganha:
        manchete = f"Em 2033, a receita de <b>{esc(nome)}</b> fica <b>{dinheiro(abs(dif33))} acima</b> do que seria sem a reforma"
    else:
        manchete = f"Em 2033, a receita de <b>{esc(nome)}</b> fica praticamente igual à que seria sem a reforma"
    selo = "Perda estimada" if perde else "Ganho estimado" if ganha else "Efeito neutro"

    kpis = (f'<div class="kpi"><span>Receita em 2025</span><b>{dinheiro(m["pre_2025"], True)}</b></div>'
            f'<div class="kpi"><span>2033, cenário contrafactual</span><b>{dinheiro(cf33, True)}</b></div>'
            f'<div class="kpi dest" style="--c:{cor}"><span>2033, com a reforma</span><b>{dinheiro(pos33, True)}</b></div>')

    s1 = (f"De 2029 a 2077, parte do IBS de cada ente é retida e distribuída pelo <b>coeficiente de participação</b>, que compara a receita média de referência do ente com a do conjunto de Estados, "
          f"Distrito Federal e Municípios (LC 227/2026, arts. 109, 114 e 115). A retenção é de 80% do IBS de 2029 a 2032 e de 90% em 2033, e decresce até 2077; o restante segue o critério de destino, "
          f"ligado ao consumo e às compras públicas locais.")
    if r_ < 0.87:
        s2 = (f"<b>O resultado de {esc(nome)} decorre do crescimento recente.</b> A participação do município na arrecadação nacional de ICMS e ISS {'cresceu' if cresc > 0 else 'caiu'} {num(abs(cresc) * 100, 0)}% entre 2019 e 2025. "
              f"Como o coeficiente usa a média de 2019 a 2026 ({pct_adapt(d['coef'])}) e não a participação de 2025 ({pct_adapt(d['s25'])}), o crescimento não é plenamente reconhecido, "
              f"e a reforma devolve uma fatia {num((1 - r_) * 100, 0)}% menor do que a atual.")
    elif r_ > 1.15:
        s2 = (f"<b>O resultado de {esc(nome)} decorre da média histórica.</b> O coeficiente usa a média de 2019 a 2026 ({pct_adapt(d['coef'])}), acima da participação de 2025 ({pct_adapt(d['s25'])}); "
              f"a reforma preserva uma fatia maior do que a atual.")
    else:
        s2 = (f"<b>O efeito é pequeno.</b> A média de 2019 a 2026 ({pct_adapt(d['coef'])}) é parecida com a participação de 2025 ({pct_adapt(d['s25'])}), e o critério histórico quase não altera o ponto de partida.")
    s3 = ("<b>Distribuição complementar (Seguro-Receita).</b> " + ("O município recebe repasse em parte do período, o que reduz o efeito acima." if recebe_seguro else
          f"A receita de {esc(nome)} pelo critério de destino fica acima do nível de nivelamento em todos os anos de 2029 a 2033; o município não recebe o repasse do art. 117 da LC 227/2026."))
    s4 = ("<b>Grau de incerteza.</b> O número depende da participação tomada como ponto de partida do cenário contrafactual; a seção 5 mostra o quanto ele varia com essa escolha.")

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
      <p class="manchete">{manchete}<span>Efeito da reforma sobre a receita de ISS e cota-parte do ICMS, em 2033, comparado ao cenário contrafactual (sem a reforma), em R$ de 2025.</span></p>
    </div>
    <div class="fig">{svg_serie(m, cor)}
      <div class="leg"><span><i class="l" style="background:{NAVY}"></i>Realizado (2019–2025)</span><span><i class="l" style="background:{GOLD}"></i>Projeção com a reforma</span><span><i class="l tr" style="border-color:#6b6b6b"></i>Cenário contrafactual (sem a reforma)</span></div>
    </div>
  </div>
  <h2 class="sec">Síntese dos resultados</h2>
  <div class="resumo"><p>{s1}</p><p>{s2}</p><p>{s3} {s4}</p></div>
  <div class="posicoes">
    <div><b>{pos_uf}º</b><span>entre {len(uf_lista)} municípios {EM_UF[uf]}, do maior ganho à maior perda. {perdem_uf} têm perda estimada em 2033.</span></div>
    <div><b>{num(pos_br)}º</b><span>entre {num(len(ok))} municípios do Brasil. {num(perdem_br)} têm perda estimada em 2033.</span></div>
    <div class="qrbox">{qr_svg(url_ficha)}<span>Ficha interativa e memória de cálculo</span></div>
  </div>
  {cab(1)}
</section>"""

    # ── p2: projeção ──
    cls = lambda v: "neg" if v < -0.0005 else "pos" if v > 0.0005 else ""
    linhas = "".join(
        f'<tr><td>{a}</td><td class="n">{mi(m["contrafactual_por_ano"][a])}</td><td class="n">{mi(m["pos_por_ano"][a])}</td>'
        f'<td class="n {cls(m["variacao_por_ano"][a])}">{mi(m["pos_por_ano"][a] - m["contrafactual_por_ano"][a])}</td>'
        f'<td class="n {cls(m["variacao_por_ano"][a])}"><b>{pct(m["variacao_por_ano"][a])}</b></td></tr>' for a in ANOS)
    acum = sum(m["pos_por_ano"][a] - m["contrafactual_por_ano"][a] for a in ANOS)
    real_c, real_s = pos33 / m["pre_2025"] - 1, cf33 / m["pre_2025"] - 1
    v29, v32 = m["variacao_por_ano"]["2029"], m["variacao_por_ano"]["2032"]
    salto = m["componentes_por_ano"]["2033"]["origem"] == 0 and m["componentes_por_ano"]["2032"]["origem"] > 0
    t_traj = f"A diferença entre os cenários {'aumenta' if abs(v33) > abs(v29) else 'varia'} a cada ano: {pct(v29)} em 2029, {pct(v32)} em 2032 e {pct(v33)} em 2033. "
    if salto and abs(v33) > abs(v32) * 1.3:
        t_traj += ("O salto de 2033 é mecânico: até 2032 resta uma parcela do ICMS e do ISS, ainda repartida pela participação de 2025, que amortece o efeito; "
                   "em 2033 esses tributos deixam de existir (ADCT, art. 128) e a receita passa a depender do IBS, distribuído sobretudo pelo coeficiente de participação.")
    svg_c, leg_c = svg_composicao(m)
    p2 = f"""
<section class="page">
  {cab(2)}
  <h2 class="sec first"><i>1.</i> Projeção da receita municipal, 2029 a 2033</h2>
  <p class="sub">Receita de {esc(nome)} nos dois cenários, em R$ milhões de 2025. O cenário contrafactual mantém a participação de 2025 na arrecadação nacional de ICMS e ISS e a aplica ao bolo projetado (PIB do Focus e da IFI); o cenário com a reforma aplica a transição prevista no ADCT e na LC 227/2026 à mesma projeção.</p>
  <table class="tab"><thead><tr><th>Ano</th><th class="n">Cenário contrafactual<br><small>R$ mi</small></th><th class="n">Com a reforma<br><small>R$ mi</small></th><th class="n">Diferença<br><small>R$ mi</small></th><th class="n">Variação</th></tr></thead><tbody>{linhas}</tbody></table>
  <div class="mini">
    <div><span>Diferença acumulada, 2029–2033</span><b class="{cls(acum)}">{dinheiro(acum)}</b><small>soma das diferenças anuais, em R$ de 2025</small></div>
    <div><span>Com a reforma, 2033 vs. 2025</span><b class="{cls(real_c)}">{pct(real_c)}</b><small>variação real da receita entre os dois anos</small></div>
    <div><span>Cenário contrafactual, 2033 vs. 2025</span><b class="{cls(real_s)}">{pct(real_s)}</b><small>variação real mantendo a participação de 2025</small></div>
  </div>
  <p class="leit">{t_traj}</p>
  <h2 class="sec"><i>2.</i> Composição da receita projetada</h2>
  <p class="sub">Quanto da receita ainda vem do ICMS e do ISS remanescentes e quanto já vem do IBS, por critério de distribuição. R$ milhões de 2025.</p>
  <div class="fig">{svg_c}<div class="leg">{leg_c}</div></div>
  <p class="nota">Inclui a cota-parte do ICMS que o município já recebia, na parcela histórica, e os 25% do IBS dos Estados repassados aos Municípios, na parcela de destino. A distribuição complementar (art. 117) é nula quando o município não recebe repasse.</p>
</section>"""

    # ── p3: receita média de referência e coeficiente ──
    linhas_b1, soma = "", 0.0
    for a in ANOS_HIST:
        if a not in h:
            continue
        f = fat.get(a, 1.0)
        soma += h[a]["total_reais_2025"]
        linhas_b1 += (f'<tr><td>{a}</td><td class="n">{num(h[a]["iss_reais_2025"] / f)}</td><td class="n">{num(h[a]["cota_parte_reais_2025"] / f)}</td><td class="n">{num(h[a]["total_reais_2025"] / f)}</td><td class="n">{num(f, 4)}</td>'
                      f'<td class="n"><b>{num(h[a]["total_reais_2025"])}</b></td><td class="n">{pct_adapt(h[a]["total_reais_2025"] / tb * 100)}</td></tr>')
    e = m.get("estimativa_2026")
    n_anos = len(ANOS_HIST) + (1 if e else 0)
    if e:
        soma += e["total_reais_2025"]
        linhas_b1 += (f'<tr class="est"><td>2026 <small>(RREO)</small></td><td class="n">{num(e["iss_reais_2025"])}</td><td class="n">{num(e["cota_parte_reais_2025"])}</td><td class="n">{num(e["total_reais_2025"])}</td>'
                      f'<td class="n">n.a.</td><td class="n"><b>{num(e["total_reais_2025"])}</b></td><td class="n">{pct_adapt(e["total_reais_2025"] / tb * 100)}</td></tr>')
    media = soma / n_anos
    origem_txt = " Os anos assinalados foram completados fora da DCA (RREO ou estimativa pela série do município)." if any(h[a].get("origem") for a in h) else ""
    p3 = f"""
<section class="page">
  {cab(3)}
  <h2 class="sec first"><i>3.</i> Receita média de referência e coeficiente de participação</h2>
  <p class="sub">O valor retido do IBS é distribuído a cada ente na proporção do seu coeficiente de participação, a razão entre a sua receita média de referência e a do conjunto de Estados, Distrito Federal e Municípios (LC 227/2026, arts. 114 e 115). No modelo, a receita média de referência do município é a média de 2019 a 2026 da arrecadação do ISS e da cota-parte do ICMS, corrigida pela variação nominal da arrecadação nacional desses impostos.</p>
  <div class="fig">{svg_participacao(d, h)}</div>
  <p class="leit">{esc(texto_participacao(nome, d))}</p>
  <h3>Cálculo da receita média de referência e do coeficiente (art. 115, III e §2º)</h3>
  <table class="tab b1"><thead><tr><th>Ano</th><th class="n">ISS<br><small>(corrente)</small></th><th class="n">+ Cota-parte do ICMS<br><small>(CF, art. 158, IV, a)</small></th><th class="n">= Receita<br><small>(corrente)</small></th><th class="n">× Fator de<br>correção</th><th class="n">= Receita corrigida<br><small>(R$ de 2025)</small></th><th class="n">Participação no<br>total nacional</th></tr></thead>
  <tbody>{linhas_b1}</tbody>
  <tfoot><tr><td colspan="5">Soma da receita corrigida</td><td class="n">{num(soma)}</td><td class="n"></td></tr>
  <tr><td colspan="5">Receita média de referência (soma ÷ {n_anos})</td><td class="n"><b>{num(media)}</b></td><td class="n"></td></tr>
  <tr><td colspan="5">Total nacional de ICMS e ISS corrigido (receita média de referência do conjunto)</td><td class="n">{num(tb)}</td><td class="n"></td></tr>
  <tr class="res"><td colspan="5">Coeficiente de participação = receita média de referência ÷ conjunto</td><td class="n" colspan="2"><b>{pct_plain(m["coef_cpt_pct"], 6)}</b></td></tr></tfoot></table>
  <p class="nota">Valores em R$. O fator de correção é a variação nominal da arrecadação nacional de ICMS e ISS entre o ano e 2025 (art. 115, §2º, II, que corrige até 2026; a escolha da data-base não altera o coeficiente, que é uma razão). Como o fator iguala o total nacional de todos os anos, a receita média de referência do conjunto equivale ao total de 2025.{origem_txt} Em 2026, ainda sem DCA, o ISS é o observado no RREO de setembro de 2025 a agosto de 2026 e a cota-parte é a de 2025 ajustada pelo crescimento de janeiro a agosto.</p>
</section>"""

    # ── p4: destino, distribuição complementar, posição, sensibilidade ──
    refs = sens_refs(m)
    erro = carrega("sensibilidade-uf.json")["por_uf"][uf]["incerteza_rel"]
    sens_linhas = [(a, refs[a], sens_var(m, nac, refs[a], 0), sens_var(m, nac, refs[a], -erro), sens_var(m, nac, refs[a], erro)) for a in sorted(refs)]
    sens_rows = ""
    for a, rf, vc, vlo, vhi in sens_linhas:
        central = a == "2025"
        cls_c = ' class="cent"' if central else ""
        sens_rows += (f'<tr{cls_c}><td>{a}{" (estimado)" if a == "2026" else ""}{" <small>· cenário central</small>" if central else ""}</td><td class="n">{pct_adapt(rf * 100)}</td>'
                      f'<td class="n {"neg" if vc < 0 else "pos"}"><b>{pct(vc)}</b></td><td class="n">{pct(min(vlo, vhi))} a {pct(max(vlo, vhi))}</td></tr>')
    pos_anos = [l[0] for l in sens_linhas if l[2] > 0]
    neg_anos = [l[0] for l in sens_linhas if l[2] < 0]
    t_sens = "Cada linha refaz o cálculo de 2033 supondo que o cenário contrafactual mantivesse a participação de outro ano, em vez da de 2025, adotada como referência central por ser o último ano fechado. "
    if pos_anos and neg_anos:
        t_sens += (f"O sinal do resultado muda conforme o ano escolhido: com a participação de {faixa_anos(pos_anos)} a reforma seria favorável ao município; com a de {faixa_anos(neg_anos)}, desfavorável. "
                   f"Quanto mais rápido o município cresceu em relação ao país, mais o resultado depende dessa escolha. ")
    t_sens += f"A última coluna acrescenta a margem de erro do consumo estimado pelo critério de destino ({num(erro * 100, 1)}% para {nome_uf}), que pesa pouco frente à escolha do ano-base."
    svg_p = svg_pares(uf_lista, cod)
    compl = (f"Após a retenção do art. 109, outros 5% do IBS de cada ente são retidos de 2029 a 2077 e distribuídos aos entes com as menores razões entre a receita do IBS e a receita média de referência ajustada, "
             f"que não passa de três vezes a média per capita do conjunto dos Municípios (arts. 110 e 117, §4º). " +
             ("Neste caso, o município recebe repasse em parte do período." if recebe_seguro else
              f"A receita de {esc(nome)} pelo critério de destino fica acima do nível de nivelamento em todos os anos de 2029 a 2033, e o município não recebe esse repasse."))
    p4 = f"""
<section class="page">
  {cab(4)}
  <h2 class="sec first"><i>4.</i> Critério de destino e distribuição complementar</h2>
  <div class="coefs">
    <div><span>Participação em 2025</span><b>{pct_adapt(m["coef_neutro_pct"])}</b><small>Ponto de partida do cenário contrafactual: a participação do município hoje.</small></div>
    <div><span>Coeficiente de participação</span><b>{pct_adapt(m["coef_cpt_pct"])}</b><small>Receita média de referência de 2019 a 2026. Distribui a parcela retida: 90% do IBS em 2033.</small></div>
    <div><span>Coeficiente de destino</span><b>{pct_adapt(m["coef_pleno_pct"])}</b><small>{pct_adapt(m["cota_parte_pct"])} pela cota-parte dos Estados e {pct_adapt(m["propria_pct"])} pelo IBS próprio (consumo e compras públicas). Vale por inteiro em 2078.</small></div>
  </div>
  <p class="leit">{compl}</p>
  <h2 class="sec"><i>5.</i> Posição relativa e análise de sensibilidade</h2>
  <h3>{esc(nome)} entre os {len(uf_lista)} municípios {EM_UF[uf]}</h3>
  <p class="sub">Variação da receita em 2033 contra o cenário contrafactual, do maior ganho (esquerda) à maior perda (direita).</p>
  <div class="fig">{svg_p}</div>
  <h3>Sensibilidade ao ano-base do cenário contrafactual</h3>
  <table class="tab sens"><thead><tr><th>Participação mantida do ano</th><th class="n">Participação</th><th class="n">Efeito em 2033</th><th class="n">Com margem de erro do destino</th></tr></thead><tbody>{sens_rows}</tbody></table>
  <p class="leit">{t_sens}</p>
</section>"""

    # ── p5 ──
    p5 = f"""
<section class="page">
  {cab(5)}
  <h2 class="sec first"><i>6.</i> Considerações para a gestão fiscal municipal</h2>
  <div class="atencao">
    <p><b>Conferir a base declarada antes da divulgação do coeficiente.</b> O CGIBS divulgará o coeficiente de participação de cada ente, com o detalhamento dos valores e das fontes, até 31 de agosto de 2027 (art. 116, §1º), a partir do Siconfi (art. 116, §2º). Ausências, repetições e lançamentos em conta indevida reduzem a receita média de referência. Vale revisar a série de {esc(nome)} ano a ano, como na tabela da seção 3, e retificar o que for necessário.</p>
    <p><b>Preparar a contestação.</b> Havendo discordância, o município poderá apresentar contestação fundamentada em 30 dias contados da publicação do coeficiente no Diário Oficial da União; o CGIBS responde em até 90 dias e não cabe nova contestação nem recurso administrativo (art. 116, §§ 7º e 8º).</p>
    <p><b>Planejar com faixa, e não com ponto.</b> Para o PPA e a LDO, é prudente trabalhar com o intervalo da seção 5 e acompanhar as atualizações do modelo e a regulamentação do CGIBS.</p>
    <p><b>Acompanhar o critério de destino.</b> A parcela de destino cresce até 2078 e depende da renda, do consumo e das compras públicas locais. É o canal pelo qual o município recupera participação no longo prazo.</p>
  </div>
  <h2 class="sec"><i>7.</i> Metodologia e base legal</h2>
  <div class="met">
    <p><b>Receita média de referência (LC 227/2026, art. 115).</b> Para o município, ISS e parcela creditada da cota-parte do ICMS (CF, art. 158, IV, a), de 2019 a 2026, corrigidos pela variação nominal da arrecadação nacional de ICMS e ISS. Dados do Siconfi: DCA (Anexo I-C) até 2025 e RREO até agosto de 2026. Quando uma DCA falta, o modelo completa a série pelo RREO anual ou pela série do próprio município e descarta valores fora da faixa entre metade e o dobro do esperado.</p>
    <p><b>Coeficiente de participação (art. 114, §1º).</b> Receita média de referência do município dividida pela do conjunto de Estados, Distrito Federal e Municípios, em reais de 2025 ({dinheiro(tb, True)} no conjunto).</p>
    <p><b>Cenário contrafactual.</b> Participação do município em 2025 vezes o bolo nacional projetado de ICMS e ISS, que cresce com o PIB nominal (Focus do BCB até 2030 e IFI de 2031 a 2033) e com a razão média entre receita de referência e PIB de 2024 a 2026 (LC 214/2025, arts. 361 a 365, na redação da LC 227/2026).</p>
    <p><b>Cenário com a reforma.</b> Soma ICMS e ISS remanescentes, repartidos pela participação de 2025; o IBS retido (80% de 2029 a 2032 e 90% em 2033, art. 109), distribuído pelo coeficiente de participação; o IBS de destino, descontada a parcela do CGIBS; e a distribuição complementar (art. 117). O peso do ICMS e do ISS cai de 90% em 2029 a zero em 2033 (ADCT, art. 128).</p>
    <p><b>Coeficiente de destino.</b> Combina a cota-parte dos Estados (no modelo, por população e partilha igualitária, o que trata os critérios de educação e meio ambiente como proporcionais à população) e o IBS próprio, estimado pelo consumo (renda per capita do Censo 2022 e POF) e pelas compras públicas da DCA.</p>
    <p><b>Distribuição complementar (arts. 110 e 117).</b> Retenção adicional de 5% do IBS, após a do art. 109, distribuída aos entes de menor razão entre IBS e receita média de referência ajustada (limitada a 3 vezes a média per capita), de modo a igualar a razão entre os beneficiários.</p>
  </div>
  <h2 class="sec"><i>8.</i> Limitações</h2>
  <p class="leit peq">Os valores são estimativas, não previsão de caixa, e dependem da projeção macroeconômica, da hipótese de que a participação de 2025 é o ponto de partida do cenário contrafactual e da regulamentação em curso. Os dados municipais são os declarados pelos próprios entes ao Siconfi, sem auditoria, e o horizonte vai de 2029 a 2033. O coeficiente efetivo será o divulgado pelo CGIBS, que poderá usar outras fontes legais e estimar entes com dados inconsistentes (art. 116, §§ 3º e 4º).</p>
  <div class="citar">
    <div><b>Como citar.</b> Vertex Advisory. <i>{esc(TITULO)}: Município de {esc(nome)} ({uf})</i>. Municípios na Reforma, {VERSAO}. Disponível em {SITE}/?m={cod}.<br>
    <span>Fontes: STN/Siconfi (DCA e RREO), IBGE (Censo 2022, POF e estimativas populacionais), BCB (Focus), IFI, EC 132/2023, LC 214/2025 e LC 227/2026.</span></div>
    <div class="qrbox">{qr_svg(url_ficha)}<span>Ficha interativa e memória de cálculo em<br><b>{SITE}</b></span></div>
  </div>
</section>"""

    css = (Path(__file__).resolve().parent / "nota.css").read_text(encoding="utf-8")
    html = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{esc(TITULO)} · {esc(nome)} ({uf})</title><style>{css}</style></head><body>{p1}{p2}{p3}{p4}{p5}</body></html>'
    saida = SAIDA / f"nota-{cod}.html"
    saida.write_text(html, encoding="utf-8")
    print(saida)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "3201308")
