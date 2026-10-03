<!--
Referência externa de consulta. NÃO é publicada no site (ver .vercelignore e .github/workflows/deploy.yml).
Fonte: "Reforma tributária: estimativas de receita sob o novo modelo de IBS para os estados",
Nota técnica elaborada para o COMSEFAZ, versão 3 (validação técnica), agosto/2026.
Documento PRELIMINAR e não oficial: os próprios autores condicionam os resultados à validação dos fundos
estaduais, à arrecadação efetiva de 2026 e à documentação das fontes. Não citar como estimativa oficial.
Conversão automática de NT_COMSEFAZ_RefTributaria_v3_final.docx para Markdown; tabelas e notas de rodapé
preservadas, formatação visual e figuras não.
Uso no painel: Tabela 9 e Tabela 9-A (fundos do art. 115, I, "b", LC 227/2026), Tabela 8 (série de ICMS) e Tabela 12 (base 2025).
-->

COMSEFAZ

# Reforma tributária

Estimativas de receita sob o novo modelo de IBS para os estados

Nota técnica Documento elaborado para o Comitê Nacional de Secretários de Fazenda, Finanças, Receita ou Tributação dos Estados e do Distrito Federal (Comsefaz), no âmbito da proposta de estudo destinada à análise e à simulação dos impactos da Reforma Tributária sobre os entes estaduais.

O presente relatório contempla os Módulos I e II previstos no contrato, reunindo as análises, metodologias e resultados desenvolvidos no âmbito do estudo.

Agosto de 2026.


## Síntese

Esta nota técnica apresenta estimativas preliminares da base tributável, das alíquotas de referência e dos efeitos federativos associados à implantação do IBS. No cenário central, a base efetiva de consumo das famílias é estimada em aproximadamente R$ 5,17 trilhões, e a base efetiva das compras governamentais, em R$ 533,8 bilhões. A partir das hipóteses adotadas no cenário-base, a calibração do modelo resulta em alíquota-padrão combinada estimada de 28,4% sobre o consumo das famílias e, após a aplicação do redutor específico simulado, em alíquota efetiva combinada de 15,9% sobre as contratações realizadas pela administração pública direta, pelas autarquias e pelas fundações públicas. Esses percentuais constituem estimativas do estudo e não correspondem às alíquotas oficiais que serão fixadas pelo Senado Federal.

Os resultados são preliminares e dependem da arrecadação efetiva para 2026, da validação dos fundos estaduais, da documentação das fontes e fórmulas e do cenário de crescimento econômico.

Quadro 1 — Indicadores centrais da simulação


| Indicador | Resultado |
|---|---|
| Base efetiva (famílias) | R$ 5,169 trilhões |
| Base efetiva (compras públicas) | R$ 533,8 bilhões |
| Receita de referência agregada | R$ 1,553 trilhão |
| Alíquota global sobre famílias | 28,4% |
| Alíquota efetiva implícita (compras públicas) | 15,904% |
| Hipótese macroeconômica central | 2,0% a.a. |

Fonte: Elaboração própria.


## 1. Escopo e objetivo

A reforma da tributação do consumo, materializada na extinção do ICMS e do ISS e sua substituição por um imposto sobre bens e serviços (IBS) gerido conjuntamente por estados e municípios, inaugura uma mudança radical no sistema tributário brasileiro, que terá repercussões de várias naturezas, inclusive federativas. Ao contrário dos tributos atuais, cuja cobrança se dá predominantemente no local em que estão localizadas as unidades produtoras de mercadorias e as sedes das empresas prestadoras de serviços, o novo IBS será baseado no chamado princípio do “destino”, ou seja, terá sua arrecadação vinculada ao local de consumo.

Como veremos, essa simples mudança produzirá um impacto distributivo muito significativo, tanto na esfera estadual quanto municipal. Nossas estimativas indicam que cerca de um terço da receita própria dos municípios mudará de mãos, quando comparamos o ISS atual com as projeções de IBS municipal. Já a substituição do ICMS pelo IBS estadual implicará uma redistribuição da ordem de R$ 34 bilhões entre as unidades federadas, que também impactará os municípios por intermédio da cota-parte.

Para chegar a esses resultados, desenvolvemos um modelo que busca estimar a participação relativa de cada ente federado (estado e município) sobre a base do novo IBS cobrado no destino. Ademais, construímos um simulador para a regra de transição da reforma tributária, que irá suavizar significativamente o efeito redistributivo anteriormente mencionado, na medida em que vai ancorar a distribuição de uma parcela decrescente do IBS (inicialmente de 90%, no quinto ano da reforma) ao coeficiente médio de participação de cada ente sobre a receita total de ICMS e ISS entre 2019 e 2026.

Em resumo, o modelo desenvolvido inclui estimativas de qual seria a receita potencial de IBS de cada unidade federada sob o novo IBS, estimativas do parâmetro de receita média que balizará a regra de transição, além de estimativas de repartição do mecanismo de distribuição complementar, o “seguro-receita”, constituído com parcela da receita do IBS e destinado a compensar parcialmente os entes federados que apresentem maior perda relativa de receita com a entrada em vigor da reforma.

Em correspondência ao produto contratado, o estudo está organizado em dois módulos complementares. O primeiro compreende a apuração da receita média de referência e dos coeficientes de participação por unidade da Federação, incluindo a conciliação das séries históricas de arrecadação, o tratamento das contribuições destinadas aos fundos estaduais e a estimação dos efeitos do regime aplicável às compras governamentais. O segundo módulo compara a evolução das receitas no cenário sem reforma, durante a transição e no regime pleno, sob diferentes hipóteses de crescimento econômico e de redutores aplicáveis às aquisições públicas.


## 2. Fundamentos constitucionais e legais

A Emenda Constitucional nº 132/2023 instituiu o IBS e a CBS, estabeleceu a transição dos tributos atuais para os novos tributos e previu mecanismos de retenção e redistribuição da receita. A Lei Complementar nº 214/2025 disciplinou aspectos gerais do IBS e da CBS, inclusive o tratamento das aquisições governamentais. A Lei Complementar nº 227/2026 detalhou o Comitê Gestor do IBS, a apuração das receitas médias e os coeficientes utilizados na transição e na distribuição complementar.

Para fins metodológicos, é necessário distinguir quatro mecanismos jurídicos que produzem efeitos diferentes nas simulações. O primeiro é a fixação das alíquotas de referência da CBS e do IBS, destinada a preservar as receitas dos tributos substituídos. O segundo é a apuração da receita média de referência de cada ente, utilizada na formação dos coeficientes de participação da parcela do IBS retida durante a transição federativa. O terceiro é a distribuição complementar, destinada aos entes que apresentem as menores relações entre sua receita recente de IBS e a receita média de referência ajustada. O quarto é o regime aplicável às compras governamentais, que combina redutor de alíquotas e destinação integral da arrecadação ao ente contratante.

Embora esses mecanismos utilizem informações relacionadas à arrecadação histórica e à base tributável, eles possuem períodos de referência, fórmulas e finalidades distintas. Por essa razão, são tratados separadamente no modelo e apenas posteriormente integrados na simulação das receitas de cada unidade da Federação.

A análise distingue três mecanismos jurídicos relacionados, mas com finalidades e metodologias próprias. O primeiro corresponde à fixação das alíquotas de referência da CBS e do IBS, disciplinada pela Lei Complementar nº 214/2025, com as alterações promovidas pela Lei Complementar nº 227/2026. O segundo corresponde ao cálculo da receita média de referência e dos coeficientes utilizados na distribuição da parcela do IBS retida durante a transição federativa, nos termos dos arts. 114 a 116 da Lei Complementar nº 227/2026. O terceiro consiste na distribuição complementar prevista no art. 117 da mesma Lei Complementar, destinada aos entes com as menores relações entre a receita recente do IBS e sua receita média de referência ajustada.

As alíquotas de referência serão fixadas por resolução do Senado Federal, com base nos cálculos previstos na legislação. Elas não correspondem, necessariamente, às alíquotas que serão efetivamente adotadas por todos os entes. A União, cada Estado e cada Município poderão fixar suas respectivas alíquotas por lei específica, aplicando-se a alíquota de referência da respectiva esfera apenas na ausência de legislação própria. Consequentemente, os percentuais apresentados neste estudo constituem hipóteses de simulação e não antecipam as alíquotas que serão oficialmente fixadas.

O cálculo legal das alíquotas de referência também não se resume à divisão da arrecadação histórica por uma base de consumo estimada. A metodologia deverá considerar as diferentes categorias de receita, os regimes diferenciados e específicos, as operações submetidas ao Simples Nacional, os créditos, as devoluções, as compras governamentais e os demais ajustes previstos na legislação. No caso da União, a receita de referência compreende, além do PIS/Pasep e da Cofins, receitas do IPI e do IOF incidente sobre operações de seguros, bem como estimativas relativas ao Imposto Seletivo. Por essa razão, a estimativa baseada predominantemente na arrecadação de PIS/Cofins deve ser interpretada como aproximação simplificada.

Quanto aos fundos estaduais, devem ser diferenciadas duas utilizações legais dessas receitas. Para o cálculo das alíquotas de referência, aplica-se a metodologia prevista no art. 350 da Lei Complementar nº 214/2025. Para o cálculo da receita média de referência e dos coeficientes da transição, aplicam-se os arts. 114 a 116 da Lei Complementar nº 227/2026, que consideram o ICMS no período de 2019 a 2026 e as contribuições elegíveis aos fundos no período de 2021 a 2023, com os respectivos critérios de atualização. Os valores e coeficientes apresentados neste estudo são estimativas e permanecerão sujeitos à apuração e à divulgação oficiais pelo CGIBS.

Nas contratações realizadas pela administração pública direta, pelas autarquias e pelas fundações públicas, a legislação prevê regime próprio de tributação e destinação da receita ao ente contratante. A aplicação da destinação da CBS é progressiva: não ocorre em 2027 e 2028, alcança 10% em 2029, 20% em 2030, 30% em 2031, 40% em 2032 e torna-se integral em 2033. Para o IBS, a destinação ao ente contratante aplica-se integralmente a partir de 2027.

Por fim, o denominado “seguro-receita” corresponde, neste estudo, à distribuição complementar prevista no art. 117 da Lei Complementar nº 227/2026. Trata-se de denominação informal para a parcela retida e redistribuída aos entes com maior perda relativa, e não da instituição de um fundo autônomo. A distribuição considera a receita do IBS dos 12 meses anteriores em relação à receita média de referência ajustada, sujeita ao limite legal baseado em três vezes a média nacional per capita da respectiva esfera federativa.

Quadro 2 — Base normativa utilizada


| Mecanismo | Finalidade | Período principal | Fundamento |
|---|---|---|---|
| Alíquotas de referência | Preservar a receita dos tributos substituídos | União: 2012-2021; entes subnacionais: 2024-2026 | LC nº 214/2025, arts. 349–370 |
| Receita média e coeficiente | Repartir a parcela retida na transição | ICMS/ISS: 2019-2026; fundos: 2021–2023 | LC nº 227/2026, arts. 114–116 |
| Distribuição complementar | Atenuar perdas relativas | 2029–2096 | LC nº 227/2026, arts. 110 e 117 |
| Compras governamentais | Calibrar a tributação e destinar receita ao adquirente | Anos-base e vigência definidos na LC | LC nº 214/2025, arts. 370 e 473 |

Fonte: Elaboração própria.


## 3. Fontes de dados

A estimação combina informações de consumo e renda, contas regionais, execução orçamentária e receitas tributárias.

Quadro 3 — Fontes e uso no modelo


| Fonte | Uso | Período | Tratamento/controle |
|---|---|---|---|
| IBGE — Censo 2022 | Renda municipal e distribuição por faixas | 2022 | Ajuste com IRPF para rendas superiores |
| IBGE — POF | Propensões a consumir e composição das despesas | 2017–2018 | Aplicação de ponderações tributárias |
| IBGE — TRU regionalizada experimental | Consumo das famílias por UF e setor | 2018 | Atualização para 2022 por renda disponível |
| RFB — IRPF | Correção da subestimação de rendas altas | 2022/2023 | Versão e extração a documentar |
| Siconfi/STN e secretarias de Fazenda | ICMS, ISS e cotas-partes | 2019–2025 | Reconciliação com DCA e demonstrativos anuais |
| Execução orçamentária | Compras governamentais — GND 3 e GND 4 | 2024–2025 | Filtros e exclusões no arquivo de parâmetros |
| Legislação estadual | Contribuições a fundos estaduais | 2021–2023 | Enquadramento individual por UF |

Fonte: Elaboração própria.


## 4. Metodologia de estimação


### 4.1 Estrutura geral do modelo

O modelo adotado para estimar a participação dos entes federados na receita do IBS consiste em dois estágios:

- Em um primeiro momento, estimar a participação relativa de cada estado e município na base do novo imposto sobre bens e serviços (IBS), que substituirá o ICMS e o ISS.
- Em um segundo momento, estimar o coeficiente de participação de cada ente federativo sobre a receita média de ICMS e ISS no período de 2019-2026, que servirá de parâmetro de entrada (junto das estimativas de receita do primeiro estágio) para projetar a receita durante o período de 50 anos de transição e, além disso, estimar os valores eventualmente recebidos por meio do chamado distribuição complementar (financiado pela parcela complementar prevista na legislação).
Em termos de complexidade e incertezas, o primeiro estágio é o mais problemático, já que o desafio é projetar o futuro com base em dados passados, de alguns ou muitos anos, que só indiretamente estão relacionados efetivamente à base potencial do novo tributo. Ainda assim, temos confiança de que a metodologia aplicada é a melhor que poderia ser adotada dentro das possibilidades existentes.

Em termos de referencial, o modelo adotado para estimar a participação de cada município e cada estado na receita do IBS tem como origem o estudo de Orair e Gobetti (2019) publicado pelo IPEA numa fase preliminar de discussão da reforma tributária. Desde então, esse modelo tem passado por constantes aperfeiçoamentos metodológicos, refinamentos relacionados ao texto aprovado da EC 132, além de atualizações decorrentes de novas fontes de informação, conforme detalhado na nota técnica também publicada pelo IPEA em 2023, de autoria de Gobetti, Orair e Monteiro.

