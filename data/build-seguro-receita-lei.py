#!/usr/bin/env python3
"""
Estudo 18: Seguro-Receita (lei, exemplo numérico, coeficiente de entrada e beneficiários de 2029 a 2033).
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
        .lei-bloco { border-left: 3px solid var(--accent); background: var(--surface); padding: 0.9rem 1.2rem; margin: 1rem 0 0.6rem; font-family: var(--serif); font-size: 0.86rem; line-height: 1.7; color: var(--text); }
        .lei-bloco .lei-rotulo { display: block; font-family: var(--mono); font-size: 0.66rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.35rem; }
        .lei-bloco p { margin: 0.35rem 0; }
        .em-palavras { font-family: var(--serif); font-size: 0.95rem; line-height: 1.75; color: var(--text); margin: 0.4rem 0 1.6rem; }
        .em-palavras .rotulo { font-family: var(--sans); font-weight: 600; font-size: 0.82rem; color: var(--accent); margin-right: 0.3rem; }
        .texto { font-family: var(--serif); font-size: 0.97rem; line-height: 1.78; color: var(--text); margin: 0.7rem 0 1rem; }
        .nota-tabela { font-family: var(--serif); font-size: 0.78rem; color: var(--text-muted); line-height: 1.6; margin: -0.8rem 0 1.5rem; }
        .tag-recebe { color: var(--pos); font-weight: 700; } .tag-nao { color: var(--text-muted); }
        .table-wrap.curta { max-height: none; } .table-wrap.curta .data-table th { white-space: normal; text-align: right; } .table-wrap.curta .data-table th.th-left { text-align: left; }
"""
head = head + extra_css + "    </style>\n</head>\n"
head = re.sub(r"<title>.*?</title>", "<title>Seguro-Receita: a lei, o cálculo e quem recebe entre 2029 e 2033 | Eduardo Reis Araújo</title>", head, flags=re.S)
head = re.sub(r'(<meta name="description" content=")[^"]*(")', r"\1Texto da lei sobre o Seguro-Receita (LC 227/2026, arts. 106 a 117), explicação em linguagem direta, exemplo numérico com Paraná, Espírito Santo e Amazonas, coeficiente de entrada dos estados e lista dos entes beneficiados de 2029 a 2033.\2", head)
head = re.sub(r'(<meta property="og:title" content=")[^"]*(")', r"\1Seguro-Receita: a lei, o cálculo e quem recebe entre 2029 e 2033\2", head)
head = re.sub(r'(<meta property="og:description" content=")[^"]*(")', r"\1A regra do art. 117 da LC 227/2026 explicada passo a passo, com exemplo numérico e a lista de estados e municípios beneficiados.\2", head)
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
est_benef = [uf for uf in NOMES if any(ent[a][f"UF-{uf}"]["repasse"] > 1 for a in ANOS)]
pr, es, am = ent[2033]["UF-PR"], ent[2033]["UF-ES"], ent[2033]["UF-AM"]
L33 = nivel[2033]
num_pr = pr["numerador"]

# ---------------------------------------------------------------- corpo
def lei(rotulo, *paras):
    return "<div class='lei-bloco'><span class='lei-rotulo'>" + rotulo + "</span>" + "".join(f"<p>{p}</p>" for p in paras) + "</div>"

def em(txt): return f"<p class='em-palavras'><span class='rotulo'>Em outras palavras.</span>{txt}</p>"
def tx(txt): return f"<p class='texto'>{txt}</p>"

