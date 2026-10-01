#!/usr/bin/env python3
"""
Converte um artigo em LaTeX para Word (.docx) sem alterar o texto, aplicando a
formatação do edital do Prêmio Tesouro Estadual (A4; margens superior e
esquerda 3 cm, inferior e direita 2 cm; Times New Roman 12; entrelinhas 1,5;
texto justificado; paginação no rodapé; ABNT; sem identificação de autoria,
inclusive nas propriedades do arquivo).

O que o script faz antes do Pandoc (apenas na cópia temporária do .tex):
  - resolve a numeração de tabelas, gráficos e equações e substitui cada \\ref
    pelo número (o Pandoc perde os rótulos do LaTeX);
  - normaliza tabelas (tabular*, tabularx, colunas L/C/R, \\shortstack,
    \\multicolumn, \\cmidrule, \\rowcolor) para a forma que o Pandoc entende;
  - retira \\label das equações (que impedia a conversão para equação nativa);
  - troca figuras em PDF por PNG quando o arquivo existe em --imgdir; quando
    não existe, deixa um quadro de espaço reservado com o nome do arquivo.

Depois do Pandoc (python-docx): margens, rodapé com paginação, estilos ABNT,
tabelas com filetes horizontais, tabela larga em seção paisagem, espaço
reservado para título, resumo/abstract e palavras-chave, espaço para
Referências e quebra de página antes de cada Anexo. Limpa metadados de autoria.

Uso:
  python3 tex2docx-edital.py artigo.tex saida.docx [--imgdir pasta_com_figuras]
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pypandoc
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

FONTE = "Times New Roman"
MARK_RC, MARK_LS, MARK_LE, MARK_EQ = "§§RC§§", "§§LS§§", "§§LE§§", "§§EQ§§"
LINHA = 1.5   # entrelinhas do corpo (edital: 1,5)
LARG_FIG = []  # larguras (cm) das figuras reais, na ordem do texto
TEM_PAISAGEM = False
ABERTURA = None  # dict com titulo, subtitulo, resumo, palavras, abstract, keywords (--abertura JSON)
TITULO = ""    # título do trabalho (pdftitle do LaTeX ou --titulo)
EQ_IMAGEM = True  # equações com \\underbrace viram imagem (True) ou equação editável do Word (False)


# ───────────────────────── pré-processamento do LaTeX ─────────────────────────
def grupo(s, i):
    """s[i] == '{' -> índice do '}' correspondente."""
    assert s[i] == "{", s[i:i + 20]
    n = 0
    for j in range(i, len(s)):
        if s[j] == "\\":
            continue
        if s[j] == "{" and (j == 0 or s[j - 1] != "\\"):
            n += 1
        elif s[j] == "}" and (j == 0 or s[j - 1] != "\\"):
            n -= 1
            if n == 0:
                return j
    raise ValueError("chave sem par")


def troca_comando(s, nome, f):
    """Substitui \\nome{arg} por f(arg), com chaves balanceadas."""
    pad = "\\" + nome + "{"
    out, i = [], 0
    while True:
        k = s.find(pad, i)
        if k < 0:
            out.append(s[i:])
            return "".join(out)
        j = grupo(s, k + len(pad) - 1)
        out.append(s[i:k])
        out.append(f(s[k + len(pad):j]))
        i = j + 1


def coluna_simples(spec):
    out, i = "", 0
    while i < len(spec):
        c = spec[i]
        if c in "lrc":
            out += c
        elif c in "XLCRp":
            if i + 1 < len(spec) and spec[i + 1] == "{":
                i = grupo(spec, i + 1)
            out += {"X": "l", "L": "l", "p": "l", "C": "c", "R": "r"}[c]
        elif c in ">@<!":
            if i + 1 < len(spec) and spec[i + 1] == "{":
                i = grupo(spec, i + 1)
        i += 1
    return out


def normaliza_tabelas(s):
    def um(tipo, s):
        out, i = [], 0
        ini = "\\begin{" + tipo + "}"
        while True:
            k = s.find(ini, i)
            if k < 0:
                out.append(s[i:])
                return "".join(out)
            p = k + len(ini)
            if tipo != "tabular":
                p = grupo(s, p) + 1                      # largura
            e = grupo(s, p)                              # especificação das colunas
            out.append(s[i:k] + "\\begin{tabular}{" + coluna_simples(s[p + 1:e]) + "}")
            i = e + 1
        return "".join(out)
    for t in ("tabular*", "tabularx"):
        s = um(t, s)
        s = s.replace("\\end{" + t + "}", "\\end{tabular}")
    # tabular simples: já vem só com a especificação; limpa @{} e afins
    def simples(m):
        return "\\begin{tabular}{" + coluna_simples(m.group(1)) + "}"
    s = re.sub(r"\\begin\{tabular\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", simples, s)
    s = re.sub(r"\\cmidrule(\([a-z]*\))?\{[^}]*\}", "", s)
    s = re.sub(r"\\rowcolor\{[^}]*\}", MARK_RC, s)
    s = troca_comando(s, "shortstack", lambda a: a.replace("\\\\", " \\newline "))
    return s


def limpa_formatacao(s):
    s = re.sub(r"\\fontsize\{[^}]*\}\{[^}]*\}\\selectfont", "", s)
    s = re.sub(r"\\renewcommand\{\\arraystretch\}\{[^}]*\}", "", s)
    s = re.sub(r"\\setlength\{\\tabcolsep\}\{[^}]*\}", "", s)
    s = re.sub(r"\\vspace\{[^}]*\}", "", s)
    s = re.sub(r"\\begin\{minipage\}(\[[a-z]\])?\{[^}]*\}", "", s)
    s = s.replace("\\end{minipage}", "").replace("\\hfill", "")
    s = s.replace("\\raggedright", "").replace("\\raggedleft", "").replace("\\small", "")
    s = s.replace("\\clearpage", "")
    global TEM_PAISAGEM
    TEM_PAISAGEM = "\\begin{landscape}" in s
    def paisagem(m):
        b = m.group(1).replace("\\begingroup", "\\begin{table}").replace("\\endgroup", "\\end{table}")
        return MARK_LS + "\n\n" + b.replace("\\captionof{table}", "\\caption") + "\n\n" + MARK_LE
    s = re.sub(r"\\begin\{landscape\}(.*?)\\end\{landscape\}", paisagem, s, flags=re.S)
    s = re.sub(r"\\setlength\{\\Urlmuskip\}\{[^}]*\}", "", s)
    for c in ("\\begingroup", "\\endgroup", "\\sloppy"):
        s = s.replace(c, "")
    return s


def renderiza_equacao_modelo(numero, saida, largura_cm=16.0, alvo_cm=15.2):
    """Equação com chaves (\\underbrace) e rótulos: desenhada numa só linha, em alta resolução,
    com as chaves sob cada termo e o rótulo centrado abaixo. Retorna a largura (cm) da imagem.
    É uma imagem (não editável): o OMML do Word quebra a linha quando os rótulos são mais largos
    que os termos, e o desenho garante a leitura."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MP
    plt.rcParams.update({"mathtext.fontset": "stix", "font.family": "STIXGeneral"})
    T1 = r"$f_t\,w_i^{0}$"; T2 = r"$s_t\,\lambda_t\,w_i^{H}$"; T3 = r"$s_t\,(1-\lambda_t)\,(1-\rho_t)\,w_i^{D}$"
    T4 = r"$S_{it}$"; T5 = r"$G_{it}$"
    itens = [("t", r"$R_{it}^{R}\;=\;A_t$"), ("col", "["), ("b", T1, "ICMS/ISS residual"), ("t", r"$+$"),
             ("b", T2, "IBS pelo histórico"), ("t", r"$+$"), ("b", T3, "IBS pelo destino"), ("col", "]"),
             ("t", r"$+$"), ("b", T4, "Seguro-Receita"), ("t", r"$-$"), ("b", T5, "CGIBS"), ("t", r"$.$")]
    fs0 = 12.0
    fig = plt.figure(figsize=(8, 2), dpi=300)
    rend = fig.canvas.get_renderer()

    def larg(txt, fs):
        t = fig.text(0, 0, txt, fontsize=fs)
        w = t.get_window_extent(rend).width * 72 / fig.dpi
        t.remove()
        return w
    def medida(fs):
        x, pos = 0.0, []
        for it in itens:
            if it[0] == "b":
                wt, wl = larg(it[1], fs), larg(it[2], 0.68 * fs)
                slot = max(wt, wl + 0.6 * fs)
                pos.append((it, x + (slot - wt) / 2, wt, x + slot / 2)); x += slot
            elif it[0] == "col":
                w = larg("[", 1.9 * fs) * 0.9
                pos.append((it, x, w, 0)); x += w + 0.1 * fs
            else:
                w = larg(it[1], fs)
                pad = 0.5 * fs if it[1] in (r"$+$", r"$-$") else (0.05 * fs if it[1] == r"$.$" else 0.0)
                pos.append((it, x + pad, w, 0)); x += w + 2 * pad
        return x, pos
    total, _ = medida(fs0)
    num_txt = "$(%s)$" % numero
    wnum = larg(num_txt, fs0)
    alvo_pt = alvo_cm / 2.54 * 72
    fs = fs0 * min(1.0, (alvo_pt - wnum * 1.0) / total)
    total, pos = medida(fs)
    wnum = larg(num_txt, fs)
    largura_pt = largura_cm / 2.54 * 72
    x0 = (largura_pt - wnum - total) / 2
    alt = 4.2 * fs
    plt.close(fig)
    fig = plt.figure(figsize=(largura_pt / 72, alt / 72), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, largura_pt); ax.set_ylim(0, alt); ax.axis("off")
    y0 = 2.6 * fs
    for it, xi, w, xc in pos:
        if it[0] == "t":
            ax.text(x0 + xi, y0, it[1], fontsize=fs, va="baseline", ha="left")
        elif it[0] == "col":
            ax.text(x0 + xi, y0 + 0.25 * fs, it[1], fontsize=1.9 * fs, va="center", ha="left")
        else:
            ax.text(x0 + xi, y0, it[1], fontsize=fs, va="baseline", ha="left")
            a, b = x0 + xi, x0 + xi + w
            h, r = 0.42 * fs, min(0.42 * fs, (b - a) / 4)
            ytop = y0 - 0.5 * fs; xm = (a + b) / 2
            verts = [(a, ytop + h * 0.0), (a, ytop - h), (a + r, ytop - h), (xm - r, ytop - h), (xm, ytop - h),
                     (xm, ytop - 2 * h), (xm + r, ytop - h), (b - r, ytop - h), (b, ytop - h), (b, ytop)]
            codes = [MP.MOVETO, MP.CURVE3, MP.CURVE3, MP.LINETO, MP.CURVE3, MP.CURVE3, MP.CURVE3, MP.LINETO, MP.CURVE3, MP.CURVE3]
            ax.add_patch(PathPatch(MP(verts, codes), fill=False, lw=0.8, ec="black"))
            ax.text(x0 + xc, ytop - 2 * h - 0.25 * fs, it[2], fontsize=0.68 * fs, va="top", ha="center")
    ax.text(largura_pt, y0, num_txt, fontsize=fs, va="baseline", ha="right")
    fig.savefig(saida, dpi=300, facecolor="white")
    plt.close(fig)
    return largura_cm, alt / 72 * 2.54


