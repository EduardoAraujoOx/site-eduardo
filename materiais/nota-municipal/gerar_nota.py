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

NAVY, GOLD, NEG, POS, CINZA, GRADE = "#1f2a55", "#b8922f", "#a02525", "#1c5cab", "#8a94a6", "#e3e7ea"


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


def svg_serie(m, cor_pos):
    """Receita realizada 2019-2025 (+2026 estimada) e projeção 2029-2033 com e sem a reforma, R$ milhões de 2025."""
    W, H = 690, 330
    L, R, T, B = 52, 78, 26, 40
    hist = {int(a): m["historico_por_ano"][a]["total_reais_2025"] / 1e6 for a in ANOS_HIST if a in m["historico_por_ano"]}
    e26 = m["estimativa_2026"]["total_reais_2025"] / 1e6 if m.get("estimativa_2026") else None
    cf = {int(a): m["contrafactual_por_ano"][a] / 1e6 for a in ANOS}
    ps = {int(a): m["pos_por_ano"][a] / 1e6 for a in ANOS}
    vals = list(hist.values()) + list(cf.values()) + list(ps.values()) + ([e26] if e26 else [])
    ticks, passo = eixo_ticks(min(vals) * 0.85, max(vals) * 1.06, 5)
    lo, hi = ticks[0], ticks[-1]
    X = lambda a: L + (a - 2019) / (2033 - 2019) * (W - L - R)
    Y = lambda v: T + (1 - (v - lo) / (hi - lo)) * (H - T - B)
    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" class="graf" role="img">']
    # faixa 2027-2028
    o.append(f'<rect x="{X(2026.6):.1f}" y="{T}" width="{X(2028.4) - X(2026.6):.1f}" height="{H - T - B}" fill="#f4f5f7"/>')
    o.append(f'<text x="{(X(2026.6) + X(2028.4)) / 2:.1f}" y="{T + 12}" text-anchor="middle" class="rot-faixa">sem projeção</text>')
    for t in ticks:
        o.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{GRADE}" stroke-width="1"/>')
        o.append(f'<text x="{L - 8}" y="{Y(t) + 3.5:.1f}" text-anchor="end" class="eixo">{num(t, 0)}</text>')
    for a in range(2019, 2034, 2):
        o.append(f'<text x="{X(a):.1f}" y="{H - B + 18}" text-anchor="middle" class="eixo">{a}</text>')
    # área da diferença
    a0 = [2029, 2030, 2031, 2032, 2033]
    topo = " ".join(f"{X(a):.1f},{Y(cf[a]):.1f}" for a in a0)
    base = " ".join(f"{X(a):.1f},{Y(ps[a]):.1f}" for a in reversed(a0))
    o.append(f'<polygon points="{topo} {base}" fill="{cor_pos}" fill-opacity=".13"/>')
    # histórico
    pts = " ".join(f"{X(a):.1f},{Y(v):.1f}" for a, v in sorted(hist.items()))
    o.append(f'<polyline points="{pts}" fill="none" stroke="{NAVY}" stroke-width="2.4" stroke-linejoin="round"/>')
    for a, v in sorted(hist.items()):
        o.append(f'<circle cx="{X(a):.1f}" cy="{Y(v):.1f}" r="3.2" fill="{NAVY}" stroke="#fff" stroke-width="1.5"/>')
    if e26 and 2025 in hist:
        o.append(f'<line x1="{X(2025):.1f}" y1="{Y(hist[2025]):.1f}" x2="{X(2026):.1f}" y2="{Y(e26):.1f}" stroke="{NAVY}" stroke-width="2" stroke-dasharray="4 3"/>')
        o.append(f'<circle cx="{X(2026):.1f}" cy="{Y(e26):.1f}" r="3.6" fill="#fff" stroke="{NAVY}" stroke-width="1.8"/>')
    # projeção
    pc = " ".join(f"{X(a):.1f},{Y(cf[a]):.1f}" for a in a0)
    pp = " ".join(f"{X(a):.1f},{Y(ps[a]):.1f}" for a in a0)
    o.append(f'<polyline points="{pc}" fill="none" stroke="{CINZA}" stroke-width="2.4" stroke-dasharray="6 4"/>')
    o.append(f'<polyline points="{pp}" fill="none" stroke="{cor_pos}" stroke-width="2.8" stroke-linejoin="round"/>')
    for a in a0:
        o.append(f'<circle cx="{X(a):.1f}" cy="{Y(ps[a]):.1f}" r="3.2" fill="{cor_pos}" stroke="#fff" stroke-width="1.5"/>')
        o.append(f'<circle cx="{X(a):.1f}" cy="{Y(cf[a]):.1f}" r="2.6" fill="#fff" stroke="{CINZA}" stroke-width="1.6"/>')
    # rótulos finais
    o.append(f'<text x="{X(2033) + 9:.1f}" y="{Y(cf[2033]) + 4:.1f}" class="rot-fim" fill="#5b6577">{num(cf[2033], 0)}</text>')
    o.append(f'<text x="{X(2033) + 9:.1f}" y="{Y(ps[2033]) + 4:.1f}" class="rot-fim" fill="{cor_pos}">{num(ps[2033], 0)}</text>')
    o.append(f'<text x="{X(2025):.1f}" y="{Y(hist[2025]) - 11:.1f}" text-anchor="middle" class="rot-pt">{num(hist[2025], 0)}</text>')
    o.append(f'<text x="2" y="{T - 9}" class="eixo-tit">R$ milhões de 2025</text>')
    o.append("</svg>")
    return "".join(o)


