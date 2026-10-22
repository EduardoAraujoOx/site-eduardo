#!/usr/bin/env python3
"""
Gera, a partir dos JSON do site (data/*.json), as tabelas, o gráfico e os números
citados no texto da Nota Técnica sobre o impacto da transição ICMS -> IBS no
Espírito Santo (nota-tecnica-impacto-es.tex). Notação do artigo do Paraná:
A_t, f_t, s_t, lambda_t, rho_t, c_t, w_i^0, w_i^H, w_i^D, S_it, G_it, R^R_it, R^C_it.

Saídas, todas em tabelas/ (incluídas pelo .tex com \\input):
  numeros.tex           macros \\Num... usadas no texto (nenhum número do texto é digitado à mão)
  tab-parametros.tex    Tabela 1: parâmetros das duas transições
  tab-trajetoria.tex    Tabela 2: receita do ente estadual com e sem reforma, 2029-2033
  tab-decomposicao.tex  Tabela 3: decomposição da diferença, em pontos percentuais de R^C
  tab-metodos.tex       Tabela 4: sensibilidade ao método do coeficiente de destino
  figura-ranking.tex    Gráfico 1: variação em 2033, 27 UFs (pgfplots)
  anexo-a1.tex          Tabela A.1: ente estadual, todas as UFs, 2029-2033
  anexo-a2.tex          Tabela A.2: coeficientes e variação consolidada (estado + municípios)
  anexo-b-memoria.tex   Tabela B.2: memória de cálculo da receita do ES em 2033
  anexo-b-anobase.tex   Tabela B.3: sensibilidade ao ano-base do cenário sem reforma

Uso:  python3 gerar-tabelas.py
Para atualizar a nota quando os dados mudarem: rodar este script e recompilar o .tex.
"""
import json
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
sens = load("sensibilidade-uf.json")
phi_pof = load("phi-dest-pof-censo.json")
phi_rob = load("phi-dest-robusto.json")
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


def en(x, d=1):
    return f"{x:,.{d}f}"


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

w0 = coefs[UF_ALVO]["coef_neutro_icms_pct"] / 100
wH = coefs[UF_ALVO]["coef_cpt_pct"] / 100
wD = coefs[UF_ALVO]["coef_pleno_pct"] / 100
qH, qD = wH / w0, wD / w0

# decomposição exata (mesma fórmula de project_uf em build-resultados-consolidados.py):
#   R^R = A[f w0 + s(1-c)(lambda wH + (1-lambda)(1-rho) wD)] + (1-c) S ;  R^C = A w0
# O repasse do Seguro-Receita ao ente estadual é conferido abaixo (zero para o ES).
RHO = 0.05
rep_estado = painel["estados"][UF_ALVO]["repasse_seguro_receita_por_ano"]["estado"]
rep_mun_2033 = painel["estados"][UF_ALVO]["repasse_seguro_receita_por_ano"]["municipio"]["2033"] / 1e6
decomp = {}
for a in ANOS:
    n = nac[a]
    f_t, s_t, lam, c_t = n["fa"], n["sa"], n["alpha_a"], n["ca"]
    assert abs(n["ibs_destino_liquido"] - n["ibs_bruto"] * (1 - lam) * (1 - RHO) * (1 - c_t)) < 1e3
    k = lam + (1 - lam) * (1 - RHO)
    d_ded = -s_t * (1 - (1 - c_t) * k) * 100
    d_h = s_t * (1 - c_t) * lam * (qH - 1) * 100
    d_d = s_t * (1 - c_t) * (1 - lam) * (1 - RHO) * (qD - 1) * 100
    d_s = (1 - c_t) * rep_estado[a] / (n["bolo_projetado"] * w0) * 100
    total = d_ded + d_h + d_d + d_s
    assert abs(total - var[a]) < 1e-6, (a, total, var[a])
    decomp[a] = (d_ded, d_h, d_d, d_s, total)

# projeção de longo prazo (2077): mesma fórmula, extrapolação
v77 = next(x for x in res["anexo_a"]["validacao_receita_estados"] if x["uf"] == UF_ALVO)
cf77 = lp["2077"]["bolo_projetado"] * w0
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

# sensibilidade ao ano-base do cenário sem reforma e ao coeficiente de destino (como a Tabela A.6 do artigo do Paraná)
ref_es = sens["por_uf"][UF_ALVO]["ref"]
incert = sens["por_uf"][UF_ALVO]["incerteza_rel"]
n33 = nac["2033"]
A33 = n33["bolo_projetado"]
lam33, c33 = n33["alpha_a"], n33["ca"]