def numera_e_resolve(s, tmp=None):
    """Numera tabelas (A.1, B.1...), gráficos e equações e resolve \\ref."""
    eventos = []
    for m in re.finditer(r"\\renewcommand\{\\thetable\}\{([A-Z])\.\\arabic\{table\}\}", s):
        eventos.append((m.start(), "prefixo", m.group(1)))
    for m in re.finditer(r"\\begin\{(table|figure)\}", s):
        eventos.append((m.start(), "abre", m.group(1)))
    for m in re.finditer(r"\\caption\{", s):
        eventos.append((m.start(), "caption", m.end()))
    for m in re.finditer(r"\\label\{([^}]*)\}", s):
        eventos.append((m.start(), "label", m.group(1)))
    for m in re.finditer(r"\\begin\{equation\}", s):
        eventos.append((m.start(), "eq", None))
    eventos.sort()
    mapa, cont, prefixo, env, ultimo = {}, {"table": 0, "figure": 0, "eq": 0}, "", None, None
    inserir = []  # (posição, texto)
    for pos, tipo, dado in eventos:
        if tipo == "prefixo":
            prefixo, cont["table"] = dado + ".", 0
        elif tipo == "abre":
            env = dado
        elif tipo == "caption":
            ml = re.search(r"\\label\{fig:mapa[^}]*\}", s[dado:dado + 400])
            chave = "mapa" if (env == "figure" and ml) else env
            cont[chave] = cont.get(chave, 0) + 1
            num = (prefixo if env == "table" else "") + str(cont[chave])
            rot = "Tabela" if env == "table" else ("Mapa" if chave == "mapa" else "Gráfico")
            inserir.append((dado, "\\textbf{" + rot + " " + num + ":}~"))
            ultimo = num
        elif tipo == "label":
            if ultimo is not None:
                mapa[dado] = ultimo
                ultimo = None
        elif tipo == "eq":
            cont["eq"] += 1
            ultimo = str(cont["eq"])
    for pos, txt in sorted(inserir, reverse=True):
        s = s[:pos] + txt + s[pos:]
    # equações: troca o ambiente por $$...$$ com o número à direita e sem \label
    n = [0]

    def eq(m):
        n[0] += 1
        if EQ_IMAGEM and "\\underbrace" in m.group(1) and tmp is not None:
            png = Path(tmp) / ("eq_%d.png" % n[0])
            larg_cm, _ = renderiza_equacao_modelo(n[0], png)
            return "\n\n" + MARK_EQ + str(png) + "|" + "%.2f" % larg_cm + MARK_EQ + "\n\n"
        corpo = re.sub(r"\\label\{[^}]*\}", "", m.group(1)).strip().rstrip(",") if False else re.sub(r"\\label\{[^}]*\}", "", m.group(1)).strip()
        return "\n\n$$" + corpo + "\\qquad\\qquad (" + str(n[0]) + ")$$\n\n"
    s = re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}", eq, s, flags=re.S)
    s = re.sub(r"\\ref\{([^}]*)\}", lambda m: mapa.get(m.group(1), "??"), s)
    return s, mapa


