#!/usr/bin/env python3
"""
Gera, a partir dos JSON do site (data/*.json), as tabelas, os gráficos e os números
citados no texto da Nota Técnica sobre o impacto da transição ICMS -> IBS no
Espírito Santo (nota-tecnica-impacto-es.tex). Notação do artigo do Paraná:
A_t, f_t, s_t, lambda_t, rho_t, c_t, w_i^0, w_i^H, w_i^D, S_it, G_it, R^R_it, R^C_it.

Saídas, todas em tabelas/ (incluídas pelo .tex com \\input):
  numeros.tex           macros \\Num... usadas no texto (nenhum número do texto é digitado à mão)
  tab-parametros.tex    Tabela 1: parâmetros das duas transições
  tab-trajetoria.tex    Tabela 2: receita do ente estadual com e sem reforma, 2029-2033
  tab-decomposicao.tex  Tabela 3: decomposição da diferença, em pontos percentuais de R^C
  tab-metodos.tex       Tabela 4: sensibilidade ao método do coeficiente de destino
  graf-participacao.tex Gráfico 1: participação anual do Estado e coeficiente histórico, 2019-2026
  graf-sensibilidade.tex Gráfico 2: (a) sensibilidade 2029-2033 e (b) extensão do cronograma até 2077
  graf-dispersao.tex    Gráfico 3: variação em 2033 contra a diferença relativa dos coeficientes, 27 UFs
  anexo-a1.tex          Tabela A.1: ente estadual, todas as UFs, 2029-2033
  anexo-a2.tex          Tabela A.2: coeficientes e variação consolidada (estado + municípios)
  anexo-a-memoria.tex   Tabela B.2: memória de cálculo da receita do ES em 2033
  anexo-a-anobase.tex   Tabela B.3: sensibilidade ao ano-base do cenário sem reforma

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
ANOS_EXT = ["2033", "2040", "2050", "2060", "2070", "2077"]
BI = 1e9
RHO = 0.05


def load(nome):
    with open(DATA / nome, encoding="utf-8") as f:
        return json.load(f)


res = load("resultados-consolidados-ibs.json")
painel = load("painel-estados.json")
faixa = load("faixa-phi-dest-estados.json")
sens = load("sensibilidade-uf.json")
phi_pof = load("phi-dest-pof-censo.json")
phi_rob = load("phi-dest-robusto.json")
seguro_lp = load("seguro-receita-repasses-longo-prazo.json")["anos"]
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


def nm(x, d=1):
    """Número dentro de modo matemático: a vírgula decimal precisa de {,} para não abrir espaço."""
    return num(x, d).replace(",", "{,}")


def tx(x, d=1):
    """Número em texto de eixo/rótulo de gráfico (sinal menos tipográfico)."""
    s = f"{abs(x):.{d}f}".replace(".", ",")
    return ("$-$" if round(x, d) < 0 else "") + s


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

# repasses do Seguro-Receita ao ente estadual: zero em 2029-2033; no longo prazo, ver abaixo
rep_estado = painel["estados"][UF_ALVO]["repasse_seguro_receita_por_ano"]["estado"]
rep_mun_2033 = painel["estados"][UF_ALVO]["repasse_seguro_receita_por_ano"]["municipio"]["2033"] / 1e6
comp_est = painel["estados"][UF_ALVO]["componentes_por_ano"]["estado"]["2033"]


def rep_longo(ano):
    v = seguro_lp[str(ano)]["repasse_por_uf"].get(UF_ALVO)
    return (v.get("estado") or 0) if isinstance(v, dict) else 0


# decomposição exata (mesma fórmula de project_uf em build-resultados-consolidados.py):
#   R^R = A[f w0 + s(1-c)(lambda wH + (1-lambda)(1-rho) wD)] + (1-c) S ;  R^C = A w0
# Cada parcela é o peso do componente no IBS vezes a diferença relativa entre o coeficiente e w0.
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

# extensão do cronograma legal até 2077 (mesma fórmula, coeficientes constantes, com o Seguro-Receita do Estado)
ext = {}
for a in ANOS_EXT:
    s = lp[a]
    hh = s["ibs_historico"] * wH
    dd = s["ibs_destino_liquido"] * wD
    rr = (1 - s["ca"]) * rep_longo(a)
    posx = (hh * (1 - s["ca"]) + dd + rr) / BI
    cfx = w0 * s["bolo_projetado"] / BI
    ext[a] = (posx, cfx, (posx / cfx - 1) * 100)
v77 = next(x for x in res["anexo_a"]["validacao_receita_estados"] if x["uf"] == UF_ALVO)
assert abs(ext["2077"][0] - v77["total_2077_autonomo"] / BI) < 1e-3
primeiro_sr = next(a for a in range(2029, 2078) if rep_longo(a) > 0)
incert = sens["por_uf"][UF_ALVO]["incerteza_rel"]
dest_2077 = lp["2077"]["ibs_destino_liquido"] * wD / BI
var77_dest = (dest_2077 * incert) / ext["2077"][1] * 100  # efeito em p.p. de +-incert no destino, mantido o repasse

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
vg = next(x for x in res["anexo_a"]["validacao_receita_estados"] if x["uf"] == UF_ALVO)
vgob = next(x for x in res["anexo_a"]["validacao_gobetti"]["pontos"] if x["uf"] == UF_ALVO)
corr_gob = res["anexo_a"]["validacao_gobetti"]["pearson_r"]

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
assert abs(ref_es["2025"] - w0) < 1e-6


def var_ano(a, w_base, delta_destino=0.0):
    n = nac[a]
    A, lam, c = n["bolo_projetado"], n["alpha_a"], n["ca"]
    # o ICMS/ISS residual segue a participação do ano-base escolhido; o IBS, os coeficientes estimados
    r = A * (n["fa"] * w_base + n["sa"] * (1 - c) * (lam * wH + (1 - lam) * (1 - RHO) * wD * (1 + delta_destino)))
    return (r / (A * w_base) - 1) * 100


bases = [
    ("2025 (ano-base adotado)", w0),
    ("2026 (estimado)", ref_es["2026"]),
    ("Média de 2019 a 2026", wH),
    ("2019", ref_es["2019"]),
]
assert all(abs(var_ano(a, w0) - var[a]) < 1e-6 for a in ANOS), "variação central inconsistente"
casos = {(b, m): [var_ano(a, wb, m) for a in ANOS] for b, wb in bases for m in (-incert, 0.0, incert)}
central = casos[(bases[0][0], 0.0)]
env_all = [(min(v[i] for v in casos.values()), max(v[i] for v in casos.values())) for i in range(5)]
env_base = [(min(casos[(b, 0.0)][i] for b, _ in bases), max(casos[(b, 0.0)][i] for b, _ in bases)) for i in range(5)]

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

# regressões do Gráfico 3 (mesmos pontos de regressao_2033)
pts = res["regressao_2033"]["pontos"]


def ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return a, b, 1 - ss_res / ss_tot


# ---------------------------------------------------------------- numeros.tex
ufu = tot[UF_ALVO]
piores = rank_2033[:3]
melhores = rank_2033[::-1][:3]
nomes_ano = dict(zip(ANOS, ["Um", "Dois", "Tres", "Quatro", "Cinco"]))
m = ["% Gerado por gerar-tabelas.py -- não editar à mão.\n"]
m.append(macro("NumRecPre", num(pre, 2)))
m.append(macro("NumRecPreArred", num(pre, 0)))
for a, nome in nomes_ano.items():
    m.append(macro(f"NumPos{nome}", num(pos[a], 2)))
    m.append(macro(f"NumCf{nome}", num(cf[a], 2)))
    m.append(macro(f"NumDif{nome}", num(abs(dif[a]), 2)))
    m.append(macro(f"NumDifMi{nome}", num(abs(dif[a]) * 1000, 0)))
    m.append(macro(f"NumVar{nome}", num(abs(var[a]), 2)))
    m.append(macro(f"NumDed{nome}", num(abs(decomp[a][0]), 2)))
    m.append(macro(f"NumHist{nome}", num(abs(decomp[a][1]), 2)))
    m.append(macro(f"NumDest{nome}", num(abs(decomp[a][2]), 2)))
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
    macro("NumCoefNq", num(w0 * 100, 4)),
    macro("NumCoefCq", num(wH * 100, 4)),
    macro("NumCoefPq", num(wD * 100, 4)),
    macro("NumCoefCRel", num(abs((qH - 1) * 100), 1)),
    macro("NumCoefPRel", num(abs((qD - 1) * 100), 1)),
    macro("NumDecDed", num(abs(decomp["2033"][0]), 1)),
    macro("NumDecCpt", num(abs(decomp["2033"][1]), 1)),
    macro("NumDecDest", num(abs(decomp["2033"][2]), 1)),
    macro("NumVarMin", num(abs(v_min), 1)),
    macro("NumVarMax", num(abs(v_max), 1)),
    macro("NumAmplitude", num(abs(v_min - v_max), 1)),
    macro("NumRepMun", num(rep_mun_2033, 1)),
    macro("NumCompHist", num(comp_est["cpt"] / BI, 2)),
    macro("NumCompDest", num(comp_est["destino"] / BI, 2)),
    macro("NumBoloNac", num(nac["2033"]["ibs_bruto"] / 1e12, 2)),
    macro("NumBoloNacBi", num(nac["2033"]["bolo_projetado"] / BI, 2)),
    macro("NumTotVar", num(abs(ufu["variacao_por_ano"]["2033"] * 100), 1)),
    macro("NumTotAcum", num(abs(ufu["acumulado_dpct"] * 100), 1)),
    macro("NumAgEst", num(var_ag, 1)),
    macro("NumVsMedia", num(abs(vs_media), 1)),
    macro("NumSomaN", num(soma_n, 1)),
    macro("NumSomaC", num(soma_c, 1)),
    macro("NumParticipDezenove", num(ref_es["2019"] * 100, 4)),
    macro("NumParticipVinteCinco", num(ref_es["2025"] * 100, 4)),
    macro("NumParticipVinteSeis", num(ref_es["2026"] * 100, 4)),
    macro("NumRotaA", num(pes["rota_A_pct"], 2)),
    macro("NumRotaB", num(pes["rota_B_pct"], 2)),
    macro("NumRotaC", num(pes["rota_C_pct"], 2)),
    macro("NumComposto", num(pes["phi_robusto_pct"], 3)),
    macro("NumIncert", num(pes["incerteza_rel"] * 100, 1)),
    macro("NumFracEst", num(frac_est, 2)),
    macro("NumThetaE", num(theta_E, 1)),
    macro("NumPhiEstCompras", num(pdes["phi_estado_compras_pct"], 3)),
    macro("NumBaseDois", num(abs(var_ano("2033", ref_es["2026"])), 1)),
    macro("NumBaseMedia", num(abs(var_ano("2033", wH)), 1)),
    macro("NumBaseDezenove", num(var_ano("2033", ref_es["2019"]), 1)),
    macro("NumEnvPior", num(abs(env_all[-1][0]), 1)),
    macro("NumEnvMelhor", num(env_all[-1][1], 1)),
    macro("NumEnvBasePior", num(abs(env_base[-1][0]), 1)),
    macro("NumEnvBaseMelhor", num(env_base[-1][1], 1)),
    macro("NumVarQuarenta", num(abs(ext["2040"][2]), 1)),
    macro("NumVarCinquenta", num(abs(ext["2050"][2]), 1)),
    macro("NumVarSessenta", num(abs(ext["2060"][2]), 1)),
    macro("NumVarSetenta", num(abs(ext["2070"][2]), 1)),
    macro("NumVarSetentaSete", num(abs(ext["2077"][2]), 1)),
    macro("NumRecSetentaSete", num(ext["2077"][0], 1)),
    macro("NumCfSetentaSete", num(ext["2077"][1], 1)),
    macro("NumAnoSR", str(primeiro_sr)),
    macro("NumDestSetentaSete", num(var77_dest, 1)),
    macro("NumGobettiRec", num(vg["total_2033_gobetti"] / BI, 2)),
    macro("NumGobettiDelta", num(abs(vg["delta_2033_pct"] * 100), 1)),
    macro("NumGobettiCorr", num(corr_gob, 4)),
    macro("NumPhiTotal", num(vgob["autonomo_pct"], 3)),
    macro("NumPhiGobetti", num(vgob["gobetti_pct"], 3)),
]
for i, u in enumerate(piores):
    m.append(macro(f"NumPior{['Um', 'Dois', 'Tres'][i]}Nome", nome_tex(est[u]["nome"])))
    m.append(macro(f"NumPior{['Um', 'Dois', 'Tres'][i]}Var", num(abs(est[u]["variacao_por_ano"]["2033"] * 100), 1)))
for i, u in enumerate(melhores):
    m.append(macro(f"NumMelhor{['Um', 'Dois', 'Tres'][i]}Nome", nome_tex(est[u]["nome"])))
    m.append(macro(f"NumMelhor{['Um', 'Dois', 'Tres'][i]}Var", num(est[u]["variacao_por_ano"]["2033"] * 100, 1)))
a_h, b_h, r2_h = ols([p["diff_cpt_pct"] for p in pts], [p["variacao_2033_pct"] for p in pts])
a_d, b_d, r2_d = ols([p["diff_destino_pct"] for p in pts], [p["variacao_2033_pct"] for p in pts])
m.append(macro("NumRdoisH", num(r2_h, 3)))
m.append(macro("NumRdoisD", num(r2_d, 3)))
if comsefaz:
    m.append(macro("NumComsefaz", num(abs(comsefaz["2033"]), 1)))
(OUT / "numeros.tex").write_text("".join(m), encoding="utf-8")


# ---------------------------------------------------------------- Tabela 1: parâmetros das duas transições
def p(x, d=0):
    return num(x * 100, d) + "\\%"


L = ["\\begin{tabular}{@{}l*{7}{r}@{}}\n\\toprule\n"]
L.append("\\cabecalhoL{Ano} & \\cabecalho{ICMS/ISS\\\\reman.\\\\$f_t$} & \\cabecalho{Base em\\\\IBS\\\\$s_t$} & "
         "\\cabecalho{Histórico\\\\no IBS\\\\$\\lambda_t$} & \\cabecalho{Histórico\\\\sobre $A_t$} & "
         "\\cabecalho{Seguro-\\\\Receita\\\\sobre $A_t$} & \\cabecalho{Destino\\\\sobre $A_t$} & \\cabecalho{Limite\\\\CGIBS\\\\$c_t$} \\\\\n\\midrule\n")
for a in ANOS:
    n = nac[a]
    s_t, lam = n["sa"], n["alpha_a"]
    L.append(f"{a} & {p(n['fa'])} & {p(s_t)} & {p(lam)} & {p(s_t * lam, 2)} & {p(s_t * (1 - lam) * RHO, 2)} & "
             f"{p(s_t * (1 - lam) * (1 - RHO), 2)} & {p(n['ca'], 2)} \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "tab-parametros.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela 3: projeção da receita estadual do ES (formato do artigo)
L = ["\\begin{tabular}{@{}lrrrr@{}}\n\\toprule\n"]
L.append("\\cabecalhoL{Ano} & \\cabecalho{Cenário sem reforma\\\\R\\$ bi} & \\cabecalho{Receita com reforma\\\\R\\$ bi} & "
         "\\cabecalho{Variação\\\\(\\%)} & \\cabecalho{Diferença\\\\R\\$ mi} \\\\\n\\midrule\n")
for a in ANOS:
    L.append(f"{a} & {num(cf[a], 2)} & {num(pos[a], 2)} & {num(var[a], 2, True)} & {num(dif[a] * 1000, 0, True)} \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "tab-trajetoria.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela 2: todas as UFs (formato do artigo)
ordem_a = sorted(est, key=lambda u: est[u]["variacao_por_ano"]["2033"])
CS = "\\rowcolor{black!10}"
L = ["\\begin{tabular}{@{}l*{11}{r}@{}}\n\\toprule\n"]
L.append("\\cabecalhoL{UF} & \\cabecalho{Receita-\\\\base\\\\2025} & \\multicolumn{5}{c}{\\textbf{\\shortstack{Receita projetada sob\\\\a reforma, R\\$ bi}}} & "
         "\\multicolumn{5}{c}{\\textbf{\\shortstack{Variação ante o cenário\\\\sem reforma (\\%)}}} \\\\\n"
         "\\cmidrule(lr){3-7}\\cmidrule(l){8-12}\n"
         " & & " + " & ".join(f"\\cabecalho{{{a}}}" for a in ANOS) + " & " + " & ".join(f"\\cabecalho{{{a}}}" for a in ANOS) + " \\\\\n\\midrule\n")
for u in ordem_a:
    v = est[u]
    d = u == UF_ALVO
    neg = (lambda s_: f"\\textbf{{{s_}}}") if d else (lambda s_: s_)
    L.append((CS if d else "") + neg(u) + " & " + neg(num(v["pre_2025"] / BI, 1)) + " & " +
             " & ".join(neg(num(v["pos_por_ano"][a] / BI, 1)) for a in ANOS) + " & " +
             " & ".join(neg(num(v["variacao_por_ano"][a] * 100, 2, True)) for a in ANOS) + " \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "tab-ufs.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela A.1: validação externa (formato do artigo)
ipea = {}
ref_md = DATA / "referencias-externas" / "NT_COMSEFAZ_RefTributaria_v3.md"
if ref_md.exists():
    nome_uf = {est[u]["nome"]: u for u in est}
    linhas_md = ref_md.read_text(encoding="utf-8").splitlines()
    i12 = next(i for i, ln in enumerate(linhas_md) if ln.startswith("Tabela 12 —"))
    i13 = next(i for i, ln in enumerate(linhas_md) if ln.startswith("Tabela 13 —"))
    assert any([c.strip() for c in ln.strip("|").split("|")][:7] == ["Ano", "2025", "2029", "2030", "2031", "2032", "2033"] for ln in linhas_md[i12:i13]), "cabeçalho da Tabela 12 mudou"
    for ln in linhas_md[i12:i13]:
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) >= 7 and cols[0] in nome_uf and cols[1].replace(".", "").isdigit() and cols[0] not in ipea:
            vals = [float(c.replace(".", "")) / 1e6 for c in cols[1:7]]  # R$ bi: 2025, 2029..2033
            ipea[nome_uf[cols[0]]] = (vals[0], vals[5])
assert len(ipea) == 27, f"validação externa: {len(ipea)} UFs lidas"
L = ["\\begin{tabular}{@{}ll*{6}{r}@{}}\n\\toprule\n"]
L.append(" & & \\multicolumn{3}{c}{\\textbf{Base 2025}} & \\multicolumn{3}{c}{\\textbf{Projeção 2033}} \\\\\n\\cmidrule(lr){3-5}\\cmidrule(l){6-8}\n"
         "\\cabecalhoL{UF} & \\cabecalhoL{Estado} & \\cabecalho{Este estudo\\\\R\\$ bi} & \\cabecalho{Ipea\\\\R\\$ bi} & \\cabecalho{$\\Delta$ base\\\\(\\%)} & "
         "\\cabecalho{Este estudo\\\\R\\$ bi} & \\cabecalho{Ipea\\\\R\\$ bi} & \\cabecalho{$\\Delta$ 2033\\\\(\\%)} \\\\\n\\midrule\n")
for u in ordem_a:
    v = est[u]
    b_e, b_i = v["pre_2025"] / BI, ipea[u][0]
    f_e, f_i = v["pos_por_ano"]["2033"] / BI, ipea[u][1]
    d = u == UF_ALVO
    neg = (lambda s_: f"\\textbf{{{s_}}}") if d else (lambda s_: s_)
    L.append((CS if d else "") + neg(u) + " & " + neg(nome_tex(v["nome"])) + " & " + neg(num(b_e, 1)) + " & " + neg(num(b_i, 1)) + " & " +
             neg(num((b_i / b_e - 1) * 100, 1, True) + "\\%") + " & " + neg(num(f_e, 1)) + " & " + neg(num(f_i, 1)) + " & " +
             neg(num((f_i / f_e - 1) * 100, 1, True) + "\\%") + " \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "anexo-a-validacao.tex").write_text("".join(L), encoding="utf-8")
ipea_es_base, ipea_es_33 = ipea[UF_ALVO]

# ---------------------------------------------------------------- Gráfico 1: participação anual e coeficiente histórico
def coord(pares):
    return " ".join(f"({x},{y:.4f})" for x, y in pares)


anos_p = [str(y) for y in range(2019, 2026)]
serie = [(int(y), ref_es[y] * 100) for y in anos_p]
G = ["\\begin{tikzpicture}\n\\begin{axis}[\n"
     "  width=0.92\\linewidth, height=6.4cm, xmin=2018.6, xmax=2026.4, ymin=1.40, ymax=1.76,\n"
     "  xtick={2019,2020,2021,2022,2023,2024,2025,2026}, xticklabel style={font=\\footnotesize, /pgf/number format/1000 sep=},\n"
     "  yticklabel style={font=\\footnotesize, /pgf/number format/.cd, fixed, fixed zerofill, precision=2, use comma},\n"
     "  ylabel={Participação na arrecadação nacional (\\%)}, ylabel style={font=\\footnotesize},\n"
     "  ymajorgrids, grid style={gray!25}, axis x line*=bottom, axis y line*=left, axis line style={gray!60},\n"
     "  legend style={font=\\scriptsize, at={(0.02,0.98)}, anchor=north west, draw=none, fill=none}, legend cell align=left,\n"
     "]\n"]
G.append(f"\\addplot[azul, very thick, mark=*, mark size=2pt] coordinates {{{coord(serie)}}};\n\\addlegendentry{{Participação anual}}\n")
G.append(f"\\addplot[azul, dashed, thick, mark=o, mark size=2.4pt, mark options={{fill=white, solid}}] coordinates {{(2025,{ref_es['2025'] * 100:.4f}) (2026,{ref_es['2026'] * 100:.4f})}};\n"
         "\\addlegendentry{2026 (estimado, RREO jan.--ago.)}\n")
G.append(f"\\addplot[black!60, dashed, no marks] coordinates {{(2018.6,{wH * 100:.4f}) (2026.4,{wH * 100:.4f})}};\n"
         f"\\addlegendentry{{Coeficiente 2019--2026 = {tx(wH * 100, 4)}\\%}}\n")
for ano, v in serie + [(2026, ref_es["2026"] * 100)]:
    pos_lbl = "above" if ano >= 2023 else "below"
    G.append(f"\\node[font=\\tiny, {pos_lbl}] at (axis cs:{ano},{v:.4f}) {{{tx(v, 4)}\\%}};\n")
G.append("\\end{axis}\n\\end{tikzpicture}\n")
(OUT / "graf-participacao.tex").write_text("".join(G), encoding="utf-8")

# ---------------------------------------------------------------- Gráfico 2: sensibilidade 2029-2033 (painel único)
xs = [int(a) for a in ANOS]
G = ["\\begin{tikzpicture}\n\\begin{axis}[\n"
     "  width=0.88\\linewidth, height=6.4cm, ymin=-11, ymax=7,\n"
     "  xmin=2028.7, xmax=2033.9, xtick={2029,2030,2031,2032,2033}, xticklabel style={font=\\footnotesize, /pgf/number format/1000 sep=},\n"
     "  yticklabel style={font=\\footnotesize, /pgf/number format/.cd, fixed, precision=0, use comma},\n"
     "  ylabel={Variação ante o cenário sem reforma (\\%)}, ylabel style={font=\\footnotesize},\n"
     "  ymajorgrids, grid style={gray!25}, axis x line*=bottom, axis y line*=left, axis line style={gray!60},\n"
     "  legend style={font=\\scriptsize, at={(0.5,-0.13)}, anchor=north, draw=none, fill=none, legend columns=3, /tikz/every even column/.append style={column sep=4pt}}, legend cell align=left,\n"
     "]\n"]
G.append(f"\\addplot[name path=ua, draw=none, forget plot] coordinates {{{coord(zip(xs, [e_[1] for e_ in env_all]))}}};\n"
         f"\\addplot[name path=la, draw=none, forget plot] coordinates {{{coord(zip(xs, [e_[0] for e_ in env_all]))}}};\n"
         "\\addplot[azulclaro!45, draw=none] fill between[of=ua and la];\n\\addlegendentry{Ano-base e destino $\\pm$" + tx(incert * 100, 1) + "\\% (envoltória)}\n")
G.append(f"\\addplot[name path=ub, draw=none, forget plot] coordinates {{{coord(zip(xs, [e_[1] for e_ in env_base]))}}};\n"
         f"\\addplot[name path=lb, draw=none, forget plot] coordinates {{{coord(zip(xs, [e_[0] for e_ in env_base]))}}};\n"
         "\\addplot[azul!35, draw=none] fill between[of=ub and lb];\n\\addlegendentry{Ano-base alternativo}\n")
estilos = [(bases[1][0], "green!45!black, dashed"), (bases[2][0], "brown!70!black, dash dot"), (bases[3][0], "red!60!black, dotted")]
for (rot, est_), (b, _) in zip(estilos, bases[1:]):
    G.append(f"\\addplot[{est_}, thick, no marks] coordinates {{{coord(zip(xs, casos[(b, 0.0)]))}}};\n\\addlegendentry{{{rot.replace('Média de', 'Média')}}}\n")
G.append(f"\\addplot[azul, very thick, mark=*, mark size=1.8pt] coordinates {{{coord(zip(xs, central))}}};\n\\addlegendentry{{Central (2025)}}\n")
G.append("\\addplot[black!70, thin, no marks, forget plot] coordinates {(2028.7,0) (2033.9,0)};\n")
G.append(f"\\node[font=\\scriptsize, azul, anchor=west] at (axis cs:2033.05,{central[-1]:.3f}) {{{tx(central[-1], 2)}\\%}};\n"
         f"\\node[font=\\scriptsize, gray, anchor=west] at (axis cs:2033.05,{env_all[-1][1]:.3f}) {{{('+' if env_all[-1][1] > 0 else '')}{tx(env_all[-1][1], 1)}\\%}};\n"
         f"\\node[font=\\scriptsize, gray, anchor=west] at (axis cs:2033.05,{env_all[-1][0]:.3f}) {{{tx(env_all[-1][0], 1)}\\%}};\n")
G.append("\\end{axis}\n\\end{tikzpicture}\n")
(OUT / "graf-sensibilidade.tex").write_text("".join(G), encoding="utf-8")

# ---------------------------------------------------------------- Gráfico 3: dispersão por UF
G = ["\\begin{minipage}[t]{0.49\\linewidth}\\centering\n"]
for (chave, rot, a_, b_, r2_, idx) in [("diff_cpt_pct", "(a) Participação na transição federativa", a_h, b_h, r2_h, 0),
                                       ("diff_destino_pct", "(b) Participação pelo destino", a_d, b_d, r2_d, 1)]:
    xs_ = [p_[chave] for p_ in pts if p_["uf"] != UF_ALVO]
    ys_ = [p_["variacao_2033_pct"] for p_ in pts if p_["uf"] != UF_ALVO]
    xmin, xmax = min(p_[chave] for p_ in pts), max(p_[chave] for p_ in pts)
    esp = next(p_ for p_ in pts if p_["uf"] == UF_ALVO)
    G.append("\\begin{tikzpicture}\n\\begin{axis}[\n"
             f"  title={{\\footnotesize {rot} $|$ $R^{{2}}={nm(r2_, 3)}$}}, title style={{yshift=-2pt}}, width=0.92\\linewidth, height=5.6cm,\n"
             "  xlabel={Diferença relativa ante a participação de 2025 (\\%)}, xlabel style={font=\\scriptsize},\n"
             "  ylabel={Variação em 2033 (\\%)}, ylabel style={font=\\scriptsize},\n"
             "  xticklabel style={font=\\scriptsize, /pgf/number format/.cd, fixed, precision=0, use comma}, yticklabel style={font=\\scriptsize, /pgf/number format/.cd, fixed, precision=0, use comma},\n"
             f"  grid=major, grid style={{gray!20}}, axis lines=box, axis line style={{gray!60}}, ymin=-11, ymax=11, xmin={xmin - 3:.1f}, xmax={xmax + 3:.1f},\n"
             "]\n")
    G.append(f"\\addplot[only marks, mark=*, mark size=1.5pt, azul!70] coordinates {{{' '.join(f'({x:.3f},{y:.3f})' for x, y in zip(xs_, ys_))}}};\n")
    G.append(f"\\addplot[azul, thin, no marks, domain={xmin:.2f}:{xmax:.2f}] {{{a_:.5f}+{b_:.5f}*x}};\n")
    G.append(f"\\addplot[only marks, mark=*, mark size=2.6pt, orange!90!black] coordinates {{({esp[chave]:.3f},{esp['variacao_2033_pct']:.3f})}};\n")
    G.append(f"\\node[font=\\scriptsize, anchor=south west] at (axis cs:{esp[chave]:.3f},{esp['variacao_2033_pct']:.3f}) {{ES}};\n")
    G.append(f"\\addplot[black!50, thin, no marks] coordinates {{({xmin - 3:.1f},0) ({xmax + 3:.1f},0)}};\n")
    G.append("\\end{axis}\n\\end{tikzpicture}\n")
    if idx == 0:
        G.append("\\end{minipage}\\hfill\n\\begin{minipage}[t]{0.49\\linewidth}\\centering\n")
G.append("\\end{minipage}\n")
(OUT / "graf-dispersao.tex").write_text("".join(G), encoding="utf-8")

# ---------------------------------------------------------------- Tabela B.1: memória de cálculo do coeficiente histórico (série nominal e ajustada)
rt = load("reforma-tributaria.json")
ph = painel["estados"][UF_ALVO]
ctot = load("coeficientes-uf.json")
anos_h = [str(a) for a in range(2019, 2026)]


def total_nac(a):
    out = sum((rt["dca_icms_outras_deducoes_por_uf"].get(a) or {}).values())
    return rt["dca_icms_br"][a] - out + rt["dca_iss_br"][a] + (rt["dca_fecop_br"].get(a, 0) or 0)


tn = {a: total_nac(a) for a in anos_h}
L = ["\\begin{tabular}{@{}l*{7}{r}@{}}\n\\toprule\n"]
L.append("\\cabecalhoL{Ano} & \\cabecalho{ICMS bruto\\\\R\\$ bi} & \\cabecalho{Outras\\\\deduções} & \\cabecalho{Cota\\\\municipal} & \\cabecalho{FECOP} & "
         "\\cabecalho{Receita de\\\\referência} & \\cabecalho{Fator de\\\\ajuste} & \\cabecalho{Referência\\\\R\\$ de 2025} \\\\\n\\midrule\n")
reais = []
for a in anos_h:
    icms = rt["dca_icms_por_uf"][a][UF_ALVO]
    outras = rt["dca_icms_outras_deducoes_por_uf"][a].get(UF_ALVO) or 0
    cota = (rt["dca_transf_munis_por_uf"][a] or {}).get(UF_ALVO)
    cota = icms * 0.25 if cota is None else cota
    fe = (rt["dca_fecop_por_uf"][a] or {}).get(UF_ALVO, 0) or 0
    refn = icms - outras - cota + fe
    fator = tn["2025"] / tn[a]
    real = refn * fator
    assert abs(real - ph["historico_por_ano"][a]["estado_reais_2025"]) < 1.0, (a, real)
    reais.append(real)
    L.append(f"{a} & {num(icms / BI, 2)} & {num(outras / BI, 2)} & {num(cota / BI, 2)} & {num(fe / BI, 2)} & {num(refn / BI, 2)} & {num(fator, 3)} & {num(real / BI, 2)} \\\\\n")
e26 = ph["estimativa_2026"]
L.append(f"2026 (est.) & {num(e26['icms_reais_2025'] / BI, 2)} & {num(e26['outras_deducoes_reais_2025'] / BI, 2)} & {num(e26['cota_parte_reais_2025'] / BI, 2)} & "
         f"{num(e26['fecop_reais_2025'] / BI, 2)} & {num(e26['estado_reais_2025'] / BI, 2)} & --- & {num(e26['estado_reais_2025'] / BI, 2)} \\\\\n")
media = (sum(reais) + e26["estado_reais_2025"]) / 8
tb25 = ctot["total_br_2025"]
assert abs(media / tb25 - wH) < 1e-9, (media / tb25, wH)
L.append("\\midrule\n")
L.append(f"\\multicolumn{{7}}{{@{{}}l}}{{\\textbf{{Média da receita de referência ajustada}}}} & \\textbf{{{num(media / BI, 2)}}} \\\\\n")
L.append(f"\\multicolumn{{7}}{{@{{}}l}}{{\\textbf{{Arrecadação nacional de referência em 2025}}}} & \\textbf{{{num(tb25 / BI, 2)}}} \\\\\n")
L.append(f"\\multicolumn{{7}}{{@{{}}l}}{{\\textbf{{Coeficiente de participação do Espírito Santo}}}} & \\textbf{{{num(wH * 100, 4)}\\%}} \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "anexo-a-coef-historico.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela B.2: memória de cálculo do ES em 2033
n33 = nac["2033"]
A33, lam33, c33 = n33["bolo_projetado"], n33["alpha_a"], n33["ca"]
hist = A33 * n33["sa"] * lam33 * wH / BI
dest = A33 * n33["sa"] * (1 - lam33) * (1 - RHO) * wD / BI
sub = hist + dest
ded = c33 * sub
rec = sub - ded
assert abs(rec - pos["2033"]) < 1e-3, (rec, pos["2033"])
rc = A33 * w0 / BI
assert abs(rc - cf["2033"]) < 1e-3
a33, a33m = num(A33 / BI, 2), nm(A33 / BI, 2)
L = ["\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{3.0cm}>{\\raggedright\\arraybackslash}p{4.3cm}>{\\raggedright\\arraybackslash}p{4.9cm}r@{}}\n\\toprule\n"]
L.append("\\cabecalhoL{Item} & \\cabecalhoL{Expressão} & \\cabecalhoL{Substituição numérica} & \\cabecalho{Valor} \\\\\n\\midrule\n")
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
(OUT / "anexo-a-memoria.tex").write_text("".join(L), encoding="utf-8")

# ---------------------------------------------------------------- Tabela B.3: sensibilidade ao ano-base
u_pct = incert * 100
L = ["\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{4.9cm}rrrr@{}}\n\\toprule\n"]
L.append(f"\\cabecalhoL{{Ano-base do cenário\\\\sem reforma}} & \\cabecalho{{Participação\\\\do Estado (\\%)}} & "
         f"\\cabecalho{{Destino\\\\$-${num(u_pct, 1)}\\%}} & \\cabecalho{{Destino\\\\central}} & \\cabecalho{{Destino\\\\$+${num(u_pct, 1)}\\%}} \\\\\n\\midrule\n")
for rot, wb in bases:
    L.append(f"{rot} & {num(wb * 100, 4)} & {num(var_ano('2033', wb, -incert), 2, True)}\\% & {num(var_ano('2033', wb), 2, True)}\\% & {num(var_ano('2033', wb, incert), 2, True)}\\% \\\\\n")
L.append("\\bottomrule\n\\end{tabular}\n")
(OUT / "anexo-a-anobase.tex").write_text("".join(L), encoding="utf-8")


# ---------------------------------------------------------------- macros adicionais (usam valores calculados acima)
tb25_nac = load("coeficientes-uf.json")["total_br_2025"]
dwH = 1e9 / tb25_nac  # efeito de R$ 1 bi de contribuições a fundos sobre o coeficiente histórico (fração do total nacional)
efeito_fundos_33 = (1 - nac["2033"]["ca"]) * nac["2033"]["alpha_a"] * dwH / w0 * 100
benef = {a: seguro_lp[a]["n_beneficiarios"] for a in ("2029", "2033")}
ufs_sr = sorted({u for a in ANOS for u, v in seguro_lp[a]["repasse_por_uf"].items() if isinstance(v, dict) and (v.get("estado") or 0) > 0})
assert ufs_sr == ["AM"], f"texto assume que só o Amazonas recebe entre os estados: {ufs_sr}"
ex = [
    macro("NumFundosPP", num(efeito_fundos_33, 0)),
    macro("NumFundosCoefPP", num(dwH * 100, 1)),
    macro("NumDestTrintaTres", num(abs(var_ano("2033", w0, incert) - var_ano("2033", w0)), 1)),
    macro("NumFracMuni", num(phi_pof["frac_muni_pct"], 2)),
    macro("NumThetaM", num(phi_pof["compras_governamentais"]["theta_municipal"] * 100, 0)),
    macro("NumThetaEInt", num(theta_E, 0)),
    macro("NumCoefMuniq", num(pdes["coef_muni_compras_pct"], 4)),
    macro("NumFundoUm", num(nac["2029"]["ibs_seguro_receita"] / BI, 2)),
    macro("NumFundoCinco", num(nac["2033"]["ibs_seguro_receita"] / BI, 2)),
    macro("NumBenefUm", str(benef["2029"])),
    macro("NumBenefCinco", str(benef["2033"])),
    macro("NumIpeaBase", num(ipea_es_base, 1)),
    macro("NumIpeaBaseDelta", num(abs((ipea_es_base / pre - 1) * 100), 1)),
    macro("NumIpeaTrintaTres", num(ipea_es_33, 1)),
    macro("NumIpeaDelta", num(abs((ipea_es_33 / pos["2033"] - 1) * 100), 1)),
    macro("NumRazaoPib", num(nac["2033"]["bolo_pct_pib"], 2)),
]
with open(OUT / "numeros.tex", "a", encoding="utf-8") as f:
    f.write("".join(ex))

# ---------------------------------------------------------------- resumo no terminal (conferência)
print(f"ES: pré-IBS 2025 R$ {pre:.2f} bi")
for a in ANOS:
    print(f"  {a}: sem {cf[a]:.2f}  com {pos[a]:.2f}  dif {dif[a]:+.2f}  var {var[a]:+.2f}%  decomp(ded,H,D,S,tot)=" +
          ",".join(f"{x:+.2f}" for x in decomp[a]))
print(f"  acumulado: R$ {dif_acum:+.2f} bi ({var_acum:+.2f}%)")
print(f"  posição entre as piores em 2033: {pos_rank}º de {len(est)}; no acumulado: {rank_acum}º; {n_perdem_2033} UFs perdem")
print(f"  w0 {w0*100:.4f}  wH {wH*100:.4f}  wD {wD*100:.4f}  qH {qH:.4f}  qD {qD:.4f}")
print(f"  faixa de métodos em 2033: {v_min:.2f}% a {v_max:.2f}%")
print("  extensão:", {a: round(ext[a][2], 2) for a in ANOS_EXT}, "| primeiro ano com SR ao Estado:", primeiro_sr, "| efeito de ±incert no destino em 2077 (p.p.):", round(var77_dest, 2))
print("  envoltória 2033: todas", [round(x, 2) for x in env_all[-1]], "| só ano-base", [round(x, 2) for x in env_base[-1]])
print(f"  R² histórico {r2_h:.3f}, destino {r2_d:.3f}")
print(f"  agregado estados 2033: {var_ag:+.2f}%; ES vs média: {vs_media:+.2f}%; agregado UF: {var_uf_ag:+.2f}%; soma wH {soma_c:.2f} vs w0 {soma_n:.2f}")
print(f"  Gobetti: receita 2033 {vg['total_2033_gobetti']/BI:.2f} bi ({vg['delta_2033_pct']*100:+.2f}%); corr {corr_gob:.4f}; φ total {vgob['autonomo_pct']:.3f} vs {vgob['gobetti_pct']:.3f}")
if comsefaz:
    print("  Comsefaz (prelim.):", {a: round(v, 2) for a, v in comsefaz.items()})