LEI1 = lei("LC 227/2026, arts. 106 a 108 (trechos)", "<strong>Art. 106.</strong> Compõem a receita inicial de cada ente federativo: I - o valor do IBS extinto e que não tenha sido apropriado como crédito relativo às operações e às importações em que o Estado, o Distrito Federal ou o Município seja destino da operação [...].", "<strong>Art. 107.</strong> O valor da receita inicial de cada ente federativo apurado na forma do art. 106 desta Lei Complementar será ajustado por meio: I - da dedução de valor destinado à devolução geral do IBS às pessoas físicas [...]; e II - quando cabível, de ajuste decorrente da fixação, pelo ente federativo, de alíquota distinta da alíquota de referência da respectiva esfera federativa [...].", "<strong>Art. 108.</strong> O valor da receita de cada ente federativo apurado na forma do art. 107 desta Lei Complementar será ajustado por meio: I - da dedução de valor destinado à concessão de créditos presumidos do IBS [...]; II - do acréscimo de valor correspondente ao IBS extinto incidente sobre as aquisições por produtores rurais e transportadores autônomos não contribuintes [...]; e III - do acréscimo dos valores arrecadados a título de multas e juros de mora [...].")
LEI2 = lei("LC 227/2026, art. 109", "<strong>Art. 109.</strong> De 2029 a 2077, serão retidos do produto da arrecadação do IBS destinada a cada Estado e Município e ao Distrito Federal, nos termos do art. 108 desta Lei Complementar: I - de 2029 a 2032, 80% (oitenta por cento); II - em 2033, 90% (noventa por cento); e III - de 2034 a 2077, percentual correspondente ao aplicado em 2033, reduzido à razão de 1/45 (um quarenta e cinco avos) por ano.")
LEI3 = lei("LC 227/2026, art. 110", "<strong>Art. 110.</strong> De 2029 a 2096, serão retidos do produto da arrecadação do IBS destinada a cada Estado e Município e ao Distrito Federal, nos termos do art. 108, após a retenção de que trata o art. 109 desta Lei Complementar: I - de 2029 a 2077, 5% (cinco por cento); e II - de 2078 a 2096, o percentual a que se refere o inciso I deste caput, reduzido à razão de 1/20 (um vinte avos) por ano.")
LEI4 = lei("LC 227/2026, art. 117, caput e §§ 3º e 4º (trechos)", "<strong>Art. 117.</strong> De 1º de janeiro de 2029 a 31 de dezembro de 2096, o valor retido nos termos do art. 110 desta Lei Complementar será distribuído mensalmente aos Estados, ao Distrito Federal ou aos Municípios com as menores razões entre: I - a média, nos 12 (doze) meses anteriores, da receita mensal do IBS apurada com base nas alíquotas de referência, nos termos do art. 108 desta Lei Complementar, após a aplicação do disposto na alínea \"b\" do inciso IV do caput do art. 158 da Constituição Federal; e II - a receita média de referência ajustada, calculada nos termos dos §§ 3º a 6º deste artigo.", "<strong>§ 3º</strong> Para fins do disposto neste artigo, entende-se por receita média de referência ajustada de cada Estado o menor valor entre: I - a receita média de referência do Estado apurada na forma do art. 115 desta Lei Complementar; e II - 3 (três) vezes o resultado da multiplicação entre: a) a receita média de referência do conjunto dos Estados dividida pela média da população do conjunto dos Estados entre 2019 e 2026; e b) a média da população do Estado entre 2019 e 2026. [O § 4º repete a regra para os Municípios; os §§ 5º e 6º tratam do Distrito Federal.]")
LEI5 = lei("LC 227/2026, art. 117, §§ 1º e 2º", "<strong>§ 1º</strong> Os recursos de que trata o caput deste artigo serão distribuídos, sequencial e sucessivamente, aos entes federativos com as menores razões de que trata o caput deste artigo, de modo que, ao fim da distribuição, para todos os entes que receberem recursos seja observada a mesma razão entre: I - a soma do valor de que trata o inciso I do caput deste artigo com o valor recebido nos termos deste artigo; e II - a receita média de referência ajustada a que se refere o inciso II do caput deste artigo.", "<strong>§ 2º</strong> De 2029 a 2033, para fins do cálculo da média da receita do IBS a que se refere o inciso I do caput deste artigo, os valores da receita relativos a meses do ano-calendário anterior serão multiplicados pela razão entre: I - a alíquota de referência do ano corrente da respectiva esfera da Federação; e II - a alíquota de referência do ano anterior da respectiva esfera da Federação, considerando-se, para o ano de 2028, a alíquota de 0,05% (cinco centésimos por cento).")