def figuras(s, imgdir, tmp):
    """Troca \\includegraphics por PNG (quando o arquivo existe) com a largura do LaTeX
    (fração da largura útil de 16 cm; 0,47 quando há duas figuras lado a lado) ou por um
    quadro de espaço reservado."""
    import pymupdf
    LARGURA = 16.0

    def bloco(m):
        txt = m.group(0)
        imgs = re.findall(r"\\includegraphics", txt)
        lado_a_lado = len(imgs) >= 2

        def f(mi):
            opc, arq = mi.group(1) or "", mi.group(2)
            fr = 0.47 if lado_a_lado else 1.0
            mw = re.search(r"width=([0-9.]*)\\(?:linewidth|textwidth)", opc)
            if mw and not lado_a_lado:
                fr = float(mw.group(1) or 1.0)
            origem = None
            if imgdir:
                nome = Path(arq)
                for cand in (nome.stem + ".png", nome.stem + ".jpg", nome.stem + ".jpeg", nome.name):
                    if (Path(imgdir) / cand).exists():
                        origem = Path(imgdir) / cand
                        break
            if origem is not None:
                if origem.suffix.lower() == ".pdf":
                    png = Path(tmp) / (origem.stem + ".png")
                    pymupdf.open(origem)[0].get_pixmap(dpi=220).save(png)
                    origem = png
                LARG_FIG.append(fr * LARGURA)
                return "\\includegraphics[width=%.2fcm]{%s}" % (fr * LARGURA, origem)
            return "\\textbf{[Inserir figura: " + Path(arq).name.replace("_", "\\_") + "]}"
        return re.sub(r"\\includegraphics(\[[^\]]*\])?\{([^}]*)\}", f, txt)
    return re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", bloco, s, flags=re.S)


