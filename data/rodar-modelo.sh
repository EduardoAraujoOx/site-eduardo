#!/usr/bin/env bash
# Reexecuta, na ordem de dependência, a cadeia que gera os JSON do painel e dos
# estudos a partir de data/reforma-tributaria.json. Rodar sempre depois de uma
# coleta DCA ou de qualquer mudança de método (inclusive o ajuste dos fundos do
# art. 115, I, "b": data/fundos-art115-b.json).
#
# Uso (a partir de qualquer pasta):  bash data/rodar-modelo.sh [etapa]
#   etapa = modelo (padrao) | planilhas | artigo-pr | tudo
set -euo pipefail
cd "$(dirname "$0")/.."
run() { echo "→ $*"; python3 "data/$1" "${@:2}" > /dev/null; }

etapa="${1:-modelo}"

# Entradas que NÃO rodam aqui (dependem de dados externos ao repositório; rodar à parte quando mudarem):
#   data/collect-renda-uf-censo-pnadc.py  -> data/renda-uf-censo-pnadc.json (SIDRA)
#   data/estima-phi-destino-robusto.py <pasta_pof> -> data/phi-dest-robusto.json (φ de destino robusto; precisa dos microdados da POF e dos caches pof_uc*.pkl)
#   data/build-populacao-sidra.py         -> data/populacao-{municipios,uf}-media-2019-2026.json (população de 2019 a 2026, API SIDRA; teto do Seguro-Receita)
#   data/sensibilidade-nowcast-2026.py    -> data/sensibilidade-nowcast-2026.json (nowcast de 2026 do histórico; precisa de data/rreo-icms-mensal.json)
# O tratamento de 2026 no coeficiente histórico está em data/parametros-cpt-2026.json (variável CPT_2026 sobrepõe).
modelo() {
  run build-fundos-art115-b.py
  run build-coeficientes-uf.py
  run build-coeficientes-municipios.py
  run build-phi-dest-pof-censo.py
  run build-ibs-projecao-nacional.py
  run build-aliquota-base-referencia.py
  run build-ibs-projecao-longo-prazo.py
  run build-aliquota-referencia-esferas.py
  run build-rateio-destino-municipios.py
  run build-seguro-receita-repasses.py
  run build-seguro-receita-repasses-longo-prazo.py
  run build-resultados-consolidados.py
  run build-painel-estados.py
  run build-faixa-phi-dest.py          # confere contra painel-estados e resultados-consolidados
  run build-painel-municipios.py
  run build-painel-seguro-receita.py   # aba Seguro-Receita do painel (grava também em painelufir/data)
  run build-sensibilidade-painel.py     # aba Sensibilidade do painel (grava também em painelufir/data)
  run build-memoria-calculo.py
  run build-carga-implicita-uf.py
  run build-divergencia-vs-nota-v22.py
  run build-simulacao-aliquota-es.py
  run build-simulacao-aliquota-es-longo-prazo.py
  # espelho do painel (painelufir/README.md)
  for f in resultados-consolidados-ibs ibs-projecao-nacional painel-estados faixa-phi-dest-estados ibs-projecao-longo-prazo seguro-receita-repasses-longo-prazo; do
    cp "data/$f.json" "painelufir/data/$f.json"
  done
  cp -r data/painel-municipios/. painelufir/data/painel-municipios/
  cp -r data/memoria-calculo/. painelufir/data/memoria-calculo/
}

planilhas() {
  run build-ibs-projecao-nacional-xlsx.py
  run build-seguro-receita-planilha.py
  run build-nota-tecnica-pdf.py
}

artigo_pr() {
  run reproject-pr-audited.py
  run build-pr-final-audited.py
  run build-pr-full-audit-sensitivity.py
  run build-tabela-cenarios-pr.py
  run build-tabelas-artigo-pr.py
  run build-tabela-unica-pr.py
  run build-tabela-uf.py
  # build-tabela-validacao-externa-pr.py precisa do caminho da nota tecnica do
  # COMSEFAZ (docx) como 1o argumento e roda a parte.
}

case "$etapa" in
  modelo) modelo ;;
  planilhas) planilhas ;;
  artigo-pr) artigo_pr ;;
  tudo) modelo; planilhas; artigo_pr ;;
  *) echo "etapa invalida: $etapa"; exit 1 ;;
esac