def var_2033(w_base, delta_destino=0.0):
    r = A33 * n33["sa"] * (1 - c33) * (lam33 * wH + (1 - lam33) * (1 - RHO) * wD * (1 + delta_destino))
    return (r / (A33 * w_base) - 1) * 100


bases = [
    ("2025 (ano-base adotado)", w0),
    ("2026 (estimado)", ref_es["2026"]),
    ("Média de 2019 a 2026", wH),
    ("2019", ref_es["2019"]),
]
assert abs(var_2033(w0) - var["2033"]) < 1e-6
assert abs(ref_es["2025"] - w0) < 1e-6

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

# coeficiente de destino do ES: rotas, composto e passagem à esfera estadual
pes = phi_rob["por_uf"][UF_ALVO]
pdes = phi_pof["por_uf"][UF_ALVO]
theta_E = phi_pof["compras_governamentais"]["theta_estadual"] * 100
frac_est = phi_pof["frac_estado_pct"]
assert abs(pdes["coef_estado_compras_pct"] / 100 - wD) < 1e-9

# ---------------------------------------------------------------- numeros.tex
ufu = tot[UF_ALVO]
piores = rank_2033[:3]
melhor = rank_2033[-1]
nomes_ano = dict(zip(ANOS, ["Um", "Dois", "Tres", "Quatro", "Cinco"]))
m = ["% Gerado por gerar-tabelas.py -- não editar à mão.\n"]
m.append(macro("NumRecPre", num(pre, 2)))
for a, nome in nomes_ano.items():
    m.append(macro(f"NumPos{nome}", num(pos[a], 2)))
    m.append(macro(f"NumCf{nome}", num(cf[a], 2)))
    m.append(macro(f"NumDif{nome}", num(abs(dif[a]), 2)))
    m.append(macro(f"NumVar{nome}", num(abs(var[a]), 2)))
m += [
    macro("NumVarFinalUma", num(abs(var["2033"]), 1)),
    macro("NumDifAcum", num(abs(dif_acum), 2)),
    macro("NumVarAcum", num(abs(var_acum), 1)),
    macro("NumCrescPos", num(cresc_real_pos, 1)),
    macro("NumCrescCf", num(cresc_real_cf, 1)),
    macro("NumQueda", num(abs(queda_2033_vs_2032), 1)),
    macro("NumRank", str(pos_rank)),
    macro("NumRankAcum", str(rank_acum)),
    macro("NumPerdem", str(n_perdem_2033)),
    macro("NumCoefN", num(w0 * 100, 3)),
    macro("NumCoefC", num(wH * 100, 3)),
    macro("NumCoefP", num(wD * 100, 3)),
    macro("NumCoefCRel", num(abs((qH - 1) * 100), 1)),
    macro("NumCoefPRel", num(abs((qD - 1) * 100), 1)),
    macro("NumDecDed", num(abs(decomp["2033"][0]), 1)),
    macro("NumDecCpt", num(abs(decomp["2033"][1]), 1)),
    macro("NumDecDest", num(abs(decomp["2033"][2]), 1)),
    macro("NumVarMin", num(abs(v_min), 1)),
    macro("NumVarMax", num(abs(v_max), 1)),
    macro("NumAmplitude", num(abs(v_min - v_max), 1)),
    macro("NumRepMun", num(rep_mun_2033, 1)),
    macro("NumVarSetentaSete", num(abs(var77), 1)),
    macro("NumRecSetentaSete", num(v77["total_2077_autonomo"] / BI, 1)),
    macro("NumCfSetentaSete", num(cf77 / BI, 1)),
    macro("NumTotVar", num(abs(ufu["variacao_por_ano"]["2033"] * 100), 1)),
    macro("NumTotAcum", num(abs(ufu["acumulado_dpct"] * 100), 1)),
    macro("NumBoloNac", num(n33["ibs_bruto"] / 1e12, 2)),
    macro("NumBoloNacBi", num(A33 / BI, 2)),
    macro("NumPrimeiroNome", nome_tex(est[piores[0]]["nome"])),
    macro("NumPrimeiroVar", num(abs(est[piores[0]]["variacao_por_ano"]["2033"] * 100), 1)),
    macro("NumSegundoNome", nome_tex(est[piores[1]]["nome"])),
    macro("NumSegundoVar", num(abs(est[piores[1]]["variacao_por_ano"]["2033"] * 100), 1)),
    macro("NumMelhorNome", nome_tex(est[melhor]["nome"])),
    macro("NumMelhorVar", num(est[melhor]["variacao_por_ano"]["2033"] * 100, 1)),
    macro("NumAgEst", num(var_ag, 1)),
    macro("NumVsMedia", num(abs(vs_media), 1)),
    macro("NumAgUF", num(abs(var_uf_ag), 1)),
    macro("NumSomaN", num(soma_n, 1)),
    macro("NumSomaC", num(soma_c, 1)),
    macro("NumParticipDezenove", num(ref_es["2019"] * 100, 2)),
    macro("NumParticipVinteCinco", num(ref_es["2025"] * 100, 2)),
    macro("NumRotaA", num(pes["rota_A_pct"], 2)),
    macro("NumRotaB", num(pes["rota_B_pct"], 2)),
    macro("NumRotaC", num(pes["rota_C_pct"], 2)),
    macro("NumComposto", num(pes["phi_robusto_pct"], 3)),
    macro("NumIncert", num(pes["incerteza_rel"] * 100, 1)),
    macro("NumFracEst", num(frac_est, 2)),
    macro("NumThetaE", num(theta_E, 1)),
    macro("NumPhiEstCompras", num(pdes["phi_estado_compras_pct"], 3)),
    macro("NumBaseMedia", num(var_2033(wH), 1)),
    macro("NumBaseDois", num(var_2033(ref_es["2026"]), 1)),
    macro("NumBaseDezenove", num(var_2033(ref_es["2019"]), 1)),
    # versões em inglês (resumo)
    macro("EnPos", en(pos["2033"], 2)),
    macro("EnVar", en(abs(var["2033"]), 1)),
    macro("EnDifAcum", en(abs(dif_acum), 2)),
    macro("EnDecCpt", en(abs(decomp["2033"][1]), 1)),
]
if comsefaz:
    m.append(macro("NumComsefaz", num(abs(comsefaz["2033"]), 1)))