def prepara_tex(tex, imgdir, tmp, trocas=()):
    global TITULO
    s = tex
    for velho, novo in trocas:
        if velho not in s:
            raise SystemExit("trecho não encontrado para --troca: " + velho[:80])
        s = s.replace(velho, novo)
    mt = re.search(r"pdftitle=\{([^}]*)\}", s)
    if mt and not TITULO:
        TITULO = mt.group(1).strip()
    # macros de nota/fonte das tabelas: versão simples, estilizada depois
    s = re.sub(r"\\newcommand\{\\tablenote\}\[1\]\{.*\}", r"\\newcommand{\\tablenote}[1]{\\par\\textit{Nota:} #1\\par}", s)
    s = re.sub(r"\\newcommand\{\\tablesource\}\[1\]\{.*\}", r"\\newcommand{\\tablesource}[1]{\\par\\textit{Fonte:} #1\\par}", s)
    ini = s.index("\\begin{document}")
    pre, corpo = s[:ini], s[ini:]
    corpo = limpa_formatacao(corpo)
    corpo = normaliza_tabelas(corpo)
    corpo, mapa = numera_e_resolve(corpo, tmp)
    corpo = figuras(corpo, imgdir, tmp)
    # \setcounter / \thetable já foram usados na numeração
    corpo = re.sub(r"\\setcounter\{table\}\{0\}", "", corpo)
    corpo = re.sub(r"\\renewcommand\{\\thetable\}\{[A-Z]\.\\arabic\{table\}\}", "", corpo)
    corpo = re.sub(r"\\addcontentsline\{[^}]*\}\{[^}]*\}\{[^}]*\}", "", corpo)
    corpo = corpo.replace("\\appendix", "")
    return pre + corpo, mapa


# ───────────────────────────── estilos e pós-processamento ─────────────────────────────
def fonte(style, nome=FONTE, tam=12, negrito=None, italico=None, cor=RGBColor(0, 0, 0)):
    f = style.font
    f.name, f.size = nome, Pt(tam)
    if negrito is not None:
        f.bold = negrito
    if italico is not None:
        f.italic = italico
    f.color.rgb = cor
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in list(rf.attrib):
        if "Theme" in a:
            del rf.attrib[a]
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), nome)


def paragrafo(style, alinh=WD_ALIGN_PARAGRAPH.JUSTIFY, linha=None, antes=0, depois=6, recuo=0, junto=False):
    pf = style.paragraph_format
    pf.alignment, pf.line_spacing = alinh, (LINHA if linha is None else linha)
    pf.space_before, pf.space_after = Pt(antes), Pt(depois)
    pf.first_line_indent = Cm(recuo)
    pf.keep_with_next = junto


def referencia_docx(caminho):
    base = subprocess.run([pypandoc.get_pandoc_path(), "--print-default-data-file", "reference.docx"],
                          capture_output=True).stdout
    Path(caminho).write_bytes(base)
    d = Document(caminho)
    st = d.styles
    def pega(n):
        return next((x for x in st if x.name == n), None)
    for n in ("Normal", "Body Text", "First Paragraph"):
        s = pega(n)
        if s is not None:
            fonte(s); paragrafo(s, recuo=1.25 if n != "Normal" else 0)
    for n, tam, caps in (("Heading 1", 12, True), ("Heading 2", 12, False), ("Heading 3", 12, False)):
        s = pega(n)
        if s is not None:
            fonte(s, tam=tam, negrito=True, italico=(n == "Heading 3"))
            s.font.all_caps = caps
            paragrafo(s, alinh=WD_ALIGN_PARAGRAPH.LEFT, antes=12, depois=6, junto=True)
    for n in ("Table Caption", "Image Caption", "Caption"):
        s = pega(n)
        if s is not None:
            fonte(s, tam=10, negrito=False, italico=False)
            paragrafo(s, alinh=WD_ALIGN_PARAGRAPH.LEFT, linha=1.0, antes=12, depois=4, junto=(n == "Table Caption"))
    s = pega("Compact")
    if s is not None:
        fonte(s, tam=10); paragrafo(s, alinh=WD_ALIGN_PARAGRAPH.LEFT, linha=1.0, depois=0)
    # idioma
    dd = d.styles.element.find(qn("w:docDefaults"))
    if dd is not None:
        rpr = dd.find(qn("w:rPrDefault") + "/" + qn("w:rPr"))
        if rpr is not None:
            lang = rpr.find(qn("w:lang"))
            if lang is None:
                lang = OxmlElement("w:lang"); rpr.append(lang)
            lang.set(qn("w:val"), "pt-BR")
    d.save(caminho)