Em relação ao que denominamos de primeiro estágio do modelo, o desafio é estimar em termos relativos a participação de cada ente federado na base de consumo do país, já que o IBS será regido pelo princípio do destino; ou seja, pertencerá ao local em que ocorreu o consumo ou onde foi entregue a mercadoria. Dada a base ampla do novo tributo, pode-se prever que ela terá uma forte correlação com o consumo, embora as alíquotas diferenciadas e os regimes especiais possam criar uma distorção entre a participação relativa no consumo e a participação relativa na arrecadação do IBS – questão esta que recebeu uma atenção especial em nosso modelo de simulação, como será detalhado adiante.

Note-se que estamos falando de participação relativa porque, dado que as alíquotas de referência do IBS serão calibradas de modo a manter a arrecadação, em proporção do PIB, igual à do ICMS e do ISS entre 2024 e 2026, então a receita de cada ente federativo, no cenário contrafactual da reforma, pode ser estimada simplesmente aplicando a proporção da base de consumo sobre a receita de cada ano base considerado. Ademais, no caso dos municípios, é preciso aplicar os novos critérios de distribuição previstos para a cota-parte sobre o IBS estadual, que, a exemplo do IBS municipal, também é estimado a partir de uma proxy de participação relativa sobre a base de consumo – nesse caso, por unidade federada.

Dois são os caminhos que seguimos para estimar a proxy de participação relativa na base de consumo:

- Tabela de Recursos e Usos (TRU) na versão regionalizada que o IBGE desenvolveu experimentalmente para o ano de 2018 e que permite identificarmos o consumo das famílias e os demais componentes da demanda final e total por unidade federada e por setor econômico, de modo a se obter uma proxy da base tributável do IBS.
- O censo do IBGE e a Pesquisa de Orçamento Familiar (POF), que, de forma combinada, são utilizadas para estimar a proxy relativa de participação na base do IBS (ou na arrecadação do IBS) por município; parte-se da renda do censo de 2022 por município (estratificada por faixa de renda) e utiliza-se a POF de 2017/2018 (também por faixa de renda e por UF) para se estimar uma espécie de “propensão média a consumir” por município relacionada à base de tributação do IBS.
Por fim, o modelo de estimativa da receita por ente federado também considerou a incidência do IBS sobre as compras governamentais, de acordo com o dispositivo constitucional aprovado, prevendo a chamada imunidade recíproca – ou seja, entrega de todo imposto (IBS mais CBS) ao ente adquirente. Para essa estimativa, recorremos a dados orçamentários de estados e municípios relativos a elementos de despesa que sejam associados à base do IBS, como aquisição de bens e serviços diversos.


### 4.2 Base de consumo das famílias

O ponto de partida da metodologia desenvolvida foi buscar uma fonte de dados que nos permitisse chegar a uma estimativa de base de consumo por município e não apenas por estado. Restrição esta que nos remete necessariamente ao censo do IBGE, especificamente aos dados de renda como fonte primária, complementados pelos dados das declarações do IRPF, que melhor captam os rendimentos das faixas de renda mais altas.

A POF, por sua vez, tem estimativas de renda e consumo para as capitais e regiões metropolitanas, mas não para o conjunto dos municípios, como seria necessário para nossos objetivos. Diante dessa lacuna, a primeira estratégia adotada para estimar a proxy de base tributável pelo IBS foi realizar um cruzamento entre a renda do censo (estratificada em cinco faixas de renda) e um indicador de “propensão média a consumir” derivado da POF, dividindo o “consumo tributável” pelo rendimento total verificado para cada uma das cinco faixas de renda em cada uma das 27 unidades federadas.

No estágio seguinte, essas “proporções” foram multiplicadas pelos rendimentos de cada município, segregados igualmente em cinco faixas de renda, para obter a proxy da base de consumo por município e por estado. Em termos de fórmula, sendo Yj a renda da faixa j e Propj a proporção dessa renda destinada ao consumo de bens e serviços tributados pelo IBS, então a base de consumo do município i será igual à:

BC = Prop₁ × Y₁ + Prop₂ × Y₂ + Prop₃ × Y₃ + Prop₄ × Y₄ + Prop₅ × Y₅

No final das contas, a proporção média da renda destinada ao consumo de bens e serviços tributados pelo IBS será diferente para cada município, correspondendo a uma média ponderada das proporções para cada faixa de renda de sua unidade federada.

Ademais, é importante observar que a base tributável difere do consumo tal qual tratado na POF por diferentes razões:

- O consumo da POF inclui itens não monetários, como aluguéis imputados, e itens submetidos a regimes diferenciados e específicos de tributação, favorecidos ou não. Os serviços privados de saúde e educação, por exemplo, terão a alíquota de IBS reduzida em 60%, enquanto os combustíveis terão uma alíquota expressa em termos ad rem, em patamar superior à alíquota de referência. E, na prática, uma redução de alíquota equivale à correspondente redução de base de cálculo do imposto.
- Além das despesas de consumo, há outras despesas identificadas na POF que também seriam passíveis de tributação pelo IBS, tais como os bens imóveis construídos e adquiridos pelas famílias, os gastos com reforma de imóveis e os serviços bancários.
Dessa forma, a base tributável pode ser equiparada a uma combinação linear de diferentes itens de consumo e despesas que aparecem na POF. Na tabela seguinte, reproduzimos as ponderações utilizadas para compor a base de consumo tributável a partir da POF de 2018 (lembrando que a previsão para que o IBGE divulgue talvez uma nova POF até o final do ano de 2026).

Havendo necessidade, as ponderações utilizadas podem ser ajustadas, mas antecipamos que isso produz alterações marginais na distribuição entre as unidades federadas.

Tabela 1 — Principais ponderações usadas na composição da base tributável


| Componente da POF | Ponderação |
|---|---|
| Despesas de consumo | 1,00 |
| Alimentação | −0,60 |
| Aluguel monetário | −0,70 |
| Aluguel não monetário | −1,00 |
| Condomínio | −0,50 |
| Gás doméstico | −0,30 |
| Transporte urbano | −0,80 |
| Gasolina — veículo próprio | +0,50 |
| Viagens esporádicas | −0,50 |
| Higiene e cuidados pessoais | −0,10 |
| Assistência à saúde | −0,60 |
| Educação | −0,60 |
| Serviços pessoais | −0,50 |
| Serviços bancários | +1,00 |
| Imóvel — aquisição | +0,30 |
| Imóvel — reforma | +0,80 |

Nota: o quadro apresenta apenas os componentes com ponderação não nula.

Fonte: Elaboração própria.

É importante observar que as ponderações expressas na tabela acima são estimativas baseadas, sempre que possível, em elementos da legislação, mas que, em muitos casos, envolveram alguma arbitrariedade na parametrização. Por exemplo, para as despesas de reforma, estamos supondo que uma parte poderia ser beneficiada por uma carga menor, como seria o caso dos prestadores de serviços do Simples. Para a aquisição de imóvel, por sua vez, estamos a considerar que a base tributável corresponderia em média a apenas 30% do valor de aquisição, visto que há algumas previsões de valores a serem deduzidos da base e que, além disso, a alíquota também é reduzida em 50%.

No resultado final, os regimes diferenciados e específicos alteram a participação relativa de cada unidade federada (e cada ente individualmente) na base tributável, como podemos ver na tabela 2 abaixo, ao compararmos a coluna de consumo da POF (de modo amplo) com a base tributável efetiva da POF (decorrente dos tratamentos tributários diferenciados).

Tabela 2 — Participações por fonte de consumo, valores em percentual do total nacional


| UF | Renda POF | Consumo POF | Base POF | Base TRU |
|---|---|---|---|---|
| AC | 0,25% | 0,27% | 0,27% | 0,31% |
| AL | 0,78% | 0,80% | 0,77% | 1,01% |
| AM | 1,08% | 1,00% | 1,01% | 1,23% |
| AP | 0,28% | 0,30% | 0,29% | 0,27% |
| BA | 4,94% | 5,66% | 5,42% | 5,12% |
| CE | 2,60% | 2,64% | 2,56% | 2,85% |
| DF | 3,26% | 2,67% | 2,76% | 2,30% |
| ES | 1,94% | 1,76% | 1,80% | 1,77% |
| GO | 3,47% | 3,54% | 3,66% | 3,07% |
| MA | 1,41% | 1,78% | 1,74% | 1,59% |
| MG | 9,48% | 10,24% | 10,09% | 9,66% |
| MS | 1,27% | 1,45% | 1,49% | 1,22% |
| MT | 1,60% | 1,73% | 1,78% | 1,37% |
| PA | 2,04% | 2,41% | 2,36% | 2,79% |
| PB | 1,22% | 1,18% | 1,16% | 1,25% |
| PE | 3,09% | 3,39% | 3,29% | 3,02% |
| PI | 0,93% | 1,00% | 0,95% | 1,05% |
| PR | 6,16% | 6,14% | 6,47% | 6,48% |
| RJ | 9,31% | 7,95% | 7,72% | 9,53% |
| RN | 1,16% | 1,47% | 1,41% | 1,27% |
| RO | 0,59% | 0,57% | 0,61% | 0,71% |
| RR | 0,19% | 0,14% | 0,14% | 0,21% |
| RS | 6,91% | 6,74% | 6,91% | 7,16% |
| SC | 4,02% | 3,96% | 4,18% | 4,75% |
| SE | 0,84% | 1,01% | 0,95% | 0,77% |
| SP | 30,74% | 29,80% | 29,79% | 28,67% |
| TO | 0,44% | 0,39% | 0,42% | 0,58% |

Fonte: IBGE. Elaboração própria.

Para se ter uma ideia do impacto agregado das ponderações que inserimos na tabela 1, em termos de tratamentos diferenciados/específicos, constatamos que a base tributável ficaria 23% menor do que o consumo em termos agregados. Em termos de alíquota de referência, o impacto é de elevação de aproximadamente 30% – de 21,5% para 28%, por exemplo.

Outro detalhe a ser destacado na tabela 2 é a diferença que podemos constatar ao comparar as participações relativas baseadas na POF e aquelas advindas do consumo das famílias de acordo com a TRU regionalizada de 2018. Para São Paulo, por exemplo, enquanto a POF indica uma participação relativa de 29,8%, a TRU revela 28,7%, e nossas estimativas baseadas no cruzamento entre a POF e o censo apontam para um patamar um pouco menor ainda, por volta de 28,1% para o ano de 2022 como podemos ver na tabela 3.

Note-se que a estimativa baseada no censo/POF diverge do dado puro da POF porque leva em consideração a aplicação das proporções médias a consumir sobre a renda de 2022 de cada município brasileiro, renda que é estimada pelo cruzamento de dados do censo com dados das declarações do IRPF.

Devido a essas divergências e à impossibilidade de avaliar qual das fontes de informação originárias estariam mais próximas da realidade, optamos por extrair uma média entre as participações relativas obtidas pelo censo/POF e pela TRU para cada uma das unidades federadas, resultando na base de IBS para o ano de 2022.

No caso da TRU, as estimativas de participação relativa de 2018 foram atualizadas para 2022 a partir da variação de uma proxy de renda disponível das famílias que construímos a partir de diferentes fontes de informação. Assim, podemos obter a média da POF/Censo e da TRU para o ano de 2022. A seguir, atualizamos a base do IBS para 2025 supondo que no intervalo de três anos o diferencial de crescimento da renda anual per capita por unidade federada tenha se mantido igual ao de 2018-2022.

Tabela 3 — Base tributável por fonte e ano


| UF | POF/Censo 2022 | TRU atualizada para 2022 | Base IBS 2022 | Base IBS 2025 |
|---|---|---|---|---|
| AC | 0,30% | 0,30% | 0,30% | 0,30% |
| AL | 0,96% | 1,03% | 1,00% | 1,02% |
| AM | 1,24% | 1,27% | 1,25% | 1,28% |
| AP | 0,28% | 0,27% | 0,27% | 0,27% |
| BA | 4,89% | 5,02% | 4,96% | 4,87% |
| CE | 2,80% | 2,80% | 2,80% | 2,75% |
| DF | 1,98% | 2,15% | 2,07% | 1,96% |
| ES | 1,82% | 1,83% | 1,82% | 1,87% |
| GO | 3,61% | 3,34% | 3,47% | 3,69% |
| MA | 2,09% | 1,58% | 1,84% | 1,82% |
| MG | 10,17% | 9,91% | 10,04% | 10,22% |
| MS | 1,56% | 1,31% | 1,43% | 1,51% |
| MT | 2,12% | 1,89% | 2,00% | 2,24% |
| PA | 2,74% | 2,90% | 2,82% | 2,89% |
| PB | 1,27% | 1,22% | 1,25% | 1,22% |
| PE | 3,14% | 2,95% | 3,05% | 2,98% |
| PI | 1,03% | 1,08% | 1,06% | 1,07% |
| PR | 6,91% | 6,60% | 6,76% | 6,84% |
| RJ | 7,83% | 8,90% | 8,37% | 7,94% |
| RN | 1,31% | 1,26% | 1,29% | 1,28% |
| RO | 0,69% | 0,71% | 0,70% | 0,69% |
| RR | 0,20% | 0,22% | 0,21% | 0,22% |
| RS | 6,57% | 7,05% | 6,81% | 6,72% |
| SC | 4,94% | 5,23% | 5,09% | 5,46% |
| SE | 0,81% | 0,77% | 0,79% | 0,78% |
| SP | 28,14% | 27,78% | 27,96% | 27,47% |
| TO | 0,59% | 0,63% | 0,61% | 0,64% |

Fonte: IBGE. Elaboração própria.

Quanto à variável de renda disponível que utilizamos para atualizar os dados de consumo, cabe esclarecer que ela parte, em primeiro lugar, de atualizações que têm sido realizadas pelo Banco Central desde 2021, último dado divulgado pelo IBGE por meio das Contas Econômicas Integradas (CEI). Por outro lado, a regionalização da renda disponível foi realizada por meio de uma proxy que criamos recorrendo a diferentes fontes de informação relativas aos diferentes componentes da RNDB, quais sejam:

- Salários: Contas Regionais e PNAD
- Benefícios sociais: Bases de dados do Ministério de Previdência e Assistência Social, FINBRA/STN para aposentadorias/pensões de estados/municípios e dados dos Grandes Números do IRPF por natureza de ocupação
- Lucros e dividendos: base de dados do IRPF/RFB referente à distribuição de renda por centis (estudo ampliado para 2017/2023)
- Outras rendas do capital: base de dados do IRPF/RFB referente à distribuição de renda por centis (estudo ampliado para 2017/2023)
Note-se que tais fontes de informação nos permitem chegar a cerca de 90% dos rendimentos que compõem a RNDB, de modo que a participação relativa de cada unidade federada obtida por meio dessa agregação pode ser considerada uma boa proxy para fins de verificação das diferentes taxas de crescimento da renda no período recente.

