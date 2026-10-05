# Coeficiente de destino robusto (φ de destino)

Status: candidato, não adotado. Nenhum resultado publicado (painel, estudos, artigo) foi alterado. Código: `data/collect-renda-uf-censo-pnadc.py`, `data/estima-phi-destino-robusto.py`; saídas: `data/renda-uf-censo-pnadc.json`, `data/phi-dest-robusto.json`, `data/phi-dest-robusto-efeito-pr.json`. Para reproduzir o efeito no modelo: `PHI_FAM_METODO=robusto` antes de `build-phi-dest-pof-censo.py` e da cadeia de `rodar-modelo.sh`.

## Por que revisar o φ atual

O φ atual é a despesa familiar média da POF 2017-18 por UF multiplicada pelos domicílios do Censo 2022, em consumo bruto. Dois problemas. O consumo bruto inclui o aluguel imputado, a alimentação de alíquota zero e o transporte coletivo, que não compõem a base do IBS. E a intensidade de consumo é a de 2018, sem acompanhar a renda relativa das UFs. Na nota técnica do COMSEFAZ e em Gobetti e Monteiro (2023) a base é tributável e a renda é a do Censo 2022 (com correção do IRPF, que não temos). O nosso φ para o Paraná (5,97%) fica abaixo de todas as demais rotas.

## O que foi feito

Três rotas, todas sobre a base tributável (pesos da LC 214/2025, cenário S1 de `teste-base-tributavel-pof.py`). A: POF por pessoa vezes moradores do Censo 2022. B: A atualizada pela renda relativa da PNAD Contínua de 2018 a 2022, com a elasticidade-renda estimada na própria POF (0,75); a PNAD tem a mesma definição de renda nos dois anos, o que evita misturar fontes. C: moradores por classe de salário mínimo do Censo 2022 vezes a base tributável por pessoa de cada classe na POF, com encolhimento de 50% para a média da grande região. O composto é a média simples das três. A incerteza combina a dispersão entre rotas e variantes (elasticidade de 0,5 a 1,0; alimentação toda a zero ou toda a 0,4; encolhimento de 0 a 1) com o erro de validação estrutural.

## Validação e comparação

Dentro da POF (leave-one-UF-out, 27 UFs), a massa de renda prediz a participação de cada UF no consumo com erro relativo médio de 6,2% (RMSE de 0,22 p.p.), as classes de renda com κ regional encolhido com 7,6% e com κ nacional com 8,9%, e a população sozinha com 40%. Esse erro estrutural entra na incerteza do φ. Contra os comparadores externos (não usados como alvo), o RMSE do composto é de 0,33 p.p. em relação à base IBS 2025 do COMSEFAZ e de 0,44 em relação a Gobetti, contra 0,67 e 0,73 do φ atual; e 0,40 em relação à base TRU 2018 do COMSEFAZ, fonte independente. Para o Paraná: rota A 6,50%, B 6,28%, C 6,67%, composto 6,49% (faixa das variantes de 6,14% a 6,72%; incerteza relativa de 8,0%), contra 5,97% do φ atual, 6,84% do COMSEFAZ e de Gobetti e 6,48% da TRU de 2018.

Ressalva importante. A PNAD Contínua mostra que a renda per capita do Paraná em relação à média nacional caiu de 1,155 (2018) para 1,102 (2022). A maior participação do Paraná na renda do Censo (6,76%) não decorre de crescimento relativo da renda desde 2018: vem de a renda do Censo 2022 ser definida de outro modo, e é a fonte do COMSEFAZ. Por isso o composto fica abaixo dos 6,84% do COMSEFAZ e de Gobetti, e a rota B (a única que atualiza pela renda observada na mesma pesquisa) é a mais baixa das três.

## Efeito no Paraná (receita estadual, R$ de 2025)

Com o φ atual (coeficiente pleno estadual de 3,8207%): +0,40% em 2033, −R$ 0,32 bilhão no acumulado de 2029 a 2033, −7,8% em 2077. Com o composto (4,1298%): +1,14% em 2033, +R$ 0,70 bilhão no acumulado, −0,5% em 2077. Municípios: −R$ 1,68 bilhão no acumulado de 2029 a 2033 (antes −R$ 2,13 bilhões) e −3,8% em 2033 (antes −4,4%). A variação de 2077 responde a 23,6 p.p. por ponto percentual do coeficiente, e a de 2033 a 2,4 p.p.; com a incerteza de 8% do φ, o desvio-padrão fica em ±0,8 p.p. em 2033 e ±7,8 p.p. em 2077. A conclusão de longo prazo (sinal e magnitude) é, portanto, pouco determinada pelo método de estimação do φ.

## Limites

Não há correção do IRPF para rendas altas; a classificação dos itens é por categoria; o composto pondera as rotas por igual; e não há dado observado de destino contra o qual validar. A calibração definitiva virá da arrecadação do IBS e da CBS a partir de 2027, e antes disso das notas fiscais eletrônicas da SEFAZ.