def svg_participacao(d, h):
    """Barras da participação nacional por ano (2019-2025, 2026 estimada) e linha da média (coeficiente histórico)."""
    W, Hh = 690, 250
    L, R, T, B = 52, 20, 26, 34
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
    o.append(f'<line x1="{L}" x2="{W - R}" y1="{yc:.1f}" y2="{yc:.1f}" stroke="{GOLD}" stroke-width="2.2" stroke-dasharray="7 5"/>')
    o.append(f'<text x="{L + 8}" y="{yc - 7:.1f}" class="rot-ouro">média {num(d["coef"], dig)}%</text>')
    o.append(f'<defs><pattern id="hach" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="#fff"/><line x1="0" y1="0" x2="0" y2="6" stroke="{NAVY}" stroke-width="2.4"/></pattern></defs>')
    o.append("</svg>")
    return "".join(o)


def svg_composicao(m):
    """Colunas empilhadas 2029-2033: ICMS/ISS residual, IBS pelo critério histórico, IBS pelo destino, Seguro-Receita (R$ milhões de 2025)."""
    W, Hh = 330, 205
    L, R, T, B = 40, 10, 22, 28
    comp = m["componentes_por_ano"]
    cats = [("origem", "ICMS e ISS que restam", CINZA), ("cpt", "IBS pelo critério histórico", NAVY), ("destino", "IBS pelo destino", GOLD), ("seguro", "Seguro-Receita", "#2f7d4f")]
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
    W, Hh = 330, 205
    L, R, T, B = 44, 8, 20, 24
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