corpo = f"""
<div class="study-hero">
  <div class="study-hero-meta">
    <span class="study-hero-tag">Estudo 18</span><span class="study-hero-topic">Reforma Tributária</span>
    <span class="study-hero-topic">Federalismo Fiscal</span><span class="study-hero-topic">Seguro-Receita</span>
    <span class="study-hero-date">Outubro de 2026</span>
  </div>
  <h1>Seguro-Receita: a lei, o cálculo e quem recebe entre 2029 e 2033</h1>
  <p class="lead">O Seguro-Receita compensa, de 2029 a 2096, os estados e os municípios que mais perdem participação relativa na arrecadação com a troca do ICMS e do ISS pelo IBS. Esta página transcreve o texto da lei, explica cada trecho em linguagem direta e mostra, com números, como se chega à razão que decide quem recebe. Ela complementa o <a href="/estudos/seguro-receita-repasses.html">Estudo 12</a>, que permite consultar o repasse de cada um dos entes.</p>
  <p class="study-meta">Estimativa, não o cálculo oficial: o Comitê Gestor do IBS (CGIBS) apurará os valores com dados que ainda não existem. A seção 7 lista as simplificações.</p>
</div>
<div class="study-content">

<h2 class="section-heading">1. A regra em cinco passos</h2>
{tx("A regra do Seguro-Receita está espalhada em vários artigos da Lei Complementar n.º 227/2026. Por isso, esta seção segue a ordem lógica do cálculo, e não a numeração dos artigos. Cada passo traz o texto legal, transcrito literalmente, e uma explicação logo em seguida.")}

<span class="section-label">Passo 1 · Quanto cada ente receberia pelo destino</span>
{LEI1}
{em("O ponto de partida é o IBS que cada estado e cada município receberia se a arrecadação fosse distribuída integralmente pelo destino, isto é, pelo local onde o consumo acontece. Os dois artigos seguintes apenas ajustam esse valor: descontam a devolução geral do imposto às famílias (o <em>cashback</em>) e os créditos presumidos, e somam, por exemplo, as multas e os juros. O resultado é a receita do ente apurada pelo critério do destino, antes de qualquer retenção.")}

<span class="section-label">Passo 2 · A parte que segue o critério histórico</span>
{LEI2}
{em("Durante a transição, a maior parte do IBS não é distribuída pelo destino. Em 2029 a 2032, 80% do que cada ente apuraria pelo destino é retido e redistribuído pelo coeficiente histórico, que reproduz a participação de 2019 a 2026. Em 2033, a retenção sobe para 90%. Só o restante (20% e depois 10%) chega ao ente pelo critério do destino.")}

<span class="section-label">Passo 3 · O fundo do Seguro-Receita</span>
{LEI3}
{em(f"Sobre a parte que sobra depois do passo anterior, retém-se 5%. Esse valor forma o fundo do Seguro-Receita. Como a parte do destino cresce a cada ano, o fundo também cresce: R$ {bi(NAC[2029]['ibs_seguro_receita'])} bilhão em 2029 e R$ {bi(NAC[2033]['ibs_seguro_receita'])} bilhões em 2033, a preços de 2025.")}

<span class="section-label">Passo 4 · A razão que decide quem recebe</span>
{LEI4}
{em("Para cada ente, calcula-se uma razão. O numerador é o IBS que ele apura pelo destino, na média dos últimos doze meses (o valor do passo 1, e não só a fração que o destino já distribui). O denominador é a receita que o ente tinha antes da reforma, a sua receita média de referência, limitada a três vezes a média nacional por habitante da sua esfera, para que um ente muito rico em receita não absorva o fundo. Uma razão baixa significa que o ente, pelo destino, arrecadaria bem menos do que arrecadava antes. Quem tem as menores razões é atendido primeiro.")}

<span class="section-label">Passo 5 · Como o fundo é distribuído</span>
{LEI5}
{em("A distribuição funciona como o enchimento de um reservatório. Começa-se pelo ente de menor razão e eleva-se a razão dele até alcançar a do segundo; os dois sobem juntos até alcançar o terceiro, e assim por diante, até o fundo acabar. Ao final, todos os entes que receberam ficam com a mesma razão, que chamamos aqui de <strong>nível de equalização</strong>. Quem já estava acima desse nível não recebe nada. O § 2º evita que a subida gradual das alíquotas, entre 2029 e 2033, faça os meses do ano anterior parecerem artificialmente pequenos.")}

<h2 class="section-heading">2. O que é o destino pleno e como o aproximamos</h2>
{tx(f"A lei fala em IBS apurado pelo critério do destino. A ideia é simples: se todo o IBS do país fosse distribuído conforme o local do consumo, sem regra de transição, cada estado e cada município receberia uma fração do total. Essa fração é o que este estudo chama de <strong>coeficiente de destino pleno</strong>, ou seja, o IBS que o ente receberia com 100% da arrecadação distribuída pelo destino, dividido pelo IBS total. Para o governo do Paraná, a estimativa é de {pc(phiE['PR'],2)}: de cada R$ 100 de IBS no país, R$ {n(100*phiE['PR'],2)} caberiam ao governo estadual paranaense.")}
{tx(f"O cálculo desse coeficiente tem duas etapas. Primeiro, estima-se a fração do consumo nacional que ocorre em cada estado; para o Paraná, {pc(phi_cons['PR'],1)}. Depois, aplica-se a essa fração a parcela do IBS que pertence à esfera estadual, {pc(frac_e,1)}, o restante cabendo aos municípios. O produto é o coeficiente do governo estadual: {pc(phi_cons['PR'],2)} × {pc(frac_e,1)} = {pc(phiE['PR'],2)}.")}
{tx("Quando o IBS estiver em operação, o CGIBS obterá esse coeficiente diretamente das notas fiscais, que informam onde cada operação foi destinada. Como esse dado ainda não existe, este estudo usa uma aproximação: estima a fração do consumo de cada estado com a Pesquisa de Orçamentos Familiares, o Censo de 2022 e a PNAD Contínua, e inclui as compras públicas, cujo IBS pertence ao ente comprador (Estudo 13 e Estudo 17). O coeficiente, portanto, é uma estimativa, e os valores que seguem devem ser lidos como ordem de grandeza, não como previsão do que o CGIBS apurará.")}

<h2 class="section-heading">3. Um exemplo completo: Paraná, Espírito Santo e Amazonas em 2033</h2>
{tx(f"Os números de 2033 mostram como a regra se aplica. O IBS nacional apurado com as alíquotas de referência é de R$ {bi(nac33['ibs_bruto'],1)} bilhões, e a dedução para o CGIBS (0,2%) reduz esse valor a R$ {bi(ibs_ref33,1)} bilhões. Multiplicando esse total pelo coeficiente de destino pleno do governo estadual, obtém-se o numerador da razão. No caso do Paraná, R$ {bi(ibs_ref33,1)} bilhões × {pc(phiE['PR'],2)} resultariam em R$ {bi(ibs_ref33*phiE['PR'],1)} bilhões; com a média móvel de doze meses, que inclui meses do ano anterior, o numerador é de R$ {bi(pr['numerador'],1)} bilhões.")}
{tab_exemplo()}
<p class="nota-tabela">Valores a preços de 2025. A razão é o IBS pelo destino dividido pela receita média de referência ajustada; o nível de equalização é a razão que o fundo consegue garantir aos entes beneficiados no ano. Fonte: modelo do site, <code>data/seguro-receita-repasses.json</code>.</p>
{tx(f"O Paraná tem razão de {n(pr['razao'],2)}: pelo destino, o governo estadual arrecadaria cerca de 20% a mais do que arrecadava antes, e por isso não recebe nada do fundo. O Espírito Santo tem razão de {n(es['razao'],2)}, inferior a 1, o que indica perda relativa, mas ainda acima do nível de equalização de {n(L33,2)}. O Amazonas, com razão de {n(am['razao'],2)}, está abaixo do nível: o fundo eleva a razão do estado até {n(L33,2)}, e a diferença, multiplicada pela receita média de referência, corresponde ao repasse de R$ {bi(am['repasse'])} bilhões.")}
<div class="meto-formula-box">$$\\text{{repasse}} = \\max\\left(0,\; \\text{{nível}} \\times \\text{{receita média de referência ajustada}} - \\text{{IBS pelo destino}}\\right)$$</div>

<h2 class="section-heading">4. O coeficiente de entrada: o nível de equalização</h2>
{tx(f"Um ente passa a receber quando a sua razão fica abaixo do nível de equalização do ano. Esse nível não é fixado na lei; resulta do tamanho do fundo e da distribuição das razões entre os {NENTES} entes. Quanto maior o fundo, mais alto o nível e mais entes são alcançados. O número de beneficiários cai de 2032 para 2033 porque as razões de todos os entes dão um salto quando o IBS passa a cobrir toda a base, e o fundo, em proporção, não acompanha o salto; nas décadas seguintes, o número volta a crescer.")}
{tab_nivel()}
<p class="nota-tabela">Valores a preços de 2025. Fonte: <code>data/seguro-receita-repasses-longo-prazo.json</code>.</p>
{tx("O nível sobe ao longo do tempo por dois motivos. O fundo cresce, porque a parte do IBS distribuída pelo destino aumenta até alcançar 98% em 2077. Ao mesmo tempo, a receita média de referência é fixa em reais de 2025, ao passo que o IBS cresce com a economia, e por isso a razão de todos os entes também sobe. O nível, porém, sobe mais depressa do que a razão dos entes que ainda não recebem, e é essa diferença que os faz entrar, um a um.")}

<h2 class="section-heading">5. Estados: quando entram e quem entra</h2>
{tx(f"Entre os estados, apenas o Amazonas é beneficiado de 2029 a 2033, e o ano de entrada dos demais depende de quando o nível de equalização alcança a razão de cada um. A tabela ordena os estados pela razão de 2033: os primeiros são os mais próximos de receber. Na última coluna, a nota técnica do Comsefaz traz a sua própria simulação para cinco estados; o Amazonas é o primeiro nas duas, e o Espírito Santo entra em {entrada['ES']} nas duas.")}
{tab_estados()}
<p class="nota-tabela">A razão considera o coeficiente de destino estimado neste estudo; a nota do Comsefaz usa o coeficiente de Gobetti e Monteiro (2023). Os estados com \"depois de 2077\" não são alcançados até esse ano. Fonte: modelo do site e Nota Técnica do Comsefaz, seção 6.4.</p>
<span class="section-label">Exemplo: Espírito Santo</span>
{tx(f"O caso do Espírito Santo ilustra a mecânica. Em 2033, a razão capixaba é de {n(es['razao'],2)} e o nível de equalização, de {n(L33,2)}, de modo que o estado ainda está longe de ser alcançado. Os dois valores sobem a cada ano, mas o nível sobe mais depressa, porque o fundo cresce mais que a receita do estado. Em {entrada['ES']}, os dois se encontram, e o Espírito Santo passa a receber.")}
{tab_es()}
<p class="nota-tabela">Fonte: <code>data/seguro-receita-repasses-longo-prazo.json</code>.</p>

<h2 class="section-heading">6. Quem recebe entre 2029 e 2033</h2>
{tx(f"Ao todo, {n_benef} entes recebem recursos do Seguro-Receita em pelo menos um dos anos de 2029 a 2033: {len(est_benef)} estado ({', '.join(NOMES[u] for u in est_benef)}) e {n_benef-len(est_benef)} municípios. A tabela lista todos, ordenados pelo repasse acumulado, e permite filtrar por nome ou por UF. Os municípios do Espírito Santo estão destacados.")}
{tab_benef}
<p class="nota-tabela">Valores em R$ milhões de 2025. A razão de 2033 é o IBS pelo destino dividido pela receita média de referência ajustada. Fonte: <code>data/seguro-receita-repasses.json</code>.</p>

<h2 class="section-heading">7. O que esta estimativa simplifica</h2>
{tx("Quatro simplificações merecem atenção. A primeira é o coeficiente de destino, que aproxima o que o CGIBS apurará com a distribuição do consumo estimada pela POF, pelo Censo e pela PNAD Contínua. A segunda é a ausência dos ajustes dos arts. 107 e 108: a devolução geral do IBS e os créditos presumidos têm percentuais que o CGIBS ainda não fixou, mas que serão iguais para todos os entes e reduzirão os numeradores na mesma proporção. A terceira é o cálculo mensal com receita constante dentro de cada ano, com a correção do § 2º. A quarta é o denominador, que usa a receita média de 2019 a 2026 com 2026 estimado e, entre os fundos estaduais do art. 115, apenas o do Amazonas.")}
{tx("Essas simplificações afetam mais o nível exato de entrada do que a lógica do mecanismo. O desenho da regra, que atende primeiro os entes de menor razão até um nível comum, aparece com clareza nos números acima e independe delas.")}

<div class="footnotes">
  <p><strong>Fontes e notas:</strong></p>
  <p>1. Texto legal: Lei Complementar n.º 227/2026, arts. 106 a 110 e 117; ADCT, art. 132 (EC 132/2023). Transcrição literal em <code>data/legislacao/11_LC227_TITULO_III_DISTRIBUICAO_IBS_ARTS_103_A_131_LITERAL.md</code>.</p>
  <p>2. Cálculo: <code>data/seguro_lei.py</code> e <code>data/build-seguro-receita-repasses.py</code>; esta página: <code>data/build-seguro-receita-lei.py</code>.</p>
  <p>3. Coeficiente de destino: <a href="/estudos/ibs-destino-pof-censo.html">Estudo 13</a> e <a href="/estudos/compras-governamentais-ibs.html">Estudo 17</a>. Projeção nacional do IBS: <a href="/estudos/ibs-projecao-nacional.html">Estudo 11</a>.</p>
  <p>4. Comparação externa: Nota Técnica do Comsefaz sobre a reforma tributária, seção 6.4 (compensação de perdas pelo Seguro-Receita).</p>
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