(OUT / "numeros.tex").write_text("".join(m), encoding="utf-8")

# ---------------------------------------------------------------- Tabela 1: parâmetros das duas transições
L = ["\\begin{tabular}{@{}l*{7}{r}@{}}\n\\toprule\n"]
L.append("\\cabecalhoL{Ano} & \\cabecalho{ICMS/ISS\\\\reman.\\\\$f_t$} & \\cabecalho{Base em\\\\IBS\\\\$s_t$} & "
         "\\cabecalho{Histórico\\\\no IBS\\\\$\\lambda_t$} & \\cabecalho{Histórico\\\\sobre $A_t$} & "
         "\\cabecalho{Seguro-\\\\Receita\\\\sobre $A_t$} & \\cabecalho{Destino\\\\sobre $A_t$} & \\cabecalho{Limite\\\\CGIBS\\\\$c_t$} \\\\\n\\midrule\n")


def p(x, d=0):
    return num(x * 100, d) + "\\%"


for a in ANOS:
    n = nac[a]
    s_t, lam = n["sa"], n["alpha_a"]
    L.append(f"{a} & {p(n['fa'])} & {p(s_t)} & {p(lam)} & {p(s_t * lam, 2)} & {p(s_t * (1 - lam) * RHO, 2)} & "
             f"{p(s_t * (1 - lam) * (1 - RHO), 2)} & {p(n['ca'], 2)} \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "tab-parametros.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela 2: trajetória
L = ["\\begin{tabular}{@{}lrrrr@{}}\n\\toprule\n"]
L.append("\\cabecalhoL{Ano} & \\cabecalho{Sem reforma\\\\$R^{C}_{it}$} & \\cabecalho{Com reforma\\\\$R^{R}_{it}$} & "
         "\\cabecalho{Diferença\\\\(R\\$ bi)} & \\cabecalho{Variação\\\\$\\Delta_{it}$ (\\%)} \\\\\n\\midrule\n")
L.append(f"2025 (base, pré-IBS) & {num(pre, 2)} & {num(pre, 2)} & --- & --- \\\\\n")
for a in ANOS:
    L.append(f"{a} & {num(cf[a], 2)} & {num(pos[a], 2)} & {num(dif[a], 2, True)} & {num(var[a], 2, True)} \\\\\n")
L.append("\\midrule\n")
L.append(f"\\textbf{{Acumulado 2029--2033}} & {num(sum(cf.values()), 2)} & {num(sum(pos.values()), 2)} & "
         f"\\textbf{{{num(dif_acum, 2, True)}}} & \\textbf{{{num(var_acum, 2, True)}}} \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "tab-trajetoria.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela 3: decomposição
L = ["\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{6.1cm}*{5}{r}@{}}\n\\toprule\n"]
L.append("\\cabecalhoL{Componente} & " + " & ".join(f"\\cabecalho{{{a}}}" for a in ANOS) + " \\\\\n\\midrule\n")
linhas = [
    ("Deduções do Seguro-Receita e do CGIBS", 0),
    ("Coeficiente histórico abaixo da participação de 2025 ($q^{H}_{i}<1$)", 1),
    ("Coeficiente de destino abaixo da participação de 2025 ($q^{D}_{i}<1$)", 2),
    ("Repasse do Seguro-Receita ao Estado", 3),
]
for rot, k in linhas:
    L.append(f"{rot} & " + " & ".join(num(decomp[a][k], 2, True) for a in ANOS) + " \\\\\n")
L.append("\\midrule\n")
L.append("\\textbf{Variação total $\\Delta_{it}$ (p.p. de $R^{C}_{it}$)} & " +
         " & ".join(f"\\textbf{{{num(decomp[a][4], 2, True)}}}" for a in ANOS) + " \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "tab-decomposicao.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela 4: sensibilidade ao método
L = ["\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{5.4cm}r*{5}{r}@{}}\n\\toprule\n"]
L.append("\\cabecalhoL{Método do coeficiente de destino} & \\cabecalho{$w^{D}_{i}$\\\\(\\%)} & " +
         " & ".join(f"\\cabecalho{{{a}}}" for a in ANOS) + " \\\\\n\\midrule\n")
for k in ordem_metodos:
    b = "\\textbf" if k == "phi_robusto" else ""
    cel = lambda s: f"\\textbf{{{s}}}" if k == "phi_robusto" else s
    L.append(f"{cel(rotulos[k])} & {cel(num(fm[k]['coef_pleno_estado_pct'], 3))} & " +
             " & ".join(cel(num(fm[k]["variacao_por_ano"][a], 2, True)) for a in ANOS) + " \\\\\n")
if comsefaz:
    L.append("\\midrule\n")
    L.append("Simulação preliminar elaborada para o Comsefaz\\textsuperscript{a} & --- & " +
             " & ".join(num(comsefaz[a], 2, True) for a in ANOS) + " \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "tab-metodos.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Gráfico 1: ranking 2033
vals = sorted(((u, est[u]["variacao_por_ano"]["2033"] * 100) for u in est), key=lambda t: t[1])
coords = [u for u, _ in vals][::-1]  # pgfplots desenha de baixo para cima; a pior UF fica no topo
F = ["\\begin{tikzpicture}\n\\begin{axis}[\n"
     "  xbar, width=\\linewidth, height=10.4cm, bar width=4.6pt,\n"
     "  symbolic y coords={" + ",".join(coords) + "}, ytick={" + ",".join(coords) + "}, y tick label style={font=\\scriptsize},\n"
     "  x tick label style={font=\\scriptsize}, xlabel={Variação da receita do ente estadual em 2033 (\\%)},\n"
     "  xlabel style={font=\\footnotesize}, xmin=-12, xmax=11, enlarge y limits=0.025,\n"
     "  xmajorgrids, grid style={gray!25}, axis x line*=bottom, axis y line*=left, axis line style={gray!60}, tick style={gray!60},\n"
     "  nodes near coords={\\pgfmathprintnumber[fixed,fixed zerofill,precision=1,use comma]{\\pgfplotspointmeta}},\n"
     "  nodes near coords align={horizontal}, every node near coord/.append style={font=\\tiny, text=black!70},\n"
     "]\n"]
outras = " ".join(f"({v:.4f},{u})" for u, v in vals if u != UF_ALVO)
F.append(f"\\addplot[fill=azulclaro, draw=none] coordinates {{{outras}}};\n")
F.append(f"\\addplot[fill=azul, draw=none] coordinates {{({est[UF_ALVO]['variacao_por_ano']['2033'] * 100:.4f},{UF_ALVO})}};\n")
F.append("\\end{axis}\n\\end{tikzpicture}\n")
(OUT / "figura-ranking.tex").write_text("".join(F), encoding="utf-8")

# ---------------------------------------------------------------- Tabela A.1 e A.2 (anexo A)
ordem_a = sorted(est, key=lambda u: est[u]["variacao_por_ano"]["2033"])
CS = "\\rowcolor{black!10}"
L = ["\\begin{longtable}{@{}>{\\raggedright\\arraybackslash}p{3.15cm}*{2}{r}*{5}{r}rr@{}}\n"]
cab = ("\\cabecalhoL{Unidade da\\\\Federação} & \\cabecalho{Pré-IBS\\\\2025} & \\cabecalho{Com\\\\reforma\\\\2033} & "
       "\\cabecalho{2029} & \\cabecalho{2030} & \\cabecalho{2031} & \\cabecalho{2032} & \\cabecalho{2033} & "
       "\\cabecalho{Acum.\\\\2029--33} & \\cabecalho{Dif. acum.\\\\(R\\$ bi)} \\\\\n")
L.append("\\toprule\n" + cab + "\\midrule\n\\endfirsthead\n")
L.append("\\toprule\n" + cab + "\\midrule\n\\endhead\n\\bottomrule\n\\endfoot\n")
soma = {"pre": 0.0, "pos33": 0.0, "dif": 0.0, "cf": 0.0}
somas_ano = {a: [0.0, 0.0] for a in ANOS}
for u in ordem_a:
    v = est[u]
    dif_u = sum(v["pos_por_ano"][a] - v["contrafactual_por_ano"][a] for a in ANOS) / BI
    soma["pre"] += v["pre_2025"] / BI
    soma["pos33"] += v["pos_por_ano"]["2033"] / BI
    soma["dif"] += dif_u
    soma["cf"] += sum(v["contrafactual_por_ano"][a] for a in ANOS) / BI
    for a in ANOS:
        somas_ano[a][0] += v["pos_por_ano"][a]
        somas_ano[a][1] += v["contrafactual_por_ano"][a]
    d = u == UF_ALVO
    neg = (lambda s: f"\\textbf{{{s}}}") if d else (lambda s: s)
    L.append((CS if d else "") + neg(nome_tex(v["nome"])) + " & " + neg(num(v["pre_2025"] / BI, 2)) + " & " +
             neg(num(v["pos_por_ano"]["2033"] / BI, 2)) + " & " +
             " & ".join(neg(num(v["variacao_por_ano"][a] * 100, 1, True)) for a in ANOS) + " & " +
             neg(num(v["acumulado_dpct"] * 100, 1, True)) + " & " + neg(num(dif_u, 2, True)) + " \\\\\n")
L.append("\\midrule\n")
L.append("\\textbf{Total dos entes estaduais} & " + f"\\textbf{{{num(soma['pre'], 1)}}} & \\textbf{{{num(soma['pos33'], 1)}}} & " +
         " & ".join(f"\\textbf{{{num((somas_ano[a][0] / somas_ano[a][1] - 1) * 100, 1, True)}}}" for a in ANOS) + " & " +
         f"\\textbf{{{num(soma['dif'] / soma['cf'] * 100, 1, True)}}} & \\textbf{{{num(soma['dif'], 2, True)}}} \\\\\n")
L.append("\\end{longtable}\n\\addtocounter{table}{-1}\n")
(OUT / "anexo-a1.tex").write_text("".join(L), encoding="utf-8")

L = ["\\begin{longtable}{@{}>{\\raggedright\\arraybackslash}p{3.15cm}*{3}{r}rrrr@{}}\n"]
cab = ("\\cabecalhoL{Unidade da\\\\Federação} & \\cabecalho{$w^{0}_{i}$\\\\(\\%)} & \\cabecalho{$w^{H}_{i}$\\\\(\\%)} & "
       "\\cabecalho{$w^{D}_{i}$\\\\(\\%)} & \\cabecalho{$q^{H}_{i}-1$\\\\(\\%)} & \\cabecalho{$q^{D}_{i}-1$\\\\(\\%)} & "
       "\\cabecalho{Estado\\\\2033\\\\(\\%)} & \\cabecalho{Estado e\\\\municípios\\\\2033 (\\%)} \\\\\n")
L.append("\\toprule\n" + cab + "\\midrule\n\\endfirsthead\n")
L.append("\\toprule\n" + cab + "\\midrule\n\\endhead\n\\bottomrule\n\\endfoot\n")
for u in ordem_a:
    c = coefs[u]
    d_h = (c["coef_cpt_pct"] / c["coef_neutro_icms_pct"] - 1) * 100
    d_d = (c["coef_pleno_pct"] / c["coef_neutro_icms_pct"] - 1) * 100
    d = u == UF_ALVO
    neg = (lambda s: f"\\textbf{{{s}}}") if d else (lambda s: s)
    L.append((CS if d else "") + neg(nome_tex(est[u]["nome"])) + " & " + neg(num(c["coef_neutro_icms_pct"], 3)) + " & " +
             neg(num(c["coef_cpt_pct"], 3)) + " & " + neg(num(c["coef_pleno_pct"], 3)) + " & " +
             neg(num(d_h, 1, True)) + " & " + neg(num(d_d, 1, True)) + " & " +
             neg(num(est[u]["variacao_por_ano"]["2033"] * 100, 1, True)) + " & " +
             neg(num(tot[u]["variacao_por_ano"]["2033"] * 100, 1, True)) + " \\\\\n")
L.append("\\end{longtable}\n\\addtocounter{table}{-1}\n")
(OUT / "anexo-a2.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela B.2: memória de cálculo do ES em 2033
hist = A33 * n33["sa"] * lam33 * wH / BI
dest = A33 * n33["sa"] * (1 - lam33) * (1 - RHO) * wD / BI
sub = hist + dest
ded = c33 * sub
rec = sub - ded + 0.0
assert abs(rec - pos["2033"]) < 1e-3, (rec, pos["2033"])
rc = A33 * w0 / BI
assert abs(rc - cf["2033"]) < 1e-3
nm = lambda x, d: num(x, d).replace(",", "{,}")
a33 = num(A33 / BI, 2)
a33m = nm(A33 / BI, 2)
L = ["\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{3.0cm}>{\\raggedright\\arraybackslash}p{4.3cm}>{\\raggedright\\arraybackslash}p{4.9cm}r@{}}\n\\toprule\n"]
L.append("\\cabecalhoL{Item} & \\cabecalhoL{Expressão} & \\cabecalhoL{Substituição numérica} & \\cabecalho{Valor} \\\\\n\\midrule\n")
w4 = lambda x: num(x, 7).replace(".", "")  # coeficiente em fração decimal, ex.: 0,0166397
linhas_mem = [
    ("Base nacional de referência", "$A_{2033}$", "Valor projetado para 2033", f"R\\$ {a33} bi"),
    ("Participação de referência do Espírito Santo", "$w^{0}_{ES}$", "Receita estadual de 2025 dividida pela base nacional de 2025", num(w0 * 100, 5) + "\\%"),
    ("Coeficiente histórico", "$w^{H}_{ES}$", "Média de 2019 a 2026 (2026 estimado) dividida pela base nacional", num(wH * 100, 5) + "\\%"),
    ("Coeficiente estadual de destino", "$w^{D}_{ES}$", "Composto de três rotas (POF, Censo 2022 e PNAD Contínua) com compras governamentais", num(wD * 100, 5) + "\\%"),
    ("Parâmetros de 2033", "$f_t,\\,s_t,\\,\\lambda_t,\\,\\rho_t,\\,c_t$",
     f"$f=0$; $s=1$; $\\lambda={nm(lam33, 2)}$; $\\rho={nm(RHO, 2)}$; $c={nm(c33, 3)}$", "---"),
    ("Cenário sem reforma", "$A_{2033}\\,w^{0}_{ES}$", f"${a33m} \\times {nm(w0, 7)}$", f"R\\$ {num(rc, 2)} bi"),
    ("ICMS residual", "$A_{2033}f_{2033}w^{0}_{ES}$", f"${a33m} \\times 0 \\times {nm(w0, 7)}$", "R\\$ 0,00 bi"),
    ("IBS pelo histórico, bruto", "$A_{2033}s_{2033}\\lambda_{2033}w^{H}_{ES}$",
     f"${a33m} \\times 1 \\times {nm(lam33, 2)} \\times {nm(wH, 7)}$", f"R\\$ {num(hist, 2)} bi"),
    ("IBS pelo destino, após Seguro-Receita", "$A_{2033}s_{2033}(1-\\lambda_{2033})(1-\\rho_{2033})w^{D}_{ES}$",
     f"${a33m} \\times 1 \\times {nm(1 - lam33, 2)} \\times {nm(1 - RHO, 2)} \\times {nm(wD, 7)}$", f"R\\$ {num(dest, 2)} bi"),
    ("Subtotal do IBS antes do CGIBS", "soma dos componentes do IBS", f"${nm(hist, 2)} + {nm(dest, 2)}$", f"R\\$ {num(sub, 2)} bi"),
    ("Dedução para o CGIBS", "$G_{ES,2033}=c\\times\\text{subtotal}$", f"${nm(c33, 3)} \\times {nm(sub, 3)}$", f"R\\$ $-${num(ded, 2)} bi"),
    ("Seguro-Receita recebido", "$S_{ES,2033}$", "Governo estadual não elegível na simulação de 2033", "R\\$ 0,00 bi"),
    ("\\textbf{Receita com reforma}", "$R^{R}_{ES,2033}$", f"${nm(sub, 3)} - {nm(ded, 3)}$", f"\\textbf{{R\\$ {num(rec, 2)} bi}}"),
    ("\\textbf{Variação ante o cenário sem reforma}", "$R^{R}/R^{C}-1$", f"${nm(rec, 3)}/{nm(rc, 3)}-1$", f"\\textbf{{{num(var['2033'], 2, True)}\\%}}"),
]
for i, (a_, b_, c_, d_) in enumerate(linhas_mem):
    L.append(f"{a_} & {b_} & {c_} & {d_} \\\\\n")
    if i in (4, 6, 11):
        L.append("\\addlinespace[2pt]\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "anexo-b-memoria.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela B.3: sensibilidade ao ano-base
u_pct = incert * 100
L = ["\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{4.9cm}rrrr@{}}\n\\toprule\n"]
L.append(f"\\cabecalhoL{{Ano-base do cenário\\\\sem reforma}} & \\cabecalho{{Participação\\\\do Estado (\\%)}} & "
         f"\\cabecalho{{Destino\\\\$-${num(u_pct, 1)}\\%}} & \\cabecalho{{Destino\\\\central}} & \\cabecalho{{Destino\\\\$+${num(u_pct, 1)}\\%}} \\\\\n\\midrule\n")
for rot, wb in bases:
    L.append(f"{rot} & {num(wb * 100, 4)} & {num(var_2033(wb, -incert), 2, True)}\\% & {num(var_2033(wb), 2, True)}\\% & {num(var_2033(wb, incert), 2, True)}\\% \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "anexo-b-anobase.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- resumo no terminal (conferência)
print(f"ES: pré-IBS 2025 R$ {pre:.2f} bi")
for a in ANOS:
    print(f"  {a}: sem {cf[a]:.2f}  com {pos[a]:.2f}  dif {dif[a]:+.2f}  var {var[a]:+.2f}%  decomp(ded,H,D,S,tot)=" +
          ",".join(f"{x:+.2f}" for x in decomp[a]))
print(f"  acumulado: R$ {dif_acum:+.2f} bi ({var_acum:+.2f}%)")
print(f"  posição entre as piores em 2033: {pos_rank}º de {len(est)}; no acumulado: {rank_acum}º; {n_perdem_2033} UFs perdem")
print(f"  w0 {w0*100:.4f}  wH {wH*100:.4f}  wD {wD*100:.4f}  qH {qH:.4f}  qD {qD:.4f}")
print(f"  rotas A/B/C {pes['rota_A_pct']:.3f}/{pes['rota_B_pct']:.3f}/{pes['rota_C_pct']:.3f} composto {pes['phi_robusto_pct']:.3f} incerteza {pes['incerteza_rel']*100:.1f}%")
print(f"  faixa de métodos em 2033: {v_min:.2f}% a {v_max:.2f}%; 2077: {var77:+.1f}%")
print("  ano-base:", {r: (round(var_2033(wb, -incert), 2), round(var_2033(wb), 2), round(var_2033(wb, incert), 2)) for r, wb in bases})
print(f"  agregado estados 2033: {var_ag:+.2f}%; ES vs média: {vs_media:+.2f}%; agregado UF: {var_uf_ag:+.2f}%; soma wH {soma_c:.2f} vs w0 {soma_n:.2f}")
if comsefaz:
    print("  Comsefaz (prelim.):", {a: round(v, 2) for a, v in comsefaz.items()})