ORDEM_TBLPR = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc",
               "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription"]
ORDEM_TCPR = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar", "textDirection",
              "tcFitText", "vAlign", "hideMark"]


def insere(pai, elem, ordem):
    """Insere elem em pai respeitando a ordem do esquema (o Word é rígido quanto a isso)."""
    nome = elem.tag.split("}")[1]
    for antigo in pai.findall(elem.tag):
        pai.remove(antigo)
    pos = ordem.index(nome)
    for filho in pai:
        n = filho.tag.split("}")[1]
        if n in ordem and ordem.index(n) > pos:
            filho.addprevious(elem)
            return elem
    pai.append(elem)
    return elem


def borda(elem_pr, tag, **lados):
    b = OxmlElement(tag)
    for lado in ("top", "left", "bottom", "right"):      # ordem do esquema
        if lado in lados:
            v, sz = lados[lado]
            e = OxmlElement("w:" + lado)
            e.set(qn("w:val"), v); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")
            b.append(e)
    insere(elem_pr, b, ORDEM_TBLPR if tag == "w:tblBorders" else ORDEM_TCPR)



def texto_celula(tc):
    """Texto da célula com espaço entre parágrafos e quebras de linha (inclui matemática)."""
    partes = []
    for p in tc.iter(qn("w:p")):
        for e in p.iter():
            if e.tag in (qn("w:t"), qn("m:t")):
                partes.append(e.text or "")
            elif e.tag == qn("w:br"):
                partes.append(" ")
        partes.append(" ")
    return "".join(partes)


def larguras_fixas(t, total_cm):
    """Layout fixo: largura de cada coluna proporcional ao conteúdo (maior palavra
    e comprimento típico), para que números e cabeçalhos não quebrem no meio."""
    tbl = t._tbl
    grid = tbl.find(qn("w:tblGrid"))
    n = len(grid.findall(qn("w:gridCol")))
    peso = [0.0] * n
    for tr in tbl.findall(qn("w:tr")):
        col = 0
        for tc in tr.findall(qn("w:tc")):
            gs = tc.find(qn("w:tcPr") + "/" + qn("w:gridSpan"))
            span = int(gs.get(qn("w:val"))) if gs is not None else 1
            txt = texto_celula(tc).replace(MARK_RC, "")
            if span == 1 and col < n:
                palavras = txt.split() or [""]
                peso[col] = max(peso[col], max(len(w) for w in palavras) + 1.5, min(len(txt), 40) * 0.5)
            col += span
    peso = [max(p, 4.0) for p in peso]
    tot = sum(peso)
    cm = [total_cm * p / tot for p in peso]
    tw = int(total_cm * 567)
    pr = tbl.tblPr
    w = OxmlElement("w:tblW"); w.set(qn("w:type"), "dxa"); w.set(qn("w:w"), str(tw)); insere(pr, w, ORDEM_TBLPR)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); insere(pr, lay, ORDEM_TBLPR)
    for gc, c in zip(grid.findall(qn("w:gridCol")), cm):
        gc.set(qn("w:w"), str(int(c * 567)))
    for tr in tbl.findall(qn("w:tr")):
        col = 0
        for tc in tr.findall(qn("w:tc")):
            tcpr = tc.get_or_add_tcPr()
            gs = tcpr.find(qn("w:gridSpan"))
            span = int(gs.get(qn("w:val"))) if gs is not None else 1
            tcw = OxmlElement("w:tcW")
            tcw.set(qn("w:type"), "dxa"); tcw.set(qn("w:w"), str(int(sum(cm[col:col + span]) * 567)))
            insere(tcpr, tcw, ORDEM_TCPR)
            col += span


def formata_tabela(t, paisagem=False):
    ncols = len(t.columns)
    tam = 9 if ncols <= 5 else (8 if ncols <= 8 else (7.5 if paisagem else 7))
    tbl = t._tbl
    pr = tbl.tblPr
    borda(pr, "w:tblBorders", top=("single", 12), bottom=("single", 12))
    w = OxmlElement("w:tblW"); w.set(qn("w:type"), "pct"); w.set(qn("w:w"), "5000")
    insere(pr, w, ORDEM_TBLPR)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "autofit")
    insere(pr, lay, ORDEM_TBLPR)
    mar = OxmlElement("w:tblCellMar")
    for lado in ("left", "right"):
        e = OxmlElement("w:" + lado); e.set(qn("w:w"), "60"); e.set(qn("w:type"), "dxa"); mar.append(e)
    insere(pr, mar, ORDEM_TBLPR)
    for ri, row in enumerate(t.rows):
        rc = any(MARK_RC in c.text for c in row.cells[:1])
        for cell in row.cells:
            tcpr = cell._tc.get_or_add_tcPr()
            if ri == 0:
                borda(tcpr, "w:tcBorders", top=("single", 12), bottom=("single", 6))
            for p in cell.paragraphs:
                pf = p.paragraph_format
                pf.line_spacing, pf.space_before, pf.space_after, pf.first_line_indent = 1.0, Pt(1), Pt(1), Cm(0)
                for r in p.runs:
                    r.font.size = Pt(tam); r.font.name = FONTE
                    if MARK_RC in r.text:
                        r.text = r.text.replace(MARK_RC, "")
                    if ri == 0:
                        r.font.bold = True
                if ri == 0:
                    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER if cell is not row.cells[0] else WD_ALIGN_PARAGRAPH.LEFT
            if rc:
                sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), "E7E6E6")
                insere(tcpr, sh, ORDEM_TCPR)
        trpr = row._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit"); trpr.append(cs)
        if ri == 0:
            th = OxmlElement("w:tblHeader"); trpr.append(th)


