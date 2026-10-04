# Sensibilidade da projeção (Monte Carlo): resultados do teste

Status: exploratório; não altera nenhum resultado publicado. Código: `data/sensibilidade-projecao-mc.py`; saída: `data/sensibilidade-projecao-mc.json`. O caso central é reproduzido sem diferença (erro máximo de 1e-16) antes de qualquer choque.

## Desenho

A variável de interesse é a variação projetada da receita do ente (receita pós-reforma sobre o contrafactual, menos 1). Duas fontes de incerteza foram simuladas, ambas calibradas em dados observados. A fonte A é a deriva da participação de cada UF no bolo ICMS+ISS em relação à participação congelada em 2025 (hipótese do modelo central). Um backtest com a DCA de 2013 a 2025 (26 UFs, DF fora por falta de série) mede o desvio-padrão do log da participação em h anos: 0,070 (1 ano), 0,150 (4 anos) e 0,226 (8 anos), que seguem aproximadamente 0,068·h^0,57. A persistência é nula (correlação média de 0,08 entre desvios sucessivos de quatro anos), então não há viés a corrigir, só dispersão. A estimativa quase não muda se a amostra termina em 2021, antes do choque dos combustíveis. A fonte B é o erro de medida do coeficiente de destino φ, com choque lognormal de σ = 0,10 por UF (σ = 0,19 como sensibilidade), renormalizado para somar 1. Ficam fora do Monte Carlo o nível do bolo (cancela na razão), o Seguro-Receita (fixo), a base do ICMS na transição (cenário jurídico), as compras governamentais (faixa de f) e base ampla/conformidade (afetam a alíquota, não o bolo).

## Resultados

No período de transição o intervalo é estreito no início e se abre rapidamente. Para os estados, a largura média do intervalo de 10% a 90% é de 3,9 pontos percentuais em 2029, 15 em 2031 e 60 em 2033, contra um efeito central médio de 0,6, 1,7 e 4,8 pontos. Em 2033 nenhum estado tem sinal estatisticamente distinguível de zero (nenhuma UF com probabilidade de ganho fora de 20%–80%). Quase toda a variância (mais de 98%) vem da deriva do contrafactual (A); o erro de φ explica menos de 0,3%, porque em 2033 cerca de 90% do IBS ainda é distribuído pelo critério histórico, fixado em lei.

No longo prazo, quando o critério de destino domina, o quadro se inverte: o contrafactual deixa de ser identificável (a deriva extrapolada passa de 60%), e a pergunta passa a ser o efeito do φ. Com o contrafactual congelado em 2025 e só o erro de φ, o sinal é robusto (percentis 10 e 90 do mesmo lado de zero) em 21 UFs em 2040 (10 de ganho e 11 de perda), em 16 em 2050 e em 15 em 2077. Em 2077 ganham AC, AP, DF, RN e SE; perdem AL, AM, ES, MS, MT, PA, RO, RR, SC e TO.

## Limites

A deriva usa distribuição normal com desvio pooled (UFs grandes oscilam um pouco mais que as pequenas: 0,164 contra 0,134 em quatro anos); o desvio é estimado em ICMS e aplicado também ao ISS; as janelas de horizonte longo se sobrepõem (cinco janelas de oito anos); parte da deriva histórica decorre de política tributária (combustíveis), que também é incerteza legítima do contrafactual; o DF usa o desvio pooled.
