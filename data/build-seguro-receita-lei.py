#!/usr/bin/env python3
"""
Estudo 18 (nota técnica): Seguro-Receita do IBS (legislação, metodologia de cálculo, resultados e beneficiários de 2029 a 2033).
Gera estudos/seguro-receita-lei-e-beneficiarios.html a partir de seguro-receita-repasses.json (2029-2033, por ente),
seguro-receita-repasses-longo-prazo.json (nível de equalização e razão dos estados até 2077), phi-dest-pof-censo.json
e ibs-projecao-nacional.json. Rodar depois de build-seguro-receita-repasses*.py.

Uso: python3 build-seguro-receita-lei.py
"""
import json, re, html
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = ROOT / "estudos" / "seguro-receita-lei-e-beneficiarios.html"
J = lambda n: json.loads((HERE / n).read_text(encoding="utf-8"))
SR = J("seguro-receita-repasses.json")["anos"]
LP = J("seguro-receita-repasses-longo-prazo.json")["anos"]
PHI = J("phi-dest-pof-censo.json")
NAC = {r["ano"]: r for r in J("ibs-projecao-nacional.json")["projecao"]}
BOLO = {r["ano"]: r["bolo_projetado"] for r in J("ibs-projecao-longo-prazo.json")["projecao"]}
ANOS = [2029, 2030, 2031, 2032, 2033]
NOMES = {'AC':'Acre','AL':'Alagoas','AM':'Amazonas','AP':'Amapá','BA':'Bahia','CE':'Ceará','DF':'Distrito Federal','ES':'Espírito Santo','GO':'Goiás','MA':'Maranhão','MG':'Minas Gerais','MS':'Mato Grosso do Sul','MT':'Mato Grosso','PA':'Pará','PB':'Paraíba','PE':'Pernambuco','PI':'Piauí','PR':'Paraná','RJ':'Rio de Janeiro','RN':'Rio Grande do Norte','RO':'Rondônia','RR':'Roraima','RS':'Rio Grande do Sul','SC':'Santa Catarina','SE':'Sergipe','SP':'São Paulo','TO':'Tocantins'}
COMSEFAZ = {'AM': 2031, 'MS': 2055, 'ES': 2056, 'RO': 2061, 'MT': 2064}   # Nota técnica do Comsefaz, seção 6.4


def n(x, d=1):
    s = f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if round(x, d) < 0 else "") + s


def mi(x, d=1): return n(x / 1e6, d)
def bi(x, d=2): return n(x / 1e9, d)
def pc(x, d=1): return n(100 * x, d) + "%"
def esc(s): return html.escape(s, quote=False)


# ---------------------------------------------------------------- dados
ent = {a: {e["id"]: e for e in SR[str(a)]["entidades"]} for a in ANOS}
nivel = {int(a): v["nivel_equalizacao"] for a, v in LP.items()}
razao_uf = {int(a): v["razao_estados"] for a, v in LP.items()}
repasse_uf = {int(a): {uf: x["estado"] for uf, x in v["repasse_por_uf"].items()} for a, v in LP.items()}
entrada = {}
for a in sorted(razao_uf):
    for uf, r in repasse_uf[a].items():
        if r > 1 and uf not in entrada:
            entrada[uf] = a
phiE = {uf: PHI["por_uf"][uf]["coef_estado_compras_pct"] / 100 for uf in NOMES}
phi_cons = {uf: PHI["por_uf"][uf]["phi_estado_compras_pct"] / 100 for uf in NOMES}
frac_e = PHI["frac_estado_pct"] / 100
nac33 = NAC[2033]
ibs_ref33 = nac33["ibs_bruto"] * (1 - nac33["ca"])

# ---------------------------------------------------------------- cabeçalho copiado do Estudo 12
src = (ROOT / "estudos" / "seguro-receita-repasses.html").read_text(encoding="utf-8")
head = src[: src.index("</style>")]
extra_css = """
        .nt-corpo { font-family: var(--serif); }
        .nt-resumo { border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); padding: 1.1rem 0 1.2rem; margin: 0.5rem 0 2rem; }
        .nt-resumo h2 { font-family: var(--sans); font-size: 0.78rem; letter-spacing: 0.09em; text-transform: uppercase; color: var(--text-muted); margin: 0 0 0.5rem; }
        .nt-resumo p { font-size: 0.93rem; line-height: 1.72; color: var(--text); margin: 0 0 0.6rem; text-align: justify; }
        .nt-resumo .palavras { font-size: 0.86rem; color: var(--text-secondary); margin-bottom: 0; }
        .texto { font-family: var(--serif); font-size: 0.99rem; line-height: 1.8; color: var(--text); margin: 0.7rem 0 1rem; text-align: justify; hyphens: auto; }
        .subsec { font-family: var(--display); font-size: 1.02rem; font-weight: 700; color: var(--text-primary); margin: 1.8rem 0 0.3rem; }
        .citacao { margin: 0.9rem 0 1.1rem 2.2rem; padding-left: 0.9rem; border-left: 2px solid var(--border); font-family: var(--serif); font-size: 0.86rem; line-height: 1.65; color: var(--text-secondary); text-align: justify; }
        .citacao p { margin: 0.3rem 0; }
        .citacao .fonte-cit { display: block; font-family: var(--sans); font-size: 0.74rem; color: var(--text-muted); margin-top: 0.25rem; }
        .eq { margin: 0.5rem 0 0.9rem; overflow-x: auto; font-size: 0.97rem; }
        .tab-titulo { display: block; font-family: var(--sans); font-size: 0.82rem; font-weight: 600; color: var(--text-primary); margin: 1.6rem 0 0.5rem; }
        .nota-tabela { font-family: var(--serif); font-size: 0.78rem; color: var(--text-muted); line-height: 1.6; margin: 0.3rem 0 1.6rem; }
        .tag-recebe { color: var(--pos); font-weight: 700; } .tag-nao { color: var(--text-muted); }
        .table-wrap.curta { max-height: none; } .table-wrap.curta .data-table th { white-space: normal; text-align: right; } .table-wrap.curta .data-table th.th-left { text-align: left; }
        .refs { font-family: var(--serif); font-size: 0.86rem; line-height: 1.65; color: var(--text); padding-left: 0; list-style: none; }
        .refs code, .nota-tabela code, .footnotes code { overflow-wrap: anywhere; word-break: break-all; }
        .refs li { margin: 0 0 0.7rem; padding-left: 1.6rem; text-indent: -1.6rem; text-align: left; }
"""
head = head + extra_css + "    </style>\n</head>\n"
head = re.sub(r"<title>.*?</title>", "<title>Seguro-Receita do IBS: legislação, cálculo e beneficiários, 2029–2033 | Eduardo Reis Araújo</title>", head, flags=re.S)
head = re.sub(r'(<meta name="description" content=")[^"]*(")', r"\1Nota técnica sobre o Seguro-Receita do IBS (ADCT, art. 132; LC 227/2026, arts. 106 a 117): legislação, metodologia de cálculo, resultados para os 27 estados e 5.569 municípios e lista dos beneficiários de 2029 a 2033.\2", head)
head = re.sub(r'(<meta property="og:title" content=")[^"]*(")', r"\1Seguro-Receita do IBS: legislação, cálculo e beneficiários, 2029–2033\2", head)
head = re.sub(r'(<meta property="og:description" content=")[^"]*(")', r"\1Nota técnica: a regra do art. 117 da LC 227/2026, a metodologia de cálculo e os estados e municípios beneficiados entre 2029 e 2033.\2", head)
head = head.replace("seguro-receita-repasses.html", "seguro-receita-lei-e-beneficiarios.html")
head = head.replace("</head>\n    </style>", "</head>")