Já sobre a variável de renda do Censo de 2022, constatamos, ao comparar com os dados das declarações de IRPF do mesmo ano, que existe uma significativa subestimativa na pesquisa do IBGE em relação à mensuração dos rendimentos mais altos. Por essa razão, optamos por mesclar os dados do IRPF com os do censo a fim de obter uma melhor proxy de renda a ser usada como referência para estimarmos a base tributável do consumo. Essa “mescla” ou fusão de bases foi feita somando a renda das declarações do IRPF, referente a X% da população de cada município, com a renda do censo relativa ao restante da população, ou seja, os (100% – X%) mais pobres.


### 4.3 Compras governamentais

Por fim, um último passo é necessário para se chegar à base tributável completa do IBS, incorporando no cálculo as compras governamentais. Ou seja, os bens e serviços adquiridos pelas três esferas da administração pública também farão parte da base do IBS, assim como fazem hoje parte da base de tributação dos distintos impostos existentes – ISS, ICMS e PIS/COFINS.

A diferença é que hoje os entes governamentais tributam-se uns aos outros e eventualmente isentam suas próprias compras – por exemplo, os estados preveem isenção sobre medicamentos, veículos e outros itens adquiridos para si próprios, mas pagam PIS/COFINS sobre esses mesmos bens para a União e pagam aos municípios ISS sobre os serviços que contratam.

Com a reforma tributária aprovada, estabeleceu-se o que se convencionou chamar de imunidade recíproca; ou seja, todo imposto incidente sobre as compras governamentais pertencerá exclusivamente ao ente adquirente. Se a compra é realizada pelo estado, toda alíquota incidente sobre o bem ou serviço adquirido pertencerá ao estado adquirente; o mesmo valendo para os municípios e para a União.

A fim de estimar qual seria o montante das compras governamentais sujeito à tributação, recorremos aos dados de execução orçamentária das três esferas da federação, filtrando os gastos relacionados aos elementos de despesa do chamado grupo de natureza da despesa 3 – Custeio - grupo de natureza da despesa 4 – Investimento - que tenham relação com a aquisição de bens ou serviços tributáveis pelo IBS. E, dada a volatilidade de parte desses gastos ao ciclo político-eleitoral, optamos por usar uma média dos últimos dois anos, tal qual apresentado na tabela 4.

Tabela 4 — Compras governamentais sujeitas ao IBS/CBS — R$ bilhões


| Esfera | 2024 | 2025 | Média | Base efetiva das Compras Governamentais |
|---|---|---|---|---|
| União | 137,71 | 148,85 | 143,28 | 90,27 |
| Estados | 225,18 | 244,92 | 235,05 | 148,08 |
| Municípios | 479,93 | 458,13 | 469,03 | 295,49 |
| Total | 842,83 | 851,91 | 847,37 | 533,84 |

Fonte: Siconfi. Elaboração própria.

Além disso, estimamos que:

- a carga tributária média embutida no preço das compras governamentais (incluindo investimentos) se situe em torno de 10%, ou R$ 85 bilhões em valores de 2025; e
- os tratamentos diferenciados concedidos aos bens e serviços adquiridos pelas administrações públicas correspondam a uma redução média de aproximadamente 30% da base já líquida dos tributos atuais.
Combinada à exclusão prévia de 10% relativa à carga tributária incorporada aos valores brutos, essa hipótese produz redução total de 37%, resultando em base efetiva estimada de R$ 533,8 bilhões.

Sobre isso, é importante observar que, embora legalmente os redutores sejam aplicados sobre as alíquotas de IBS, na prática isso equivale a aplicar tais redutores sobre a base de cálculo, como fizemos ao estimar a base tributável de consumo das famílias. Do ponto de vista operacional, é mais simples ajustar as bases de cálculo de cada estado e município do que estimar a alíquota efetiva de IBS de cada ente, ponderada pelos distintos tratamentos diferenciados. Feitas essas considerações, apresentamos na tabela 5 as estimativas de base de tributação do IBS por unidade federada, tanto para o consumo das famílias quanto para as compras governamentais.

Tabela 5 — Base estimada do IBS por UF — R$ bilhões


| UF | Consumo famílias | Compras estaduais | Compras municipais | Total |
|---|---|---|---|---|
| AC | 15,3 | 1,6 | 1,1 | 18,0 |
| AL | 52,5 | 2,8 | 5,2 | 60,5 |
| AM | 66,1 | 4,8 | 5,8 | 76,7 |
| AP | 14,2 | 1,3 | 1,0 | 16,4 |
| BA | 251,9 | 13,9 | 21,4 | 287,2 |
| CE | 142,2 | 6,2 | 11,8 | 160,1 |
| DF | 101,2 | 6,4 | 107,5 |  |
| ES | 96,4 | 3,7 | 6,5 | 106,6 |
| GO | 190,7 | 4,6 | 9,9 | 205,2 |
| MA | 94,1 | 4,9 | 9,6 | 108,6 |
| MG | 528,1 | 8,0 | 31,4 | 567,6 |
| MS | 77,9 | 3,2 | 4,5 | 85,6 |
| MT | 115,7 | 5,0 | 7,1 | 127,8 |
| PA | 149,6 | 7,1 | 11,1 | 167,9 |
| PB | 63,0 | 3,1 | 5,5 | 71,6 |
| PE | 154,2 | 6,9 | 10,4 | 171,6 |
| PI | 55,3 | 4,3 | 5,6 | 65,3 |
| PR | 353,6 | 9,5 | 16,5 | 379,6 |
| RJ | 410,7 | 9,2 | 22,2 | 442,0 |
| RN | 66,3 | 1,6 | 4,6 | 72,5 |
| RO | 35,9 | 1,7 | 1,8 | 39,4 |
| RR | 11,3 | 1,5 | 1,2 | 14,0 |
| RS | 347,4 | 7,4 | 15,7 | 370,5 |
| SC | 282,1 | 6,0 | 12,2 | 300,3 |
| SE | 40,3 | 3,0 | 2,9 | 46,1 |
| SP | 1.419,9 | 21,6 | 64,0 | 1.505,5 |
| TO | 33,3 | 2,1 | 3,2 | 38,7 |

Fonte: IBGE. Elaboração própria.

Vale lembrar que o IBGE estima que o consumo das famílias totalizou cerca de R$ 8 trilhões em 2025, mas com a exclusão dos impostos e do consumo não-monetário (como aluguel imputado), a base tributável cai para pouco mais de R$ 6 trilhões. Nesta base, temos bens e serviços que serão submetidos à alíquota de referência cheia de IBS e CBS, enquanto outros se beneficiarão de diferentes hipóteses de alíquotas reduzidas ou regimes especiais, de modo que, por essa razão, estimamos que a base efetiva (afetada pelos tratamentos diferenciados) se situará em torno de R$ 5,17 trilhões.

Figura 1 — Decomposição da base efetiva das compras governamentais

Fonte: elaboração própria.


### 4.4 Receitas de referência e alíquotas

A reforma tributária, como é sabido, se baseou no princípio da neutralidade em termos de carga tributária e sua distribuição entre as três esferas da federação, prevendo que os novos impostos inaugurados pela EC 132 mantenham sua arrecadação equivalente aos tributos extintos. Mas como é que essa equivalência será considerada na prática?

Nos termos dos arts. 349 a 365 da Lei Complementar nº 214/2025, com as alterações promovidas pela Lei Complementar nº 227/2026, as alíquotas de referência serão fixadas pelo Senado Federal com base em cálculos do Tribunal de Contas da União, elaborados a partir de propostas do Poder Executivo federal e do Comitê Gestor do IBS. A CBS toma como referência a relação entre a receita da União e o PIB no período de 2012 a 2021, enquanto as alíquotas estadual e municipal do IBS procuram preservar a relação entre as respectivas receitas e o PIB no período de 2024 a 2026.

A alíquota combinada de 28,4% apresentada nesta nota constitui uma estimativa mecânica para o cenário central. Não se trata de previsão da alíquota que será oficialmente fixada, pois o cálculo definitivo deverá incorporar bases tributáveis efetivamente observadas, regimes diferenciados e específicos, créditos presumidos, devoluções, Simples Nacional e demais ajustes previstos na legislação.

A legislação prevê, contudo, mecanismo de avaliação e limitação da alíquota de referência. Nos termos do art. 475, §§ 9º a 12, da Lei Complementar nº 214/2025, a primeira avaliação quinquenal utilizará os dados disponíveis de 2026 a 2030 para estimar as alíquotas de referência do IBS e da CBS aplicáveis a partir de 2033. Caso a soma das alíquotas de referência estimadas do IBS e da CBS para aplicação a partir de 2033 seja superior a 26,5%, a legislação não determina sua redução automática. O parâmetro de 26,5% não deve ser interpretado como teto absoluto ou como limite de aplicação automática. Nos termos do art. 475, §§ 9º a 12, da Lei Complementar nº 214/2025, o Poder Executivo da União, ouvido o Comitê Gestor do IBS, deverá encaminhar ao Congresso Nacional, no prazo de até 90 dias após a conclusão da primeira avaliação quinquenal, projeto de lei complementar propondo medidas destinadas a reduzir o percentual para patamar igual ou inferior a 26,5%.

As medidas poderão envolver alterações no escopo e na forma de aplicação dos regimes especiais e de incentivo, da devolução personalizada do IBS e da CBS, da Cesta Básica Nacional de Alimentos e dos regimes diferenciados e específicos de tributação. Entre as alternativas estão a redução ou maior focalização dos tratamentos favorecidos, a revisão de percentuais de redução, a restrição dos bens, serviços ou contribuintes beneficiados, a modificação de bases de cálculo e regras de creditamento e a substituição de desonerações generalizadas por mecanismos de devolução direcionados às famílias de baixa renda.

A finalidade dessas medidas será ampliar a base efetivamente tributada e, dessa forma, permitir a preservação da arrecadação com uma alíquota-padrão inferior. Eventuais mudanças dependerão de aprovação pelo Congresso Nacional e, no caso dos regimes diferenciados, deverão ser acompanhadas de regra de transição para a alíquota-padrão.

A alíquota-padrão combinada estimada nesse estudo de 28,4% não constitui um parâmetro independente de distribuição da receita entre os entes federativos, mas o resultado da calibração necessária para compatibilizar a base tributável estimada com a receita agregada de referência. O simulador determina inicialmente a participação relativa de cada Estado e Município na base efetiva do IBS e, posteriormente, aplica essas participações sobre o montante total de receita a ser preservado.

Como a alíquota-padrão incide uniformemente sobre as bases consideradas, sua alteração isolada produz uma variação proporcional tanto na receita de cada ente quanto na receita total. Desse modo, a alíquota se cancela no cálculo das participações relativas e não modifica, por si só, os resultados distributivos do modelo. O mesmo raciocínio se aplica aos tratamentos tributários expressos como percentuais da alíquota-padrão, desde que sejam mantidas as respectivas proporções, inclusive o redutor considerado para as compras governamentais.

Assim, os ganhos e as perdas estimados pelo simulador decorrem principalmente da distribuição territorial da base de consumo, da composição das operações sujeitas aos diferentes tratamentos tributários, das compras governamentais, dos coeficientes de receita média e das regras de transição, e não do valor nominal da alíquota-padrão utilizada na calibração.

Essa neutralidade deixa de ocorrer se a alteração da alíquota for acompanhada de mudanças na base tributável, nos regimes diferenciados ou específicos, nas operações sujeitas à alíquota zero ou no redutor aplicado às compras governamentais. Nesses casos, os efeitos podem variar entre Estados e Municípios e, consequentemente, modificar as estimativas de ganhos e perdas federativas.

Nossas estimativas preliminares (vide tabela 6) indicam que, se a carga tributária de 2026 permanecer igual à de 2025, as receitas médias de ISS e ICMS a serem consideradas no cálculo das alíquotas de referência seriam, respectivamente, de R$ 156 bilhões e R$ 871 bilhões, sendo neste último valor incluído cerca de R$ 5 bilhões de receita média de contribuições econômicas dos estados do Amazonas, Goiás e Mato Grosso.

Tabela 6 — Base estimada da CBS/IBS por diferentes média — R$ milhões


| Ano/período | PIS/COFINS | ICMS (com fundos) | ISS | Total | PIB |
|---|---|---|---|---|---|
| 2012 | 213.434 | 329.259 | 45.453 | 588.146 | 4.814.760 |
| 2013 | 245.383 | 365.247 | 49.378 | 660.007 | 5.331.619 |
| 2014 | 240.768 | 387.477 | 55.397 | 683.642 | 5.778.953 |
| 2015 | 247.333 | 401.060 | 56.094 | 704.488 | 5.995.787 |
| 2016 | 248.509 | 418.457 | 55.382 | 722.348 | 6.269.328 |
| 2017 | 285.986 | 446.634 | 58.074 | 790.694 | 6.585.479 |
| 2018 | 304.947 | 482.726 | 63.837 | 851.510 | 7.004.141 |
| 2019 | 290.735 | 515.050 | 73.693 | 878.341 | 7.389.131 |
| 2020 | 269.628 | 525.960 | 73.671 | 868.960 | 7.609.597 |
| 2021 | 333.482 | 662.009 | 90.360 | 1.085.253 | 9.012.142 |
| 2022 | 337.135 | 698.425 | 107.477 | 1.142.828 | 10.079.677 |
| 2023 | 356.835 | 707.144 | 122.393 | 1.186.042 | 10.943.345 |
| 2024 | 445.157 | 813.196 | 142.305 | 1.400.208 | 11.779.251 |
| 2025 | 470.055 | 868.284 | 157.923 | 1.495.779 | 12.738.566 |
| 2026 | 470.055 | 868.284 | 157.923 | 1.495.779 | 12.738.566 |
| em % PIB | CBS | IBS-E | IBS-M | Total | PIB |
| Média 2012-21 | 4,12% | 6,86% | 0,94% | 11,92% | 100,0% |
| Média 2024-26 | 3,72% | 6,85% | 1,23% | 11,79% | 100,0% |
| em R$ milhões | CBS | IBS-E | IBS-M | Total | PIB |
| Média 2012-21 | 524.387 | 874.297 | 119.858 | 1.518.542 | 12.738.566 |
| Média 2024-26 | 473.841 | 871.997 | 156.580 | 1.502.417 | 12.738.566 |

Fonte: IBGE, Siconfi, STN. Elaboração própria.

