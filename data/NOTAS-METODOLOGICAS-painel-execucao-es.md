# Notas metodológicas — painel de execução orçamentária (ES)

Registro de decisões metodológicas tomadas ao longo do desenvolvimento do
`painel-execucao-orcamentaria-es.html`, para não se perderem entre sessões de
trabalho. Não é um documento público; é memória de continuidade.

## Disciplina do "mesmo corte"

Nunca comparar um ano em curso com o fechamento de um ano já encerrado. A
comparação correta é sempre contra o mesmo dia-do-ano (mesmo corte de
calendário) em anos anteriores. Essa foi exatamente a classe de bug corrigida
no `collect-ordem-cronologica-es.py` (rotulagem de ano na virada dez/jan) e
reaproveitada deliberadamente em `build_kpis()` de
`build-painel-execucao-es.py`, via `build_gap_mesmo_corte_por_ug()`, para o
KPI "Gap liquidado − pago vs. mesmo período do ano anterior".

## Estoque vs. fluxo

O gap liquidado-pago é um estoque (o quanto está represado, acumulado). O
prazo de pagamento NL→OB é um fluxo (a velocidade com que cada obrigação é
processada). São medidas de coisas diferentes e podem se mover de forma
independente — uma UG pode ter um estoque grande mas um fluxo rápido (represa
antiga, mas não está piorando), ou o contrário. O caso mais completo — e por
isso o mais revelador — é uma UG onde as duas pioram juntas (ex.: Hospital
Doutor Roberto Arnizaut Silvares), que é o sinal mais forte de tensão de caixa
que o painel consegue produzir hoje.

## Censura à direita

A base de Ordem Cronológica de Pagamentos só registra pagamentos que já
chegaram a OB. Obrigações liquidadas e ainda não pagas não aparecem — por
isso os meses mais recentes tendem a subestimar o prazo real (não a
superestimar). Isso vale tanto para o prazo mediano por UG quanto para
qualquer leitura mês a mês.

## Fonte (TCE-ES) descartada como cruzamento

A tentativa de cruzar receita por Fonte (TCE-ES/CidadES) com despesa por
Fonte (SIGEFES) foi abandonada por decisão do usuário: a defasagem de
publicação entre as duas bases é grande demais para sustentar uma leitura
direta, e o resultado ficava confuso de explicar. O código permanece no
repositório (não foi removido), mas a comparação foi tirada da interface
pública do painel.

## Disponibilidade de caixa: linha de trabalho encerrada

Por instrução explícita do usuário, a linha de investigação sobre
disponibilidade de caixa (RREO Anexo 6 ou equivalente) foi interrompida e não
deve ser retomada sem um novo pedido explícito.

## Percentis são cortes da mesma distribuição

Mediana, P75 e P90 não são medidas diferentes — são cortes da mesma
distribuição de dias entre NL e OB. A comunicação no painel deve deixar isso
claro (evitar que pareçam três indicadores distintos).

## Travessões

Em textos gerados dinamicamente pelo painel (títulos de exportação, rótulos),
usar dois-pontos (":") em vez de travessão ("—") como separador. Travessões
que já existiam como placeholder de "sem dado" (`fmtR$`, `fmtDias`, texto
default de KPI) não são afetados por essa regra — são um uso diferente
("—" como "sem valor"), não pontuação de frase.
