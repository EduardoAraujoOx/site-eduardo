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

## Correção das rendas altas pelo IRPF (sensibilidade)

A fonte mais recente que se consegue ler por script é a Tabela 8 de "Grandes Números do IRPF", ano-calendário 2024 (exercício 2025), da Receita Federal (`data/collect-irpf-grandes-numeros.py`, `data/irpf-uf-faixas-ac2024.json`). O painel público do IRPF 2026 (ano-base 2025, lançado em julho de 2026) é um Power BI sem download, e não há microdados públicos. A correção (`data/estima-phi-destino-irpf.py`) reponderaria as classes de topo da rota C por um fator por UF (renda declarada no topo do IRPF dividida pela massa de renda do topo no Censo, normalizada para não mudar o total nacional). O fator é de 0,96 para o Paraná, 0,77 para o Espírito Santo e 1,46 para São Paulo. O efeito sobre o composto é pequeno: Paraná de 6,485% para 6,476%, Espírito Santo de 1,854% para 1,842%, São Paulo de 28,6% para 29,0%. O erro contra a base IBS 2025 do COMSEFAZ sobe de 0,33 para 0,38 ponto percentual e contra Gobetti de 0,44 para 0,51, o que indica que a correção não aproxima o composto das fontes externas. Fica como sensibilidade documentada, fora do composto. Como referência cruzada, a participação na renda total declarada ao IRPF é de 6,56% para o Paraná e 1,78% para o Espírito Santo, próximas do composto (6,49% e 1,85%).

## Tratamento de 2026 no coeficiente histórico

A lei calcula a média de 2019 a 2026; o repositório usa 2019 a 2025 (omite 2026) e a nota do COMSEFAZ repete 2025 em 2026. Backtest (`data/teste-cpt-2026.py`; 20 UFs sem quebras; anos terminais de 2020 a 2025; alvo é a média de oito anos): omitir 2026 erra 0,90% da participação em média, repetir 2025 erra 0,45% e estimar 2026 pelo RREO de janeiro a agosto erra 0,24%. Repetir 2025 melhora o nosso tratamento (reduz o erro à metade) e o nowcast melhora mais. Efeito no coeficiente histórico estadual: Paraná de 3,9963% para 3,9887% (repetir) ou 3,9777% (nowcast); Espírito Santo de 1,5694% para 1,5815% ou 1,5849%.

## Espírito Santo e validação externa

O φ total do Espírito Santo passa de 1,724% para 1,854%. O IBS hipotético de 2025 da nota do COMSEFAZ (e da apresentação de Gobetti à SEFAZ-ES) é de 1,87% a 1,88%: a diferença cai de −0,16 para −0,03 ponto percentual (de −8% para −1%); contra Gobetti (2023, 1,62%) o composto fica 0,23 ponto acima, e contra a TRU de 2018 (1,77%) 0,08 acima. A variação da receita estadual do Espírito Santo em 2033 contra o cenário sem reforma vai de −8,95% (atual) para −8,50% (φ robusto), −7,86% (mais a repetição de 2025 no histórico) e −7,67% (com o nowcast); a simulação da nota do COMSEFAZ dá −7,10% (variação da participação estadual de 2033 sobre 2025). Em 2077, de −35,2% para −30,9%. Nas quatro UFs publicadas na Tabela 12 da nota (PR, ES, SP e MG), o erro médio quadrático em 2033 cai de 1,33 ponto (atual) para 0,86 (φ robusto), 0,69 (com repetição de 2025, o tratamento da nota) e 0,84 (com nowcast).