Como os valores definitivos de 2026 ainda não estavam disponíveis na data-base do estudo, adotou-se, para este exercício preliminar, a hipótese de manutenção nominal dos valores observados em 2025. Essa convenção deverá ser substituída pelos valores realizados quando disponíveis, podendo alterar as receitas de referência e as alíquotas estimadas. Já a receita média de PIS/COFINS, a ser preservada sob a CBS, chegaria a R$ 524 bilhões em valores de 2025, considerando o período de 2012 a 2021.

Com base nessas receitas de referência e nos valores de base de consumo e compras governamentais anteriormente apresentados, estimamos que a alíquota global de referência do IBS/CBS chegaria a 28,4% (vide tabela 7), percentual este que poderá ficar maior caso a calibragem da alíquota da CBS incorpore também parte da receita atual do IPI, que idealmente deveria ser absorvida pelo novo imposto seletivo, mas provavelmente não será.

Tabela 7 — Receita e alíquota de referência (CBS/IBS)— R$ milhões


|  | Base Estimada | Receita Estimada | Alíquota estimada |
|---|---|---|---|
| Compras Governamentais | 533.841 | 84.902 | 15,9% |
| Estados | 148.082 | 23.551 | 15,9% |
| Municípios | 295.492 | 46.995 | 15,9% |
| União | 90.267 | 14.356 | 15,9% |
| Compras das famílias | 5.169.233 | 1.468.062 | 28,4% |
| Estados | 5.169.233 | 848.446 | 16,4% |
| Municípios | 5.169.233 | 109.585 | 2,1% |
| União | 5.169.233 | 510.031 | 9,9% |
| Impostos atuais | Impostos novos | 1.552.964 | 28,4% |
| ICMS | IBS-E | 871.997 | 15,9% |
| ISS | IBS-M | 156.580 | 2,9% |
| PIS/COFINS | CBS | 524.387 | 9,6% |

Fonte: IBGE, Siconfi, STN. Elaboração própria.

Para entender o cálculo acima, precisamos lembrar que a incidência da CBS/IBS sobre as compras governamentais será distinta daquela aplicada sobre o consumo privado, quando as três esferas da federação tributarão simultaneamente qualquer operação.

Nas compras governamentais, a alíquota efetiva será menor. No cenário central, estimamos uma redução de 44% em relação à alíquota combinada geral do IBS e da CBS, resultando em uma alíquota de 15,9%, em vez de 28,4%. Além disso, o produto da arrecadação incidente sobre essas operações pertencerá exclusivamente ao ente adquirente, em consonância com a lógica da imunidade recíproca.

Nos termos dos arts. 472 e 473 da Lei Complementar nº 214/2025, as alíquotas do IBS e da CBS incidentes sobre as compras governamentais serão reduzidas uniformemente mediante a aplicação de redutor próprio. Após essa redução, o produto da arrecadação será integralmente destinado ao ente federativo contratante, mediante a redução a zero das alíquotas devidas aos demais entes e a elevação equivalente da alíquota devida ao próprio ente adquirente.

Logo, diferentemente do modelo atual, em que os entes podem suportar tributos destinados a outras esferas da Federação, no novo modelo o componente tributário incidente sobre a aquisição pública terá como contrapartida uma receita atribuída ao próprio ente contratante, antes da aplicação dos demais mecanismos de retenção e distribuição do IBS. Isso não significa que o valor integral da despesa pública se transforme em receita, mas que a parcela correspondente ao IBS e à CBS será destinada ao ente adquirente.

Em termos federativos, esse modelo fará com que os Municípios, que atualmente concentram a maior parte das compras governamentais, fiquem com a maior parcela da receita futura incidente sobre essas operações. Na base considerada pelo estudo, as compras municipais correspondem a aproximadamente 55,4% das aquisições governamentais, enquanto os Estados respondem por 27,7% e a União, por 16,9%.

Isso não significa, entretanto, que os Municípios obtenham vantagem fiscal líquida em decorrência desse tratamento. A contrapartida da maior participação na receita das compras governamentais é uma participação menor na receita derivada do IBS sobre o consumo das famílias. Ao final, a soma dessas duas fontes permanece igual ao valor de referência do ISS atual, estimado em aproximadamente R$ 156 bilhões pela média do período de 2024 a 2026.

No cenário central, dos R$ 156,5 bilhões correspondentes à receita municipal de referência, R$ 46,9 bilhões provêm das compras governamentais e R$ 109,5 bilhões do consumo das famílias. Para os Estados, a receita de referência de R$ 871,9 bilhões é composta por R$ 23,5 bilhões provenientes das compras governamentais e R$ 848,4 bilhões provenientes do consumo privado. Na União, dos R$ 524,3 bilhões de receita de referência, R$ 14,3 bilhões são associados às compras governamentais e R$ 510 bilhões ao consumo das famílias.

Os Estados e a União, na medida em que apresentam menor participação relativa nas compras governamentais, ficam com uma parcela proporcionalmente maior da receita derivada do consumo das famílias. Quando consideramos os dois lados da equação, estima-se que a alíquota do IBS municipal incidente sobre esse consumo fique em torno de 2,1%, enquanto a alíquota do IBS estadual alcançaria 16,4% e a da CBS, de competência da União, 9,9%. A soma desses componentes corresponde à alíquota combinada estimada de 28,4%.


### 4.5 Análise de sensibilidade ao redutor das compras governamentais

Como ressaltado anteriormente, a neutralidade dos resultados em relação ao valor nominal da alíquota deixa de ocorrer quando há alteração no tratamento relativo das diferentes bases tributáveis. No caso da CBS e do IBS, a base considerada nas simulações é composta por dois grandes componentes: o consumo das famílias e as compras governamentais. Assim, mudanças no redutor aplicado às aquisições do setor público modificam a distribuição da carga tributária entre essas duas bases e, consequentemente, a alíquota necessária sobre o consumo privado para que seja preservada a arrecadação global de referência.

Diante da incerteza quanto ao percentual que será efetivamente aplicado às compras governamentais, além do cenário central foram simulados dois cenários alternativos de sensibilidade. No cenário central, apresentado na Tabela 7, considera-se uma alíquota efetiva de 15,9% sobre as compras governamentais, correspondente a 56% da alíquota geral e, portanto, a um redutor de 44%. Nesse caso, as aquisições públicas, cuja base estimada é de R$ 533,841 bilhões, geram uma receita de R$ 84,902 bilhões, enquanto a alíquota combinada necessária sobre o consumo das famílias é estimada em 28,4%.

Os cenários alternativos procuram avaliar como diferentes níveis de redução aplicados às compras governamentais afetariam essa composição. No primeiro cenário, denominado cenário A ou cenário de redutor mais elevado, a alíquota incidente sobre as compras governamentais é reduzida para 14,0%. Considerando a alíquota geral necessária nesse exercício, esse percentual equivale à aplicação de aproximadamente 49% da alíquota de referência, resultando em um redutor implícito próximo de 51%. Como consequência, a receita proveniente das compras governamentais diminui para R$ 74,738 bilhões, uma redução de R$ 10,164 bilhões em relação ao cenário central. Para que a arrecadação total permaneça inalterada, a perda de receita nessa base precisa ser compensada pelo consumo das famílias, elevando a alíquota combinada incidente sobre o consumo privado de 28,4% para 28,6%, conforme apresentado na Tabela 7a.

Tabela 7a — Receita e alíquota de referência (CBS/IBS)— R$ milhões


| Base | Base R$ mi | Receita | Alíquota |
|---|---|---|---|
| Compras governos | 533.841 | 74.738 | 14,00% |
| E | 148.082 | 20.732 | 14,00% |
| M | 295.492 | 41.369 | 14,00% |
| U | 90.267 | 12.637 | 14,00% |
| Compras famílias | 5.169.233 | 1.478.227 | 28,60% |
| E | 5.169.233 | 851.266 | 16,47% |
| M | 5.169.233 | 115.211 | 2,23% |
| U | 5.169.233 | 511.750 | 9,90% |
| Impostos atuais |  | 1.552.964 | 28,60% |
| ICMS |  | 871.997 | 16,06% |
| ISS |  | 156.580 | 2,88% |
| PIS/COFINS |  | 524.387 | 9,66% |

Fonte: Elaboração própria.

No segundo cenário, denominado cenário B ou cenário de redutor menos elevado, a alíquota aplicada às compras governamentais é elevada para 19,0%. Esse percentual representa aproximadamente 67,7% da alíquota geral necessária nesse cenário, correspondendo a um redutor implícito de cerca de 32,3%. A maior tributação das aquisições públicas eleva a receita dessa base para R$ 101,430 bilhões, montante R$ 16,528 bilhões superior ao observado no cenário central. Com uma parcela maior da arrecadação sendo obtida sobre as compras governamentais, reduz-se a receita que precisa ser obtida sobre o consumo privado, permitindo que a alíquota combinada incidente sobre o consumo das famílias diminua para aproximadamente 28,8%, conforme demonstrado na Tabela 7b.

Tabela 7b— Receita e alíquota de referência (CBS/IBS)— R$ milhões


| Base | Base R$ mi | Receita | Alíquota |
|---|---|---|---|
| Compras governos | 533.841 | 101.430 | 19,00% |
| E | 148.082 | 28.136 | 19,00% |
| M | 295.492 | 56.143 | 19,00% |
| U | 90.267 | 17.151 | 19,00% |
| Compras famílias | 5.169.233 | 1.451.534 | 28,08% |
| E | 5.169.233 | 843.861 | 16,32% |
| M | 5.169.233 | 100.436 | 1,94% |
| U | 5.169.233 | 507.237 | 9,81% |
| Impostos atuais |  | 1.552.964 | 28,08% |
| ICMS |  | 871.997 | 15,77% |
| ISS |  | 156.580 | 2,83% |
| PIS/COFINS |  | 524.387 | 9,48% |

Fonte: Elaboração própria.

A comparação dos três exercícios evidencia, portanto, uma relação inversa entre a alíquota incidente sobre as compras governamentais e a alíquota necessária sobre o consumo das famílias. Essa relação decorre diretamente da hipótese de neutralidade arrecadatória adotada nas simulações: a receita total, assim como as receitas agregadas de referência da União, dos Estados e dos Municípios, é mantida constante. Dessa forma, qualquer redução da arrecadação proveniente das aquisições governamentais precisa ser compensada pelo aumento da arrecadação incidente sobre o consumo privado e vice-versa.

A magnitude dessa compensação pode ser observada mais claramente na comparação entre os dois cenários extremos. A elevação da alíquota aplicada às compras governamentais de 14,0% para 19,0% aumenta a receita associada a essas operações em R$ 26,692 bilhões, ou aproximadamente 35,7%. Em contrapartida, a necessidade de arrecadação sobre o consumo das famílias diminui em magnitude semelhante, permitindo uma redução de aproximadamente 0,5 ponto percentual na alíquota combinada geral, de 28,6% para 28,1%. A Tabela 7c sintetiza essa relação entre a alíquota aplicada às aquisições públicas, o redutor correspondente, a receita gerada por essa base e a alíquota necessária sobre o consumo das famílias.

Tabela 7c — Análise de sensibilidade da alíquota aplicável às compras governamentais — R$ milhões


| Cenário | Alíquota nas compras governamentais | Parcela da alíquota geral aplicada | Redutor implícito | Receita nas compras governamentais | Alíquota sobre o consumo das famílias |
|---|---|---|---|---|---|
| Redutor mais elevado | 14,00% | 49,00% | 51,00% | 74.738 | 28,60% |
| Cenário central | 15,90% | 56,00% | 44,00% | 84.902 | 28,40% |
| Redutor menos elevado | 19,00% | 67,70% | 32,30% | 101.430 | 28,10% |

Fonte: Elaboração própria.

Apesar das mudanças na composição da arrecadação, as receitas agregadas de referência permanecem constantes nos três cenários: R$ 871,997 bilhões para os Estados, R$ 156,580 bilhões para os Municípios e R$ 524,387 bilhões para a União. Os exercícios de sensibilidade mostram, portanto, predominantemente uma redistribuição da origem da receita entre as compras governamentais e o consumo privado, sem produzir, pelas hipóteses adotadas, ganho ou perda agregada imediata para qualquer uma das três esferas federativas.

Essa neutralidade agregada, contudo, não implica que os efeitos distributivos entre os entes sejam necessariamente nulos. A distribuição territorial das compras governamentais não coincide integralmente com a distribuição territorial do consumo das famílias. Dessa forma, uma alíquota relativamente maior sobre as aquisições públicas tende a aumentar a importância dessa base na distribuição da receita, favorecendo relativamente os locais nos quais se concentra maior volume de compras governamentais. Em sentido contrário, um redutor mais elevado reduz a participação dessa base e aumenta a importância relativa da arrecadação associada ao consumo privado e, consequentemente, da sua distribuição segundo o princípio do destino.

Ainda assim, os resultados indicam que alterações isoladas no redutor aplicado às compras governamentais produzem impacto relativamente limitado sobre a alíquota geral necessária à preservação da arrecadação. Mesmo no cenário em que a alíquota sobre as aquisições públicas é elevada para 19,0%, a alíquota combinada estimada para o consumo das famílias permanece próxima de 28,1%, apenas 0,3 ponto percentual abaixo do cenário central de 28,4% e ainda significativamente superior ao parâmetro legal de 26,5%.

Esse resultado reforça a conclusão de que uma eventual aproximação da alíquota combinada ao parâmetro de 26,5%, caso necessária após a avaliação oficial das alíquotas de referência, dependeria de alterações mais abrangentes na estrutura do sistema. Entre elas estão a revisão dos tratamentos tributários favorecidos, dos percentuais de redução de alíquota, das hipóteses de alíquota zero e dos demais dispositivos que reduzem o tamanho da base efetivamente tributável. A alteração isolada do redutor aplicado às compras governamentais, mesmo em magnitude relevante, não seria suficiente para produzir essa redução.

Por fim, é importante distinguir os efeitos sobre o nível das alíquotas daqueles relacionados à distribuição das receitas entre os entes federativos. Caso a base efetiva do IBS se revele diferente daquela estimada nesta nota técnica, a alíquota necessária para preservar a receita de referência de ICMS e ISS também será diferente. Entretanto, a proporção entre as parcelas estadual e municipal da alíquota não se altera, uma vez que é determinada pela relação entre as respectivas receitas de referência, estimada em aproximadamente 85% para os Estados e 15% para os Municípios.