def rodape(secao):
    secao.footer.is_linked_to_previous = False
    p = secao.footer.paragraphs[0] if secao.footer.paragraphs else secao.footer.add_paragraph()
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    run.font.name, run.font.size = FONTE, Pt(10)
    for tipo, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if tipo:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tipo); run._r.append(e)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; run._r.append(e)


def pagina(secao, paisagem=False):
    secao.page_width, secao.page_height = (Cm(29.7), Cm(21.0)) if paisagem else (Cm(21.0), Cm(29.7))
    secao.orientation = WD_ORIENT.LANDSCAPE if paisagem else WD_ORIENT.PORTRAIT
    secao.top_margin, secao.left_margin = Cm(3), Cm(3)
    secao.bottom_margin, secao.right_margin = Cm(2), Cm(2)
    secao.footer_distance = Cm(1.0)


def novo_par_antes(ref, texto="", estilo=None):
    p = OxmlElement("w:p")
    ref._p.addprevious(p)
    from docx.text.paragraph import Paragraph
    par = Paragraph(p, ref._parent)
    if estilo:
        par.style = estilo
    if texto:
        par.add_run(texto)
    return par


def p_fmt(par, alinh, negrito=False, tam=12, antes=0, depois=6, linha=None, cor=None, italico=False, caps=False):
    par.paragraph_format.alignment = alinh
    par.paragraph_format.first_line_indent = Cm(0)
    par.paragraph_format.line_spacing = LINHA if linha is None else linha
    par.paragraph_format.space_before, par.paragraph_format.space_after = Pt(antes), Pt(depois)
    for r in par.runs:
        r.font.name, r.font.size, r.font.bold, r.font.italic = FONTE, Pt(tam), negrito, italico
        r.font.all_caps = caps
        if cor:
            r.font.color.rgb = cor



def desfaz_tabelas_de_figura(d):
    """O Pandoc põe cada figura com suas notas numa tabela de uma linha. Aqui a
    figura vira parágrafo centralizado; legenda e depois Nota/Fonte, em parágrafos."""
    body = d.element.body
    for tbl in list(body.findall(qn("w:tbl"))):
        linhas = tbl.findall(qn("w:tr"))
        if len(linhas) != 1:
            continue
        cels = linhas[0].findall(qn("w:tc"))
        def txt(c):
            return "".join(t.text or "" for t in c.iter(qn("w:t")))
        eh_fig = [("[Inserir figura" in txt(c)) or (c.find(".//" + qn("w:drawing")) is not None) for c in cels]
        if not any(eh_fig):
            continue
        alvo = None
        for c, f in zip(cels, eh_fig):
            if f:
                for par in c.findall(qn("w:p")):
                    if alvo is None:
                        tbl.addprevious(par)
                        alvo = par
                        pp = Paragraph(par, d._body)
                        pp.paragraph_format.keep_with_next = True
                        pp.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    else:                                  # figura lado a lado: mesmas linhas do primeiro parágrafo
                        sp = OxmlElement("w:r"); t = OxmlElement("w:t"); t.text = "  "; t.set(qn("xml:space"), "preserve"); sp.append(t)
                        alvo.append(sp)
                        for r in par.findall(qn("w:r")):
                            alvo.append(r)
        legenda = tbl.getnext()
        ancora = legenda if legenda is not None else tbl
        notas = [par for c, f in zip(cels, eh_fig) if not f for par in c.findall(qn("w:p"))]
        for par in reversed(notas):
            ancora.addnext(par)
        tbl.getparent().remove(tbl)


def ajusta_figuras(d):
    """O Pandoc reduz a figura à largura da célula em que a colocou; devolve a largura do LaTeX."""
    from docx.shared import Emu
    alvo = iter(LARG_FIG)
    for dr in d.element.body.iter(qn("w:drawing")):
        ext = dr.find(".//" + qn("wp:extent"))
        if ext is None:
            continue
        try:
            larg = next(alvo)
        except StopIteration:
            break
        cx, cy = int(ext.get("cx")), int(ext.get("cy"))
        ncx = int(Cm(larg)); ncy = int(ncx * cy / cx)
        ext.set("cx", str(ncx)); ext.set("cy", str(ncy))
        for e in dr.iter(qn("a:ext")):
            if e.get("cx") is not None:
                e.set("cx", str(ncx)); e.set("cy", str(ncy))


