# Sensibilidade da projeção (Monte Carlo): resultados do teste

Status: exploratório; não altera nenhum resultado publicado. Código: `data/sensibilidade-calibra-deriva.py` (calibração e testes), `data/sensibilidade-projecao-mc.py` (simulação); saídas: `data/sensibilidade-calibra-deriva.json`, `data/sensibilidade-projecao-mc.json`; apoio: `data/sidra-pib-pop-uf.json` (SIDRA, PIB e população por UF). O caso central é reproduzido sem diferença (erro máximo de 1e-16) antes de qualquer choque.

## Desenho

A variável de interesse é a variação projetada da receita do ente (receita pós-reforma sobre o contrafactual, menos 1). Duas fontes de incerteza são simuladas. A fonte A é a deriva da participação de cada UF no bolo ICMS+ISS em relação à participação congelada em 2025. A fonte B é o erro de medida do coeficiente de destino φ (lognormal, σ = 0,10 por UF, renormalizado para somar 1). Ficam fora do Monte Carlo o nível do bolo (cancela na razão), o Seguro-Receita (fixo), a base do ICMS na transição (cenário jurídico), as compras governamentais e a base ampla/conformidade (afetam a alíquota, não o bolo).

## Correção da calibração da deriva

A primeira calibração usava a DCA bruta de 2013 a 2025 para 26 UFs e dava desvio de 22,6% em oito anos. Esse número estava inflado por quebras de classificação na própria série: GO, MS, MT, TO e RO têm "outras deduções" de 20% a 37% do ICMS que só aparecem separadas a partir de 2019 (a participação bruta de GO salta de 3,5% para 4,8% em 2017 e volta a 3,3% em 2021), e CE tem um erro em 2018. Excluídas essas UFs (e o DF, sem ICMS em 2013 a 2018), o desvio em oito anos cai para 15,2% (s1 = 0,048; β = 0,555). Uma segunda amostra independente, a série líquida 2019 a 2025 com as 27 UFs, dá 13,8% extrapolado para oito anos.

A validação fora da amostra (calibrar em 2013 a 2019, testar em 2019 a 2025) mostra que a calibração corrigida acerta: intervalos de 80% cobrem 85% a 88% dos casos observados (alvo de 80%), contra 93% a 96% da calibração anterior, que era larga demais.

## Resultados com a calibração corrigida

A meia-largura do intervalo de 10% a 90% (média dos estados) é de 1,4 pontos percentuais em 2029, 5,1 em 2031 e 20,1 em 2033 (antes: 2,0, 7,6 e 30,0). Em 2029, sete estados já têm chance de ganho fora da faixa de 20% a 80%, mas nenhum tem sinal estatisticamente distinguível de zero em nenhum ano. Para o ES, a variação em 2033 é de −7,6% com intervalo de −23,7% a +14,2% (chance de ganho de 33%). Na variação acumulada 2029 a 2033, que é o número exibido no site, a meia-largura média cai para 7,6 pontos e o ES fica em −3,6% com intervalo de −9,9% a +4,5% (chance de ganho de 29%).

Mais de 98% da variância continua vindo do contrafactual; o erro de φ explica menos de 0,4%. No longo prazo, com o contrafactual congelado, o sinal é robusto em 21, 16, 15 e 15 UFs em 2040, 2050, 2060 e 2077.

## O que não estreita o intervalo

Escala de volatilidade própria por UF piora o ajuste fora da amostra (cobertura de 70% a 75% para a escala bruta, empate com a escala comum para a encolhida), então mantém-se a escala comum. Após remover as quebras, as caudas deixam de ser pesadas (curtose padronizada de 2,8), o que valida a distribuição normal. Persistência do desvio anterior e convergência do nível não explicam o desvio futuro. A variação da participação populacional explica cerca de 18% da variância (β ≈ 1,2) e a do PIB regional cerca de 25%, mas o PIB regional não é conhecido antecipadamente; a população poderia entrar como âncora (projeções do IBGE), reduzindo o desvio em cerca de 9%, ao custo de mexer no resultado central. Um nowcast de 2026 com o RREO encurta o horizonte em um ano e reduz o desvio em cerca de 7%.

## Limites

O desvio é normal com variância comum a todas as UFs; as janelas de oito anos são poucas e se sobrepõem; parte da deriva histórica decorre de política tributária dos próprios estados (incentivos, combustíveis), que também é incerteza legítima do contrafactual; o ICMS é usado como medida também para o ISS; o DF usa o desvio comum.

## Robustez e validação (segunda rodada)

Comparação fora da amostra de quatro modelos para a deriva (`data/sensibilidade-modelos-deriva.py`; 20 UFs, origens de 2019 a 2024, janela expansiva, horizontes de 1 a 4 anos; pontuação CRPS, menor é melhor). O passeio aleatório do modelo adotado vence: a âncora populacional com coeficiente 1 tem CRPS 7% pior, com coeficiente estimado 58% pior, e a escala por porte 2,6% pior. Isso é coerente com a literatura de previsão, em que o passeio aleatório é difícil de superar. Cobertura fora da amostra do modelo adotado: 87% para o intervalo de 80% e 93% para o de 90%, ou seja, ligeiramente folgado.

Incerteza sobre a própria incerteza (`data/sensibilidade-incerteza-parametros.py`): o bootstrap em blocos de três anos dos choques anuais dá, para o desvio em oito anos, mediana de 16,6% e intervalo de 90% de 13,4% a 22,0% (estimativa pontual: 15,2%). A simulação principal sorteia um par (s1, β) por rodada, o que alarga a faixa. Um fator de escala kappa estimado por validação cruzada leave-one-origin-out resulta em 0,8, mas o ganho de CRPS é de apenas 1,5%, ou seja, o ótimo é plano e os dados não discriminam; por isso a faixa adotada mantém kappa = 1 e a versão reduzida em 20% fica como sensibilidade.

Três calibrações lado a lado (`data/sensibilidade-calibracoes.py`), meia-largura do intervalo de 10% a 90% em pontos percentuais para 2029, 2031, 2033 e acumulado: parâmetros pontuais 1,4, 5,1, 20,1 e 7,6; bootstrap (adotada) 1,4, 5,6, 22,3 e 8,3; bootstrap com kappa de 0,8: 1,1, 4,5, 17,7 e 6,6. Em nenhuma delas algum estado tem sinal distinguível de zero em 2033 ou no acumulado; a chance de ganho do ES em 2033 varia de 31% a 35%.

Métricas de risco em R$ de 2025 (receita em risco com 95% e perda esperada na cauda) estão em `resultados.estado.risco_em_reais` do JSON da simulação. Para o ES, na variação acumulada de 2029 a 2033, a receita em risco é de cerca de R$ 14 bilhões e a perda esperada na cauda de R$ 18 bilhões.