Da mesma forma, a magnitude da alíquota de referência, isoladamente, não altera a lógica de distribuição da receita do IBS entre as unidades federadas. Dada uma determinada receita agregada de referência — correspondente, nas simulações, à média das receitas consideradas de ICMS e ISS no período de 2024 a 2026 —, a alíquota necessária depende essencialmente do tamanho da base tributável. A distribuição territorial dessa receita, por sua vez, depende da localização da base de consumo utilizada como aproximação do princípio do destino. É a interação entre a composição da base tributável e sua distribuição territorial, e não propriamente o nível nominal da alíquota, que determina os efeitos distributivos entre os entes.


### 4.6 Receita média estadual e fundos

A receita potencial de IBS foi estimada a partir das bases de consumo das famílias e compras governamentais da tabela 5 multiplicadas pelas alíquotas de referência da tabela 7, resultando nos valores apresentados abaixo na última coluna da tabela 8. Ou seja, os valores que seriam arrecadados por cada estado em 2025 se o IBS já estivesse em vigor. E tais valores são comparados tanto com a receita de 2025 quanto com a receita média entre 2019-26. Para 2026, como ainda não há valores consolidados de arrecadação, foram replicados os valores de 2025. Os dados de ICMS considerados no cálculo da receita média dos Estados, por UF, estão disponíveis na Tabela 1 dos Anexos.

Tabela 8 — Série histórica de arrecadação de ICMS Considerada para fins de cálculo do coeficiente médio


| UF | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| AC | 1.413.047.877 | 1.374.411.191 | 1.699.401.407 | 1.791.035.054 | 1.912.132.558 | 2.159.968.117 | 2.220.306.998 |
| AL | 4.524.018.870 | 4.694.975.122 | 5.814.528.596 | 6.278.856.330 | 7.338.987.309 | 8.488.852.336 | 9.008.104.971 |
| AM | 10.074.255.068 | 10.841.227.594 | 13.052.900.720 | 13.995.104.514 | 14.246.214.071 | 15.698.510.025 | 16.924.101.052 |
| AP | 945.433.657 | 1.014.886.218 | 1.280.215.545 | 1.353.113.642 | 1.372.246.908 | 1.517.410.287 | 1.702.927.683 |
| BA | 24.717.431.903 | 24.902.441.199 | 31.192.924.695 | 33.249.026.669 | 34.491.946.020 | 39.497.020.152 | 41.998.968.647 |
| CE | 13.147.344.027 | 13.222.260.499 | 16.231.219.820 | 17.124.667.700 | 17.053.549.032 | 20.202.084.845 | 21.447.585.488 |
| DF | 8.173.794.512 | 8.651.619.388 | 9.886.056.687 | 10.101.854.331 | 10.005.366.684 | 11.716.571.023 | 12.598.092.680 |
| ES | 11.412.477.440 | 11.924.539.408 | 15.398.157.881 | 16.651.163.707 | 17.733.378.621 | 20.888.555.332 | 22.615.846.717 |
| GO | 17.025.786.285 | 17.816.879.619 | 23.176.424.978 | 24.065.860.418 | 24.349.471.727 | 29.215.644.410 | 30.532.863.823 |
| MA | 7.831.039.575 | 8.143.958.001 | 9.939.309.949 | 11.469.444.478 | 10.880.745.024 | 13.870.071.546 | 15.813.244.158 |
| MG | 51.981.254.181 | 52.509.448.732 | 67.891.975.280 | 70.717.964.393 | 72.002.914.431 | 81.523.297.331 | 87.712.076.044 |
| MS | 9.105.261.630 | 10.161.119.076 | 12.729.194.728 | 14.085.685.560 | 15.341.904.903 | 17.030.658.703 | 17.621.634.611 |
| MT | 11.314.668.509 | 12.826.040.161 | 18.663.854.526 | 19.699.173.746 | 20.820.000.395 | 23.086.882.922 | 26.030.429.022 |
| PA | 12.201.125.161 | 13.833.806.281 | 16.943.385.590 | 19.972.649.936 | 20.795.796.348 | 24.394.691.448 | 25.079.145.958 |
| PB | 5.883.211.654 | 6.099.027.762 | 7.495.184.696 | 7.672.335.351 | 8.045.036.216 | 9.713.259.973 | 10.554.097.792 |
| PE | 17.303.792.773 | 17.281.660.445 | 21.038.660.785 | 21.348.483.645 | 21.327.078.192 | 26.156.973.043 | 27.634.962.928 |
| PI | 4.480.942.492 | 4.724.378.652 | 5.698.763.328 | 5.772.556.806 | 6.729.290.554 | 7.713.816.236 | 8.476.783.763 |
| PR | 31.416.662.448 | 31.392.396.858 | 39.072.064.259 | 42.216.673.875 | 44.609.334.809 | 51.674.948.955 | 53.382.822.594 |
| RJ | 41.519.003.852 | 43.582.737.274 | 53.067.624.798 | 50.773.538.277 | 49.775.817.400 | 56.894.602.954 | 62.386.507.273 |
| RN | 5.739.341.693 | 5.881.117.295 | 6.827.095.461 | 7.185.173.927 | 8.274.531.189 | 8.459.893.757 | 9.448.358.871 |
| RO | 4.085.334.904 | 4.446.389.853 | 5.816.879.406 | 6.016.430.599 | 6.113.516.376 | 7.507.448.778 | 8.125.984.783 |
| RR | 1.117.103.860 | 1.239.989.996 | 1.569.336.033 | 1.593.763.457 | 1.701.621.014 | 2.010.397.365 | 2.142.489.273 |
| RS | 36.531.283.543 | 36.380.727.218 | 47.560.078.646 | 43.382.235.770 | 44.865.768.615 | 50.610.915.120 | 53.696.398.855 |
| SC | 23.744.802.846 | 23.938.422.018 | 29.050.783.066 | 34.592.343.274 | 36.258.395.880 | 42.724.622.758 | 45.161.068.246 |
| SE | 3.518.877.397 | 3.498.299.445 | 4.246.252.466 | 4.563.523.938 | 5.026.932.174 | 5.608.879.033 | 6.095.788.957 |
| SP | 149.065.122.716 | 149.339.299.258 | 188.360.756.435 | 203.977.683.842 | 196.690.936.766 | 223.844.100.208 | 238.061.225.357 |
| TO | 3.015.156.617 | 3.286.800.375 | 4.195.029.337 | 4.504.435.587 | 5.025.473.342 | 5.947.178.599 | 6.400.909.147 |
| Total | 511.287.575.490 | 523.008.858.937 | 657.898.059.120 | 694.154.778.826 | 702.788.386.559 | 808.157.255.259 | 862.872.725.691 |

Fonte: Siconfi e Secretarias Estaduais de Fazenda. Elaboração própria.

Como a receita média estadual e a receita total de IBS utilizada no exercício correspondem a montantes distintos, a identificação de ganhos e perdas deve priorizar a variação da participação percentual de cada unidade federada. A comparação direta em reais deve ser acompanhada de conciliação que separe o efeito da mudança do total de receita do efeito redistributivo propriamente dito.

Em relação aos fundos estaduais, a Lei Complementar nº 227/2026 estabelece critérios específicos para a apuração da receita média de referência dos Estados, utilizada na definição dos coeficientes de participação aplicáveis à transição federativa do IBS. De acordo com o art. 115, a receita estadual é composta pela arrecadação do ICMS, líquida da parcela pertencente aos Municípios, acrescida, quando aplicável, das receitas provenientes de contribuições destinadas ao financiamento de fundos estaduais que atendam aos requisitos definidos pela legislação.

No caso dessas contribuições, são consideradas apenas as contribuições destinadas a fundos que já se encontravam em funcionamento em 30 de abril de 2023 e cujo recolhimento tenha sido estabelecido como condição para a aplicação de diferimento, regime especial ou outro tratamento diferenciado relativo ao ICMS. Além disso, não são consideradas as contribuições incidentes sobre produtos primários e semielaborados que tenham sido substituídas por contribuições semelhantes nos termos do art. 136 do ADCT.

Para fins desta estimativa, foram considerados os fundos dos Estados do Amazonas, Goiás e Mato Grosso. Embora existam mecanismos semelhantes em outras unidades da Federação, nesses três Estados foram identificadas receitas de contribuições enquadráveis nos critérios legais que são contabilizadas separadamente da arrecadação de ICMS. Nos demais casos, as receitas correspondentes já se encontram incorporadas à arrecadação do imposto ou não demandam inclusão adicional, evitando-se, assim, eventual dupla contagem.

A legislação estabelece também períodos distintos para o cálculo dos dois componentes da receita média estadual. Para a arrecadação do ICMS, devem ser considerados os valores anuais de 2019 a 2026, sendo cada valor corrigido até 2026 pela variação nominal da arrecadação total de ICMS e ISS dos Estados, Distrito Federal e Municípios.

Para as contribuições destinadas aos fundos estaduais, entretanto, o período considerado é especificamente de 2021 a 2023. Os valores de cada um desses anos devem ser atualizados em duas etapas: primeiramente, do respectivo ano até 2023, pela variação nominal da arrecadação de ICMS do próprio Estado; posteriormente, o valor obtido para 2023 deve ser atualizado até 2026 pela variação nominal da arrecadação total de ICMS e ISS dos Estados, Distrito Federal e Municípios. Os valores históricos identificados para Amazonas, Goiás e Mato Grosso são apresentados na tabela abaixo. Para o cálculo da receita média de referência e dos respectivos coeficientes, contudo, são utilizados apenas os valores de 2021 a 2023, devidamente corrigidos nos termos da legislação.

Tabela 9 — Contribuições a fundos consideradas no período legal — R$ milhões


| UF | 2021 | 2022 | 2023 |
|---|---|---|---|
| AM | 2.521,3 | 2.456,5 | 2.413,9 |
| GO | 1.508,3 | 1.718,4 | 1.862,7 |
| MT | 81,2 | 95,2 | 79,4 |

Fonte: Siconfi e Secretarias Estaduais de Fazenda. Elaboração própria.

Tabela 9-A — Matriz de enquadramento das contribuições aos fundos estaduais


| UF | Fundo ou componente | Fundamento estadual | Vínculo com o ICMS | Situação em 30/4/2023 | Tratamento contábil identificado |
|---|---|---|---|---|---|
| AM | FMPES — Fundo de Apoio às Micro e Pequenas Empresas e ao Desenvolvimento Social | Lei nº 2.826/2003 e legislação complementar | Contribuição vinculada à fruição de incentivos fiscais de ICMS | Em funcionamento | Registrado fora do ICMS, em fonte própria, mas agregado com outras contribuições econômicas |
| GO | PROTEGE — contribuições condicionais | Lei nº 14.469/2003 e alterações | Contribuições exigidas como condição para benefícios, incentivos e regimes especiais de ICMS | Em funcionamento | Arrecadação por códigos próprios, como 4014, 4402 e 4888, separadamente do ICMS ordinário |
| MT | FUNDES e FUNDED | Lei nº 11.308/2021 e legislação do PRODEIC | Contrapartidas cobradas de beneficiários de incentivos industriais e comerciais de ICMS | Em funcionamento | Receitas próprias, separadas do ICMS ordinário |
| RJ | FOT — Fundo Orçamentário Temporário | Lei nº 8.645/2019 e regulamentação estadual; informações na SEFAZ/RJ | Depósito exigido como condição para fruição de determinados benefícios e incentivos fiscais de ICMS | Em funcionamento | Contabilizado em subcontas da própria receita de ICMS, inclusive principal, juros, multas, dívida ativa e quota municipal |

Fonte: Siconfi e Secretarias Estaduais de Fazenda. Elaboração própria.

A própria LC nº 227/2026 determina que os Estados informem ao CGIBS as normas instituidoras e os valores das contribuições consideradas, acompanhados da documentação comprobatória. O CGIBS será responsável pelo cálculo definitivo dos coeficientes e deverá divulgar, para cada ente, os valores utilizados, suas respectivas fontes e os cálculos realizados.


## Receita estadual: média, 2025 e IBS hipotético

Note-se que, devido à redução das alíquotas de combustíveis, energia e telecomunicações em 2022, às diferentes respostas dadas pelos estados à LC 194, bem como às diferentes dinâmicas econômicas, a participação relativa das unidades federadas na arrecadação agregada de ICMS se alterou no período, alterando também a mensuração de ganhos/perdas com a reforma. A última coluna da tabela abaixo mede a variação em pontos percentuais entre o IBS hipotético e a receita média histórica.

Tabela 10 — Estimativa de receita de IBS estadual (base 2025) em comparação ao ICMS - R$ bilhões


| UF | Média 2019–26 | % | ICMS 2025 | % | IBS hipotético | % | Δ p.p. |
|---|---|---|---|---|---|---|---|
| AC | 2,32 | 0,26% | 2,22 | 0,26% | 2,77 | 0,32% | +0,06 |
| AL | 8,51 | 0,96% | 9,01 | 1,04% | 9,06 | 1,04% | +0,08 |
| AM | 20,67 | 2,34% | 20,46 | 2,36% | 11,61 | 1,33% | -1,01 |
| AP | 1,70 | 0,19% | 1,70 | 0,20% | 2,54 | 0,29% | +0,10 |
| BA | 42,46 | 4,80% | 42,00 | 4,83% | 43,54 | 4,99% | +0,19 |
| CE | 21,90 | 2,48% | 21,45 | 2,47% | 24,32 | 2,79% | +0,31 |
| DF | 13,20 | 1,49% | 12,60 | 1,45% | 17,11 | 1,96% | +0,47 |
| ES | 21,52 | 2,43% | 22,62 | 2,60% | 16,41 | 1,88% | -0,55 |
| GO | 32,77 | 3,71% | 32,73 | 3,77% | 32,03 | 3,67% | -0,03 |
| MA | 14,47 | 1,64% | 15,81 | 1,82% | 16,23 | 1,86% | +0,22 |
| MG | 89,41 | 10,11% | 87,71 | 10,10% | 87,96 | 10,09% | -0,02 |
| MS | 17,64 | 1,99% | 17,62 | 2,03% | 13,30 | 1,52% | -0,47 |
| MT | 24,47 | 2,77% | 26,12 | 3,01% | 19,78 | 2,27% | -0,50 |
| PA | 24,45 | 2,76% | 25,08 | 2,89% | 25,68 | 2,95% | +0,18 |
| PB | 10,27 | 1,16% | 10,55 | 1,21% | 10,84 | 1,24% | +0,08 |
| PE | 28,17 | 3,19% | 27,63 | 3,18% | 26,41 | 3,03% | -0,16 |
| PI | 8,07 | 0,91% | 8,48 | 0,98% | 9,76 | 1,12% | +0,21 |
| PR | 54,13 | 6,12% | 53,38 | 6,15% | 59,55 | 6,83% | +0,71 |
| RJ | 66,44 | 7,51% | 62,39 | 7,18% | 68,87 | 7,90% | +0,38 |
| RN | 9,59 | 1,08% | 9,45 | 1,09% | 11,13 | 1,28% | +0,19 |
| RO | 7,78 | 0,88% | 8,13 | 0,94% | 6,15 | 0,71% | -0,17 |
| RR | 2,10 | 0,24% | 2,14 | 0,25% | 2,09 | 0,24% | +0,00 |
| RS | 57,92 | 6,55% | 53,70 | 6,18% | 58,20 | 6,67% | +0,12 |
| SC | 43,39 | 4,91% | 45,16 | 5,20% | 47,27 | 5,42% | +0,51 |
| SE | 6,02 | 0,68% | 6,10 | 0,70% | 7,09 | 0,81% | +0,13 |
| SP | 249,02 | 28,16% | 238,06 | 27,40% | 236,49 | 27,12% | -1,04 |
| TO | 5,97 | 0,67% | 6,40 | 0,74% | 5,80 | 0,67% | -0,01 |

