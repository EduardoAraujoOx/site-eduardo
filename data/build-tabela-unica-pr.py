#!/usr/bin/env python3
"""
Tabela única do artigo: receita per capita municipal do Paraná (ISS + cota-parte
do ICMS em 2025, substituídos pelo IBS depois) nos municípios de maior e menor
valor em 2025, com colunas 2025, 2029, 2033, 2050 e 2077, e medidas de
dispersão (razão máx./mín. e Gini) calculadas sobre todos os municípios elegíveis.

Reaproveita montar() de build-tabelas-artigo-pr.py (base final auditada, ISS com
correções do PIT/TCE-PR, R$ constantes de 2025, população fixa). 2029-2033 vêm
direto da base final auditada; 2050 e 2077 seguem a mesma fórmula de 2033 com
ibs-projecao-longo-prazo.json (Seguro-Receita: fatia de 2033 x fundo municipal
do PR no ano).

Uso: python3 build-tabela-unica-pr.py
"""
import csv, importlib.util, json, statistics
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("bt", HERE / "build-tabelas-artigo-pr.py")
bt = importlib.util.module_from_spec(spec); spec.loader.exec_module(bt)

ANOS = [2025, 2029, 2033, 2050, 2077]
N = 10
OUT = bt.OUT


def dma_rel(v):
    m = statistics.mean(v)
    return sum(abs(x - m) for x in v) / len(v) / m


def medidas(v):
    return {"Razão máx./mín.": (max(v) / min(v), 1), "Índice de Gini": (bt.gini(v), 3)}


