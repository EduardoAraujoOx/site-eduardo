# Auditoria dos fundos do art. 115, I, "b" (LC 227/2026) e da variável `outras`

Gerado em 03/out/2026. Nenhum código do painel foi alterado; as simulações rodaram em cópia isolada.

Arquivos:
- `dca-contribuicoes-economicas-2021-2025.csv`: linhas de "Contribuições Econômicas" (RO1.2.2.*) do DCA Anexo I-C, por UF e ano (SICONFI/STN).
- `checagem-rreo-vs-dca-icms.json`: ICMS do RREO Anexo 03 (12 meses) contra o ICMS bruto e `outras` do DCA, MT, MS, TO, RO e controles (2023-2025).
- `impacto-27ufs-antes-depois.csv`: coeficiente histórico, base 2025, receita 2029 e 2033, variação 2033, Seguro-Receita 2033 e 2077 e receita per capita 2077, para o modelo atual (base) e dois cenários (A_dca: AM +R$ 3,21 bi; B_comsefaz: AM +3,16, GO +2,14, MT +0,11).

Método do cenário: o valor é somado ao FECOP/fundos estaduais de cada UF em 2019-2025 (deflacionado como o restante da série) na cópia de `reforma-tributaria.json`, e a cadeia de scripts é reexecutada (coeficientes, phi, projeção nacional e de longo prazo, rateio, Seguro-Receita e resultados consolidados). O valor de AM no cenário A foi calculado pelo método do art. 115, §3º, II: média 2021-2023 da conta DCA RO1.2.2.1.99 (2021: RO1.2.2.0.99), corrigida pela variação do ICMS da UF até 2023 e pela variação nacional de ICMS+ISS de 2023 a 2026 (fator 1,2554).

Ressalva: a regeneração da linha de base difere ligeiramente dos JSON publicados (razão bolo/PIB 7,9947% contra 7,9944%), o que indica que os arquivos publicados não foram todos regenerados após a última atualização de dados; as comparações usam sempre a linha de base regenerada.
