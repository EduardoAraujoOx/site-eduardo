#!/bin/sh
# Copia para municipios-na-reforma/data os arquivos que o portal lê.
# Chamado pelo buildCommand de municipios-na-reforma/vercel.json (diretório de execução: municipios-na-reforma).
# Fica num script porque a Vercel limita o buildCommand a 256 caracteres.
set -e
mkdir -p data
cp -r ../data/painel-municipios ../data/memoria-calculo data/
cp ../data/malha-municipios.json ../data/malha-uf.json \
   ../data/resultados-consolidados-ibs.json ../data/ibs-projecao-nacional.json \
   ../data/cronograma-municipal.json ../data/cgibs-publicacoes.json ../data/cgibs-editorial.json \
   data/
