#!/usr/bin/env python3
"""
Gera a Nota Técnica do Estudo 11 (série histórica e projeção do IBS total,
Brasil, 2029-2033) em HTML print-ready, a partir de
data/ibs-projecao-nacional.json e data/macro-parametros.json.

O HTML é depois renderizado em PDF via Playwright/Chromium
(scripts/render-nota-tecnica-pdf.js).

Uso:
  python3 data/build-nota-tecnica-pdf.py
  node data/render-nota-tecnica-pdf.js
"""

import json
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
PROJ = json.loads((HERE / "ibs-projecao-nacional.json").read_text())
MACRO = json.loads((HERE / "macro-parametros.json").read_text())
OUTPUT_HTML = HERE / "_nota-tecnica-estudo11.html"

fmtnum = lambda v, d=1: f"{v:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")
fmtbi = lambda v, d=1: fmtnum(v / 1e9, d)
fmtpct = lambda v, d=2: fmtnum(v, d) + "%"
fmtpct_signed = lambda v, d=2: ("+" if v >= 0 else "") + fmtnum(v, d) + "%"


def hist_rows():
    rows = []
    for h in PROJ["historico"]:
        rows.append(f"""<tr>
            <td class="l">{h['ano']}</td>
            <td>{fmtbi(h['icms'])}</td>
            <td>{fmtbi(h['iss'])}</td>
            <td>{fmtbi(h['bolo_nominal'])}</td>
            <td>{fmtbi(h['bolo_real_2025'])}</td>
            <td>{fmtbi(h['pib_nominal'])}</td>
            <td>{fmtpct(h['bolo_pct_pib'])}</td>
            <td class="ref">{h['fonte_icms']}</td>
        </tr>""")
    return "\n".join(rows)


def macro_rows():
    rows = []
    for m in PROJ["macro_path"]:
        rows.append(f"""<tr>
            <td class="l">{m['ano']}</td>
            <td>{fmtpct_signed(m['pib_real_pct']*100)}</td>
            <td>{fmtpct_signed(m['ipca_pct']*100)}</td>
            <td>{fmtpct_signed(m['pib_nominal_pct_crescimento']*100)}</td>
            <td>{fmtbi(m['pib_nominal'])}</td>
            <td class="ref l">{m['fonte']}</td>
        </tr>""")
    return "\n".join(rows)


def proj_rows():
    rows = []
    for p in PROJ["projecao"]:
        rows.append(f"""<tr class="hl">
            <td class="l">{p['ano']}</td>
            <td>{fmtpct(p['fa']*100, 0)}</td>
            <td>{fmtpct(p['sa']*100, 0)}</td>
            <td>{fmtbi(p['icms_iss_residual'])}</td>
            <td>{fmtbi(p['ibs_bruto'])}</td>
            <td>{fmtbi(p['bolo_projetado'])}</td>
            <td>{fmtpct(p['bolo_pct_pib'])}</td>
        </tr>""")
    return "\n".join(rows)


def adct_rows():
    rows = []
    for p in PROJ["projecao"]:
        rows.append(f"<tr><td class='l'>{p['ano']}</td><td>{fmtpct(p['fa']*100,0)}</td><td>{fmtpct(p['sa']*100,0)}</td></tr>")
    return "\n".join(rows)


p2029 = next(r for r in PROJ["projecao"] if r["ano"] == 2029)
p2033 = next(r for r in PROJ["projecao"] if r["ano"] == 2033)
meta = PROJ["_meta"]

HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Nota Técnica: Estudo 11, Série histórica e projeção do IBS total do Brasil, 2029-2033</title>
<style>
    @page {{ size: A4; margin: 22mm 18mm 20mm 18mm; }}
    * {{ box-sizing: border-box; }}
    body {{
        font-family: Georgia, 'Times New Roman', serif;
        color: #1D1D1B;
        font-size: 10.3pt;
        line-height: 1.55;
        margin: 0;
    }}
    .cover {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 240mm;
        page-break-after: always;
        text-align: center;
    }}
    .cover .tag {{
        font-family: Arial, sans-serif;
        font-size: 9pt;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #1A3A5C;
        margin-bottom: 1.2rem;
    }}
    .cover h1 {{
        font-family: Georgia, serif;
        font-size: 24pt;
        font-weight: 700;
        color: #1D1D1B;
        line-height: 1.3;
        margin: 0 auto 1.2rem;
        max-width: 500px;
    }}
    .cover .subtitle {{
        font-family: Arial, sans-serif;
        font-size: 11pt;
        color: #4A4A48;
        max-width: 460px;
        margin: 0 auto 2rem;
        line-height: 1.6;
    }}
    .cover .meta {{
        font-family: Arial, sans-serif;
        font-size: 9pt;
        color: #6E6E6E;
        border-top: 1px solid #E8E5DF;
        padding-top: 1rem;
        max-width: 460px;
        margin: 2rem auto 0;
    }}
    .cover .answer-box {{
        border: 1.5pt solid #1A3A5C;
        background: #F0F4F8;
        border-radius: 6px;
        padding: 1.2rem 1.6rem;
        max-width: 460px;
        margin: 0 auto 1.5rem;
        text-align: left;
    }}
    .cover .answer-label {{
        font-family: Arial, sans-serif;
        font-size: 8pt;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #1A3A5C;
        margin-bottom: 0.4rem;
    }}
    .cover .answer-value {{
        font-family: Georgia, serif;
        font-size: 13pt;
        font-weight: 700;
        color: #1D1D1B;
        line-height: 1.3;
    }}

    h2 {{
        font-family: Arial, sans-serif;
        font-size: 13pt;
        font-weight: 700;
        color: #1A3A5C;
        border-bottom: 1.5pt solid #1A3A5C;
        padding-bottom: 0.3rem;
        margin: 1.8rem 0 0.8rem;
        page-break-after: avoid;
    }}
    h3 {{
        font-family: Arial, sans-serif;
        font-size: 10.5pt;
        font-weight: 700;
        color: #1D1D1B;
        margin: 1.3rem 0 0.5rem;
        page-break-after: avoid;
    }}
    p {{ margin: 0 0 0.7rem; text-align: justify; }}
    .lead {{ font-style: italic; color: #4A4A48; }}
    code {{ font-family: 'Courier New', monospace; font-size: 9pt; background: #F0F0EC; padding: 0.05rem 0.25rem; border-radius: 2px; }}
    ul, ol {{ margin: 0 0 0.7rem; padding-left: 1.4rem; }}
    li {{ margin-bottom: 0.3rem; text-align: justify; }}

    .law-box {{
        border-left: 3pt solid #1A3A5C;
        background: #F7F7F4;
        padding: 0.7rem 1rem;
        margin: 0.7rem 0 1rem;
        font-size: 9.6pt;
    }}
    .law-box .art {{ font-weight: 700; }}

    table {{ width: 100%; border-collapse: collapse; font-size: 8.6pt; margin: 0.6rem 0 1rem; page-break-inside: avoid; }}
    th {{ background: #1A3A5C; color: #fff; font-family: Arial, sans-serif; font-weight: 700; font-size: 8.2pt; padding: 0.35rem 0.4rem; text-align: center; }}
    td {{ border: 0.5pt solid #DADAD5; padding: 0.3rem 0.4rem; text-align: right; font-family: 'Courier New', monospace; font-size: 8.4pt; }}
    td.l {{ text-align: left; font-family: Arial, sans-serif; font-weight: 700; }}
    td.ref {{ color: #6E6E6E; font-family: Arial, sans-serif; font-size: 8pt; text-align: left; }}
    tr:nth-child(even) td {{ background: #FAFAF7; }}
    tr.hl td {{ background: #F0F4F8; font-weight: 700; }}

    .formula-box {{
        background: #F7F7F4;
        border: 0.5pt solid #DADAD5;
        border-radius: 4px;
        padding: 0.8rem 1rem;
        margin: 0.6rem 0 1rem;
        font-family: 'Courier New', monospace;
        font-size: 9pt;
        line-height: 1.7;
    }}

    .footer-note {{
        font-family: Arial, sans-serif;
        font-size: 7.6pt;
        color: #8A8A85;
        border-top: 0.5pt solid #E8E5DF;
        margin-top: 2rem;
        padding-top: 0.5rem;
    }}
    .refs {{ font-size: 9pt; }}
    .refs li {{ margin-bottom: 0.5rem; }}
</style>
</head>
<body>

<div class="cover">
    <div class="tag">Nota Técnica &middot; Estudo 11</div>
    <h1>Série histórica e projeção do IBS total do Brasil, 2029&ndash;2033</h1>
    <p class="subtitle">
        Estimativa do valor total do IBS nacional durante o quinquênio de transição da Reforma
        Tributária, a partir da série histórica de ICMS e ISS (SICONFI, 2015&ndash;2025) e de
        projeções oficiais de crescimento do PIB e inflação.
    </p>
    <div class="answer-box">
        <div class="answer-label">Resposta</div>
        <div class="answer-value">
            IBS bruto nacional: de R$ {fmtbi(p2029['ibs_bruto'])} bi em 2029 a
            R$ {fmtbi(p2033['ibs_bruto'])} bi em 2033 (valores nominais)
        </div>
    </div>
    <div class="meta">
        Eduardo Reis Araújo &bull; www.eduardoreisaraujo.com.br/estudos/ibs-projecao-nacional.html<br>
        Documento gerado em {date.today().strftime('%d/%m/%Y')} &bull; consulta ao Boletim Focus de {meta['data_pesquisa_focus']}
    </div>
</div>

<h2>1. Objetivo</h2>
<p>
    Esta nota técnica responde a uma pergunta objetiva: <strong>quanto será o valor total do
    IBS (Imposto sobre Bens e Serviços) no Brasil, ano a ano, entre 2029 e 2033</strong>,
    o quinquênio de transição definido pela Reforma Tributária do consumo (EC 132/2023). A
    resposta exige combinar três elementos: (i) o tamanho atual do "bolo" tributário que o IBS
    substitui, a soma nacional de ICMS e ISS; (ii) uma projeção de como esse bolo deve
    crescer com a economia, o que depende de premissas explícitas sobre PIB e inflação; e (iii) o
    cronograma constitucional que converte, ano a ano, parte desse bolo de ICMS/ISS em IBS.
</p>

<h2>2. Resumo executivo</h2>
<table>
    <thead><tr><th class="l">Ano</th><th>f<sub>a</sub> (ICMS+ISS residual)</th><th>s<sub>a</sub> (IBS)</th>
    <th>ICMS+ISS residual (R$ bi)</th><th>IBS bruto (R$ bi)</th><th>Total = bolo projetado (R$ bi)</th><th>Bolo / PIB</th></tr></thead>
    <tbody>{proj_rows()}</tbody>
</table>
<p>
    O IBS bruto cresce de {fmtpct(p2029['ibs_bruto']/p2029['bolo_projetado']*100, 0)} do bolo
    tributário em 2029 (início da transição) até 100% em 2033, quando o ICMS e o ISS são extintos
    (ADCT art. 128). Em 2033, o bolo total projetado (ICMS+ISS+IBS) é de
    R$ {fmtbi(p2033['bolo_projetado'])} bi, equivalente a {fmtpct(p2033['bolo_pct_pib'])} do PIB,
    a mesma proporção observada em 2025, por premissa metodológica explicada na Seção 4.
</p>

<h2>3. Fontes de dados</h2>
<h3>3.1 Arrecadação histórica de ICMS e ISS</h3>
<ul>
    <li><strong>ICMS, 2015&ndash;2018:</strong> {meta['fontes']['icms_2015_2018']}, coluna
    "TOTAL (últimos 12 meses)", período 6 (bimestre nov-dez), 27 estados + Distrito Federal.</li>
    <li><strong>ICMS, 2019&ndash;2025:</strong> {meta['fontes']['icms_2019_2025']}.</li>
    <li><strong>ISS, 2015&ndash;2025:</strong> {meta['fontes']['iss_2015_2025']} (cerca de 5.570
    municípios por ano), conta identificada por texto ("Imposto sobre Serviços de Qualquer
    Natureza, ISSQN") porque o código da conta no plano de contas do DCA mudou de esquema mais
    de uma vez entre 2015 e 2025.</li>
</ul>
<p>
    As duas fontes de ICMS convergem: o valor bruto do RREO Anexo 3 coincide com o valor bruto do
    DCA Anexo I-C com diferença inferior a 1%, checado estado a estado. Já a coleta de ISS
    nacional via RREO Anexo 3 apresentou cobertura muito baixa (menos de 15% dos municípios
    respondem a essa conta específica) e foi descartada em favor do DCA, que atinge cobertura de
    90% a 99% dos municípios brasileiros em cada ano.
</p>

<h3>3.2 PIB e inflação</h3>
<ul>
    <li><strong>Histórico (2015&ndash;2025):</strong> {meta['fontes']['pib_ipca_historico']}.</li>
    <li><strong>Projeção 2026&ndash;2030:</strong> {meta['fontes']['projecao_macro_2026_2030']},
    consultado em tempo real via API do Sistema de Expectativas de Mercado do Banco Central
    (data da pesquisa: {meta['data_pesquisa_focus']}).</li>
    <li><strong>Projeção 2031&ndash;2033:</strong> {meta['fontes']['projecao_macro_2031_2033']}.</li>
</ul>

<h3>3.3 Base legal da transição</h3>
<p>{meta['fontes']['cronograma_adct']}.</p>

<h2>4. Metodologia</h2>

<h3>4.1 O bolo histórico: ICMS + ISS, Brasil, 2015&ndash;2025</h3>
<table>
    <thead><tr><th class="l">Ano</th><th>ICMS (R$ bi)</th><th>ISS (R$ bi)</th>
    <th>ICMS+ISS nominal (R$ bi)</th><th>ICMS+ISS real, 2025 (R$ bi)</th>
    <th>PIB nominal (R$ bi)</th><th>ICMS+ISS / PIB</th><th>Fonte ICMS</th></tr></thead>
    <tbody>{hist_rows()}</tbody>
</table>

<h3>4.2 Premissa central: razão bolo/PIB constante</h3>
<p>
    A projeção assume que a razão ICMS+ISS/PIB se mantém constante no nível de 2025
    (&asymp;{fmtpct(meta['razao_bolo_pib_base'])} do PIB) a partir de 2026, ou seja, elasticidade
    unitária do bolo tributário em relação ao PIB nominal. Essa não é uma escolha arbitrária de
    modelagem: é o próprio desenho legal da transição para o IBS.
</p>
<div class="law-box">
    <span class="art">Art. 130, caput, ADCT</span> (incluído pela EC 132/2023): resolução do
    Senado Federal fixará, para todas as esferas federativas, as alíquotas de referência do IBS e
    da CBS, observados a forma de cálculo e os limites previstos em lei complementar, de forma a
    assegurar que a receita de cada ente seja equivalente à dos tributos que estão sendo
    substituídos.<br><br>
    <span class="art">Art. 130, &sect;3&ordm;, IV, ADCT</span>: define a "Receita-Base dos Entes
    Subnacionais" como a receita de Estados, Distrito Federal e Municípios com o IBS (art. 156-A
    da Constituição), apurada <em>como proporção do PIB</em>.
</div>
<p>
    Ou seja: a Constituição não fixa de antemão qual será a alíquota do IBS. Ela é recalculada
    todo ano, por resolução do Senado, para que a arrecadação resultante mantenha a mesma
    proporção do PIB observada na base histórica do tributo que está sendo substituído. É esse
    mecanismo constitucional, e não uma hipótese técnica externa, que justifica projetar o bolo
    tributário como uma fração fixa do PIB projetado.
</p>
<p>
    Entre 2019 e 2025, a razão ICMS+ISS/PIB realizada variou entre
    {fmtpct(meta['faixa_historica_razao_2019_2025']['min'])} e
    {fmtpct(meta['faixa_historica_razao_2019_2025']['max'])}, uma banda de cerca de
    {fmtnum(meta['faixa_historica_razao_2019_2025']['max'] - meta['faixa_historica_razao_2019_2025']['min'])}
    pontos percentuais em torno do valor-base usado aqui. Essa variação histórica é a melhor
    medida disponível da incerteza real em torno da premissa de razão constante: anos de PIB
    atipicamente forte ou fraco, ou mudanças na composição do consumo, podem deslocar a razão
    observada para cima ou para baixo do valor projetado.
</p>

<h3>4.3 Trajetória do PIB nominal, 2026&ndash;2033</h3>
<p>
    O PIB nominal de cada ano é obtido compondo o PIB nominal de 2025 pelo crescimento real e
    pela inflação projetados:
</p>
<div class="formula-box">
    PIB(t) = PIB(t&minus;1) &times; (1 + g<sub>t</sub>) &times; (1 + IPCA<sub>t</sub>)
</div>
<table>
    <thead><tr><th class="l">Ano</th><th>PIB real</th><th>IPCA</th><th>Cresc. nominal do PIB</th>
    <th>PIB nominal projetado (R$ bi)</th><th class="l">Fonte</th></tr></thead>
    <tbody>{macro_rows()}</tbody>
</table>
<p>
    O bolo projetado de cada ano é obtido aplicando a razão constante da Seção 4.2 ao PIB
    projetado: <code>Bolo(t) = (Bolo(2025)/PIB(2025)) &times; PIB(t)</code>.
</p>

<h3>4.4 O cronograma constitucional de transição</h3>
<div class="law-box">
    <span class="art">ADCT art. 128</span>: a alíquota do ICMS e do ISS será reduzida a
    cada ano, de 2029 a 2032, à razão de um décimo, e extinta em 2033.<br>
    <span class="art">ADCT art. 131</span>: no mesmo período, o IBS é implementado
    progressivamente, complementando a fração já extinta do ICMS/ISS.
</div>
<p>
    Traduzindo o cronograma legal em números:
</p>
<table>
    <thead><tr><th class="l">Ano</th><th>f<sub>a</sub> (fração ICMS+ISS residual)</th><th>s<sub>a</sub> = 1&minus;f<sub>a</sub> (fração IBS)</th></tr></thead>
    <tbody>{adct_rows()}</tbody>
</table>

<h3>4.5 Fórmula final</h3>
<div class="formula-box">
    ICMS+ISS residual(a) = Bolo<sub>projetado</sub>(a) &times; f<sub>a</sub><br>
    IBS bruto(a) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= Bolo<sub>projetado</sub>(a) &times; s<sub>a</sub><br>
    Total(a) = ICMS+ISS residual(a) + IBS bruto(a) = Bolo<sub>projetado</sub>(a)
</div>
<p>
    Esta nota técnica trabalha só no agregado nacional, então não entra nos coeficientes de
    redistribuição por unidade federativa (&phi;<sup>neutro</sup>, &phi;<sup>CPT</sup>,
    &phi;<sup>dest</sup>) nem na fração &alpha;<sub>a</sub> que separa o critério histórico do
    critério destino: esses parâmetros determinam <em>como</em> o bolo é dividido entre estados e
    municípios, não o seu <em>tamanho total</em>. No agregado nacional, o valor total de IBS
    depende apenas de f<sub>a</sub>/s<sub>a</sub>.
</p>

<h2>5. Limitações e simplificações</h2>
<ol>
    <li>A razão ICMS+ISS/PIB é mantida constante no nível de 2025 a partir de 2026
    (elasticidade-PIB unitária), sem estimar uma elasticidade histórica separada por regressão.
    Com apenas 11 observações anuais e quebras estruturais conhecidas (pandemia em 2020,
    choque inflacionário em 2021&ndash;2022), uma elasticidade estimada seria pouco robusta. A
    banda histórica da Seção 4.2 serve como medida alternativa de incerteza.</li>
    <li>"IBS bruto" não desconta a taxa de manutenção do Comitê Gestor do IBS (CGIBS, art. 51 LC
    227/2026) nem a retenção do Seguro-Receita (ADCT art. 132), mecanismos que incidem sobre a
    parcela distribuída aos entes pelo critério destino, não sobre o total nacional
    arrecadado.</li>
    <li>Para 2031&ndash;2033, fora do horizonte do Boletim Focus (~5 anos à frente), usa-se a
    projeção da IFI, que reporta uma taxa média para o intervalo 2027&ndash;2035, não ano a ano.
    Os valores de 2,2% (PIB real) e 3,0% (IPCA) são tratados como constantes nos três anos por
    simplificação explícita.</li>
    <li>Os valores são nominais (a preços correntes de cada ano), não deflacionados. A coluna
    "ICMS+ISS real, 2025" na tabela histórica (Seção 4.1) mostra o efeito da correção pela
    inflação apenas para o período já realizado (2015&ndash;2025); a projeção 2026&ndash;2033 não
    reapresenta essa correção porque a inflação projetada já está embutida na composição do PIB
    nominal.</li>
</ol>

<h2>6. Referências</h2>
<ol class="refs">
    <li>BRASIL. <em>Emenda Constitucional nº 132, de 20 de dezembro de 2023.</em> Altera o
    Sistema Tributário Nacional. Diário Oficial da União, 21 dez. 2023.</li>
    <li>BRASIL. <em>Lei Complementar nº 214, de 16 de janeiro de 2025</em> e <em>Lei
    Complementar nº 227, de 2026</em>. Regulamentam a Reforma Tributária sobre o consumo.</li>
    <li>SECRETARIA DO TESOURO NACIONAL. <em>Sistema de Informações Contábeis e Fiscais do Setor
    Público Brasileiro (SICONFI)</em>. RREO Anexo 3 e DCA Anexo I-C. Disponível em:
    apidatalake.tesouro.gov.br/ords/siconfi.</li>
    <li>BANCO CENTRAL DO BRASIL. <em>Sistema Gerenciador de Séries Temporais (SGS)</em>, séries
    1207 (PIB nominal) e 433 (IPCA). Disponível em: api.bcb.gov.br/dados/serie.</li>
    <li>BANCO CENTRAL DO BRASIL. <em>Sistema de Expectativas de Mercado, Boletim Focus</em>,
    projeções anuais de PIB e IPCA. Consulta de {meta['data_pesquisa_focus']} via API Olinda.</li>
    <li>INSTITUIÇÃO FISCAL INDEPENDENTE (IFI), Senado Federal. <em>Relatório de Acompanhamento
    Fiscal (RAF) nº 107</em>, 18 de dezembro de 2025.</li>
</ol>

<div class="footer-note">
    Nota técnica gerada automaticamente a partir de data/ibs-projecao-nacional.json e
    data/macro-parametros.json (repositório do site). Metodologia replicável: scripts de coleta
    e cálculo disponíveis em data/collect-icms-rreo-2015-2018.py,
    data/collect-iss-dca-2015-2018.py, data/collect-macro-focus-ifi.py e
    data/build-ibs-projecao-nacional.py.
</div>

</body>
</html>
"""

OUTPUT_HTML.write_text(HTML)
print(f"Gravado em {OUTPUT_HTML}")
