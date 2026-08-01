#!/usr/bin/env python3
"""
Gera a Nota Técnica do Estudo 11 (série histórica e projeção do IBS total,
Brasil, 2029-2033) em HTML print-ready, a partir de
data/ibs-projecao-nacional.json e data/macro-parametros.json.

O gráfico de trajetória (histórico + projeção) é renderizado como imagem
estática via matplotlib, já que o PDF não roda o Chart.js usado na página
web. O HTML é depois renderizado em PDF via Playwright/Chromium
(scripts/render-nota-tecnica-pdf.js).

Depende de matplotlib (pip install matplotlib).

Uso:
  python3 data/build-nota-tecnica-pdf.py
  node data/render-nota-tecnica-pdf.js
"""

import base64
import json
from datetime import date
from io import BytesIO
from pathlib import Path

HERE = Path(__file__).parent
PROJ = json.loads((HERE / "ibs-projecao-nacional.json").read_text())
MACRO = json.loads((HERE / "macro-parametros.json").read_text())
OUTPUT_HTML = HERE / "_nota-tecnica-estudo11.html"

fmtnum = lambda v, d=1: f"{v:,.{d}f}".replace(",", "§").replace(".", ",").replace("§", ".")
fmtbi = lambda v, d=1: fmtnum(v / 1e9, d)
fmtpct = lambda v, d=2: fmtnum(v, d) + "%"
fmtpct_signed = lambda v, d=2: ("+" if v >= 0 else "") + fmtnum(v, d) + "%"


def trajetoria_chart_data_uri():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    historico = PROJ["historico"]
    macro_path = PROJ["macro_path"]
    projecao = PROJ["projecao"]
    razao = PROJ["_meta"]["razao_bolo_pib_base"] / 100
    proj_por_ano = {p["ano"]: p["bolo_projetado"] for p in projecao}

    anos_real = [h["ano"] for h in historico]
    valores_real = [h["bolo_nominal"] / 1e9 for h in historico]

    # Linha do total projetado: até 2029 (depois disso, o total se abre em duas linhas).
    ultimo = historico[-1]
    anos_proj = [ultimo["ano"]] + [m["ano"] for m in macro_path if m["ano"] <= 2029]
    valores_proj = [ultimo["bolo_nominal"] / 1e9] + [
        (proj_por_ano.get(m["ano"], razao * m["pib_nominal"])) / 1e9
        for m in macro_path if m["ano"] <= 2029
    ]

    # A partir de 2029, o cronograma do ADCT art. 128 abre o total em duas trajetórias opostas.
    anos_residual = [p["ano"] for p in projecao]
    valores_residual = [p["icms_iss_residual"] / 1e9 for p in projecao]
    valores_ibs = [p["ibs_bruto"] / 1e9 for p in projecao]

    fig, ax = plt.subplots(figsize=(7.0, 2.9), dpi=150)
    ax.plot(anos_real, valores_real, color="#1A3A5C", linewidth=2.2, marker="o", markersize=3.5, label="Realizado (2013–2025)")
    ax.plot(anos_proj, valores_proj, color="#2a78d6", linewidth=2.2, linestyle=(0, (5, 3)), marker="o", markersize=3.5, label="Projetado, total (2026–2029)")
    ax.plot(anos_residual, valores_residual, color="#b03a2e", linewidth=2.2, marker="o", markersize=3.5, label="ICMS+ISS residual (2029–2033)")
    ax.fill_between(anos_residual, valores_residual, 0, color="#b03a2e", alpha=0.08)
    ax.plot(anos_residual, valores_ibs, color="#1e8449", linewidth=2.2, marker="o", markersize=3.5, label="IBS bruto (2029–2033)")
    ax.fill_between(anos_residual, valores_ibs, 0, color="#1e8449", alpha=0.08)

    ax.set_ylabel("R$ bi", fontsize=9)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
    ax.tick_params(labelsize=8.5, colors="#4A4A48")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#DADAD5")
    ax.grid(axis="y", color="#E8E5DF", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=7.5, frameon=False, ncol=2)
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("ascii")