def insere_equacoes_imagem(d):
    for p in d.paragraphs:
        t = p.text.strip()
        if t.startswith(MARK_EQ) and t.endswith(MARK_EQ):
            caminho, larg = t[len(MARK_EQ):-len(MARK_EQ)].split("|")
            for r in list(p.runs):
                r._r.getparent().remove(r._r)
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(6), Pt(6)
            p.paragraph_format.keep_together = True
            p.add_run().add_picture(caminho, width=Cm(float(larg)))


def sinal_menos(d):
    """Hífen antes de número negativo vira sinal de menos (U+2212), sem alterar intervalos."""
    pad = re.compile(r"(?<![\w.,])-(?=\d)")
    corpos = [d.element.body]
    for sec in d.sections:
        corpos.append(sec.footer._element)
    for corpo in corpos:
        for t in corpo.iter(qn("w:t")):
            if t.text and "-" in t.text:
                t.text = pad.sub("\u2212", t.text)


def pos_processa(docx_in, docx_out):
    d = Document(docx_in)
    desfaz_tabelas_de_figura(d)
    ajusta_figuras(d)
    insere_equacoes_imagem(d)
    cinza = RGBColor(0x59, 0x59, 0x59)
    sec = d.sections[0]
    pagina(sec); rodape(sec)
    corpo = d.paragraphs
    primeiro = corpo[0]

    # 1. espaço reservado: título, resumo, abstract e palavras-chave
    blocos = [
        ((TITULO or "[INSERIR TÍTULO DO TRABALHO]"), WD_ALIGN_PARAGRAPH.CENTER, True, 14, 0, 18, not TITULO),
        ("RESUMO", WD_ALIGN_PARAGRAPH.LEFT, True, 12, 6, 6, False),
        ("[Inserir resumo: de 150 a 500 palavras, em parágrafo único, conforme a ABNT NBR 6028. Não identificar autoria.]",
         WD_ALIGN_PARAGRAPH.JUSTIFY, False, 12, 0, 6, True),
        ("Palavras-chave: [inserir de 3 a 5 palavras-chave, separadas por ponto e vírgula].", WD_ALIGN_PARAGRAPH.LEFT, False, 12, 6, 14, True),
        ("ABSTRACT", WD_ALIGN_PARAGRAPH.LEFT, True, 12, 6, 6, False),
        ("[Insert abstract in English, consistent with the Portuguese resumo.]", WD_ALIGN_PARAGRAPH.JUSTIFY, False, 12, 0, 6, True),
        ("Keywords: [insert 3 to 5 keywords, separated by semicolons].", WD_ALIGN_PARAGRAPH.LEFT, False, 12, 6, 14, True),
    ]
    if ABERTURA:
        A = ABERTURA
        J, L, C = WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER
        blocos = [(A["titulo"], C, True, 14, 0, 6, False)]
        if A.get("subtitulo"):
            blocos.append((A["subtitulo"], C, True, 12, 0, 18, False))
        blocos += [("RESUMO", L, True, 12, 6, 6, False), (A["resumo"], J, False, 12, 0, 6, False),
                   ("Palavras-chave: " + A["palavras"], L, False, 12, 6, 14, False),
                   ("ABSTRACT", L, True, 12, 6, 6, False), (A["abstract"], J, False, 12, 0, 6, False),
                   ("Keywords: " + A["keywords"], L, False, 12, 6, 14, False)]
    for texto, alinh, neg, tam, antes, depois, cinza_ in blocos:
        par = novo_par_antes(primeiro, texto)
        p_fmt(par, alinh, negrito=neg, tam=tam, antes=antes, depois=depois, cor=cinza if cinza_ else None,
              italico=cinza_, linha=(1.0 if ABERTURA and alinh == WD_ALIGN_PARAGRAPH.JUSTIFY else None))
        for rot in ("Palavras-chave:", "Keywords:"):
            if ABERTURA and texto.startswith(rot):
                par.runs[0].text = texto[len(rot):]
                r = par.runs[0]._r.addprevious  # insere o rótulo em negrito antes do texto
                nr = OxmlElement("w:r"); par.runs[0]._r.addprevious(nr)
                from docx.text.run import Run
                rr = Run(nr, par); rr.text = rot; rr.font.bold = True; rr.font.name = FONTE; rr.font.size = Pt(tam)
    # quebra de página após o bloco de abertura
    primeiro.paragraph_format.page_break_before = False

    # 2. estilos de nota/fonte, marcadores de paisagem e quebra antes dos anexos
    anexo_ini = None
    for p in d.paragraphs:
        t = p.text.strip()
        if t.startswith(("Nota:", "Fonte:")) and len(p.runs) >= 1:
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(10) if t.startswith("Fonte:") else Pt(0)
            for r in p.runs:
                r.font.size, r.font.name = Pt(9), FONTE
        if p.style.name.startswith("Heading 1") and t.lower().startswith("anexo"):
            p.paragraph_format.page_break_before = True
            if anexo_ini is None:
                anexo_ini = p
        if "[Inserir figura:" in t:
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            for r in p.runs:
                r.font.size, r.font.color.rgb = Pt(10), cinza

    # 3. Referências: se o texto já traz a seção, formata as entradas (ABNT NBR 6023: alinhadas à
    #    esquerda, espaço simples, separadas por uma linha); senão, deixa espaço reservado.
    ref_h = next((p for p in d.paragraphs if p.style.name.startswith("Heading 1") and p.text.strip().lower().endswith("referências")), None)
    if ref_h is not None:
        el = ref_h._p.getnext()
        while el is not None and el.tag == qn("w:p"):
            par = Paragraph(el, ref_h._parent)
            if par.style.name.startswith("Heading"):
                break
            pf = par.paragraph_format
            pf.alignment, pf.line_spacing, pf.first_line_indent = WD_ALIGN_PARAGRAPH.LEFT, 1.0, Cm(0)
            pf.space_before, pf.space_after = Pt(0), Pt(8)
            for r in par.runs:
                r.font.size, r.font.name = Pt(11), FONTE
            el = el.getnext()
    elif anexo_ini is not None:
        h = novo_par_antes(anexo_ini, "REFERÊNCIAS", "Heading 1")
        h.paragraph_format.page_break_before = False
        ph = novo_par_antes(anexo_ini, "[Inserir as referências citadas no texto, em ordem alfabética, conforme a ABNT NBR 6023.]")
        p_fmt(ph, WD_ALIGN_PARAGRAPH.LEFT, tam=12, cor=cinza, italico=True)

    # 4. seção paisagem: entre os marcadores
    from copy import deepcopy
    ls = le = None
    for p in d.paragraphs:
        if p.text.strip() == MARK_LS:
            ls = p
        if p.text.strip() == MARK_LE:
            le = p
    body_sect = d.element.body.find(qn("w:sectPr"))
    if ls is not None and le is not None:
        for par, paisagem in ((ls, False), (le, True)):
            for r in list(par.runs):
                r._r.getparent().remove(r._r)
            sp = deepcopy(body_sect)
            ppr = par._p.get_or_add_pPr()
            ppr.append(sp)
            sz = sp.find(qn("w:pgSz"))
            if paisagem:
                sz.set(qn("w:w"), "16838"); sz.set(qn("w:h"), "11906"); sz.set(qn("w:orient"), "landscape")
            par.paragraph_format.space_after = Pt(0)
    else:
        for par in (ls, le):
            if par is not None:
                par._p.getparent().remove(par._p)

    # 5. tabelas
    # paisagem: tabela cujo "parágrafo final de seção" é paisagem => identifica pelo número de colunas (>=11)
    for t in d.tables:
        pais = TEM_PAISAGEM and len(t.columns) >= 11
        formata_tabela(t, paisagem=pais)
        larguras_fixas(t, 24.7 if pais else 16.0)

    # 6. metadados sem autoria
    cp = d.core_properties
    cp.author = cp.last_modified_by = cp.comments = cp.keywords = cp.subject = cp.category = ""
    cp.title = ""
    sinal_menos(d)
    d.save(docx_out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tex"); ap.add_argument("saida")
    ap.add_argument("--imgdir", default=None)
    ap.add_argument("--troca", nargs=2, action="append", default=[], metavar=("VELHO", "NOVO"),
                    help="substitui um trecho do .tex antes da conversão (pode repetir)")
    ap.add_argument("--equacao-editavel", action="store_true",
                    help="mantém a equação com chaves como equação do Word (editável), em vez de imagem")
    ap.add_argument("--titulo", default=None, help="título do trabalho (padrão: pdftitle do LaTeX)")
    ap.add_argument("--abertura", default=None, help="JSON com titulo, subtitulo, resumo, palavras, abstract, keywords")
    ap.add_argument("--linha", type=float, default=1.5, help="entrelinhas do corpo (padrão 1,5, como no edital)")
    a = ap.parse_args()
    global LINHA, TITULO, EQ_IMAGEM, ABERTURA
    if a.abertura:
        import json
        ABERTURA = json.loads(Path(a.abertura).read_text(encoding="utf-8"))
    EQ_IMAGEM = not a.equacao_editavel
    LINHA = a.linha
    TITULO = a.titulo or ""
    with tempfile.TemporaryDirectory() as tmp:
        tex = Path(a.tex).read_text(encoding="utf-8")
        novo, mapa = prepara_tex(tex, a.imgdir, tmp, a.troca)
        (Path(tmp) / "x.tex").write_text(novo, encoding="utf-8")
        ref = Path(tmp) / "ref.docx"
        referencia_docx(ref)
        bruto = Path(tmp) / "bruto.docx"
        pypandoc.convert_file(str(Path(tmp) / "x.tex"), "docx", outputfile=str(bruto),
                              extra_args=["--number-sections", "--reference-doc", str(ref), "--wrap=none"])
        pos_processa(bruto, a.saida)
    print("ok", a.saida, "| referências resolvidas:", len(mapa))


if __name__ == "__main__":
    main()
