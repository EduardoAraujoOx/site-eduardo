#!/usr/bin/env python3
"""
Coleta a arrecadacao do Poder Executivo do ES por Fonte de recurso, 2023-2026,
a partir da base declaratoria do TCE-ES (CidadES - Prestacao de Contas
Mensal), nao do microdado bruto do SIGEFES usado para despesas.

Por que essa fonte e nao o microdado de Receitas do dados.es.gov.br: o
microdado bruto (Receitas-<ano>.csv, ~1GB/ano, mesmo esquema das Despesas)
registra eventos de lancamento (TipoArquivo=ARRECADADA-BRUTA/LIQUIDA/DEDUCAO,
RECOLHIDA-BRUTA, TipoLancamento C/D) sem um dicionario de dados atualizado
que explique essas fases -- reproduziria o mesmo risco de erro de
interpretacao que ja aconteceu (e foi corrigido) do lado da despesa. A base
do TCE-ES ja vem consolidada por (UG, classificacao, fonte, mes), com
"PrevisaoInicial"/"PrevisaoAtualizada"/"Arrecadada" nomeados sem ambiguidade,
e e' declaratoria e homologada (Anexo IV da IN 68/2020), nao um extrato
bruto de sistema.

Duas armadilhas no arquivo do TCE-ES, verificadas empiricamente antes de
implementar:

1. PrevisaoInicial e PrevisaoAtualizada sao ESTOQUE (o valor da previsao
   vigente, repetido em cada linha mensal daquela combinacao UG/fonte/
   classificacao) -- somar direto por varios meses infla o total pelo
   numero de meses. A leitura correta e pegar, para cada combinacao, o
   valor do ULTIMO mes disponivel no corte, nunca somar entre meses.
2. Arrecadada e FLUXO (o valor daquele mes especificamente) -- essa sim
   soma corretamente entre meses para chegar no acumulado do ano.

Poder classificado pelo 4o caractere do CodigoUnidadeGestora do TCE-ES
(ex.: "500E0600004"), que usa letras em vez dos digitos do SIGEFES:
E=Executivo, D=Defensoria, J=Judiciario, L=Legislativo, M=Ministerio
Publico, T=TCE. Esse codigo NAO e' o mesmo CodigoUG usado no SIGEFES
(Despesas/OrcamentosExecucoes) -- os dois lados nao sao join-aveis por
codigo de UG, so' por nome, entao o cruzamento fica por Fonte e por
totais agregados do Executivo, nao por UG individual.

Fonte de recurso identificada pelo par (CodigoFonteReduzida,
CodigoDetalhamento) -- o codigo reduzido sozinho e' ambiguo (o mesmo "500"
aparece com nomes diferentes conforme o detalhamento, ex.: recursos nao
vinculados vs. o mesmo bloco 500 com destinacao MDE ou Saude), entao o
par completo e' a chave real da fonte, com NomeFonteReduzida como rotulo.

Defasagem de publicacao: os dados do TCE-ES sao declaratorios e chegam com
mais atraso que o microdado de despesas -- em setembro de 2026, so' ha
dados ate' julho/2026. O corte usado na comparacao entre anos e' sempre o
ultimo mes disponivel no ano mais recente, nao um mes fixo arbitrario.
"""

import csv
import io
import json
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PACKAGE = "receitas-e-despesas-estaduais"
API_PACKAGE_SHOW = f"https://dados.es.gov.br/api/3/action/package_show?id={PACKAGE}"

ANOS = [2023, 2024, 2025, 2026]

DATA_DIR = Path(__file__).parent
OUTPUT = DATA_DIR / "receita-executivo-es.json"


def resource_url(ano, resources):
    nome = f"estado-receitas-{ano}.zip"
    for r in resources:
        if r["name"] == nome:
            return r["url"]
    raise RuntimeError(f"Recurso {nome} nao encontrado no pacote {PACKAGE}")


def baixar_csv_do_zip(url):
    with urllib.request.urlopen(url, timeout=120) as resp:
        conteudo = resp.read()
    with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
        nome_csv = next(n for n in zf.namelist() if n.endswith(".csv"))
        with zf.open(nome_csv) as f:
            texto = f.read().decode("latin1")
    return list(csv.DictReader(io.StringIO(texto), delimiter=";"))


def eh_executivo(codigo_ug):
    return len(codigo_ug) > 3 and codigo_ug[3] == "E"


def to_float(s):
    if not s:
        return 0.0
    s = s.strip()
    if not s:
        return 0.0
    return float(s.replace(".", "").replace(",", "."))