Fonte: Siconfi e Secretarias Estaduais de Fazenda. Elaboração própria.

Por exemplo, comparando a participação média que São Paulo teve no ICMS entre 2019 e 2026 com sua futura participação no IBS, estimamos uma perda de 1,04 ponto percentual sobre a arrecadação agregada. Mas quando comparamos o IBS com o resultado do ICMS de 2025, a perda é mínima, em torno de 0,3 ponto percentual.

Para Mato Grosso, ao contrário, a perda comparativa com a média de 2019-26 era de 0,5 ponto percentual, mas frente a 2025 chega a 0,7 ponto percentual. Lembrando que essas participações relativas – devido a diferentes dinâmicas econômicas – tendem a se alterar um pouco até 2029, quando efetivamente entrará em vigor o IBS.

A Tabela 11 reúne as cinco maiores reduções e os cinco maiores aumentos de participação estadual. Entre as perdas relativas, destacam-se São Paulo e Amazonas, com recuos de 1,04 e 1,01 ponto percentual, respectivamente. No sentido oposto, Paraná e Santa Catarina registram os maiores acréscimos, de 0,71 e 0,51 ponto percentual. As diferenças expressas em reais devem ser interpretadas como aproximações ilustrativas, pois resultam da aplicação das

participações a bases agregadas que não são diretamente equivalentes.

A Figura 2 sintetiza visualmente esses movimentos e evidencia que a mudança para o princípio do destino produz efeitos heterogêneos entre as UFs. Essa redistribuição, contudo, não ocorre integralmente no início da reforma, pois é

amortecida pelas regras de transição analisadas na seção seguinte

Tabela 11 — Maiores variações de participação estadual


| UF | Receita média | IBS hipotético | Δ p.p. | Diferença R$ bi* |
|---|---|---|---|---|
| SP | 28,16% | 27,12% | -1,04 | -12,53 |
| AM | 2,34% | 1,33% | -1,01 | -9,06 |
| ES | 2,43% | 1,88% | -0,55 | -5,11 |
| MT | 2,77% | 2,27% | -0,50 | -4,69 |
| MS | 1,99% | 1,52% | -0,47 | -4,34 |
| PR | 6,12% | 6,83% | +0,71 | 5,42 |
| SC | 4,91% | 5,42% | +0,51 | 3,87 |
| DF | 1,49% | 1,96% | +0,47 | 3,91 |
| RJ | 7,51% | 7,90% | +0,38 | 2,43 |
| CE | 2,48% | 2,79% | +0,31 | 2,42 |

Fonte: Elaboração própria com base nas simulações do estudo.

Figura 2 — Maiores aumentos e reduções de participação

Fonte: elaboração própria.

Lembrando que, pela LC nº 227/2026, o ICMS utiliza 2019–2026, com atualização anual até 2026 pela variação nominal agregada de ICMS e ISS. As contribuições aos fundos utilizam 2021–2023: primeiro são atualizadas até 2023 pela variação nominal do ICMS da própria UF e, depois, até 2026 pela variação nominal agregada de ICMS e ISS.


### 4.6 Transição e distribuição complementar (seguro-receita)

A regulamentação da reforma tributário previu que, durante 50 anos, uma parcela da arrecadação do IBS será retida pelo Comitê Gestor do IBS e será redistribuída com base em um coeficiente vinculado à receita média de cada ente federado no período de 2019 e 2026. A receita média dos municípios será considerada pela soma entre o ISS e a cota-parte do ICMS, enquanto a receita média dos estados será o ICMS líquido da cota-parte transferida aos seus municípios.

Na prática, é como se as “regras atuais” de distribuição, materializadas no coeficiente médio de participação sobre a receita de 2019 e 2026, continuassem a ser aplicadas no rateio dos recursos entre os governos subnacionais por mais cinco décadas. Mas a proporção da receita de IBS sujeita às regras atuais (ou “antigas” quando a reforma entrar em vigor) será gradualmente reduzida, enquanto crescerá a parcela arrecadada com base nas “regras novas”.

O porcentual de receita do IBS retido pelo Comitê Gestor e redistribuído pelo critério da receita média será inicialmente de 80% nos quatro primeiros anos de transição, será ampliado para 90% no quinto ano da reforma e posteriormente reduzido em 2 p.p. por ano até o quinquagésimo ano. Da parcela restante, arrecadada com base nas novas regras, ainda haverá a retenção de mais 5% a fim de financiar o seguro-receita destinado a compensar os entes que apresentarem as maiores perdas relativas de receita (comparando a receita no “destino” com a média de 2019-26).

Para calcular a receita média de cada ente, procedemos à coleta de dados de arrecadação própria de ICMS e ISS por meio da base de dado do SICONFI/STN e, no caso da cota-parte de ICMS dos municípios recorremos à base de dados de cada uma das 26 secretarias estaduais de fazenda do país. Lembrando que na receita média dos estados também devem ser considerados os valores arrecadados pelos fundos específicos e que, eventualmente, se encontrem contabilizados como contribuição econômica, por exemplo.

De acordo com a legislação aprovada, os valores arrecadados entre 2019 e 2026 devem ser corrigidos até o ano mais recente pela variação nominal do somatório de todas as receitas de ICMS e ISS. No final das contas, isso equivale a extrair uma média dos coeficientes anuais de participação relativa de cada ente sobre a receita total de ICMS mais ISS.

Esses coeficientes médios são usados tanto para a repartição das receitas retidas relacionadas à transição quanto para a verificação do eventual patamar de perda a ser compensado pelo seguro-receita. O nível de perda é dado pela comparação entre o coeficiente médio do passado e a participação relativa na receita de IBS dos últimos 12 meses, mas o seguro-receita é limitado a recompor até o limite de três vezes a receita per capita da respectiva esfera federada.

A distribuição do seguro-receita entre os estados e municípios será feita por ordem decrescente da perda relativa apurada. Na prática, os valores provisionados no fundo de compensação (5% da receita de IBS não retido pelo Comitê Gestor) vão sendo distribuídos sequencialmente para os entes que apresentam as maiores perdas até que o recurso disponível se esgote.


## 5. Resultados


### 6.1 Início da transição: 2029–2033

Para demonstrar como os efeitos redistributivos serão introduzidos ao longo do tempo, a Tabela 12 apresenta a aplicação das regras de transição federativa e de distribuição complementar entre 2029 e 2033. O cenário central parte da receita de 2025 e adota crescimento de 2% ao ano como hipótese de referência para a evolução da arrecadação.

Tabela 12 — Simulação da regra de transição e seguro-receita do IBS entre 2029 e 2033— R$ mil


| Ano | 2025 | 2029 | 2030 | 2031 | 2032 | 2033 | Tx média cresc. |
|---|---|---|---|---|---|---|---|
| Total | 1.026.616.761 | 1.113.364.682 | 1.135.631.975 | 1.158.344.615 | 1.181.511.507 | 1.205.141.737 | 2,0% |
| ICMS+ISS | 1.026.616.761 | 1.002.028.213 | 908.505.580 | 810.841.230 | 708.906.904 | - | - |
| IBS | - | 111.336.468 | 227.126.395 | 347.503.384 | 472.604.603 | 1.205.141.737 | - |
| Retido -repartição média | - | 89.069.175 | 181.701.116 | 278.002.708 | 378.083.682 | 1.084.627.563 | - |
| Demais | - | 22.267.294 | 45.425.279 | 69.500.677 | 94.520.921 | 120.514.174 | - |
| Seguro-receita | - | 1.113.365 | 2.271.264 | 3.475.034 | 4.726.046 | 6.025.709 | - |
| Destino | - | 21.153.929 | 43.154.015 | 66.025.643 | 89.794.875 | 114.488.465 | - |
| % Tributos atuais | 100% | 90% | 80% | 70% | 60% | 0% | - |
| % IBS retido para transição |  | 80% | 80% | 80% | 80% | 90% | - |
| Distrito Federal | 16.460.712 | 17.927.119 | 18.362.668 | 18.808.468 | 19.264.755 | 19.908.303 | 2,4% |
| Acre | 1.663.398 | 1.817.344 | 1.867.348 | 1.918.627 | 1.971.209 | 2.070.014 | 2,8% |
| Alagoas | 6.945.289 | 7.488.425 | 7.593.586 | 7.699.959 | 7.807.548 | 7.682.800 | 1,3% |
| Amazonas | 16.235.923 | 17.441.561 | 17.620.787 | 17.923.176 | 18.426.570 | 18.859.437 | 1,9% |
| Amapá | 1.273.495 | 1.392.732 | 1.432.447 | 1.473.194 | 1.514.997 | 1.557.861 | 2,6% |
| Bahia | 31.395.685 | 34.101.321 | 34.837.140 | 35.588.750 | 36.356.491 | 37.545.477 | 2,3% |
| Ceará | 16.161.369 | 17.592.323 | 18.010.813 | 18.439.007 | 18.877.123 | 19.592.624 | 2,4% |
| Espírito Santo | 16.943.675 | 18.196.329 | 18.377.607 | 18.558.858 | 18.740.009 | 18.477.633 | 1,1% |
| Goiás | 25.195.705 | 27.291.835 | 27.804.137 | 28.326.014 | 28.857.644 | 29.520.284 | 2,0% |
| Maranhão | 11.938.393 | 12.860.363 | 13.029.023 | 13.199.286 | 13.371.148 | 13.010.328 | 1,1% |
| Minas Gerais | 66.130.419 | 71.754.806 | 73.227.075 | 74.729.532 | 76.262.797 | 78.568.327 | 2,2% |
| Mato Grosso do Sul | 13.236.600 | 14.275.176 | 14.479.181 | 14.685.636 | 14.894.557 | 15.115.701 | 1,7% |
| Mato Grosso | 19.688.844 | 21.121.042 | 21.307.347 | 21.492.656 | 21.676.854 | 21.112.142 | 0,9% |
| Pará | 18.809.833 | 20.348.331 | 20.703.368 | 21.064.468 | 21.431.730 | 21.531.805 | 1,7% |
| Paraíba | 7.959.867 | 8.609.068 | 8.757.382 | 8.908.185 | 9.061.518 | 9.092.029 | 1,7% |
| Pernambuco | 20.872.284 | 22.627.615 | 23.071.648 | 23.524.391 | 23.986.015 | 24.697.414 | 2,1% |
| Piauí | 6.386.752 | 6.915.175 | 7.042.004 | 7.171.140 | 7.302.625 | 7.275.446 | 1,6% |
| Paraná | 40.190.694 | 43.689.281 | 44.667.638 | 45.667.654 | 46.689.803 | 48.090.337 | 2,3% |
| Rio de Janeiro | 48.187.388 | 52.597.293 | 53.994.128 | 55.425.798 | 56.893.137 | 60.438.440 | 2,9% |
| Rio Grande do Norte | 7.175.214 | 7.805.139 | 7.985.341 | 8.169.629 | 8.358.095 | 8.598.060 | 2,3% |
| Rondônia | 6.117.639 | 6.573.015 | 6.641.687 | 6.710.476 | 6.779.361 | 6.685.512 | 1,1% |
| Roraima | 1.607.077 | 1.739.049 | 1.769.929 | 1.801.348 | 1.833.316 | 1.856.811 | 1,8% |
| Rio Grande do Sul | 40.555.665 | 44.281.968 | 45.472.992 | 46.693.944 | 47.945.545 | 51.112.076 | 2,9% |
| Santa Catarina | 33.719.683 | 36.456.983 | 37.071.910 | 37.696.850 | 38.331.959 | 38.219.120 | 1,6% |
| Sergipe | 4.629.431 | 5.023.559 | 5.127.036 | 5.232.642 | 5.340.422 | 5.405.174 | 2,0% |
| São Paulo | 179.259.832 | 194.877.482 | 199.254.842 | 203.729.345 | 208.303.127 | 217.704.326 | 2,5% |
| Tocantins | 4.811.381 | 5.175.479 | 5.235.681 | 5.296.221 | 5.357.088 | 5.229.275 | 1,0% |
| Total estados | 663.552.246 | 719.979.812 | 734.744.745 | 749.935.254 | 765.635.444 | 788.956.757 | 2,2% |
| Total municípios | 363.064.515 | 393.384.870 | 400.887.230 | 408.409.361 | 415.876.063 | 416.184.981 | 1,7% |

Fonte: Elaboração própria com base nas simulações do estudo.

Como mostra a Tabela 12, entre 2029 e 2032 haverá coexistência entre ICMS e ISS e o novo IBS. Ao mesmo tempo, já estarão em operação a transição federativa e o mecanismo de distribuição complementar. A participação do IBS na arrecadação potencial aumentará gradualmente: 10% em 2029, 20% em 2030, 30% em 2031 e 40% em 2032. A substituição integral dos tributos atuais ocorrerá em 2033.

O ano de 2032 ilustra o funcionamento dessa etapa. Dos R$ 1,182 trilhão estimados, aproximadamente R$ 708,9 bilhões correspondem a ICMS e ISS e R$ 472,6 bilhões ao IBS. Desse montante de IBS, cerca de R$ 378,1 bilhões serão

retidos e redistribuídos segundo os coeficientes vinculados à receita média de 2019 a 2026. Dos R$ 94,5 bilhões restantes, aproximadamente R$ 4,7 bilhões serão destinados ao seguro-receita e R$ 89,8 bilhões serão distribuídos