def transicao_chart_data_uri():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    projecao = PROJ["projecao"]
    anos = [p["ano"] for p in projecao]
    residual = [p["icms_iss_residual"] / 1e9 for p in projecao]
    ibs = [p["ibs_bruto"] / 1e9 for p in projecao]

    fig, ax = plt.subplots(figsize=(7.0, 2.9), dpi=150)
    ax.plot(anos, residual, color="#b03a2e", linewidth=2.2, marker="o", markersize=4, label="ICMS+ISS residual")
    ax.fill_between(anos, residual, 0, color="#b03a2e", alpha=0.10)
    ax.plot(anos, ibs, color="#1e8449", linewidth=2.2, marker="o", markersize=4, label="IBS bruto")
    ax.fill_between(anos, ibs, 0, color="#1e8449", alpha=0.10)

    ax.set_ylabel("R$ bi", fontsize=9)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    ax.xaxis.set_major_locator(mticker.MultipleLocator(1))
    ax.tick_params(labelsize=8.5, colors="#4A4A48")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#DADAD5")
    ax.grid(axis="y", color="#E8E5DF", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.legend(loc="center left", fontsize=8.5, frameon=False)
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("ascii")


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


def referencia_rows():
    r = PROJ["_meta"]["receita_referencia"]
    rows = []
    for a in r["anos"]:
        rows.append(f"""<tr>
            <td class="l">{a['ano']}</td>
            <td>{fmtbi(a['bolo'])}</td>
            <td>{fmtbi(a['pib'])}</td>
            <td>{fmtpct(a['razao_pct'])}</td>
            <td class="ref l">{a['status']}</td>
        </tr>""")
    rows.append(f"""<tr class="hl">
        <td class="l" colspan="3">Média 2024&ndash;2026 (usada na projeção)</td>
        <td colspan="2">{fmtpct(r['razao_media_pct'])}</td>
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

    .chart-block {{ margin: 0.8rem 0 1.2rem; page-break-inside: avoid; }}
    .chart-img {{ width: 100%; display: block; }}
    .chart-caption {{ font-family: Arial, sans-serif; font-size: 8pt; color: #6E6E6E; text-align: center; margin: 0.3rem 0 0; }}
</style>
</head>
<body>

<div class="cover">
    <div class="tag">Nota Técnica &middot; Estudo 11</div>
    <h1>Série histórica e projeção do IBS total do Brasil, 2029&ndash;2033</h1>
    <p class="subtitle">
        Estimativa do valor total do IBS nacional durante o quinquênio de transição da Reforma
        Tributária, a partir da série histórica de ICMS e ISS (SICONFI, 2013&ndash;2025) e de
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
    resposta exige combinar três elementos: (i) qual é a arrecadação total de ICMS e ISS hoje, o
    tributo que o IBS substitui; (ii) uma projeção de como essa arrecadação deve
    crescer com a economia, o que depende de premissas explícitas sobre PIB e inflação; e (iii) o
    cronograma constitucional que converte, ano a ano, parte dessa arrecadação de ICMS/ISS em IBS.
</p>

<h2>2. Resumo executivo</h2>
<table>
    <thead><tr><th class="l">Ano</th><th>f<sub>a</sub> (ICMS+ISS residual)</th><th>s<sub>a</sub> (IBS)</th>
    <th>ICMS+ISS residual (R$ bi)</th><th>IBS bruto (R$ bi)</th><th>Total = receita projetada (R$ bi)</th><th>Carga tributária (% PIB)</th></tr></thead>
    <tbody>{proj_rows()}</tbody>
</table>
<p>
    O IBS bruto cresce de {fmtpct(p2029['ibs_bruto']/p2029['bolo_projetado']*100, 0)} da
    arrecadação total em 2029 (início da transição) até 100% em 2033, quando o ICMS e o ISS são
    extintos (ADCT art. 128). Em 2033, a arrecadação total projetada (ICMS+ISS+IBS) é de
    R$ {fmtbi(p2033['bolo_projetado'])} bi, equivalente a {fmtpct(p2033['bolo_pct_pib'])} do PIB,
    a mesma proporção média observada em 2024-2026 (LC 214/2025, arts. 361 a 365), explicada na
    Seção 4.
</p>
<div class="chart-block">
    <img class="chart-img" src="{trajetoria_chart_data_uri()}" alt="Arrecadação de ICMS+ISS, Brasil: realizado 2013-2025, projetado 2026-2029 e a abertura em ICMS+ISS residual e IBS bruto entre 2029 e 2033">
    <p class="chart-caption">Arrecadação de ICMS+ISS, Brasil (R$ bi, nominal). A linha tracejada,
    a partir de 2026, é a projeção do total (Seção 4.2). Em 2029 essa linha se abre em duas: o
    cronograma do ADCT art. 128 converte parte da arrecadação de ICMS/ISS em IBS ano a ano, até a
    extinção do ICMS e do ISS em 2033 (Seção 4.4).</p>
</div>

<h2>3. Fontes de dados</h2>
<h3>3.1 Arrecadação histórica de ICMS e ISS</h3>
<ul>
    <li><strong>ICMS, 2013&ndash;2025:</strong> {meta['fontes']['icms_2013_2025']}, conta
    identificada pelo texto da definição constitucional do imposto ("Operações Relativas à
    Circulação de Mercadorias..."), não pelo código, que muda de esquema ao longo dos anos,
    excluindo o adicional do Fundo Estadual de Combate à Pobreza, multas e dívida ativa, 27
    estados + Distrito Federal.</li>
    <li><strong>ISS, 2013&ndash;2025:</strong> {meta['fontes']['iss_2013_2025']} (cerca de 5.570
    municípios por ano), conta identificada por texto ("Imposto sobre Serviços de Qualquer
    Natureza, ISSQN") porque o código da conta no plano de contas do DCA mudou de esquema mais
    de uma vez entre 2013 e 2025.</li>
</ul>
<p>
    O SICONFI não publica o DCA Anexo I-C para nenhum dos dois tributos antes de 2013. Para
    2015&ndash;2018, o ICMS do DCA foi comparado com o RREO Anexo 3, outro demonstrativo do
    SICONFI: a diferença fica sempre abaixo de 1,3%, checado estado a estado, o que confirma que
    os dois demonstrativos captam a mesma arrecadação. O RREO não é usado para o ISS porque
    apresenta cobertura municipal muito baixa (menos de 15% dos municípios respondem a essa conta
    específica nesse demonstrativo); o DCA atinge cobertura de 90% a 99% dos municípios
    brasileiros em cada ano.
</p>

<h3>3.2 PIB e inflação</h3>
<ul>
    <li><strong>Histórico (2013&ndash;2025):</strong> {meta['fontes']['pib_ipca_historico']}.</li>
    <li><strong>Projeção 2026&ndash;2030:</strong> {meta['fontes']['projecao_macro_2026_2030']},
    consultado em tempo real via API do Sistema de Expectativas de Mercado do Banco Central
    (data da pesquisa: {meta['data_pesquisa_focus']}).</li>
    <li><strong>Projeção 2031&ndash;2033:</strong> {meta['fontes']['projecao_macro_2031_2033']}.</li>
</ul>

<h3>3.3 Base legal da transição</h3>
<p>{meta['fontes']['cronograma_adct']}.</p>

<h2>4. Metodologia</h2>

<h3>4.1 A arrecadação histórica: ICMS + ISS, Brasil, 2013&ndash;2025</h3>
<table>
    <thead><tr><th class="l">Ano</th><th>ICMS (R$ bi)</th><th>ISS (R$ bi)</th>
    <th>ICMS+ISS nominal (R$ bi)</th><th>ICMS+ISS real, 2025 (R$ bi)</th>
    <th>PIB nominal (R$ bi)</th><th>ICMS+ISS / PIB</th><th>Fonte ICMS</th></tr></thead>
    <tbody>{hist_rows()}</tbody>
</table>

<h3>4.2 Premissa central: o período de referência que a lei manda usar</h3>
<p>
    A projeção assume que a arrecadação de ICMS e ISS, medida como proporção do PIB (a "carga
    tributária"), se mantém constante a partir de 2027 no nível médio dos anos de 2024, 2025 e
    2026 (&asymp;{fmtpct(meta['razao_bolo_pib_base'])} do PIB). Não é uma média escolhida por
    conveniência: é o período de três anos que a própria lei da reforma manda usar para calibrar
    a alíquota do IBS, ano a ano, durante toda a transição.
</p>
<div class="law-box">
    <span class="art">LC 214/2025, arts. 361 a 365</span> (redação dada pela LC 227/2026): para
    cada ano da transição (2029 a 2033), a alíquota de referência do IBS estadual e municipal é
    fixada de forma a equivaler à <em>média da razão entre a receita de referência (ICMS+ISS) e o
    PIB nos anos de 2024 a 2026</em>. O mesmo período de três anos vale para todos os cinco anos
    da transição: a lei não recalcula essa base a cada ano.
</div>
<p>
    Isso substitui a leitura mais simples de que bastaria olhar para o último ano fechado (2025).
    A tabela abaixo mostra os três anos que compõem a média e o resultado usado na projeção:
</p>
<table>
    <thead><tr><th class="l">Ano</th><th>ICMS+ISS (R$ bi)</th><th>PIB (R$ bi)</th>
    <th>Razão</th><th class="l">Situação</th></tr></thead>
    <tbody>{referencia_rows()}</tbody>
</table>
<p>
    Existe um segundo mecanismo na lei, com um período histórico bem diferente, que é fácil de
    confundir com este: o <strong>Teto de Referência</strong> do art. 130, &sect;4&ordm; e
    &sect;5&ordm;, do ADCT, calculado sobre a média de 2012 a 2021. Esse teto não fixa a alíquota
    ano a ano; funciona como uma trava de segurança que só entra em ação se a receita observada
    superar esse teto histórico mais amplo: no caso do IBS, se a média de 2029&ndash;2033 da soma
    CBS+Imposto Seletivo+IBS superar a média 2012&ndash;2021 da soma
    IPI+ICMS+ISS+PIS/Cofins+IOF-seguros. Isso não altera os valores projetados aqui para
    2029&ndash;2033, por dois motivos: (i) mesmo que o teto seja ultrapassado, a redução da
    alíquota só entra em vigor em 2035, dois anos depois do fim desta projeção; e (ii) o teto
    compara o sistema novo e o antigo por inteiro, somando o lado federal (CBS, Imposto Seletivo,
    PIS/Cofins, IPI, IOF-seguros) ao lado subnacional (IBS, ICMS, ISS), enquanto esta nota técnica
    modela só o lado subnacional. Simular esse teto exigiria dados federais fora do escopo deste
    estudo. Por isso ele é citado aqui como contexto, mas não entra na conta acima.
</p>
<p>
    2026 ainda não fechou: a razão desse ano usa o ICMS+ISS do RREO (últimos 12 meses até abril
    de 2026) sobre o PIB projetado pelo Boletim Focus para o ano, uma estimativa preliminar que
    será atualizada para o dado fechado (DCA) assim que estiver disponível.
</p>
<p>
    Na prática, isso significa que o legislador não fixou de antemão qual será a alíquota do IBS:
    ela será calculada pelo Senado para que a arrecadação resultante mantenha, em cada ano da
    transição, a mesma proporção do PIB medida nessa base histórica de três anos. É esse
    mecanismo legal, e não uma hipótese técnica externa, que justifica projetar a arrecadação de
    ICMS e ISS como uma fração fixa do PIB projetado.
</p>
<p>
    Entre 2019 e 2025, a razão ICMS+ISS/PIB realizada variou entre
    {fmtpct(meta['faixa_historica_razao_2019_2025']['min'])} e
    {fmtpct(meta['faixa_historica_razao_2019_2025']['max'])}, uma banda de cerca de
    {fmtnum(meta['faixa_historica_razao_2019_2025']['max'] - meta['faixa_historica_razao_2019_2025']['min'])}
    pontos percentuais em torno do valor-base usado aqui. Essa variação histórica é a melhor
    medida disponível da incerteza real em torno da premissa de carga tributária constante: anos
    de PIB atipicamente forte ou fraco, ou mudanças na composição do consumo, podem deslocar a
    arrecadação observada para cima ou para baixo do valor projetado.
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
    A arrecadação projetada de cada ano é obtida aplicando a razão de referência (a média
    2024-2026 da Seção 4.2) ao PIB projetado: <code>Receita(t) = Razão(2024-2026) &times;
    PIB(t)</code>.
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
<div class="chart-block">
    <img class="chart-img" src="{transicao_chart_data_uri()}" alt="ICMS+ISS residual encolhendo e IBS bruto crescendo, Brasil, 2029-2033">
    <p class="chart-caption">ICMS+ISS residual vs. IBS bruto, Brasil (R$ bi, nominal). As duas linhas partem de
    pontos opostos em 2029 e se afastam ano a ano até a extinção do ICMS/ISS em 2033: em cada ano, a soma das
    duas é a arrecadação total projetada (Seção 4.5).</p>
</div>

<h3>4.5 Fórmula final</h3>
<div class="formula-box">
    ICMS+ISS residual(a) = Receita<sub>projetada</sub>(a) &times; f<sub>a</sub><br>
    IBS bruto(a) &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= Receita<sub>projetada</sub>(a) &times; s<sub>a</sub><br>
    Total(a) = ICMS+ISS residual(a) + IBS bruto(a) = Receita<sub>projetada</sub>(a)
</div>
<p>
    Esta nota técnica trabalha só no agregado nacional, então não entra nos coeficientes de
    redistribuição por unidade federativa (&phi;<sup>neutro</sup>, &phi;<sup>CPT</sup>,
    &phi;<sup>dest</sup>) nem na fração &alpha;<sub>a</sub> que separa o critério histórico do
    critério destino: esses parâmetros determinam <em>como</em> a arrecadação é dividida entre estados e
    municípios, não o seu <em>tamanho total</em>. No agregado nacional, o valor total de IBS
    depende apenas de f<sub>a</sub>/s<sub>a</sub>.
</p>

<h2>5. Limitações e simplificações</h2>
<ol>
    <li>A razão ICMS+ISS/PIB (a carga tributária) é mantida constante na média de 2024-2026 a
    partir de 2027, ou seja, presume-se que a arrecadação cresce sempre na mesma proporção do
    PIB medida nesse período de referência, sem estimar por métodos estatísticos se ela
    historicamente cresceu mais rápido ou mais devagar que a economia. Com apenas 13 observações
    anuais e quebras estruturais conhecidas (pandemia em 2020, choque inflacionário em
    2021&ndash;2022), uma estimativa desse tipo seria pouco robusta. A banda histórica da Seção
    4.2 serve como medida alternativa de incerteza.</li>
    <li>O dado de 2026 usado na média de referência é uma estimativa preliminar (RREO, últimos 12
    meses até abril de 2026, sobre o PIB projetado pelo Focus), a ser substituída pelo dado
    fechado (DCA) assim que disponível.</li>
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
    inflação apenas para o período já realizado (2013&ndash;2025); a projeção 2026&ndash;2033 não
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
    e cálculo disponíveis em data/collect-icms-dca-2013-2018.py,
    data/collect-iss-dca-2013-2014.py, data/collect-iss-dca-2015-2018.py,
    data/collect-macro-focus-ifi.py e data/build-ibs-projecao-nacional.py.
</div>

</body>
</html>
"""

OUTPUT_HTML.write_text(HTML)
print(f"Gravado em {OUTPUT_HTML}")