def main():
    pacote = json.loads(urllib.request.urlopen(API_PACKAGE_SHOW, timeout=30).read())
    resources = pacote["result"]["resources"]

    # (ano, fonte_key) -> {mes: arrecadada_do_mes}
    arrecadado_mensal = defaultdict(lambda: defaultdict(float))
    # (ug, classificacao, fonte_key) -> {mes: previsao_atualizada_na_data}
    previsao_por_serie = defaultdict(dict)
    fonte_nomes = {}
    cortes = {}

    for ano in ANOS:
        url = resource_url(ano, resources)
        print(f"Baixando {url}...", flush=True)
        linhas = baixar_csv_do_zip(url)
        linhas_exec = [r for r in linhas if eh_executivo(r["CodigoUnidadeGestora"])]
        print(f"  {ano}: {len(linhas_exec)} linhas do Executivo (de {len(linhas)} totais)", flush=True)

        for r in linhas_exec:
            mes = int(r["Mes"])
            fonte_key = f"{r['CodigoFonteReduzida']}|{r['CodigoDetalhamento']}"
            fonte_nomes[fonte_key] = r["NomeFonteReduzida"]

            arrecadado_mensal[(ano, fonte_key)][mes] += to_float(r["Arrecadada"])

            serie_key = (ano, r["CodigoUnidadeGestora"], r["ClassificacaoReceita"], fonte_key)
            # Guarda o valor de PrevisaoAtualizada por mes desta serie (pode haver
            # linhas duplicadas para o mesmo mes; a ultima lida prevalece, o que
            # e' inofensivo pois o valor e' o mesmo estoque vigente naquele mes).
            previsao_por_serie[serie_key][mes] = to_float(r["PrevisaoAtualizada"])

        cortes[ano] = max(int(r["Mes"]) for r in linhas_exec)

    # Corte UNIFORME para comparacao entre anos: o menor corte entre os anos
    # (normalmente o do ano corrente, ainda incompleto). Usar o corte
    # proprio de cada ano misturaria fechamento de ano encerrado com ano em
    # curso -- exatamente o vies que ja foi corrigido do lado da despesa.
    corte_comparacao = min(cortes.values())

    # Consolida previsao atualizada por fonte no corte de comparacao: para
    # cada serie (UG/classificacao/fonte), pega o ultimo mes <= corte_comparacao.
    previsao_por_ano_fonte = defaultdict(lambda: defaultdict(float))
    for (ano, ug, classif, fonte_key), por_mes in previsao_por_serie.items():
        meses_validos = [m for m in por_mes if m <= corte_comparacao]
        if not meses_validos:
            continue
        ultimo_mes = max(meses_validos)
        previsao_por_ano_fonte[ano][fonte_key] += por_mes[ultimo_mes]

    # Series por fonte: arrecadado acumulado mes a mes, ate' o fechamento de
    # cada ano (usada so' para o total de fechamento de anos encerrados).
    series_por_fonte = defaultdict(dict)  # fonte_key -> {ano: {mes: acumulado}}
    for (ano, fonte_key), por_mes in arrecadado_mensal.items():
        acumulado = 0.0
        serie = {}
        for mes in range(1, cortes[ano] + 1):
            acumulado += por_mes.get(mes, 0.0)
            serie[mes] = round(acumulado, 2)
        series_por_fonte[fonte_key][ano] = serie

    fontes_saida = []
    for fonte_key, nome in fonte_nomes.items():
        codigo_fonte, codigo_detalhamento = fonte_key.split("|")
        serie = series_por_fonte.get(fonte_key, {})
        arrecadado_mesmo_corte_por_ano = {
            ano: (serie[ano].get(corte_comparacao, 0.0) if ano in serie else 0.0) for ano in ANOS
        }
        arrecadado_fechamento_por_ano = {
            ano: (serie[ano][cortes[ano]] if ano in serie and cortes[ano] in serie[ano] else 0.0)
            for ano in ANOS
        }
        fontes_saida.append(
            {
                "fonte_key": fonte_key,
                "codigo_fonte_reduzida": codigo_fonte,
                "codigo_detalhamento": codigo_detalhamento,
                "nome_fonte": nome,
                "previsao_atualizada_no_corte_por_ano": {
                    str(a): round(previsao_por_ano_fonte.get(a, {}).get(fonte_key, 0.0), 2) for a in ANOS
                },
                "arrecadado_mesmo_corte_por_ano": {
                    str(a): round(v, 2) for a, v in arrecadado_mesmo_corte_por_ano.items()
                },
                "arrecadado_fechamento_por_ano": {
                    str(a): round(v, 2) for a, v in arrecadado_fechamento_por_ano.items()
                },
            }
        )

    output = {
        "fonte": (
            "dados.es.gov.br - pacote 'receitas-e-despesas-estaduais' (TCE-ES, "
            "CidadES - Prestacao de Contas Mensal), arquivos estado-receitas-<ano>.zip"
        ),
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "escopo": "Poder Executivo (4o caractere do CodigoUnidadeGestora do TCE-ES = 'E')",
        "corte_por_ano_mes": cortes,
        "corte_comparacao_mes": corte_comparacao,
        "metodologia": (
            "PrevisaoAtualizada e' estoque (valor vigente, repetido a cada mes por "
            "combinacao UG/classificacao/fonte) -- usa o valor do ultimo mes "
            "disponivel no corte, nunca soma entre meses. Arrecadada e' fluxo "
            "(valor daquele mes) -- soma acumulada mes a mes ate' o corte. Fonte "
            "identificada pelo par (CodigoFonteReduzida, CodigoDetalhamento), "
            "porque o codigo reduzido sozinho e' ambiguo entre destinacoes "
            "diferentes do mesmo bloco de recursos. A comparacao entre anos usa "
            "sempre o MESMO mes de corte (o menor entre os anos disponiveis, "
            "normalmente o do ano corrente ainda incompleto) para nao misturar "
            "ano em curso com fechamento de ano encerrado; 'arrecadado_fechamento_"
            "por_ano' guarda o total de fechamento de cada ano encerrado a parte, "
            "sem entrar na comparacao."
        ),
        "fontes_receita": sorted(
            fontes_saida, key=lambda x: -x["arrecadado_mesmo_corte_por_ano"].get("2026", 0)
        ),
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nSalvo em {OUTPUT} ({len(fontes_saida)} fontes de receita, cortes: {cortes})")


if __name__ == "__main__":
    main()