diretamente pelo critério do destino.

Em 2033, embora o IBS substitua integralmente os tributos atuais, 90% de sua arrecadação ainda estará sujeita à retenção principal. Por essa razão, as mudanças de participação apresentadas na Tabela 11 serão incorporadas de forma gradual, reduzindo o impacto imediato da redistribuição sobre os entes que apresentam perda relativa.

No cenário central, nenhum estado apresenta redução de receita em termos absolutos em relação a 2025. Isso não significa, contudo, ausência de perda relativa: a avaliação do efeito da reforma deve comparar cada resultado com um cenário contrafactual sem reforma submetido às mesmas hipóteses macroeconômicas.

Note-se que, curiosamente, a receita média do conjunto dos estados cresceria a uma taxa de 2,2% a.a., acima da média, enquanto a dos municípios cresceria a 1,7% a.a. Isso se explica pelo fato de que, no quinto ano da reforma, 90% da receita de IBS estaria sendo distribuída pela média de 2019-2026, e a receita média dos estados nesse período é superior ao valor que arrecadaram em 2025 – ao contrário do que acontece com os municípios.

A Figura 3 apresenta a evolução agregada das receitas no cenário central entre 2025 e 2033 e encerra a análise da primeira etapa da transição.

Figura 3 — Evolução agregada no cenário central, 2025–2033

Fonte: elaboração própria.


### 6.2 Horizonte longo

Após o período inicial, a redução progressiva da parcela retida amplia o peso do princípio do destino na distribuição do IBS. A Tabela 13 acompanha esse processo em intervalos de dez anos até 2078 e apresenta, para cada ente, a taxa

média de crescimento desde o ano-base.

Tabela 13 — Simulação da regra de transição e seguro-receita do IBS nas próximas cinco décadas — R$ mil


| Ano | Média passada (2019-2026) | 2038 | 2048 | 2058 | 2068 | 2078 | Tx média cresc. |
|---|---|---|---|---|---|---|---|
| Total | 1.026.616.761 | 1.330.573.857 | 1.621.962.107 | 1.977.162.758 | 2.410.150.370 | 2.937.959.852 | 2,0% |
| ICMS+ISS | 1.026.616.761 | 0 | 0 | 0 | 0 | 0 | - |
| IBS | - | 1.330.573.857 | 1.621.962.107 | 1.977.162.758 | 2.410.150.370 | 2.937.959.852 | - |
| Retido/repartição média | - | 1.064.459.086 | 973.177.264 | 790.865.103 | 482.030.074 | 0 | - |
| Demais | - | 266.114.771 | 648.784.843 | 1.186.297.655 | 1.928.120.296 | 2.937.959.852 | - |
| Seguro-receita | - | 13.305.739 | 32.439.242 | 59.314.883 | 96.406.015 | 146.897.993 | - |
| Destino | - | 252.809.033 | 616.345.601 | 1.126.982.772 | 1.831.714.281 | 2.791.061.859 | - |
| % Tributos atuais | 100% | 0% | 0% | 0% | 0% | 0% | - |
| % IBS retido para transição |  | 80% | 60% | 40% | 20% | 0% | - |
| Distrito Federal | 16.460.712 | 22.236.596 | 27.730.951 | 34.565.338 | 43.063.172 | 53.625.260 | 2,3% |
| Acre | 1.663.398 | 2.315.916 | 2.897.332 | 3.622.333 | 4.525.925 | 5.651.558 | 2,3% |
| Alagoas | 6.945.289 | 8.478.981 | 10.327.417 | 12.578.808 | 15.320.996 | 18.660.969 | 1,9% |
| Amazonas | 16.235.923 | 20.828.462 | 25.095.843 | 29.728.730 | 34.398.249 | 39.471.933 | 1,7% |
| Amapá | 1.273.495 | 1.789.511 | 2.350.861 | 3.072.253 | 3.996.863 | 5.179.100 | 2,7% |
| Bahia | 31.395.685 | 41.321.469 | 50.049.383 | 60.618.307 | 73.416.006 | 88.911.787 | 2,0% |
| Ceará | 16.161.369 | 21.727.212 | 26.717.868 | 32.852.369 | 40.392.363 | 49.659.238 | 2,1% |
| Espírito Santo | 16.943.675 | 19.820.286 | 22.745.530 | 26.474.583 | 32.081.012 | 38.659.595 | 1,6% |
| Goiás | 25.195.705 | 32.262.645 | 38.523.120 | 45.978.344 | 54.851.358 | 65.405.600 | 1,8% |
| Maranhão | 11.938.393 | 14.435.604 | 17.770.387 | 21.873.458 | 26.921.384 | 33.131.228 | 1,9% |
| Minas Gerais | 66.130.419 | 86.145.619 | 103.547.838 | 124.440.615 | 149.518.191 | 179.611.473 | 1,9% |
| Mato Grosso do Sul | 13.236.600 | 16.200.758 | 18.558.416 | 21.761.434 | 26.323.539 | 31.665.182 | 1,7% |
| Mato Grosso | 19.688.844 | 22.751.775 | 26.374.536 | 30.492.882 | 36.024.048 | 43.857.866 | 1,5% |
| Pará | 18.809.833 | 23.770.550 | 28.970.553 | 35.308.099 | 43.032.034 | 52.445.640 | 2,0% |
| Paraíba | 7.959.867 | 10.036.957 | 12.231.635 | 14.906.199 | 18.165.580 | 22.137.655 | 1,9% |
| Pernambuco | 20.872.284 | 26.952.256 | 32.085.014 | 38.173.272 | 45.389.368 | 53.935.298 | 1,8% |
| Piauí | 6.386.752 | 8.143.276 | 10.196.240 | 12.757.841 | 15.952.396 | 19.934.283 | 2,2% |
| Paraná | 40.190.694 | 53.315.433 | 65.527.124 | 80.530.468 | 98.962.523 | 121.605.487 | 2,1% |
| Rio de Janeiro | 48.187.388 | 66.495.471 | 80.488.460 | 97.421.195 | 117.910.168 | 142.700.904 | 2,1% |
| Rio Grande do Norte | 7.175.214 | 9.581.991 | 11.897.468 | 14.767.560 | 18.324.134 | 22.730.217 | 2,2% |
| Rondônia | 6.117.639 | 7.193.262 | 8.309.999 | 9.570.876 | 11.476.178 | 13.922.415 | 1,6% |
| Roraima | 1.607.077 | 2.037.187 | 2.451.913 | 2.950.584 | 3.550.076 | 4.270.634 | 1,9% |
| Rio Grande do Sul | 40.555.665 | 56.141.309 | 67.727.578 | 81.696.047 | 98.534.432 | 118.829.819 | 2,0% |
| Santa Catarina | 33.719.683 | 42.365.097 | 52.052.644 | 63.951.459 | 78.565.453 | 96.513.194 | 2,0% |
| Sergipe | 4.629.431 | 6.035.310 | 7.521.721 | 9.369.720 | 11.666.391 | 14.519.620 | 2,2% |
| São Paulo | 179.259.832 | 237.956.199 | 284.199.119 | 339.283.886 | 404.865.387 | 482.899.288 | 1,9% |
| Tocantins | 4.811.381 | 5.728.501 | 6.873.199 | 8.244.532 | 9.886.865 | 11.853.125 | 1,7% |
| Total estados | 663.552.246 | 866.067.635 | 1.043.222.150 | 1.256.991.190 | 1.517.114.092 | 1.831.788.369 | 1,9% |
| Total municípios | 363.064.515 | 464.506.222 | 578.739.958 | 720.171.568 | 893.036.277 | 1.106.171.483 | 2,1% |

Fonte: Elaboração própria com base nas simulações do estudo.

No cenário central, a receita agregada aumenta de aproximadamente R$ 1,027 trilhão no ano-base para R$ 1,331 trilhão em 2038 e R$ 2,938 trilhões em 2078. Paralelamente, a parcela do IBS sujeita à retenção principal diminui de 80% em 2038 para 60% em 2048, 40% em 2058, 20% em 2068 e zero em 2078. Assim, o crescimento da arrecadação ocorre simultaneamente à substituição gradual do critério histórico pelo princípio do destino.

As taxas médias estimadas para o período indicam o grau de ganho ou perda relativa de cada ente em comparação com o crescimento agregado do IBS. Uma taxa positiva de crescimento não significa, por si só, ganho com a reforma:

para os entes cuja participação diminui, a expansão da economia pode elevar a receita em termos absolutos e, ainda assim, produzir resultado inferior ao de um cenário contrafactual sem reforma sujeito à mesma hipótese macroeconômica.

Entre 2025 e 2078, a receita do conjunto dos estados cresce, em média, 1,9% ao ano, enquanto a dos municípios avança 2,1% ao ano. A inversão em relação ao período inicial decorre, sobretudo, da distribuição complementar, que tende a beneficiar proporcionalmente os municípios, onde se concentram as perdas relativas mais acentuadas. Segundo as estimativas, em 2078 os municípios receberão 79% dos recursos desse mecanismo, e os estados, 21%.

A Figura 4 sintetiza a trajetória agregada até 2078 e evidencia a redução da parcela retida ao longo da transição.

Figura 4 — Evolução agregada até 2078 — série provisória

Fonte: elaboração própria.


### 6.3 Sensibilidade às hipóteses de crescimento

Para avaliar a sensibilidade das projeções à trajetória da arrecadação, foram construídos três cenários: conservador, com crescimento anual de 1,5%; central, com crescimento de 2%; e de maior expansão, com crescimento de 3% ao ano. As taxas de crescimento não alteram os percentuais legais de substituição dos tributos atuais pelo IBS, nem os percentuais de retenção e distribuição da transição federativa. Elas modificam apenas o volume de recursos sobre o qual essas regras incidem.

A Tabela 14 compara os resultados dos três cenários nos anos iniciais da transição e, posteriormente, em intervalos de dez anos até 2078. Em todos eles, o IBS corresponde a 10% da arrecadação potencial em 2029, 20% em 2030, 30% em

2031 e 40% em 2032, passando a substituir integralmente ICMS e ISS em 2033.

Tabela 14 — Simulação da regra de transição e seguro-receita do IBS com diferentes taxas de crescimento — R$ mil


| Ano | Total | Tributos atuais | IBS | Retido | Não retido | Seguro-receita | Destino | Var. vs. 2025 | CAGR |
|---|---|---|---|---|---|---|---|---|---|
| 2025 | 1.028.576.869 | 1.028.576.869 | - | - | - | - | - | - | - |
| 2029 | 1.157.672.327 | 1.041.905.095 | 115.767.233 | 92.613.786 | 23.153.447 | 1.157.672 | 21.995.774 | 12,6% | 3,0% |
| 2030 | 1.192.402.497 | 953.921.998 | 238.480.499 | 190.784.400 | 47.696.100 | 2.384.805 | 45.311.295 | 15,9% | 3,0% |
| 2031 | 1.228.174.572 | 859.722.200 | 368.452.372 | 294.761.897 | 73.690.474 | 3.684.524 | 70.005.951 | 19,4% | 3,0% |
| 2032 | 1.265.019.809 | 759.011.886 | 506.007.924 | 404.806.339 | 101.201.585 | 5.060.079 | 96.141.506 | 23,0% | 3,0% |
| 2033 | 1.302.970.404 | - | 1.302.970.404 | 1.172.673.363 | 130.297.040 | 6.514.852 | 123.782.188 | 26,7% | 3,0% |
| 2038 | 1.510.499.808 | - | 1.510.499.808 | 1.208.399.847 | 302.099.962 | 15.104.998 | 286.994.964 | 46,9% | 3,0% |
| 2048 | 2.029.985.434 | - | 2.029.985.434 | 1.217.991.260 | 811.994.173 | 40.599.709 | 771.394.465 | 97,4% | 3,0% |
| 2058 | 2.728.130.674 | - | 2.728.130.674 | 1.091.252.270 | 1.636.878.404 | 81.843.920 | 1.555.034.484 | 165,2% | 3,0% |
| 2068 | 3.666.379.498 | - | 3.666.379.498 | 733.275.900 | 2.933.103.598 | 146.655.180 | 2.786.448.418 | 256,5% | 3,0% |
| 2078 | 4.927.307.460 | - | 4.927.307.460 | (0) | 4.927.307.460 | 246.365.373 | 4.680.942.087 | 379,0% | 3,0% |
|  |  |  |  |  |  |  |  |  |  |
| Ano | Total | Tributos atuais | IBS | Retido | Não retido | Seguro-receita | Destino | Var. vs. 2025 | CAGR |
| 2025 | 1.028.576.869 | 1.028.576.869 | - | - | - | - | - | - | - |
| 2029 | 1.091.693.997 | 982.524.598 | 109.169.400 | 87.335.520 | 21.833.880 | 1.091.694 | 20.742.186 | 6,1% | 1,5% |
| 2030 | 1.108.069.407 | 886.455.526 | 221.613.881 | 177.291.105 | 44.322.776 | 2.216.139 | 42.106.637 | 7,7% | 1,5% |
| 2031 | 1.124.690.448 | 787.283.314 | 337.407.135 | 269.925.708 | 67.481.427 | 3.374.071 | 64.107.356 | 9,3% | 1,5% |
| 2032 | 1.141.560.805 | 684.936.483 | 456.624.322 | 365.299.458 | 91.324.864 | 4.566.243 | 86.758.621 | 11,0% | 1,5% |
| 2033 | 1.158.684.217 | - | 1.158.684.217 | 1.042.815.796 | 115.868.422 | 5.793.421 | 110.075.001 | 12,6% | 1,5% |
| 2038 | 1.248.231.973 | - | 1.248.231.973 | 998.585.578 | 249.646.395 | 12.482.320 | 237.164.075 | 21,4% | 1,5% |
| 2048 | 1.448.624.164 | - | 1.448.624.164 | 869.174.498 | 579.449.665 | 28.972.483 | 550.477.182 | 40,8% | 1,5% |
| 2058 | 1.681.187.482 | - | 1.681.187.482 | 672.474.993 | 1.008.712.489 | 50.435.624 | 958.276.865 | 63,4% | 1,5% |
| 2068 | 1.951.086.707 | - | 1.951.086.707 | 390.217.341 | 1.560.869.366 | 78.043.468 | 1.482.825.897 | 89,7% | 1,5% |
| 2078 | 2.264.315.777 | - | 2.264.315.777 | (0) | 2.264.315.777 | 113.215.789 | 2.151.099.988 | 120,1% | 1,5% |
|  |  |  |  |  |  |  |  |  |  |
| Ano | Total | Tributos atuais | IBS | Retido | Não retido | Seguro-receita | Destino | Var. vs. 2025 | CAGR |
| 2025 | 1.028.576.869 | 1.028.576.869 | - | - | - | - | - | - | - |
| 2029 | 1.113.364.682 | 1.002.028.213 | 111.336.468 | 89.069.175 | 22.267.294 | 1.113.365 | 21.153.929 | 8,2% | 2,0% |
| 2030 | 1.135.631.975 | 908.505.580 | 227.126.395 | 181.701.116 | 45.425.279 | 2.271.264 | 43.154.015 | 10,4% | 2,0% |
| 2031 | 1.158.344.615 | 810.841.230 | 347.503.384 | 278.002.708 | 69.500.677 | 3.475.034 | 66.025.643 | 12,6% | 2,0% |
| 2032 | 1.181.511.507 | 708.906.904 | 472.604.603 | 378.083.682 | 94.520.921 | 4.726.046 | 89.794.875 | 14,9% | 2,0% |
| 2033 | 1.205.141.737 | - | 1.205.141.737 | 1.084.627.563 | 120.514.174 | 6.025.709 | 114.488.465 | 17,2% | 2,0% |
| 2038 | 1.330.573.857 | - | 1.330.573.857 | 1.064.459.086 | 266.114.771 | 13.305.739 | 252.809.033 | 29,4% | 2,0% |
| 2048 | 1.621.962.107 | - | 1.621.962.107 | 973.177.264 | 648.784.843 | 32.439.242 | 616.345.601 | 57,7% | 2,0% |
| 2058 | 1.977.162.758 | - | 1.977.162.758 | 790.865.103 | 1.186.297.655 | 59.314.883 | 1.126.982.772 | 92,2% | 2,0% |
| 2068 | 2.410.150.370 | - | 2.410.150.370 | 482.030.074 | 1.928.120.296 | 96.406.015 | 1.831.714.281 | 134,3% | 2,0% |
| 2078 | 2.937.959.852 | - | 2.937.959.852 | (0) | 2.937.959.852 | 146.897.993 | 2.791.061.859 | 185,6% | 2,0% |