def main():
    linhas, eleg = bt.montar()
    final, _, _, _, lp, seg = bt.carregar()
    soma_seg = sum(float(r["seguro_2033_final"]) for r in final.values())
    for l in linhas:
        r = final[l["codigo_ibge"]]
        rec = {2025: l["base_2025"], 2029: float(r["receita_2029_final"]),
               2033: float(r["receita_2033_final"])}
        cpt, dest = float(r["cpt_final_pct"]) / 100, float(r["destino_pct"]) / 100
        fatia = float(r["seguro_2033_final"]) / soma_seg
        for y in (2050, 2077):
            p = lp[y]
            fundo = seg[str(y)]["repasse_por_uf"]["PR"]["municipio"]
            rec[y] = ((1 - p["ca"]) * p["ibs_historico"] * cpt + p["ibs_destino_liquido"] * dest
                      + (1 - p["ca"]) * fatia * fundo)
        for y in ANOS:
            l[f"pc{y}"] = rec[y] / l["pop"]
    assert all(abs(l["pc2033"] - l["pc_2033"]) < 1e-6 and abs(l["pc2077"] - l["pc_2077"]) < 1e-6 for l in linhas)

    rank = sorted(eleg, key=lambda l: -l["pc2025"])
    ext = rank[:N] + rank[-N:]
    disp = {y: medidas([l[f"pc{y}"] for l in eleg]) for y in ANOS}
    json.dump({"n": len(eleg), "extremos": [{k: l[k] for k in ["municipio", "pop"] + [f"pc{y}" for y in ANOS]} for l in ext],
               "dispersao": {str(y): {k: v[0] for k, v in d.items()} for y, d in disp.items()}},
              open(OUT / "resumo-tabela-unica.json", "w"), ensure_ascii=False, indent=1)
    with open(OUT / "municipios-percapita-pr-anos.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        ids = {l["codigo_ibge"] for l in eleg}
        w.writerow(["codigo_ibge", "municipio", "pop_media"] + [f"receita_pc_{y}" for y in ANOS] + ["elegivel"])
        for l in sorted(linhas, key=lambda l: -l["pc2025"]):
            w.writerow([l["codigo_ibge"], l["municipio"], round(l["pop"], 1)] + [round(l[f"pc{y}"], 2) for y in ANOS]
                       + [l["codigo_ibge"] in ids])
    gerar_docx(ext, disp, len(eleg))
    return ext, disp, len(eleg)


def gerar_docx(ext, disp, n_eleg):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, Cm
    br = bt._br
    doc = Document()
    s = doc.sections[0]; s.left_margin = s.right_margin = Cm(2.2)
    doc.styles["Normal"].font.name = "Times New Roman"; doc.styles["Normal"].font.size = Pt(11)

    def par(t, bold=False, italic=False, size=None, after=4):
        p = doc.add_paragraph(); r = p.add_run(t); r.bold, r.italic = bold, italic
        if size: r.font.size = Pt(size)
        p.paragraph_format.space_after = Pt(after)

    def borda(c, **kw):
        b = OxmlElement("w:tcBorders")
        for lado, v in kw.items():
            e = OxmlElement(f"w:{lado}"); e.set(qn("w:val"), v); e.set(qn("w:sz"), "6"); b.append(e)
        c._tc.get_or_add_tcPr().append(b)

    par("Tabela 1 – Receita per capita de ISS e cota-parte do ICMS (2025) e do IBS municipal (2029-2077): "
        "municípios paranaenses de maior e menor valor em 2025 e medidas de dispersão (R$ de 2025)", bold=True, size=10)
    cab = ["Município", "População"] + [str(y) for y in ANOS]
    t = doc.add_table(rows=1, cols=len(cab)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    def linha(vals, bold=False, sep=None, ultima=False):
        cells = t.add_row().cells if vals is not cab else t.rows[0].cells
        for i, v in enumerate(vals):
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(9); r.bold = bold
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT if i else WD_ALIGN_PARAGRAPH.LEFT
            cells[i].paragraphs[0].paragraph_format.space_after = Pt(0)
            if sep: borda(cells[i], **sep)
    linha(cab, bold=True, sep=dict(top="single", bottom="single"))
    for i, l in enumerate(ext):
        rk = i + 1 if i < N else n_eleg - 2 * N + i + 1
        linha([f"{rk}. {l['municipio']}", br(l["pop"])] + [br(l[f"pc{y}"]) for y in ANOS],
              sep=dict(bottom="dashed") if i == N - 1 else None)
    nomes = list(disp[2025].keys())
    c = t.add_row().cells; m = c[0].merge(c[-1]); m.text = ""
    r = m.paragraphs[0].add_run(f"Medidas de dispersão – {n_eleg} municípios com dados auditados"); r.bold = True; r.font.size = Pt(9)
    m.paragraphs[0].paragraph_format.space_after = Pt(0); borda(m, top="single")
    for k, nome in enumerate(nomes):
        casas = disp[2025][nome][1]
        linha([nome, ""] + [br(disp[y][nome][0], casas) for y in ANOS],
              sep=dict(bottom="single") if k == len(nomes) - 1 else None)
    for row in t.rows:
        for i, w in enumerate([5.2, 2.0] + [1.9] * len(ANOS)):
            row.cells[i].width = Cm(w)
    par("", after=2)
    par("Fonte: elaboração própria, com base na DCA/Siconfi, Portal da Transparência do PR e PIT/TCE-PR (base municipal final auditada). "
        "Receita per capita = ISS + cota-parte do ICMS em 2025, substituídos pelo IBS municipal de 2029 em diante, conforme o cronograma "
        "do art. 131 do ADCT (EC 132/2023) e PIB real de 2,2% a.a. após 2033. Valores em R$ constantes de 2025; população fixa (média "
        "2019-2026). Razão máx./mín. = maior valor per capita dividido pelo menor; o Índice de Gini (0 = igualdade perfeita) "
        "considera todos os municípios elegíveis, e não só os exibidos.", italic=True, size=8)
    doc.save(OUT / "tabela-unica-dispersao-percapita-pr.docx")


if __name__ == "__main__":
    ext, disp, n = main()
    for i, l in enumerate(ext): print(f"{l['municipio']:<24}", *[f"{l[f'pc{y}']:>8.0f}" for y in ANOS])
    for k in disp[2025]: print(f"{k:<36}", *[f"{disp[y][k][0]:>9.3f}" for y in ANOS])
    print(n)