# ---------------------------------------------------------------- tabelas
def tab_exemplo():
    linhas = []
    for uf in ("PR", "ES", "AM"):
        e = ent[2033][f"UF-{uf}"]
        recebe = e["repasse"] > 1
        linhas.append(
            f"<tr><td class='td-ente'>{NOMES[uf]}</td><td>{pc(phiE[uf],2)}</td><td>{bi(e['numerador'])}</td><td>{bi(e['denom_capado'])}</td>"
            f"<td>{n(e['razao'],2)}</td><td>{n(nivel[2033],2)}</td>"
            f"<td>{'<span class=tag-recebe>recebe R$ ' + bi(e['repasse']) + ' bi</span>' if recebe else '<span class=tag-nao>não recebe</span>'}</td></tr>")
    return ("<div class='table-wrap curta'><table class='data-table'><thead><tr><th class='th-left'>Ente (esfera estadual)</th>"
            "<th>Destino pleno</th><th>IBS pelo destino (R$ bi)</th><th>Receita de referência ajustada (R$ bi)</th>"
            "<th>Razão</th><th>Nível de equalização</th><th>Resultado em 2033</th></tr></thead><tbody>" + "".join(linhas) + "</tbody></table></div>")


def tab_nivel():
    anos = [2029, 2030, 2031, 2032, 2033, 2040, 2050, 2060, 2070, 2077]
    linhas = []
    for a in anos:
        v = LP[str(a)]
        linhas.append(f"<tr><td class='td-ente'>{a}</td><td>{bi(v['pool'])}</td><td>{n(100*v['pool']/BOLO[a],2)}%</td>"
                      f"<td>{n(v['nivel_equalizacao'],2)}</td><td>{v['n_beneficiarios']}</td></tr>")
    return ("<div class='table-wrap curta'><table class='data-table'><thead><tr><th class='th-left'>Ano</th><th>Fundo (R$ bi de 2025)</th>"
            "<th>Fundo (% da arrecadação de referência)</th><th>Nível de equalização</th><th>Entes beneficiados</th></tr></thead><tbody>"
            + "".join(linhas) + "</tbody></table></div>")


def tab_estados():
    ordem = sorted(NOMES, key=lambda u: razao_uf[2033][u])
    linhas = []
    for uf in ordem:
        e = ent[2033][f"UF-{uf}"]
        acum = sum(ent[a][f"UF-{uf}"]["repasse"] for a in ANOS)
        ano = entrada.get(uf)
        com = COMSEFAZ.get(uf)
        cls = " class='row-es'" if uf == "ES" else ""
        linhas.append(
            f"<tr{cls}><td class='td-ente'>{NOMES[uf]} <small>{uf}</small></td><td>{n(razao_uf[2033][uf],2)}</td>"
            f"<td>{ano if ano else 'depois de 2077'}</td><td>{com if com else '—'}</td>"
            f"<td>{mi(e['repasse']) if e['repasse']>1 else '—'}</td><td>{mi(acum) if acum>1 else '—'}</td></tr>")
    return ("<div class='table-wrap curta'><table class='data-table'><thead><tr><th class='th-left'>Estado</th><th>Razão em 2033</th>"
            "<th>Ano em que entra (esta estimativa)</th><th>Ano em que entra (nota do Comsefaz)</th><th>Repasse em 2033 (R$ mi)</th>"
            "<th>Repasse acumulado 2029–2033 (R$ mi)</th></tr></thead><tbody>" + "".join(linhas) + "</tbody></table></div>")


def tab_es():
    anos = [2029, 2033, 2040, 2050, 2054, 2056, 2058]
    linhas = []
    for a in anos:
        r = razao_uf[a]["ES"]; L = nivel[a]
        sit = "<span class=tag-recebe>entra</span>" if repasse_uf[a]["ES"] > 1 else "<span class=tag-nao>não entra</span>"
        linhas.append(f"<tr><td class='td-ente'>{a}</td><td>{n(r,3)}</td><td>{n(L,3)}</td><td>{n(L-r,3)}</td><td>{sit}</td></tr>")
    return ("<div class='table-wrap curta'><table class='data-table'><thead><tr><th class='th-left'>Ano</th><th>Razão do Espírito Santo</th>"
            "<th>Nível de equalização</th><th>Nível menos razão</th><th>Situação</th></tr></thead><tbody>" + "".join(linhas) + "</tbody></table></div>")


