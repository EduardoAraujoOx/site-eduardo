#!/usr/bin/env python3
"""
Gera, a partir dos JSON do site (data/*.json), as tabelas, a figura e os números
citados no texto da Nota Técnica sobre o impacto da transição ICMS -> IBS no
Espírito Santo (nota-tecnica-impacto-es.tex).

Saídas, todas em tabelas/ (incluídas pelo .tex com \\input):
  numeros.tex          macros \\Num... usadas no texto (nenhum número do texto é digitado à mão)
  tab-trajetoria.tex   Tabela 2: receita do ente estadual capixaba com e sem reforma, 2029-2033
  tab-decomposicao.tex Tabela 3: decomposição da diferença, em pontos percentuais do contrafactual
  tab-metodos.tex      Tabela 4: sensibilidade ao método de estimação do coeficiente de destino
  figura-ranking.tex   Figura 1: variação em 2033, 27 UFs (pgfplots)
  anexo-a.tex          Anexo A: ente estadual, todas as UFs, 2029-2033
  anexo-b.tex          Anexo B: coeficientes de participação e variação consolidada (estado + municípios)

Uso:  python3 gerar-tabelas.py
Para atualizar a nota quando os dados mudarem: rodar este script e recompilar o .tex.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent.parent / "data"
OUT = HERE / "tabelas"
OUT.mkdir(exist_ok=True)

UF_ALVO = "ES"
ANOS = ["2029", "2030", "2031", "2032", "2033"]
BI = 1e9


def load(nome):
    with open(DATA / nome, encoding="utf-8") as f:
        return json.load(f)


res = load("resultados-consolidados-ibs.json")
painel = load("painel-estados.json")
faixa = load("faixa-phi-dest-estados.json")
nac = {str(r["ano"]): r for r in load("ibs-projecao-nacional.json")["projecao"]}
lp = {str(r["ano"]): r for r in load("ibs-projecao-longo-prazo.json")["projecao"]}
coefs = {e["uf"]: e for e in res["anexo_a"]["estados"]}
est = res["por_uf_estado"]
tot = res["por_uf"]


# ---------------------------------------------------------------- formatação pt-BR
def num(x, d=1, sinal=False):
    """Número no padrão brasileiro; sinal negativo em modo matemático, para não quebrar linha."""
    s = f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if round(x, d) < 0:
        return "$-$" + s
    if sinal and round(x, d) > 0:
        return "$+$" + s
    return s


def pct(x, d=1, sinal=False):
    return num(x, d, sinal) + "\\%"


def nome_tex(s):
    return s.replace("&", "\\&")


def macro(nome, valor):
    return f"\\newcommand{{\\{nome}}}{{{valor}}}\n"


# ---------------------------------------------------------------- números do Espírito Santo
e = est[UF_ALVO]
pos = {a: e["pos_por_ano"][a] / BI for a in ANOS}
cf = {a: e["contrafactual_por_ano"][a] / BI for a in ANOS}
var = {a: e["variacao_por_ano"][a] * 100 for a in ANOS}
dif = {a: pos[a] - cf[a] for a in ANOS}
pre = e["pre_2025"] / BI
dif_acum = sum(dif.values())
var_acum = e["acumulado_dpct"] * 100
assert abs(var_acum - dif_acum / sum(cf.values()) * 100) < 1e-6

rank_2033 = sorted(est, key=lambda u: est[u]["variacao_por_ano"]["2033"])
pos_rank = rank_2033.index(UF_ALVO) + 1
rank_acum = sorted(est, key=lambda u: est[u]["acumulado_dpct"]).index(UF_ALVO) + 1
n_perdem_2033 = sum(1 for u in est if est[u]["variacao_por_ano"]["2033"] < 0)

cresc_real_pos = (pos["2033"] / pre - 1) * 100
cresc_real_cf = (cf["2033"] / pre - 1) * 100
queda_2033_vs_2032 = (pos["2033"] / pos["2032"] - 1) * 100

cn = coefs[UF_ALVO]["coef_neutro_icms_pct"]
cc = coefs[UF_ALVO]["coef_cpt_pct"]
cp = coefs[UF_ALVO]["coef_pleno_pct"]

# decomposição exata (mesma fórmula de project_uf em build-resultados-consolidados.py):
#   total = residual*phi_n + (1-ca)*hist*phi_c + dest_liq*phi_p + (1-ca)*repasse
#   contrafactual = (residual + ibs_bruto)*phi_n
# O repasse do Seguro-Receita ao ente estadual é conferido abaixo (zero para o ES).
rep_estado = painel["estados"][UF_ALVO]["repasse_seguro_receita_por_ano"]["estado"]
rep_mun_2033 = painel["estados"][UF_ALVO]["repasse_seguro_receita_por_ano"]["municipio"]["2033"] / 1e6
decomp = {}
for a in ANOS:
    n = nac[a]
    ref = n["icms_iss_residual"] + n["ibs_bruto"]
    ca = n["ca"]
    neutro_ded = (n["icms_iss_residual"] + (1 - ca) * n["ibs_historico"] + n["ibs_destino_liquido"]) / ref
    d_ded = (neutro_ded - 1) * 100
    d_cpt = (1 - ca) * n["ibs_historico"] / ref * (cc / cn - 1) * 100
    d_dest = n["ibs_destino_liquido"] / ref * (cp / cn - 1) * 100
    d_rep = (1 - ca) * rep_estado[a] / (ref * cn / 100) * 100
    total = d_ded + d_cpt + d_dest + d_rep
    assert abs(total - var[a]) < 1e-6, (a, total, var[a])
    decomp[a] = (d_ded, d_cpt, d_dest, d_rep, total)

# projeção de longo prazo (2077), mesma fórmula, extrapolação
v77 = next(x for x in res["anexo_a"]["validacao_receita_estados"] if x["uf"] == UF_ALVO)
cf77 = lp["2077"]["bolo_projetado"] * cn / 100
var77 = (v77["total_2077_autonomo"] / cf77 - 1) * 100

# faixa de métodos
fm = faixa["por_uf"][UF_ALVO]["metodos"]
ordem_metodos = ["phi_robusto", "pof_censo_ponderado", "pof_censo_bruto", "gobetti_2023"]
rotulos = {
    "phi_robusto": "Composto de três rotas (adotado)",
    "pof_censo_ponderado": "POF/Censo, ponderado por tributabilidade",
    "pof_censo_bruto": "POF/Censo, consumo bruto",
    "gobetti_2023": "Gobetti e Monteiro (2023)",
}
v_min = min(fm[m]["variacao_por_ano"]["2033"] for m in ordem_metodos)
v_max = max(fm[m]["variacao_por_ano"]["2033"] for m in ordem_metodos)
assert abs(fm["phi_robusto"]["variacao_por_ano"]["2033"] - var["2033"]) < 1e-4

# simulação preliminar publicada em nota técnica elaborada para o Comsefaz (v3, ago/2026), Tabela 12
comsefaz = None
ref_md = DATA / "referencias-externas" / "NT_COMSEFAZ_RefTributaria_v3.md"
if ref_md.exists():
    linhas = ref_md.read_text(encoding="utf-8").splitlines()
    def le_linha(prefixo):
        for ln in linhas:
            if ln.startswith(f"| {prefixo} | 16.943.675") or (prefixo == "Total" and ln.startswith("| Total | 1.026.616.761")):
                return [float(c.strip().replace(".", "")) for c in ln.strip("|").split("|")[1:7]]
        return None
    l_es, l_tot = le_linha("Espírito Santo"), le_linha("Total")
    if l_es and l_tot:
        share = l_es[0] / l_tot[0]
        comsefaz = {a: (l_es[i + 1] / (share * l_tot[i + 1]) - 1) * 100 for i, a in enumerate(ANOS)}

# ---------------------------------------------------------------- numeros.tex
m = []
m.append("% Gerado por gerar-tabelas.py -- não editar à mão.\n")
m.append(macro("NumRecPre", num(pre, 2)))
for a, nome in zip(ANOS, ["Um", "Dois", "Tres", "Quatro", "Cinco"]):
    m.append(macro(f"NumPos{nome}", num(pos[a], 2)))
    m.append(macro(f"NumCf{nome}", num(cf[a], 2)))
    m.append(macro(f"NumDif{nome}", num(abs(dif[a]), 2)))
    m.append(macro(f"NumVar{nome}", num(abs(var[a]), 2)))
m.append(macro("NumVarFinalUma", num(abs(var["2033"]), 1)))
m.append(macro("NumDifFinalMil", num(abs(dif["2033"]), 2)))
m.append(macro("NumDifAcum", num(abs(dif_acum), 2)))
m.append(macro("NumVarAcum", num(abs(var_acum), 1)))
m.append(macro("NumCrescPos", num(cresc_real_pos, 1)))
m.append(macro("NumCrescCf", num(cresc_real_cf, 1)))
m.append(macro("NumQueda", num(abs(queda_2033_vs_2032), 1)))
m.append(macro("NumRank", str(pos_rank)))
m.append(macro("NumRankAcum", str(rank_acum)))
m.append(macro("NumPerdem", str(n_perdem_2033)))
m.append(macro("NumCoefN", num(cn, 3)))
m.append(macro("NumCoefC", num(cc, 3)))
m.append(macro("NumCoefP", num(cp, 3)))
m.append(macro("NumCoefCRel", num(abs((cc / cn - 1) * 100), 1)))
m.append(macro("NumCoefPRel", num(abs((cp / cn - 1) * 100), 1)))
m.append(macro("NumDecDed", num(abs(decomp["2033"][0]), 1)))
m.append(macro("NumDecCpt", num(abs(decomp["2033"][1]), 1)))
m.append(macro("NumDecDest", num(abs(decomp["2033"][2]), 1)))
m.append(macro("NumVarMin", num(abs(v_min), 1)))
m.append(macro("NumVarMax", num(abs(v_max), 1)))
m.append(macro("NumAmplitude", num(abs(v_min - v_max), 1)))
m.append(macro("NumGobettiVar", num(abs(fm["gobetti_2023"]["variacao_por_ano"]["2033"]), 1)))
m.append(macro("NumRepMun", num(rep_mun_2033, 1)))
m.append(macro("NumVarSetentaSete", num(abs(var77), 1)))
m.append(macro("NumRecSetentaSete", num(v77["total_2077_autonomo"] / BI, 1)))
m.append(macro("NumCfSetentaSete", num(cf77 / BI, 1)))
ufu = tot[UF_ALVO]
m.append(macro("NumTotVar", num(abs(ufu["variacao_por_ano"]["2033"] * 100), 1)))
m.append(macro("NumTotAcum", num(abs(ufu["acumulado_dpct"] * 100), 1)))
m.append(macro("NumTotPos", num(ufu["pos_por_ano"]["2033"] / BI, 1)))
m.append(macro("NumTotPre", num(ufu["pre_2025"] / BI, 1)))
if comsefaz:
    m.append(macro("NumComsefaz", num(abs(comsefaz["2033"]), 1)))
# agregado dos entes estaduais e posição do ES frente à média dos Estados
pos_ag = sum(v["pos_por_ano"]["2033"] for v in est.values())
cf_ag = sum(v["contrafactual_por_ano"]["2033"] for v in est.values())
var_ag = (pos_ag / cf_ag - 1) * 100
vs_media = ((1 + est[UF_ALVO]["variacao_por_ano"]["2033"]) / (pos_ag / cf_ag) - 1) * 100
pos_uf_ag = sum(v["pos_por_ano"]["2033"] for v in tot.values())
cf_uf_ag = sum(v["contrafactual_por_ano"]["2033"] for v in tot.values())
var_uf_ag = (pos_uf_ag / cf_uf_ag - 1) * 100
soma_n = sum(c["coef_neutro_icms_pct"] for c in coefs.values())
soma_c = sum(c["coef_cpt_pct"] for c in coefs.values())
m.append(macro("NumAgEst", num(var_ag, 1)))
m.append(macro("NumVsMedia", num(abs(vs_media), 1)))
m.append(macro("NumAgUF", num(abs(var_uf_ag), 1)))
m.append(macro("NumSomaN", num(soma_n, 1)))
m.append(macro("NumSomaC", num(soma_c, 1)))
# bolo nacional 2033 e estaduais
m.append(macro("NumBoloNac", num(nac["2033"]["ibs_bruto"] / 1e12, 2)))
# piores e melhores 2033
piores = rank_2033[:3]
melhores = rank_2033[-1]
m.append(macro("NumPrimeiroNome", nome_tex(est[piores[0]]["nome"])))
m.append(macro("NumPrimeiroVar", num(abs(est[piores[0]]["variacao_por_ano"]["2033"] * 100), 1)))
m.append(macro("NumSegundoNome", nome_tex(est[piores[1]]["nome"])))
m.append(macro("NumSegundoVar", num(abs(est[piores[1]]["variacao_por_ano"]["2033"] * 100), 1)))
m.append(macro("NumMelhorNome", nome_tex(est[melhores]["nome"])))
m.append(macro("NumMelhorVar", num(est[melhores]["variacao_por_ano"]["2033"] * 100, 1)))
(OUT / "numeros.tex").write_text("".join(m), encoding="utf-8")

# ---------------------------------------------------------------- Tabela 2: trajetória
L = []
L.append("\\begin{tabular}{@{}l*{4}{>{\\raggedleft\\arraybackslash}p{2.55cm}}@{}}\n\\toprule\n")
L.append("\\rowcolor{azul}\\cabecalhoL{Ano} & \\cabecalho{Sem reforma\\\\(R\\$ bi)} & \\cabecalho{Com reforma\\\\(R\\$ bi)} & "
         "\\cabecalho{Diferença\\\\(R\\$ bi)} & \\cabecalho{Variação\\\\(\\%)} \\\\\n\\midrule\n")
L.append(f"2025 (base, pré-IBS) & {num(pre, 2)} & {num(pre, 2)} & --- & --- \\\\\n")
for i, a in enumerate(ANOS):
    cor = "\\rowcolor{zebra}" if i % 2 == 0 else ""
    L.append(f"{cor}{a} & {num(cf[a], 2)} & {num(pos[a], 2)} & {num(dif[a], 2, True)} & {num(var[a], 2, True)} \\\\\n")
L.append("\\midrule\n")
L.append(f"\\rowcolor{{azulfundo}}\\textbf{{Acumulado 2029--2033}} & {num(sum(cf.values()), 2)} & {num(sum(pos.values()), 2)} & "
         f"\\textbf{{{num(dif_acum, 2, True)}}} & \\textbf{{{num(var_acum, 2, True)}}} \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "tab-trajetoria.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela 3: decomposição
L = []
L.append("\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{5.9cm}*{5}{>{\\raggedleft\\arraybackslash}p{1.45cm}}@{}}\n\\toprule\n")
L.append("\\rowcolor{azul}\\cabecalhoL{Componente} & " + " & ".join(f"\\cabecalho{{{a}}}" for a in ANOS) + " \\\\\n\\midrule\n")
linhas = [
    ("Deduções do CGIBS e do Seguro-Receita", 0),
    ("Coeficiente histórico (CPT) abaixo do neutro", 1),
    ("Coeficiente de destino abaixo do neutro", 2),
    ("Repasse do Seguro-Receita ao Estado", 3),
]
for i, (rot, k) in enumerate(linhas):
    cor = "\\rowcolor{zebra}" if i % 2 == 0 else ""
    L.append(f"{cor}{rot} & " + " & ".join(num(decomp[a][k], 2, True) for a in ANOS) + " \\\\\n")
L.append("\\midrule\n")
L.append("\\rowcolor{azulfundo}\\textbf{Variação total (p.p. do contrafactual)} & " +
         " & ".join(f"\\textbf{{{num(decomp[a][4], 2, True)}}}" for a in ANOS) + " \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "tab-decomposicao.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela 4: sensibilidade ao método
L = []
L.append("\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{5.6cm}>{\\raggedleft\\arraybackslash}p{1.45cm}*{5}{>{\\raggedleft\\arraybackslash}p{1.15cm}}@{}}\n\\toprule\n")
L.append("\\rowcolor{azul}\\cabecalhoL{Método do coeficiente de destino} & \\cabecalho{$\\varphi^{dest}$ (\\%)} & " +
         " & ".join(f"\\cabecalho{{{a}}}" for a in ANOS) + " \\\\\n\\midrule\n")
for i, k in enumerate(ordem_metodos):
    cor = "\\rowcolor{azulfundo}" if k == "phi_robusto" else ("\\rowcolor{zebra}" if i % 2 == 0 else "")
    L.append(f"{cor}{rotulos[k]} & {num(fm[k]['coef_pleno_estado_pct'], 3)} & " +
             " & ".join(num(fm[k]["variacao_por_ano"][a], 2, True) for a in ANOS) + " \\\\\n")
if comsefaz:
    L.append("\\midrule\n")
    L.append("Simulação preliminar elaborada para o Comsefaz\\textsuperscript{a} & --- & " +
             " & ".join(num(comsefaz[a], 2, True) for a in ANOS) + " \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "tab-metodos.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Figura 1: ranking 2033
vals = [(u, est[u]["variacao_por_ano"]["2033"] * 100) for u in est]
vals.sort(key=lambda t: t[1])
coords = [u for u, _ in vals][::-1]  # pgfplots desenha de baixo para cima; a pior UF fica no topo
F = []
F.append("\\begin{tikzpicture}\n\\begin{axis}[\n"
         "  xbar, width=\\linewidth, height=10.2cm, bar width=4.6pt,\n"
         "  symbolic y coords={" + ",".join(coords) + "}, ytick={" + ",".join(coords) + "}, y tick label style={font=\\scriptsize},\n"
         "  x tick label style={font=\\scriptsize}, xlabel={Variação da receita do ente estadual em 2033 (\\%)},\n"
         "  xlabel style={font=\\footnotesize}, xmin=-12, xmax=11, enlarge y limits=0.025,\n"
         "  xmajorgrids, grid style={gray!25}, axis x line*=bottom, axis y line*=left, axis line style={gray!60}, tick style={gray!60},\n"
         "  nodes near coords={\\pgfmathprintnumber[fixed,fixed zerofill,precision=1,use comma]{\\pgfplotspointmeta}},\n"
         "  nodes near coords align={horizontal}, every node near coord/.append style={font=\\tiny, text=black!70},\n"
         "]\n")
outras = " ".join(f"({v:.4f},{u})" for u, v in vals if u != UF_ALVO)
F.append(f"\\addplot[fill=azulclaro, draw=none] coordinates {{{outras}}};\n")
v_es = est[UF_ALVO]["variacao_por_ano"]["2033"] * 100
F.append(f"\\addplot[fill=azul, draw=none] coordinates {{({v_es:.4f},{UF_ALVO})}};\n")
F.append("\\end{axis}\n\\end{tikzpicture}\n")
(OUT / "figura-ranking.tex").write_text("".join(F), encoding="utf-8")

# ---------------------------------------------------------------- Anexo A
ordem_a = sorted(est, key=lambda u: est[u]["variacao_por_ano"]["2033"])
L = []
L.append("\\begin{longtable}{@{}>{\\raggedright\\arraybackslash}p{3.0cm}>{\\raggedleft\\arraybackslash}p{1.15cm}>{\\raggedleft\\arraybackslash}p{1.15cm}"
         "*{5}{>{\\raggedleft\\arraybackslash}p{1.0cm}}>{\\raggedleft\\arraybackslash}p{1.25cm}>{\\raggedleft\\arraybackslash}p{1.35cm}@{}}\n")
cab = ("\\rowcolor{azul}\\cabecalhoL{Unidade da\\\\Federação} & \\cabecalho{Pré-IBS\\\\2025} & \\cabecalho{Com\\\\reforma\\\\2033} & "
       "\\cabecalho{2029} & \\cabecalho{2030} & \\cabecalho{2031} & \\cabecalho{2032} & \\cabecalho{2033} & "
       "\\cabecalho{Acum.\\\\2029--33} & \\cabecalho{Dif. acum.\\\\(R\\$ bi)} \\\\\n")
L.append("\\toprule\n" + cab + "\\midrule\n\\endfirsthead\n")
L.append("\\toprule\n" + cab + "\\midrule\n\\endhead\n")
L.append("\\bottomrule\n\\endfoot\n")
soma = {"pre": 0.0, "pos33": 0.0, "dif": 0.0, "cf": 0.0}
somas_ano = {a: [0.0, 0.0] for a in ANOS}
for i, u in enumerate(ordem_a):
    v = est[u]
    dif_u = sum(v["pos_por_ano"][a] - v["contrafactual_por_ano"][a] for a in ANOS) / BI
    soma["pre"] += v["pre_2025"] / BI
    soma["pos33"] += v["pos_por_ano"]["2033"] / BI
    soma["dif"] += dif_u
    soma["cf"] += sum(v["contrafactual_por_ano"][a] for a in ANOS) / BI
    for a in ANOS:
        somas_ano[a][0] += v["pos_por_ano"][a]
        somas_ano[a][1] += v["contrafactual_por_ano"][a]
    destaque = u == UF_ALVO
    cor = "\\rowcolor{destaque}" if destaque else ("\\rowcolor{zebra}" if i % 2 == 0 else "")
    negr = (lambda s: f"\\textbf{{{s}}}") if destaque else (lambda s: s)
    L.append(cor + negr(nome_tex(v["nome"])) + " & " + negr(num(v["pre_2025"] / BI, 2)) + " & " +
             negr(num(v["pos_por_ano"]["2033"] / BI, 2)) + " & " +
             " & ".join(negr(num(v["variacao_por_ano"][a] * 100, 1, True)) for a in ANOS) + " & " +
             negr(num(v["acumulado_dpct"] * 100, 1, True)) + " & " + negr(num(dif_u, 2, True)) + " \\\\\n")
L.append("\\midrule\n")
L.append("\\rowcolor{azulfundo}\\textbf{Total dos entes estaduais} & " + f"\\textbf{{{num(soma['pre'], 1)}}} & \\textbf{{{num(soma['pos33'], 1)}}} & " +
         " & ".join(f"\\textbf{{{num((somas_ano[a][0] / somas_ano[a][1] - 1) * 100, 1, True)}}}" for a in ANOS) + " & " +
         f"\\textbf{{{num(soma['dif'] / soma['cf'] * 100, 1, True)}}} & \\textbf{{{num(soma['dif'], 2, True)}}} \\\\\n")
L.append("\\end{longtable}\n")
(OUT / "anexo-a.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Anexo B
L = []
L.append("\\begin{longtable}{@{}>{\\raggedright\\arraybackslash}p{3.0cm}*{3}{>{\\raggedleft\\arraybackslash}p{1.4cm}}"
         "*{2}{>{\\raggedleft\\arraybackslash}p{1.55cm}}*{2}{>{\\raggedleft\\arraybackslash}p{1.55cm}}@{}}\n")
cab = ("\\rowcolor{azul}\\cabecalhoL{Unidade da\\\\Federação} & \\cabecalho{$\\varphi^{neutro}$\\\\(\\%)} & \\cabecalho{$\\varphi^{CPT}$\\\\(\\%)} & "
       "\\cabecalho{$\\varphi^{dest}$\\\\(\\%)} & \\cabecalho{CPT vs.\\\\neutro\\\\(\\%)} & \\cabecalho{Destino\\\\vs. neutro\\\\(\\%)} & "
       "\\cabecalho{Estado\\\\2033\\\\(\\%)} & \\cabecalho{Estado e\\\\municípios\\\\2033 (\\%)} \\\\\n")
L.append("\\toprule\n" + cab + "\\midrule\n\\endfirsthead\n")
L.append("\\toprule\n" + cab + "\\midrule\n\\endhead\n")
L.append("\\bottomrule\n\\endfoot\n")
for i, u in enumerate(ordem_a):
    c = coefs[u]
    d_cpt = (c["coef_cpt_pct"] / c["coef_neutro_icms_pct"] - 1) * 100
    d_dest = (c["coef_pleno_pct"] / c["coef_neutro_icms_pct"] - 1) * 100
    destaque = u == UF_ALVO
    cor = "\\rowcolor{destaque}" if destaque else ("\\rowcolor{zebra}" if i % 2 == 0 else "")
    negr = (lambda s: f"\\textbf{{{s}}}") if destaque else (lambda s: s)
    L.append(cor + negr(nome_tex(est[u]["nome"])) + " & " + negr(num(c["coef_neutro_icms_pct"], 3)) + " & " +
             negr(num(c["coef_cpt_pct"], 3)) + " & " + negr(num(c["coef_pleno_pct"], 3)) + " & " +
             negr(num(d_cpt, 1, True)) + " & " + negr(num(d_dest, 1, True)) + " & " +
             negr(num(est[u]["variacao_por_ano"]["2033"] * 100, 1, True)) + " & " +
             negr(num(tot[u]["variacao_por_ano"]["2033"] * 100, 1, True)) + " \\\\\n")
L.append("\\end{longtable}\n")
(OUT / "anexo-b.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- resumo no terminal (conferência)
print(f"ES: pré-IBS 2025 R$ {pre:.2f} bi")
for a in ANOS:
    print(f"  {a}: sem {cf[a]:.2f}  com {pos[a]:.2f}  dif {dif[a]:+.2f}  var {var[a]:+.2f}%  decomp(ded,cpt,dest,rep,tot)=" +
          ",".join(f"{x:+.2f}" for x in decomp[a]))
print(f"  acumulado: R$ {dif_acum:+.2f} bi ({var_acum:+.2f}%)")
print(f"  posição entre as piores em 2033: {pos_rank}º de {len(est)}; no acumulado: {rank_acum}º; {n_perdem_2033} UFs perdem")
print(f"  crescimento real 2025-2033: com reforma {cresc_real_pos:+.1f}%, sem reforma {cresc_real_cf:+.1f}%; 2033 vs 2032: {queda_2033_vs_2032:+.1f}%")
print(f"  coef: neutro {cn:.4f} CPT {cc:.4f} destino {cp:.4f}")
print(f"  faixa de métodos em 2033: {v_min:.2f}% a {v_max:.2f}%")
print(f"  2077: {var77:+.1f}% (R$ {v77['total_2077_autonomo']/BI:.1f} bi vs {cf77/BI:.1f} bi)")
if comsefaz:
    print("  Comsefaz (prelim.):", {a: round(v, 2) for a, v in comsefaz.items()})
print(f"  agregado estados 2033: {var_ag:+.2f}%; ES vs média: {vs_media:+.2f}%; agregado UF: {var_uf_ag:+.2f}%; soma CPT {soma_c:.2f} vs neutro {soma_n:.2f}")
print(f"  total UF (estado+mun.) 2033: {ufu['variacao_por_ano']['2033']*100:+.2f}%, acum {ufu['acumulado_dpct']*100:+.2f}%")
print("  repasse SR ao Estado:", rep_estado, "| aos municípios 2033: R$ %.1f mi" % rep_mun_2033)