Fonte: Elaboração própria com base nas simulações do estudo.

No curto prazo, as diferenças entre os cenários ainda são relativamente moderadas. Em 2029, a receita total alcança R$ 1,092 trilhão no cenário conservador, R$ 1,113 trilhão no cenário central e R$ 1,158 trilhão no cenário de maior expansão. Em relação a 2025, esses valores representam aumentos acumulados de 6,1%, 8,2% e 12,6%, respectivamente.

Em 2033, primeiro ano de substituição integral dos tributos atuais pelo IBS, a receita total atinge R$ 1,159 trilhão, R$ 1,205 trilhão e R$ 1,303 trilhão nos três cenários, o que corresponde a crescimentos acumulados de 12,6%, 17,2% e

26,7% em relação a 2025. Apesar da substituição integral, 90% do IBS ainda estará sujeito à retenção principal, de modo que a maior parcela dos recursos continuará sendo repartida segundo os coeficientes vinculados à receita média

de referência.

O cenário de 2% ocupa posição intermediária e, por isso, constitui a referência principal do estudo. Nessa trajetória, a receita passa de R$ 1,029 trilhão em 2025 para R$ 1,205 trilhão em 2033, R$ 1,331 trilhão em 2038 e R$ 1,622 trilhão

em 2048. Posteriormente, alcança R$ 1,977 trilhão em 2058, R$ 2,410 trilhões em 2068 e R$ 2,938 trilhões em 2078. Ao final do período, a receita equivale a aproximadamente 2,86 vezes o valor do ano-base, com crescimento acumulado de 185,6%.

O efeito da capitalização faz com que as diferenças entre os cenários se ampliem progressivamente. Em 2033, a receita do cenário de 3% supera a do cenário central em aproximadamente 8,1%, enquanto o cenário central supera o conservador em cerca de 4,0%. Em 2048, essas diferenças alcançam, respectivamente, 25,2% e 12,0%; em 2078, chegam a 67,7% e 29,8%. Na comparação direta entre os extremos, a distância aumenta de aproximadamente 6,0% em 2029 para 117,6% em 2078, quando as receitas projetadas somam R$ 4,927 trilhões no cenário de 3% e R$ 2,264 trilhões no cenário de 1,5%.

Além do nível da arrecadação, a Tabela 14 evidencia a mudança em sua forma de distribuição. Em 2033, após a retenção complementar, aproximadamente 9,5% da receita será destinada diretamente segundo o princípio do destino. Essa participação aumenta para cerca de 19% em 2038, 38% em 2048, 57% em 2058 e 76% em 2068.


### 6.4 Compensação de perdas pelo seguro-receita

No cenário baseline, considera-se crescimento da arrecadação de 2% ao ano. O denominado Fundo de Compensação de Perdas corresponde, para fins deste estudo, à parcela da arrecadação do IBS retida para a distribuição complementar prevista nos arts. 110 e 117 da Lei Complementar nº 227/2026. De 2029 a 2077, a retenção complementar corresponde a 5% da parcela da receita remanescente após a retenção principal da transição. O crescimento do montante disponível decorre, portanto, de dois movimentos simultâneos: a expansão anual de 2% da arrecadação e a redução gradual da retenção principal, que aumenta a base sobre a qual incide o percentual destinado à compensação.

Em 2029, quando o IBS representa apenas 10% da arrecadação potencial e 80% dessa parcela ainda é objeto da retenção principal, o mecanismo complementar dispõe de aproximadamente R$ 1,1 bilhão. O montante aumenta para R$ 6 bilhões em 2033, R$ 13,3 bilhões em 2038, R$ 32,4 bilhões em 2048, R$ 59,3 bilhões em 2058 e R$ 96,4 bilhões em 2068. Em 2077, último ano de aplicação integral do percentual de 5%, o valor alcança aproximadamente R$ 141,1 bilhões.

O crescimento do mecanismo não decorre apenas da hipótese de expansão de 2% ao ano. Em 2029, a retenção complementar representa somente 0,1% da arrecadação total, pois incide sobre uma parcela ainda reduzida do IBS não submetida à retenção principal. Essa participação aumenta para aproximadamente 0,5% da arrecadação em 2033, 1% em 2038, 2% em 2048, 3% em 2058, 4% em 2068 e 4,9% em 2077. Dessa forma, a ampliação do mecanismo está diretamente relacionada ao avanço da distribuição pelo destino e à redução progressiva da parcela distribuída segundo os coeficientes históricos.

Tabela – Distribuição estimada do seguro-receita aos governos estaduais: cenário baseline de crescimento de 2% ao ano - em R$ mil


| UF | Primeiro ano de recebimento | Valor em 2078 | Total acumulado 2029–2078 |
|---|---|---|---|
| AM | 2031 | 15.761.903 | 331.915.955 |
| ES | 2056 | 5.150.007 | 55.217.703 |
| MS | 2055 | 4.516.926 | 50.940.922 |
| MT | 2064 | 3.473.051 | 24.617.819 |
| RO | 2061 | 1.361.787 | 11.478.096 |
| Total | – | 30.263.674 | 474.170.495 |

Fonte: Elaboração própria com base nas simulações do estudo.

Em 2078, a retenção principal será zerada, mas o percentual destinado à distribuição complementar começará a ser reduzido à razão de 1/20 ao ano. Consequentemente, a alíquota aplicável nesse exercício será de 4,75%, resultando em um montante estimado de R$ 139,6 bilhões. Apesar do crescimento de 2% da arrecadação total, esse valor será ligeiramente inferior ao de 2077, em razão do início da redução legal do percentual da retenção complementar.

A distribuição simulada revela forte concentração dos recursos nos Municípios. Nos dois primeiros anos, 2029 e 2030, nenhum Estado aparece como beneficiário, de modo que, segundo os resultados do modelo, a totalidade dos recursos seria destinada a entes municipais. A participação estadual começa em 2031, com a entrada do Amazonas, e cresce gradualmente: corresponde a aproximadamente 10,9% do mecanismo em 2033, 13,3% em 2038, 13,6% em 2048, 14,6% em 2058 e 18% em 2068.

No final do período analisado, os Estados representam aproximadamente 20,6% da distribuição, enquanto os Municípios concentram cerca de 79,4%. Aplicando-se o percentual legal de 4,75% em 2078, aproximadamente R$ 28,8 bilhões seriam destinados aos Estados e R$ 110,8 bilhões aos Municípios. Esse resultado confirma que, no cenário simulado, a distribuição complementar possui impacto predominantemente municipal, refletindo perdas relativas mais disseminadas ou intensas entre os Municípios.

Entre os Estados, o Amazonas é o primeiro a ingressar no mecanismo, em 2031, e permanece como único beneficiário estadual até 2054. Mato Grosso do Sul passa a receber recursos em 2055, seguido pelo Espírito Santo em 2056, Rondônia em 2061 e Mato Grosso em 2064. Assim, ao final do período, apenas cinco Estados aparecem como beneficiários da distribuição complementar.

Em 2078, mantidas as participações calculadas pelo simulador e aplicado o percentual corrigido de 4,75%, o Amazonas receberia aproximadamente R$ 15 bilhões, o Espírito Santo R$ 4,9 bilhões, Mato Grosso do Sul R$ 4,3 bilhões, Mato Grosso R$ 3,3 bilhões e Rondônia R$ 1,3 bilhão. O Amazonas concentraria aproximadamente 52% da parcela estadual distribuída nesse exercício e cerca de 10,7% do total do mecanismo.

Considerando a soma simples dos valores anuais entre 2029 e 2078, sem desconto a valor presente, o mecanismo movimentaria aproximadamente R$ 2,783 trilhões. Desse total, cerca de R$ 474,2 bilhões, ou 17%, seriam destinados aos Estados, enquanto aproximadamente R$ 2,309 trilhões, ou 83%, seriam direcionados aos Municípios. Entre os beneficiários estaduais, o Amazonas responderia pela maior parcela acumulada, em razão de seu ingresso antecipado e de sua permanência no mecanismo durante quase todo o período.

A ausência de recursos para determinado Estado não significa necessariamente inexistência de perdas com a reforma. Significa que, segundo as premissas do modelo, esse ente não se encontra entre aqueles com as menores relações entre sua receita recente do IBS e a receita média de referência ajustada, critério utilizado para ordenar os beneficiários da distribuição complementar.


## 9. Considerações finais

O modelo de projeção de receitas apresentado nesta nota técnica tem sido aperfeiçoado e atualizado anualmente, o que continuará ocorrendo pelos próximos anos, tanto pela necessidade de se considerar as receitas obtidas pelos entes federados até 2026, quanto também pelo resultado a ser obtido com a CBS no ano de sua introdução, em 2027, quando poderemos ter um panorama mais preciso sobre a base tributável efetiva do novo sistema tributário em gestação.

Além disso, o simulador permite customizar os parâmetros de projeção considerando as particularidades de cada estado, como seu diferencial de crescimento em relação às demais unidades federadas. Dessa forma, é possível aprimorar ao longo do tempo as estimativas inicialmente apresentadas na presente nota técnica, propiciando às autoridades estaduais melhores projeções para seu planejamento orçamentário futuro.

Os resultados do cenário central indicam que a mudança para a tributação no destino produz redistribuição relevante entre as unidades da Federação, ainda que o mecanismo de transição atenue seus efeitos no curto e no médio prazo. Os resultados devem ser avaliados principalmente pela alteração das participações relativas e pela comparação com um contrafactual sem reforma submetido às mesmas hipóteses macroeconômicas.

As estimativas de alíquotas, receitas e taxas de crescimento permanecem condicionadas à validação da base de 2026, à conciliação das informações fiscais, à confirmação das contribuições estaduais elegíveis e à definição oficial dos redutores aplicáveis às compras governamentais. Por essa razão, a contribuição principal do estudo não é produzir um único valor pontual, mas oferecer um modelo reproduzível para avaliar cenários e atualizar os resultados à medida que novas informações sejam disponibilizadas.

A organização das evidências por UF permitirá ao COMSEFAZ utilizar o modelo tanto no acompanhamento da regulamentação quanto no planejamento orçamentário e na futura verificação dos coeficientes divulgados pelo CGIBS.


## Referências

BRASIL. Emenda Constitucional nº 132, de 20 de dezembro de 2023. Altera o Sistema Tributário Nacional. Disponível em: https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm.

BRASIL. Lei Complementar nº 214, de 16 de janeiro de 2025, texto compilado. Institui o IBS, a CBS e o Imposto Seletivo. Disponível em: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm.

BRASIL. Lei Complementar nº 227, de 13 de janeiro de 2026. Institui o Comitê Gestor do IBS e disciplina a distribuição da receita. Disponível em: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm.

Orair, R.O.; Gobetti, S.W. Reforma Tributária e Federalismo Fiscal: Uma Análise das Propostas de Criação de um Novo Imposto Sobre o Valor Adicionado Para o Brasil. Texto para Discussão 2530. Rio de Janeiro: IPEA, 2019.

Gobetti, S.W.; Orair, R.O.; Monteiro, P.K. Os impactos redistributivos (na Federação) da reforma tributária. Nota técnica 17, Carta de Conjuntura do IPEA nº 59. Rio de Janeiro: IPEA, 2023.

IBGE. Censo Demográfico 2022; Pesquisa de Orçamentos Familiares 2017–2018; Contas Nacionais e Regionais; Tabela de Recursos e Usos regionalizada experimental.

STN. Siconfi/FINBRA e Declaração das Contas Anuais.

RFB. Grandes Números do IRPF e bases de distribuição de renda.


---

## Notas de rodapé do documento original

1. As declarações do IRPF foram utilizadas como base de mensuração da renda de quem ganha acima de cinco salários-mínimos e que representam cerca de 20% da população adulta. Para essa parcela da população, em média as declarações do IRPF revelam uma renda duas vezes maior do que aquela captada pelo censo.

2. De acordo com o art. 115 da LC 227, a receita média de referência dos Estados deve considerar, além do ICMS propriamente dito, “a receita com contribuições destinadas ao financiamento de fundos estaduais estabelecidas como condição à aplicação de diferimento, regime especial ou outro tratamento diferenciado relativo ao ICMS”. Somente AM, MT e GO possuem receitas dessa natureza sendo contabilizadas por fora do ICMS.