def main(cod):
    idx = carrega("painel-municipios/index.json")
    uf = next(m["uf"] for c, m in idx["municipios"].items() if c == cod)
    m = carrega(f"painel-municipios/{uf}.json")["municipios"][cod]
    nome = m["nome"]
    nac_j = carrega("ibs-projecao-nacional.json")
    nac = {str(r["ano"]): r for r in nac_j["projecao"]}
    ref_nac = idx["referencia_nacional"]
    tb, fat = ref_nac["total_br_2025"], ref_nac["fatores_ajuste"]

    # posições
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
    perde = v33 < -0.0005
    ganha = v33 > 0.0005
    cor = NEG if perde else POS if ganha else CINZA
    cor_clara = "#ff9d94" if perde else "#9cc6ff" if ganha else "#d5dae6"
    selo = "Perda estimada" if perde else "Ganho estimado" if ganha else "Receita estável"
    lado = "a menos" if perde else "a mais"
    recebe_seguro = any((m["repasse_seguro_receita_por_ano"].get(a) or 0) > 1 for a in ANOS)

    # participação
    h = m["historico_por_ano"]
    valores = [h[a]["total_reais_2025"] / tb * 100 if a in h else None for a in ANOS_HIST]
    est26 = m["estimativa_2026"]["total_reais_2025"] / tb * 100 if m.get("estimativa_2026") else None
    d = {"valores": valores, "est": est26, "coef": m["coef_cpt_pct"], "s25": valores[-1]}

    pop = round(m["pop_media"])
    nome_uf = NOMES_UF[uf]

    # sensibilidade
    refs = sens_refs(m)
    erro = carrega("sensibilidade-uf.json")["por_uf"][uf]["incerteza_rel"]
    sens_linhas = []
    for a in sorted(refs):
        sens_linhas.append((a, refs[a], sens_var(m, nac, refs[a], 0), sens_var(m, nac, refs[a], -erro), sens_var(m, nac, refs[a], erro)))
    var24 = next(l for l in sens_linhas if l[0] == "2024")[2] if any(l[0] == "2024" for l in sens_linhas) else None

    # ── páginas ──
    def cab(n, titulo):
        return (f'<div class="cab"><span>NOTA MUNICIPAL · {esc(nome.upper())} ({uf})</span><span>municipiosnareforma.com.br</span></div>'
                f'<div class="rod"><span>{esc(nome)} ({uf}) · dados de {VERSAO} · Municípios na Reforma, iniciativa da Vertex Advisory</span><span>{n} / 5</span></div>')

    # p1
    kpis = (f'<div class="kpi"><span>Receita em 2025</span><b>{dinheiro(m["pre_2025"], True)}</b></div>'
            f'<div class="kpi"><span>2033 sem a reforma</span><b>{dinheiro(cf33, True)}</b></div>'
            f'<div class="kpi dest" style="--c:{cor}"><span>2033 com a reforma</span><b>{dinheiro(pos33, True)}</b></div>')
    p_muda = (f"Entre 2029 e 2033, o ICMS e o ISS são extintos de forma gradual e substituídos pelo IBS. Durante a transição, a parte do IBS que cabe a cada município é repartida por dois critérios: "
              f"o <b>histórico</b>, que preserva a fatia que o município teve na arrecadação nacional entre 2019 e 2026, e o de <b>destino</b>, que acompanha o consumo e as compras públicas locais. "
              f"Em 2033 o critério histórico responde por cerca de 90% da repartição; o destino só chega a 100% em 2078 (ADCT, art. 131).")
    cresc = d["s25"] / d["valores"][0] - 1
    r_ = d["coef"] / d["s25"]
    if r_ < 0.87:
        p_porque = (f"<b>Por que {esc(nome)} {'perde' if perde else 'tem efeito negativo'}.</b> A fatia do município na arrecadação nacional {'cresceu' if cresc > 0 else 'caiu'} {num(abs(cresc) * 100, 0)}% entre 2019 e 2025. "
                    f"Como a regra usa a <i>média</i> de 2019 a 2026 ({pct_adapt(d['coef'])}) e não a fatia de 2025 ({pct_adapt(d['s25'])}), o crescimento recente não é plenamente reconhecido: "
                    f"o município é comparado com o que arrecadaria se mantivesse a fatia de hoje, e a reforma lhe devolve uma fatia {num((1 - r_) * 100, 0)}% menor.")
    elif r_ > 1.15:
        p_porque = (f"<b>Por que {esc(nome)} ganha.</b> A fatia do município na arrecadação nacional {'cresceu' if cresc > 0 else 'caiu'} {num(abs(cresc) * 100, 0)}% entre 2019 e 2025. "
                    f"A regra usa a <i>média</i> de 2019 a 2026 ({pct_adapt(d['coef'])}), acima da fatia de 2025 ({pct_adapt(d['s25'])}); a reforma preserva uma fatia maior do que a de hoje.")
    else:
        p_porque = (f"<b>Por que o efeito é pequeno.</b> A média de 2019 a 2026 ({pct_adapt(d['coef'])}) é parecida com a fatia de 2025 ({pct_adapt(d['s25'])}); o critério histórico quase não altera o ponto de partida.")
    p_seguro = ("<b>Seguro-Receita.</b> " + ("O município recebe repasse do Seguro-Receita em parte do período, o que reduz o efeito acima." if recebe_seguro else
                f"Em 2029–2033, a receita de {esc(nome)} pelo critério de destino fica acima do nível de nivelamento em todos os anos; por isso o município não recebe o repasse compensatório do Seguro-Receita (ADCT, art. 132)."))
    p_incert = (f"<b>O que torna o número incerto.</b> O resultado é uma comparação entre dois cenários e depende de qual fatia se considera como ponto de partida do cenário sem a reforma. "
                f"A página 4 mostra o quanto ele se altera conforme essa escolha.")

    p1 = f"""
<section class="page capa">
  <div class="banda">
    <div class="kick">EFEITO DA REFORMA TRIBUTÁRIA NA RECEITA MUNICIPAL</div>
    <h1>{esc(nome)}</h1>
    <div class="meta">{esc(nome_uf)} · {num(pop)} habitantes · ISS e cota-parte do ICMS substituídos pelo IBS</div>
    <div class="hero" style="--c:{cor};--hc:{cor_clara}">
      <div class="hn"><em>{selo}</em><b>{pct(v33)}</b><small>efeito da reforma na receita em 2033</small></div>
      <p>Em 2033, {esc(nome)} deve arrecadar <strong>{dinheiro(abs(dif33))} {lado} por ano</strong> do que arrecadaria sem a reforma.
         <span>Comparação entre os dois cenários do mesmo ano, em reais de 2025.</span></p>
    </div>
  </div>
  <div class="kpis">{kpis}</div>
  <h2 class="sec">Em resumo</h2>
  <div class="resumo">
    <p>{p_muda}</p>
    <p>{p_porque}</p>
    <p>{p_seguro}</p>
    <p>{p_incert}</p>
  </div>
  <div class="posicoes">
    <div><b>{pos_uf}º</b><span>entre {len(uf_lista)} municípios {EM_UF[uf]} com base de 2025, do maior ganho à maior perda. {perdem_uf} deles têm perda estimada em 2033.</span></div>
    <div><b>{num(pos_br)}º</b><span>entre {num(len(ok))} municípios do Brasil com base de 2025. {num(perdem_br)} têm perda estimada em 2033.</span></div>
  </div>
  <p class="aviso-peq">As cifras são estimativas de um modelo, construídas com a regra de transição vigente e dados oficiais declarados pelos próprios entes. Não são previsão de caixa nem substituem a análise jurídica e orçamentária do município.</p>
  {cab(1, '')}
</section>"""

    # p2
    linhas = "".join(
        f'<tr><td>{a}</td><td class="n">{mi(m["contrafactual_por_ano"][a])}</td><td class="n">{mi(m["pos_por_ano"][a])}</td>'
        f'<td class="n {"neg" if m["variacao_por_ano"][a] < -0.0005 else "pos" if m["variacao_por_ano"][a] > 0.0005 else ""}">{mi(m["pos_por_ano"][a] - m["contrafactual_por_ano"][a])}</td>'
        f'<td class="n {"neg" if m["variacao_por_ano"][a] < -0.0005 else "pos" if m["variacao_por_ano"][a] > 0.0005 else ""}"><b>{pct(m["variacao_por_ano"][a])}</b></td></tr>' for a in ANOS)
    acum = sum(m["pos_por_ano"][a] - m["contrafactual_por_ano"][a] for a in ANOS)
    real_c, real_s = pos33 / m["pre_2025"] - 1, cf33 / m["pre_2025"] - 1
    v29, v32 = m["variacao_por_ano"]["2029"], m["variacao_por_ano"]["2032"]
    salto = m["componentes_por_ano"]["2033"]["origem"] == 0 and m["componentes_por_ano"]["2032"]["origem"] > 0
    t_traj = (f"A diferença entre os dois cenários {'aumenta' if abs(v33) > abs(v29) else 'varia'} a cada ano: de {pct(v29)} em 2029 para {pct(v32)} em 2032 e {pct(v33)} em 2033. ")
    if salto and abs(v33) > abs(v32) * 1.3:
        t_traj += ("O salto do último ano tem uma razão mecânica. Até 2032 resta uma parcela do ICMS e do ISS, que continua repartida pela fatia de 2025 e amortece o efeito; "
                   "em 2033 esses tributos deixam de existir e a receita passa a depender por inteiro do IBS, repartido sobretudo pelo critério histórico.")
    p2 = f"""
<section class="page">
  {cab(2, '')}
  <h2 class="sec first">A trajetória da receita</h2>
  <p class="sub">Receita de ISS e cota-parte do ICMS realizada de 2019 a 2025 e projetada de 2029 a 2033 (IBS e tributos remanescentes), com e sem a reforma, em R$ milhões de 2025.</p>
  <div class="fig">{svg_serie(m, cor)}
    <div class="leg"><span><i class="l" style="background:{NAVY}"></i>Realizada (2026: estimada pelo RREO)</span><span><i class="l tr" style="border-color:{CINZA}"></i>2033 sem a reforma</span><span><i class="l" style="background:{cor}"></i>Com a reforma</span></div></div>
  <h3>Ano a ano</h3>
  <table class="tab"><thead><tr><th>Ano</th><th class="n">Sem a reforma<br><small>R$ mi</small></th><th class="n">Com a reforma<br><small>R$ mi</small></th><th class="n">Diferença<br><small>R$ mi</small></th><th class="n">Variação</th></tr></thead><tbody>{linhas}</tbody></table>
  <div class="mini">
    <div><span>Diferença acumulada, 2029–2033</span><b class="{'neg' if acum < 0 else 'pos'}">{dinheiro(acum)}</b><small>soma das diferenças anuais, em R$ de 2025</small></div>
    <div><span>Com a reforma, 2033 vs. 2025</span><b class="{'neg' if real_c < 0 else 'pos'}">{pct(real_c)}</b><small>variação real da receita entre os dois anos</small></div>
    <div><span>Sem a reforma, 2033 vs. 2025</span><b class="{'neg' if real_s < 0 else 'pos'}">{pct(real_s)}</b><small>variação real mantendo a fatia de 2025</small></div>
  </div>
  <p class="leit">{t_traj}</p>
  <p class="leit">O cenário <i>sem a reforma</i> mantém a fatia que {esc(nome)} tinha na arrecadação nacional de ICMS e ISS em 2025 e a aplica ao bolo nacional projetado (PIB, Focus e IFI). O cenário <i>com a reforma</i> aplica as regras de transição do ADCT e da LC 227/2026 à mesma projeção. A diferença entre os dois mede o efeito da reforma, e não a evolução da receita em si.</p>
</section>"""

    # p3 — participação e tabela B.1
    corr = lambda a, v: v / fat[a] if (a in fat and fat[a]) else v
    linhas_b1 = ""
    soma = 0.0
    for a in ANOS_HIST:
        if a not in h:
            continue
        f = fat.get(a, 1.0)
        iss_c, cota_c, tot_c = h[a]["iss_reais_2025"] / f, h[a]["cota_parte_reais_2025"] / f, h[a]["total_reais_2025"] / f
        soma += h[a]["total_reais_2025"]
        linhas_b1 += (f'<tr><td>{a}</td><td class="n">{num(iss_c)}</td><td class="n">{num(cota_c)}</td><td class="n">{num(tot_c)}</td><td class="n">{num(f, 4)}</td>'
                      f'<td class="n"><b>{num(h[a]["total_reais_2025"])}</b></td><td class="n">{pct_adapt(h[a]["total_reais_2025"] / tb * 100)}</td></tr>')
    e = m.get("estimativa_2026")
    n_anos = len(ANOS_HIST) + (1 if e else 0)
    if e:
        soma += e["total_reais_2025"]
        linhas_b1 += (f'<tr class="est"><td>2026 <small>(RREO)</small></td><td class="n">{num(e["iss_reais_2025"])}</td><td class="n">{num(e["cota_parte_reais_2025"])}</td><td class="n">{num(e["total_reais_2025"])}</td>'
                      f'<td class="n">n.a.</td><td class="n"><b>{num(e["total_reais_2025"])}</b></td><td class="n">{pct_adapt(e["total_reais_2025"] / tb * 100)}</td></tr>')
    media = soma / n_anos
    origem_txt = ""
    if any((h[a].get("origem") for a in h)):
        origem_txt = " Os anos assinalados foram completados fora da DCA (RREO ou estimativa pela série do município)."
    p3 = f"""
<section class="page">
  {cab(3, '')}
  <h2 class="sec first">Por que o resultado é este: a participação histórica</h2>
  <p class="sub">A reforma distribui o IBS pela fatia que cada município teve, em média, na arrecadação nacional de ICMS e ISS de 2019 a 2026. O gráfico compara a fatia de cada ano com essa média.</p>
  <div class="fig">{svg_participacao(d, h)}</div>
  <p class="leit">{esc(texto_participacao(nome, d))}</p>
  <h3>A conta, ano a ano</h3>
  <table class="tab b1"><thead><tr><th>Ano</th><th class="n">ISS<br><small>(corrente)</small></th><th class="n">+ Cota-parte<br>de ICMS</th><th class="n">= Referência<br><small>(corrente)</small></th><th class="n">× Fator de<br>ajuste</th><th class="n">= Referência em<br>R$ de 2025</th><th class="n">Fatia do<br>total nacional</th></tr></thead>
  <tbody>{linhas_b1}</tbody>
  <tfoot><tr><td colspan="5">Soma da referência em R$ de 2025</td><td class="n">{num(soma)}</td><td class="n"></td></tr>
  <tr><td colspan="5">Média de {n_anos} anos (soma ÷ {n_anos})</td><td class="n"><b>{num(media)}</b></td><td class="n"></td></tr>
  <tr><td colspan="5">Total nacional de ICMS e ISS em 2025 (denominador)</td><td class="n">{num(tb)}</td><td class="n"></td></tr>
  <tr class="res"><td colspan="5">Coeficiente histórico = média ÷ total nacional</td><td class="n" colspan="2"><b>{pct_plain(m["coef_cpt_pct"], 6)}</b></td></tr></tfoot></table>
  <p class="nota">Valores em R$. O fator de ajuste leva cada ano a reais de 2025 pela variação da arrecadação nacional de ICMS e ISS (LC 227/2026, art. 115, §2º, II).{origem_txt} Em 2026, ainda sem DCA, o ISS é o observado no RREO de setembro de 2025 a agosto de 2026 e a cota-parte é a de 2025 ajustada pelo crescimento de janeiro a agosto.</p>
</section>"""

    # p4 — composição, pares, sensibilidade
    svg_c, leg_c = svg_composicao(m)
    svg_p = svg_pares(uf_lista, cod)
    sens_rows = ""
    for a, rf, vc, vlo, vhi in sens_linhas:
        central = a == "2025"
        cls_c = ' class="cent"' if central else ""
        sens_rows += (f'<tr{cls_c}><td>{a}{" (est.)" if a == "2026" else ""}{" <small>· cenário central</small>" if central else ""}</td><td class="n">{pct_adapt(rf * 100)}</td>'
                      f'<td class="n {"neg" if vc < 0 else "pos"}"><b>{pct(vc)}</b></td><td class="n">{pct(min(vlo, vhi))} a {pct(max(vlo, vhi))}</td></tr>')
    pos_anos = [l[0] for l in sens_linhas if l[2] > 0]
    neg_anos = [l[0] for l in sens_linhas if l[2] < 0]
    t_sens = ("Cada linha refaz o cálculo de 2033 supondo que o cenário sem a reforma mantivesse a fatia nacional de outro ano, em vez da de 2025, que é a referência central por ser o último ano fechado. ")
    if pos_anos and neg_anos:
        t_sens += (f"O sinal do resultado muda conforme o ano escolhido: com a fatia de {faixa_anos(pos_anos)} a reforma seria favorável ao município; com a de {faixa_anos(neg_anos)}, desfavorável. "
                   f"Quanto mais rápido o município cresceu em relação ao país, mais o resultado depende dessa escolha. ")
    t_sens += (f"A última coluna acrescenta a margem de erro do consumo estimado pelo critério de destino ({num(erro * 100, 1)}% para {NOMES_UF[uf]}), que pesa pouco frente à escolha do ano-base.")
    p4 = f"""
<section class="page">
  {cab(4, '')}
  <h2 class="sec first">De onde vem a receita e como o município se compara</h2>
  <div class="duas">
    <div><h3>Composição da receita projetada</h3><p class="sub">R$ milhões de 2025. Quanto ainda vem do ICMS e do ISS e quanto já vem do IBS.</p>
      <div class="fig">{svg_c}<div class="leg v">{leg_c}</div></div></div>
    <div><h3>{esc(nome)} entre os municípios {EM_UF[uf]}</h3><p class="sub">Variação da receita em 2033, do maior ganho (esquerda) à maior perda (direita). {len(uf_lista)} municípios com base de 2025.</p>
      <div class="fig">{svg_p}</div></div>
  </div>
  <div class="coefs">
    <div><span>Participação neutra, 2025</span><b>{pct_adapt(m["coef_neutro_pct"])}</b><small>A fatia de hoje, sem a reforma: o ponto de partida da comparação.</small></div>
    <div><span>Coeficiente histórico</span><b>{pct_adapt(m["coef_cpt_pct"])}</b><small>Média de 2019 a 2026. Define cerca de 90% da repartição em 2033.</small></div>
    <div><span>Coeficiente de destino</span><b>{pct_adapt(m["coef_pleno_pct"])}</b><small>{pct_adapt(m["cota_parte_pct"])} pela cota-parte estadual e {pct_adapt(m["propria_pct"])} pelo consumo e compras próprios. Pesa 100% só em 2078.</small></div>
  </div>
  <h2 class="sec">Quanto o resultado depende das hipóteses</h2>
  <p class="sub">Efeito da reforma em 2033 conforme o ano cuja fatia o cenário sem a reforma mantém.</p>
  <table class="tab sens"><thead><tr><th>Fatia mantida do ano</th><th class="n">Fatia nacional</th><th class="n">Efeito em 2033</th><th class="n">Com margem de erro do destino</th></tr></thead><tbody>{sens_rows}</tbody></table>
  <p class="leit">{t_sens}</p>
  {cab(4, '')}
</section>"""

    # p5 — pontos de atenção e metodologia
    p5 = f"""
<section class="page">
  {cab(5, '')}
  <h2 class="sec first">Pontos de atenção para a gestão</h2>
  <div class="atencao">
    <p><b>Conferir a base declarada.</b> O coeficiente histórico nasce do ISS e da cota-parte do ICMS lançados no SICONFI (DCA) entre 2019 e 2025. Valores ausentes, repetidos ou lançados em conta errada reduzem a média e, com ela, a fatia futura do município. Os entes podem retificar suas declarações, e vale revisar a série de {esc(nome)} ano a ano na tabela da página 3.</p>
    <p><b>Tratar a janela de 2019 a 2026 como fechada.</b> A média da lei termina em 2026. O que o município arrecadar depois dessa data não altera o coeficiente histórico, que passa a depender da conferência do passado e da regulamentação.</p>
    <p><b>Planejar com faixa, e não com ponto.</b> Para o PPA e a LDO, é prudente trabalhar com o intervalo da página 4 e acompanhar as atualizações do modelo e a regulamentação do Comitê Gestor do IBS.</p>
    <p><b>Acompanhar o critério de destino.</b> A parcela por destino cresce até 2078 e depende da renda, do consumo e das compras públicas locais. É o canal pelo qual o município recupera fatia no longo prazo.</p>
  </div>
  <h2 class="sec">Metodologia</h2>
  <div class="met">
    <p><b>Receita de referência.</b> Para o município, é o ISS bruto somado à cota-parte de ICMS recebida do estado, declarados ao SICONFI (DCA, Anexo I-C), de 2019 a 2025. Em 2026, pelo RREO até agosto. Quando uma DCA falta, o painel completa a série pelo RREO anual ou, na falta dele, pela série do próprio município, e descarta valores fora da faixa entre metade e o dobro do esperado.</p>
    <p><b>Coeficiente histórico.</b> Média da receita de referência de 2019 a 2026, em reais de 2025, dividida pelo total nacional de ICMS e ISS de 2025 ({dinheiro(tb, True)}), conforme o art. 115 da LC 227/2026.</p>
    <p><b>Cenário sem a reforma.</b> Fatia do município em 2025 vezes o bolo nacional projetado de ICMS e ISS, que cresce com o PIB nominal (Focus do BCB até 2030 e IFI de 2031 a 2033) e com a razão média entre a arrecadação e o PIB de 2024 a 2026.</p>
    <p><b>Cenário com a reforma.</b> Em cada ano, soma quatro parcelas: o ICMS e o ISS que restam, repartidos pela fatia de 2025; o IBS pelo critério histórico, pelo coeficiente histórico; o IBS pelo critério de destino, pelo coeficiente de destino, descontada a parcela do Comitê Gestor; e o repasse do Seguro-Receita. O peso do ICMS e do ISS cai de 90% em 2029 a zero em 2033, conforme o cronograma do ADCT (art. 128 e 131).</p>
    <p><b>Coeficiente de destino.</b> Combina a cota-parte estadual do município (população e partilha igualitária) com o IBS próprio, estimado pelo consumo (renda domiciliar per capita do Censo 2022 e despesa da POF) e pelas compras públicas declaradas à DCA.</p>
    <p><b>Seguro-Receita.</b> Repasse compensatório ao ente cuja receita pelo critério de destino fica abaixo do nível de nivelamento do ano, com teto de três vezes a média nacional per capita da esfera (ADCT, art. 132; LC 227/2026, art. 117, §6º).</p>
  </div>
  <h2 class="sec">Limitações</h2>
  <p class="leit peq">Os valores são estimativas, não previsão de caixa. Dependem da projeção macroeconômica, da hipótese de que a fatia de 2025 é o ponto de partida do cenário sem a reforma e da regulamentação ainda em curso. Os dados municipais são os declarados pelos próprios entes ao SICONFI, sem auditoria, e o horizonte de projeção vai de 2029 a 2033. A memória de cálculo completa, com todos os números intermediários e a possibilidade de refazer a conta em planilha, está no portal.</p>
  <div class="citar"><b>Como citar.</b> Vertex Advisory. <i>Nota Municipal: {esc(nome)} ({uf})</i>. Municípios na Reforma, {VERSAO}. Disponível em municipiosnareforma.com.br/?m={cod}. Fontes: STN/SICONFI (DCA e RREO), IBGE (Censo 2022, POF), BCB (Focus), IFI, EC 132/2023, LC 214/2025 e LC 227/2026.</div>
</section>"""

    css = (Path(__file__).resolve().parent / "nota.css").read_text(encoding="utf-8")
    html = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Nota Municipal · {esc(nome)} ({uf})</title><style>{css}</style></head><body>{p1}{p2}{p3}{p4}{p5}</body></html>'
    saida = SAIDA / f"nota-{cod}.html"
    saida.write_text(html, encoding="utf-8")
    print(saida)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "3201308")
