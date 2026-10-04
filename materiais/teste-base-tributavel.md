# Teste: base tributável sintética do IBS a partir da POF (rota alternativa)

Status: teste exploratório. Não alimenta nenhum resultado publicado (painel, estudos, tabelas do artigo). Código: `data/teste-base-tributavel-pof.py`; saída: `data/teste-base-tributavel-pof.json`.

## O que foi feito

Os microdados da POF 2017-18 (despesas de consumo, mesma fórmula de anualização e mensalização do IBGE usada em `estima-elasticidade-pof.py`) foram classificados em 17 categorias legais, e a base tributável de cada UF foi calculada como a soma do consumo de cada categoria multiplicado por um peso que representa o tratamento da LC 214/2025: alíquota zero (peso 0), redução de 60% (0,4), redução de 40% em bares e restaurantes (0,6), locação com redução de 70% (0,3), condomínio (0,5), transporte coletivo urbano e jogos fora da base, aluguel imputado fora da base (não há operação tributável), e alíquota cheia no restante. A alimentação em domicílio foi classificada item a item pelo Cadastro de Produtos da POF (quadros e palavras-chave dos Anexos I e XV da lei para alíquota zero; os demais itens com redução de 60%; bebidas alcoólicas e refrigerantes com alíquota cheia). Dois cenários extremos delimitam a incerteza dessa classificação (toda a alimentação em domicílio a zero, ou toda a 0,4). Outro cenário usa os pesos da Tabela 1 da nota técnica do COMSEFAZ.

## Resultados principais

A reprodução do consumo bruto (pesos todos iguais a 1, com aluguel imputado) coincide com o coeficiente bruto POF×Censo do modelo até a quinta casa decimal, o que valida a leitura dos microdados. Os regimes diferenciados reduzem a base a cerca de 60% do consumo (59,9% no cenário de lei; 58,3% a 62,9% nos extremos da alimentação; 61,9% com os pesos do COMSEFAZ, cuja nota fala em base 23% menor sem contar o aluguel imputado).

A participação de cada UF muda pouco em relação ao coeficiente atual: diferença média absoluta de 0,13 p.p. (4,2% em termos relativos), correlação de 0,9995. A maior mudança é o Rio de Janeiro (de 8,48% para 7,73%), seguido de São Paulo (30,26% para 29,73%) e do Paraná (5,97% para 6,39%). O motivo é a retirada do aluguel imputado, que pesa mais em UFs com maior proporção de domicílios próprios de alto valor, e a retirada do transporte coletivo e da alimentação básica.

A incerteza interna da classificação da alimentação é menor do que o efeito dos regimes: a diferença média entre os dois extremos é de 0,045 p.p. A troca entre a classificação da lei e os pesos do COMSEFAZ muda 0,047 p.p. em média.

Comparada à coluna "Base POF" da Tabela 2 da nota do COMSEFAZ (microdados puros), a base do cenário de lei fica a 0,044 p.p. em média (1,6%), e com os pesos deles a 0,038 p.p. Ou seja, a reprodução independente da rota COMSEFAZ é boa. Contra a Tabela 1 de Gobetti 2023, a base de lei fica a 0,38 p.p. em média (13,7%), no mesmo patamar do coeficiente atual.

## Limites

Ficam fora da base os bens imóveis, reformas e serviços bancários que a nota inclui (não são "despesa de consumo" na POF), o Simples e o MEI, os créditos, o cashback e o seletivo. Pesos são aplicados à categoria inteira (por exemplo, todo gasto de saúde a 0,4, sem separar itens com alíquota zero ou plena). A POF é de 2017-18; a nova edição deve sair até o fim de 2026.

## Conclusão operacional

A rota de base sintética reproduz a distribuição do coeficiente atual com diferenças pequenas, o que dá confiança cruzada nos dois caminhos, mas não traz, hoje, informação nova suficiente para substituir o φ. Seu valor está em ser calibrada com a arrecadação observada da CBS a partir de 2027: ali o total e a composição da base passarão a ser dados, não pressupostos.