def lista_beneficiarios():
    todos = {}
    for a in ANOS:
        for i, e in ent[a].items():
            if e["repasse"] > 1:
                todos.setdefault(i, e)
    linhas = []
    for i, e in sorted(todos.items(), key=lambda kv: -sum(ent[a][kv[0]]["repasse"] for a in ANOS)):
        rep = [ent[a][i]["repasse"] for a in ANOS]
        nome = NOMES[e["uf"]] if e["esfera"] == "estado" else e["nome"]
        tipo = "Estado" if e["esfera"] == "estado" else "Município"
        cls = " class='row-es'" if e["uf"] == "ES" else ""
        linhas.append(f"<tr{cls}><td class='td-ente'>{esc(nome)}</td><td class='td-tipo'>{tipo}</td><td>{e['uf']}</td><td>{n(ent[2033][i]['razao'],2)}</td>"
                      + "".join(f"<td>{mi(x) if x>1 else '—'}</td>" for x in rep) + f"<td><strong>{mi(sum(rep))}</strong></td></tr>")
    total = [sum(e['repasse'] for e in ent[a].values()) for a in ANOS]
    foot = "<tr><td class='td-ente'>Total do fundo</td><td></td><td></td><td></td>" + "".join(f"<td>{mi(x)}</td>" for x in total) + f"<td>{mi(sum(total))}</td></tr>"
    return len(todos), ("<div class='table-toolbar'><input type='search' class='search-input' id='filtro' placeholder='Filtrar por nome ou UF…' aria-label='Filtrar'></div>"
            "<div class='table-wrap'><table class='data-table' id='tab-benef'><thead><tr><th class='th-left'>Ente</th><th class='th-left'>Esfera</th><th>UF</th><th>Razão 2033</th>"
            + "".join(f"<th>{a}</th>" for a in ANOS) + "<th>Acumulado</th></tr></thead><tbody>" + "".join(linhas) + f"</tbody><tfoot>{foot}</tfoot></table></div>")


n_benef, tab_benef = lista_beneficiarios()
NENTES = f"{len(ent[2033]):,}".replace(",", ".")
NENTES_MUN = f"{sum(1 for e in ent[2033].values() if e['esfera'] != 'estado'):,}".replace(",", ".")
est_benef = [uf for uf in NOMES if any(ent[a][f"UF-{uf}"]["repasse"] > 1 for a in ANOS)]
pr, es, am = ent[2033]["UF-PR"], ent[2033]["UF-ES"], ent[2033]["UF-AM"]
L33 = nivel[2033]
num_pr = pr["numerador"]

# ---------------------------------------------------------------- quantidades para o texto
def benef(a, esfera=None):
    return [e for e in ent[a].values() if e["repasse"] > 1 and (esfera is None or (e["esfera"] == "estado") == (esfera == "estado"))]

acum = {}
for a in ANOS:
    for i, e in ent[a].items():
        if e["repasse"] > 1:
            acum[i] = acum.get(i, 0) + e["repasse"]
tot_acum = sum(acum.values())
ranking = sorted(acum, key=lambda i: -acum[i])
nome_de = lambda i: NOMES[ent[2033][i]["uf"]] if ent[2033][i]["esfera"] == "estado" else ent[2033][i]["nome"]
top10 = ranking[:10]
part_top10 = sum(acum[i] for i in top10) / tot_acum
n_teto = sum(1 for i in acum if ent[2033][i]["teto"] < ent[2033][i]["denom_ref"])
saem33 = [i for i in acum if ent[2033][i]["repasse"] <= 1]
todos_anos = [i for i in acum if all(ent[a][i]["repasse"] > 1 for a in ANOS)]
muni_acum = [i for i in acum if ent[2033][i]["esfera"] != "estado"]
por_uf = {}
for i in muni_acum:
    por_uf[ent[2033][i]["uf"]] = por_uf.get(ent[2033][i]["uf"], 0) + 1
maiores_uf = sorted(por_uf.items(), key=lambda kv: -kv[1])[:3]
es_mun = sorted((nome_de(i), acum[i]) for i in muni_acum if ent[2033][i]["uf"] == "ES")
fator_ibs = NAC[2033]["ibs_bruto"] / NAC[2032]["ibs_bruto"]
fator_fundo = NAC[2033]["ibs_seguro_receita"] / NAC[2032]["ibs_seguro_receita"]
fator_nivel = nivel[2033] / nivel[2032]
import statistics as _st
fator_razao = _st.median(e['razao'] for e in ent[2033].values()) / _st.median(e['razao'] for e in ent[2032].values())
lista_nomes = lambda xs: (", ".join(xs[:-1]) + " e " + xs[-1]) if len(xs) > 1 else xs[0]


def tab_fundo():
    linhas = []
    for a in ANOS:
        v = NAC[a]
        linhas.append(f"<tr><td class='td-ente'>{a}</td><td>{bi(v['ibs_bruto'],1)}</td><td>{bi(v['ibs_seguro_receita'])}</td>"
                      f"<td>{n(nivel[a],2)}</td><td>{len(benef(a,'estado'))}</td><td>{len(benef(a,'municipio'))}</td><td>{len(benef(a))}</td></tr>")
    return ("<div class='table-wrap curta'><table class='data-table'><thead><tr><th class='th-left'>Ano</th><th>IBS com alíquotas de referência (R$ bi)</th>"
            "<th>Fundo (R$ bi)</th><th>Nível de equalização</th><th>Estados atendidos</th><th>Municípios atendidos</th><th>Total de entes</th></tr></thead><tbody>"
            + "".join(linhas) + "</tbody></table></div>")


def ref(txt): return f"<li>{txt}</li>"
def tx(txt): return f"<p class='texto'>{txt}</p>"
def sub(txt): return f"<h3 class='subsec'>{txt}</h3>"
def cit(fonte, *paras): return "<div class='citacao'>" + "".join(f"<p>{p}</p>" for p in paras) + f"<span class='fonte-cit'>{fonte}</span></div>"
def eq(latex): return "<div class='eq'>$$" + latex + "$$</div>"
def tit(txt): return f"<span class='tab-titulo'>{txt}</span>"

EQ_RAZAO = r"r_{i,a}=\frac{N_{i,a}}{D_i}\tag{1}"
EQ_NUM = r"N_{i,a}=\mathrm{IBS}^{\mathrm{ref}}_{a}\,\left(1-\gamma_a\right)\,\varphi_i\,f_a,\qquad f_a=\frac{1}{12}\sum_{k=1}^{12}\Big[(k-1)+(13-k)\,g_a\Big],\quad g_a=\frac{B_{a-1}}{B_a}\tag{2}"
EQ_DEN = r"D_i=\min\left\{R_i,\;3\,\frac{\sum_{j\in E}R_j}{\sum_{j\in E}P_j}\,P_i\right\}\tag{3}"
EQ_REP = r"x_{i,a}=\max\left\{0,\;L_a\,D_i-N_{i,a}\right\},\qquad \sum_i x_{i,a}=F_a\tag{4}"
EQ_FUNDO = r"F_a=0{,}05\,\left(1-\alpha_a\right)\,\mathrm{IBS}^{\mathrm{ref}}_{a}\tag{5}"

ref_pr = f"{pc(phi_cons['PR'],2)} × {pc(frac_e,1)} = {pc(phiE['PR'],2)}"

corpo = f"""
<div class="study-hero">
  <div class="study-hero-meta">
    <span class="study-hero-tag">Estudo 18 · Nota técnica</span><span class="study-hero-topic">Reforma Tributária</span>
    <span class="study-hero-topic">Federalismo Fiscal</span><span class="study-hero-topic">Seguro-Receita</span>
    <span class="study-hero-date">Outubro de 2026</span>
  </div>
  <h1>Seguro-Receita do IBS: legislação, metodologia de cálculo e beneficiários entre 2029 e 2033</h1>
  <p class="study-meta">Eduardo Reis Araújo</p>
  <p class="study-meta">Estimativa própria, e não o cálculo oficial: o Comitê Gestor do IBS (CGIBS) apurará os valores com dados que ainda não existem. Esta nota complementa o <a href="/estudos/seguro-receita-repasses.html">Estudo 12</a>, que permite consultar o repasse de cada ente, e a aba Seguro-Receita do <a href="https://painelufir.vercel.app/#seguro-receita">painel da reforma tributária</a>.</p>
</div>
<div class="study-content nt-corpo">

<div class="nt-resumo">
  <h2>Resumo</h2>
  <p>Esta nota examina o Seguro-Receita, fundo de nivelamento previsto no art. 132 do ADCT e regulamentado pelo art. 117 da Lei Complementar n.º 227/2026, e estima quem o receberá entre 2029 e 2033. O texto transcreve o desenho legal, formaliza o cálculo da razão que ordena os entes e do nível de equalização que encerra a distribuição e aplica o procedimento aos 27 entes estaduais e aos 5.569 municípios, a preços de 2025. O fundo cresce de R$ {bi(NAC[2029]['ibs_seguro_receita'])} bilhão em 2029 para R$ {bi(NAC[2033]['ibs_seguro_receita'])} bilhões em 2033. Atende de {min(len(benef(a)) for a in ANOS[:4])} a {max(len(benef(a)) for a in ANOS[:4])} entes por ano até 2032 e {len(benef(2033))} em 2033, quando a extinção do ICMS e do ISS eleva as razões mais do que o nível de equalização. Entre os estados, só o Amazonas é atendido no período; o Espírito Santo passa a receber em {entrada['ES']}, e o Paraná não recebe até 2077. A estimativa usa um coeficiente de destino aproximado e dispensa ajustes que o CGIBS ainda não definiu, de modo que os valores devem ser lidos como ordem de grandeza.</p>
  <p class="palavras"><strong>Palavras-chave:</strong> Seguro-Receita; IBS; reforma tributária; federalismo fiscal; transição.</p>
</div>

<h2 class="section-heading">1. Introdução</h2>
{tx("A Emenda Constitucional n.º 132/2023 substitui o ICMS e o ISS pelo Imposto sobre Bens e Serviços (IBS), cuja receita será partilhada entre estados e municípios. A partilha, porém, não muda de uma só vez. Entre 2029 e 2077, a distribuição migra do critério histórico, que reproduz a participação de cada ente na arrecadação de 2019 a 2026, para o critério do destino, que acompanha o local do consumo. A migração redistribui receita entre os entes e cria ganhadores e perdedores.")}
{tx("Para amortecer as perdas relativas, a Constituição criou uma regra de proteção, aqui chamada de Seguro-Receita. O art. 132 do ADCT reserva 5% do IBS apurado pelo critério do destino para um fundo que socorre os entes com as menores razões entre o IBS que recebem e a receita que tinham antes da reforma. A Lei Complementar n.º 227/2026 regulamenta o fundo no art. 117, e caberá ao CGIBS fazer os cálculos e as distribuições.")}
{tx("A regra é de leitura difícil. Seus elementos estão espalhados por vários artigos, o resultado depende de uma distribuição sequencial, e os dados exigidos para aplicá-la, como o IBS apurado por ente, ainda não existem. Essa combinação torna incerto saber quem receberá o fundo e quando. O tema interessa tanto aos entes que dependerão dele quanto aos demais, pois o fundo é formado com recursos retidos de todos.")}
{tx(f"Esta nota tem três objetivos. O primeiro é apresentar o desenho legal do Seguro-Receita. O segundo é formalizar o cálculo da razão que ordena os entes e do nível de equalização que encerra a distribuição. O terceiro é aplicar o procedimento aos 27 entes estaduais e aos {NENTES_MUN} municípios, para identificar os beneficiários de 2029 a 2033 e o ano em que cada estado passa a receber o fundo, até 2077. Os resultados são estimativas.")}
{tx("A seção 2 descreve a legislação. A seção 3 expõe a metodologia de cálculo, os dados e as simplificações adotadas. A seção 4 traz os resultados, e a seção 5 resume as conclusões. As referências encerram a nota.")}

<h2 class="section-heading">2. Legislação</h2>
{sub("2.1 Fundamento constitucional")}
{tx("O fundamento do Seguro-Receita é o art. 132 do ADCT, incluído pela Emenda Constitucional n.º 132/2023. O dispositivo manda reter 5% do imposto de estados, Distrito Federal e municípios, apurado com as alíquotas de referência e deduzida a retenção do art. 131, § 1.º, para distribuí-lo aos entes com as menores razões entre dois valores.")}
{cit("ADCT, art. 132, caput", "<strong>Art. 132.</strong> Do imposto dos Estados, do Distrito Federal e dos Municípios apurado com base nas alíquotas de referência de que trata o art. 130 [...], deduzida a retenção de que trata o art. 131, § 1.º, será retido montante correspondente a 5% (cinco por cento) para distribuição aos entes com as menores razões entre: I – o valor apurado nos termos dos arts. 149-C e 156-A, § 4.º, II, e § 5.º, I e IV, com base nas alíquotas de referência, após a aplicação do disposto no art. 158, IV, “b”, todos da Constituição Federal; e II – a respectiva receita média, apurada nos termos do art. 131, § 2.º, I, II e III, [...] limitada a 3 (três) vezes a média nacional por habitante da respectiva esfera federativa.")}
{tx("O § 1.º do mesmo artigo estabelece o método de distribuição, que é sequencial e sucessivo, de modo que todos os entes atendidos terminem com a mesma razão. O § 3.º remete a lei complementar a redução gradual do percentual entre 2078 e 2097.")}
{sub("2.2 Regulamentação pela Lei Complementar n.º 227/2026")}
{tx("Os arts. 106 a 108 definem a receita de cada ente pelo critério do destino. O ponto de partida é o IBS extinto e não apropriado como crédito nas operações em que o ente é o destino (art. 106, I). O art. 107 ajusta esse valor pela devolução geral do imposto às pessoas físicas e, quando couber, pela fixação de alíquota diferente da de referência. O art. 108 deduz os créditos presumidos e acrescenta, entre outros itens, as aquisições de produtores rurais e transportadores autônomos não contribuintes e os valores de multas e juros de mora.")}
{tx("Os arts. 109 e 110 dimensionam o fundo. O art. 109 retém, da receita assim apurada, 80% de 2029 a 2032 e 90% em 2033, percentual que cai à razão de 1/45 ao ano entre 2034 e 2077; essa parcela retida segue o critério histórico. Do que resta, o art. 110 retém 5% de 2029 a 2077 e, de 2078 a 2096, percentual decrescente à razão de 1/20 ao ano. É essa segunda retenção que forma o fundo.")}
{cit("LC 227/2026, art. 110", "<strong>Art. 110.</strong> De 2029 a 2096, serão retidos do produto da arrecadação do IBS destinada a cada Estado e Município e ao Distrito Federal, nos termos do art. 108 desta Lei Complementar, após a retenção de que trata o art. 109 desta Lei Complementar: I – de 2029 a 2077, 5% (cinco por cento); e II – de 2078 a 2096, o percentual a que se refere o inciso I deste caput, reduzido à razão de 1/20 (um vinte avos) por ano.")}
{tx("O denominador da razão vem do art. 115. A receita média de referência dos estados é a média anual de 2019 a 2026 da arrecadação do ICMS, líquida da cota-parte dos municípios, somada à receita de contribuições a fundos estaduais condicionadas a tratamento diferenciado do imposto. A dos municípios soma o ISS e a cota-parte do ICMS. Os valores de cada ano são corrigidos até 2026 pela variação nominal da arrecadação total de ICMS e ISS (art. 115, § 2.º). O art. 116 atribui ao CGIBS os cálculos e a divulgação do coeficiente de cada ente até 31 de agosto de 2027, com prazo de 30 dias para contestação.")}
{sub("2.3 Distribuição complementar: o art. 117")}
{tx("O art. 117 reúne o núcleo da regra. A distribuição é mensal, de 2029 a 2096, e ordena os entes pela razão entre o IBS apurado pelas alíquotas de referência, na média dos doze meses anteriores, e a receita média de referência ajustada.")}
{cit("LC 227/2026, art. 117, caput, § 1.º e § 3.º (trechos)", "<strong>Art. 117.</strong> De 1.º de janeiro de 2029 a 31 de dezembro de 2096, o valor retido nos termos do art. 110 desta Lei Complementar será distribuído mensalmente aos Estados, ao Distrito Federal ou aos Municípios com as menores razões entre: I – a média, nos 12 (doze) meses anteriores, da receita mensal do IBS apurada com base nas alíquotas de referência, nos termos do art. 108 desta Lei Complementar, após a aplicação do disposto na alínea “b” do inciso IV do caput do art. 158 da Constituição Federal; e II – a receita média de referência ajustada, calculada nos termos dos §§ 3.º a 6.º deste artigo.", "<strong>§ 1.º</strong> Os recursos [...] serão distribuídos, sequencial e sucessivamente, aos entes federativos com as menores razões [...], de modo que, ao fim da distribuição, para todos os entes que receberem recursos seja observada a mesma razão entre: I – a soma do valor de que trata o inciso I do caput deste artigo com o valor recebido nos termos deste artigo; e II – a receita média de referência ajustada [...].", "<strong>§ 3.º</strong> [...] entende-se por receita média de referência ajustada de cada Estado o menor valor entre: I – a receita média de referência do Estado apurada na forma do art. 115 [...]; e II – 3 (três) vezes o resultado da multiplicação entre: a) a receita média de referência do conjunto dos Estados dividida pela média da população do conjunto dos Estados entre 2019 e 2026; e b) a média da população do Estado entre 2019 e 2026.")}
{tx("Dois outros dispositivos do art. 117 completam o cálculo. O § 2.º corrige, de 2029 a 2033, os meses do ano anterior pela razão entre as alíquotas de referência do ano corrente e do anterior, para que a elevação gradual das alíquotas não reduza artificialmente o numerador. O § 4.º repete para os municípios o limite do § 3.º, e os §§ 5.º e 6.º dão tratamento próprio ao Distrito Federal, que soma as médias per capita das duas esferas.")}

<h2 class="section-heading">3. Metodologia de cálculo</h2>
{sub("3.1 A razão")}
{tx("Seja i um estado, o Distrito Federal ou um município, e a um ano de 2029 em diante. A razão que ordena os entes é o quociente entre o IBS que o ente apura pelo destino e a sua receita média de referência ajustada.")}
{eq(EQ_RAZAO)}
{tx("Nessa expressão, N<sub>i,a</sub> é o numerador e D<sub>i</sub> é o denominador. Uma razão baixa indica que o ente, pelo destino, arrecadaria bem menos do que arrecadava antes da reforma.")}
{sub("3.2 O numerador")}
{tx("O numerador é o IBS total do ente pelo critério do destino, calculado com as alíquotas de referência e líquido da parcela do CGIBS.")}
{eq(EQ_NUM)}
{tx("Em (2), IBS<sup>ref</sup><sub>a</sub> é o IBS nacional apurado com as alíquotas de referência (Estudo 11), γ<sub>a</sub> é a parcela destinada ao CGIBS e φ<sub>i</sub> é o coeficiente de destino pleno do ente, isto é, a fração do IBS que ele receberia se todo o imposto fosse distribuído pelo destino. O fator f<sub>a</sub> traduz a média móvel de doze meses e a correção do § 2.º do art. 117. No mês k do ano a, a janela contém k − 1 meses do ano corrente, que valem um, e 13 − k meses do ano anterior, que valem g<sub>a</sub>, a razão entre as bases de consumo B dos dois anos. Fora de 2029 a 2033, g<sub>a</sub> reflete apenas o crescimento real da base.")}
{tx("Convém observar que o numerador não se limita à fração do IBS que o destino já distribui durante a transição. O art. 117 remete ao IBS apurado com as alíquotas de referência, e por isso o numerador equivale ao que o ente receberia com 100% da arrecadação distribuída pelo destino.")}
{sub("3.3 O coeficiente de destino pleno")}
{tx(f"O coeficiente φ<sub>i</sub> é o insumo mais incerto do numerador, pois o CGIBS o obterá das notas fiscais, que informam o destino de cada operação, e esse dado ainda não existe. Na falta dele, a nota estima a fração do consumo nacional que ocorre em cada estado pela média de três rotas, a Pesquisa de Orçamentos Familiares 2017–2018, o Censo 2022 e a PNAD Contínua, e a multiplica pela parcela do IBS que pertence à esfera estadual. No caso do Paraná, a conta é {ref_pr}: de cada R$ 100 de IBS no país, R$ {n(100*phiE['PR'],2)} caberiam ao governo estadual paranaense. Para os municípios, o consumo é estimado pela renda domiciliar per capita do Censo 2022 e pela elasticidade-renda da POF, e as compras públicas são atribuídas ao ente comprador (Estudos 13 e 17).")}
{sub("3.4 O denominador")}
{tx("O denominador é a receita média de referência R<sub>i</sub>, limitada a três vezes a média per capita da esfera E, estadual ou municipal.")}
{eq(EQ_DEN)}
{tx("Em (3), P<sub>i</sub> é a população média do ente entre 2019 e 2026. O limite impede que um ente com receita muito elevada em relação à sua população absorva uma parcela desproporcional do fundo. No caso do Distrito Federal, o limite soma as médias per capita das duas esferas, como determina o § 6.º do art. 117.")}
{sub("3.5 A distribuição")}
{tx("A distribuição funciona como o enchimento de um reservatório. Começa-se pelo ente de menor razão e eleva-se a razão dele até alcançar a do segundo; os dois sobem juntos até alcançar a do terceiro, e assim por diante, até que o fundo se esgote. Ao final, todos os entes atendidos têm a mesma razão, o nível de equalização L<sub>a</sub>. Quem já estava acima desse nível não recebe nada.")}
{eq(EQ_REP)}
{tx("O nível L<sub>a</sub> é a solução da segunda condição em (4), obtida numericamente. O fundo F<sub>a</sub> decorre dos arts. 109 e 110, em que α<sub>a</sub> é a fração retida pelo critério histórico, 80% de 2029 a 2032 e 90% em 2033.")}
{eq(EQ_FUNDO)}
{tx("O cálculo da lei é mensal. A estimativa o reproduz com doze meses por ano, cada um com o fator correspondente de (2) e o fundo anual, e o resultado de cada ente é a média dos doze repasses.")}
{sub("3.6 Dados e simplificações")}
{tx("A receita média de referência vem do Siconfi (DCA e RREO) e das estimativas de população do IBGE, e o IBS nacional vem da projeção do Estudo 11. Cinco simplificações merecem atenção. A primeira é o coeficiente de destino, que aproxima o que o CGIBS apurará. A segunda é a ausência dos ajustes dos arts. 107 e 108, isto é, da devolução geral do imposto às famílias e dos créditos presumidos, cujo efeito sobre cada ente depende de dados que ainda não existem; supõe-se que afetem os entes de modo semelhante. A terceira é a receita mensal constante dentro de cada ano. A quarta está no denominador: a receita de 2026 é estimada; os valores anuais são deflacionados a reais de 2025, e não corrigidos pela variação nominal da arrecadação, como pede o § 2.º do art. 115; e, entre os fundos estaduais do art. 115, I, “b”, só o do Amazonas está incluído. A quinta é o Distrito Federal, cujo numerador se restringe ao ICMS. Essas simplificações afetam mais o nível exato de entrada dos entes do que a lógica do mecanismo.")}

<h2 class="section-heading">4. Resultados</h2>
{sub("4.1 O fundo e o nível de equalização")}
{tx(f"O fundo cresce com o peso do critério do destino. De R$ {bi(NAC[2029]['ibs_seguro_receita'])} bilhão em 2029, chega a R$ {bi(NAC[2033]['ibs_seguro_receita'])} bilhões em 2033, a preços de 2025, e o nível de equalização passa de {n(nivel[2029],2)} para {n(nivel[2033],2)} (Tabela 1). O número de entes atendidos é estável até 2032, entre {min(len(benef(a)) for a in ANOS[:4])} e {max(len(benef(a)) for a in ANOS[:4])}, e cai para {len(benef(2033))} em 2033.")}
{tit("Tabela 1 – Fundo, nível de equalização e entes atendidos, 2029–2033")}
{tab_fundo()}
<p class="nota-tabela">Valores a preços de 2025. Fonte: elaboração própria a partir de <code>data/seguro-receita-repasses.json</code>.</p>
{tx(f"A queda de 2033 tem uma causa precisa. Nesse ano, o ICMS e o ISS deixam de existir, e o IBS apurado com as alíquotas de referência passa a cobrir toda a base: sua arrecadação é {n(fator_ibs,2)} vezes a de 2032. O fundo, por depender apenas da parcela distribuída pelo destino, cresce {n(100*(fator_fundo-1),0)}%. Os numeradores acompanham a arrecadação, e a razão mediana dos entes sobe {n(fator_razao,1)} vez, ao passo que o nível de equalização, que depende também do tamanho do fundo, sobe {n(100*(fator_nivel-1),0)}%. Como as razões crescem mais do que o nível, {len(saem33)} entes que recebiam em 2032 deixam de receber.")}
{tx("Nos anos seguintes, o número de beneficiários volta a crescer, e o nível de equalização aumenta de forma contínua (Tabela 2). Dois fatores explicam o movimento. O fundo aumenta, porque o critério do destino ganha peso até chegar a 98% em 2077. Ao mesmo tempo, a receita média de referência é fixa em reais de 2025, ao passo que o IBS cresce com a economia, e por isso as razões também sobem. O nível, porém, sobe mais depressa e alcança, um a um, os entes que estavam acima dele.")}
{tit("Tabela 2 – Fundo, nível de equalização e entes atendidos, anos selecionados até 2077")}
{tab_nivel()}
<p class="nota-tabela">Valores a preços de 2025. Fonte: elaboração própria a partir de <code>data/seguro-receita-repasses-longo-prazo.json</code>.</p>
{sub("4.2 Um exemplo: Paraná, Espírito Santo e Amazonas em 2033")}
{tx(f"Os números de 2033 mostram como a regra se aplica a três estados. O IBS nacional apurado com as alíquotas de referência é de R$ {bi(nac33['ibs_bruto'],1)} bilhões, e a dedução do CGIBS (0,2%) o reduz a R$ {bi(ibs_ref33,1)} bilhões. Multiplicado pelo coeficiente de destino pleno de cada estado, esse valor dá o numerador. No Paraná, por exemplo, R$ {bi(ibs_ref33,1)} bilhões × {pc(phiE['PR'],2)} resultariam em R$ {bi(ibs_ref33*phiE['PR'],1)} bilhões; com a média móvel de doze meses, que inclui meses do ano anterior, o numerador é de R$ {bi(pr['numerador'],1)} bilhões.")}
{tit("Tabela 3 – Razão e repasse de três estados em 2033")}
{tab_exemplo()}
<p class="nota-tabela">Valores a preços de 2025. A razão é o IBS pelo destino dividido pela receita média de referência ajustada. Fonte: elaboração própria a partir de <code>data/seguro-receita-repasses.json</code>.</p>
{tx(f"O Paraná tem razão de {n(pr['razao'],2)}. Pelo destino, o governo estadual arrecadaria mais do que arrecadava antes da reforma e, por isso, não recebe nada do fundo. O Espírito Santo tem razão de {n(es['razao'],2)}, que indica perda relativa, mas ainda está acima do nível de equalização de {n(L33,2)}. O Amazonas, com razão de {n(am['razao'],2)}, está abaixo do nível: o fundo eleva a razão do estado até {n(L33,2)}, e a diferença, multiplicada pelo denominador, corresponde ao repasse de R$ {bi(am['repasse'])} bilhão.")}
{sub("4.3 Estados: quando cada um passa a receber")}
{tx(f"Entre os estados, apenas o Amazonas recebe o fundo de 2029 a 2033. O ano de entrada dos demais depende de quando o nível de equalização alcança a razão de cada um, e seis estados chegam a ser atendidos até 2077: Amazonas ({entrada['AM']}), Rondônia ({entrada['RO']}), Mato Grosso ({entrada['MT']}), Espírito Santo ({entrada['ES']}), Mato Grosso do Sul ({entrada['MS']}) e Tocantins ({entrada['TO']}). Os demais, entre os quais o Paraná, não são alcançados nesse horizonte (Tabela 4).")}
{tit("Tabela 4 – Estados ordenados pela razão de 2033 e ano de entrada no fundo")}
{tab_estados()}
<p class="nota-tabela">A razão considera o coeficiente de destino estimado nesta nota; o COMSEFAZ usa o de Gobetti e Monteiro (2023). “Depois de 2077” indica que o estado não é alcançado até esse ano. Fontes: elaboração própria e Nota Técnica do COMSEFAZ, seção 6.4.</p>
{tx(f"A comparação com a Nota Técnica do COMSEFAZ oferece um teste de ordem de grandeza. A nota simula cinco estados e também coloca o Amazonas como o primeiro a ser atendido ({COMSEFAZ['AM']}, contra {entrada['AM']} nesta estimativa). Para o Espírito Santo, as duas projeções coincidem em {entrada['ES']}. Nos demais, as datas diferem em alguns anos: Mato Grosso do Sul entra em {entrada['MS']} (COMSEFAZ: {COMSEFAZ['MS']}), Rondônia em {entrada['RO']} ({COMSEFAZ['RO']}) e Mato Grosso em {entrada['MT']} ({COMSEFAZ['MT']}). As diferenças decorrem, em boa parte, do coeficiente de destino, que cada estimativa calcula por método próprio.")}
{tx(f"O caso do Espírito Santo ilustra a mecânica. Em 2033, a razão capixaba é de {n(es['razao'],2)} e o nível, de {n(L33,2)}, de modo que o estado ainda está longe de ser alcançado. Os dois valores sobem a cada ano, mas o nível sobe mais depressa, porque o fundo cresce mais que a receita do estado. Em {entrada['ES']}, os dois se encontram, e o estado passa a receber (Tabela 5).")}
{tit("Tabela 5 – Razão do Espírito Santo e nível de equalização, anos selecionados")}
{tab_es()}
<p class="nota-tabela">Fonte: elaboração própria a partir de <code>data/seguro-receita-repasses-longo-prazo.json</code>.</p>
{sub("4.4 Beneficiários entre 2029 e 2033")}
{tx(f"Ao todo, {n_benef} entes recebem recursos do Seguro-Receita em pelo menos um dos anos de 2029 a 2033: {len(est_benef)} estado ({', '.join(NOMES[u] for u in est_benef)}) e {n_benef-len(est_benef)} municípios. O acumulado do período é de R$ {bi(tot_acum,1)} bilhões. O Amazonas fica com R$ {bi(acum['UF-AM'],1)} bilhões, ou {pc(acum['UF-AM']/tot_acum,0)} do total, e os dez maiores beneficiários concentram {pc(part_top10,0)}: {lista_nomes([nome_de(i) for i in top10])}.")}
{tx(f"Os municípios beneficiados concentram-se em poucas UFs: {lista_nomes([f'{NOMES[u]} ({k})' for u, k in maiores_uf])}. Entre os maiores beneficiários há polos de serviços, portuários, petrolíferos e de mineração, como São Paulo, Santos, Macaé e Parauapebas. A composição sugere que a regra alcança entes cuja arrecadação de origem é elevada em relação ao consumo local. Em {n_teto} dos {n_benef} entes, o denominador é o limite de três vezes a média per capita, e não a receita de referência, o que indica que boa parte dos beneficiados tem receita per capita elevada. No Espírito Santo, {len(es_mun)} municípios são beneficiados, com os seguintes valores no acumulado do período: {lista_nomes([f'{nm} (R$ {mi(v,0)} milhões)' for nm, v in sorted(es_mun, key=lambda x: -x[1])])}.")}
{tx(f"Permanecem no fundo durante todo o período {len(todos_anos)} entes; os outros {len(saem33)} saem em 2033, pelo motivo exposto na seção 4.1. A Tabela 6 lista todos os beneficiários e admite filtro por nome ou por UF.")}
{tit("Tabela 6 – Entes beneficiados pelo Seguro-Receita, 2029–2033 (R$ milhões de 2025)")}
{tab_benef}
<p class="nota-tabela">A razão de 2033 é o IBS pelo destino dividido pela receita média de referência ajustada. Os municípios do Espírito Santo estão destacados. Fonte: elaboração própria a partir de <code>data/seguro-receita-repasses.json</code>.</p>

<h2 class="section-heading">5. Considerações finais</h2>
{tx(f"O Seguro-Receita funciona como um piso de transição. O fundo atende primeiro os entes de menor razão entre o IBS pelo destino e a receita de referência, e os eleva a um nível comum. Entre 2029 e 2033, o mecanismo alcança cerca de 300 entes, quase todos municípios, e apenas um estado, o Amazonas. Os demais estados só entram quando o nível de equalização, que cresce com o fundo, ultrapassa a sua razão, o que ocorre a partir de {entrada['RO']} no caso de Rondônia e em {entrada['ES']} no do Espírito Santo. A concentração do fundo e a data de entrada de cada estado, mais do que o valor exato dos repasses, são as informações mais robustas desta estimativa.")}
{tx("As estimativas têm limites claros. O coeficiente de destino é aproximado, os ajustes dos arts. 107 e 108 estão ausentes, e a receita média de referência de 2026 ainda não existe. A precisão melhorará quando o CGIBS divulgar os coeficientes e os cálculos de cada ente, o que a lei prevê para agosto de 2027, e a estimativa poderá então ser refeita com esses dados. Enquanto isso, a nota oferece uma referência para que estados e municípios saibam em que posição da regra tendem a estar.")}

<h2 class="section-heading">Referências</h2>
<ul class="refs">
{ref("BRASIL. <strong>Emenda Constitucional n.º 132, de 20 de dezembro de 2023</strong>. Altera o Sistema Tributário Nacional. Brasília: Diário Oficial da União, 2023.")}
{ref("BRASIL. <strong>Lei Complementar n.º 214, de 16 de janeiro de 2025</strong>. Institui o Imposto sobre Bens e Serviços (IBS), a Contribuição Social sobre Bens e Serviços (CBS) e o Imposto Seletivo (IS). Brasília: Diário Oficial da União, 2025.")}
{ref("BRASIL. <strong>Lei Complementar n.º 227, de 2026</strong>. Arts. 106 a 110, 115 a 117. Brasília: Diário Oficial da União, 2026. Transcrição literal em <code>data/legislacao/11_LC227_TITULO_III_DISTRIBUICAO_IBS_ARTS_103_A_131_LITERAL.md</code>.")}
{ref("GOBETTI, S. W. <strong>Nota técnica para o COMSEFAZ sobre a reforma tributária do consumo</strong>. Comitê Nacional de Secretários de Estado da Fazenda, 2026. Seção 6.4.")}
{ref("GOBETTI, S. W.; MONTEIRO, P. K. <strong>Carta de Conjuntura</strong>, n. 60, Nota de Conjuntura 18. Brasília: Instituto de Pesquisa Econômica Aplicada, 28 ago. 2023.")}
{ref("INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. <strong>Pesquisa de Orçamentos Familiares 2017–2018</strong>; <strong>Censo Demográfico 2022</strong>; <strong>Pesquisa Nacional por Amostra de Domicílios Contínua</strong>; <strong>Estimativas da população</strong> (SIDRA, tabelas 4714 e 6579). Rio de Janeiro: IBGE.")}
{ref("SECRETARIA DO TESOURO NACIONAL. <strong>Siconfi</strong>: Declaração de Contas Anuais (Anexo I-C) e Relatório Resumido da Execução Orçamentária (Anexo 3). Brasília: STN.")}
{ref("ARAÚJO, E. R. <strong>Estudo 11</strong>: Quanto será o IBS total do Brasil em 2029–2033? Série histórica e projeção. Disponível em: <a href='/estudos/ibs-projecao-nacional.html'>/estudos/ibs-projecao-nacional.html</a>.")}
{ref("ARAÚJO, E. R. <strong>Estudo 12</strong>: Repasses do Seguro-Receita por ente. Disponível em: <a href='/estudos/seguro-receita-repasses.html'>/estudos/seguro-receita-repasses.html</a>.")}
{ref("ARAÚJO, E. R. <strong>Estudo 13</strong>: Uma estimativa independente do coeficiente de destino do IBS. Disponível em: <a href='/estudos/ibs-destino-pof-censo.html'>/estudos/ibs-destino-pof-censo.html</a>.")}
{ref("ARAÚJO, E. R. <strong>Estudo 17</strong>: Compras governamentais e o IBS. Disponível em: <a href='/estudos/compras-governamentais-ibs.html'>/estudos/compras-governamentais-ibs.html</a>.")}
</ul>
<div class="footnotes">
  <p>Código: cálculo em <code>data/seguro_lei.py</code> e <code>data/build-seguro-receita-repasses.py</code>; esta página em <code>data/build-seguro-receita-lei.py</code>.</p>
</div>

</div>
<footer class="footer">Eduardo Reis Araújo · Políticas públicas orientadas por evidências</footer>
<script src="/js/search.js"></script>
<script>
document.getElementById('filtro').addEventListener('input', function () {{
  const q = this.value.toLowerCase();
  document.querySelectorAll('#tab-benef tbody tr').forEach(tr => {{ tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none'; }});
}});
</script>
</body>
</html>
"""

# cabeçalho de navegação e hero vêm do corpo; reaproveita o <header> do Estudo 12
header = src[src.index("<body>"): src.index('<div class="study-hero">')]
OUT.write_text(head + header + corpo, encoding="utf-8")
print("ok", OUT, n_benef, len(est_benef), entrada)
