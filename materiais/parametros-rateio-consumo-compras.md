# Parâmetros do rateio por consumo e compras governamentais: decisões e justificativas

Este documento registra, para cada parâmetro que entra no coeficiente de destino do IBS (Estudo 17), o valor adotado, a evidência que o sustenta, as alternativas descartadas e o que o alteraria. A regra geral de decisão é a seguinte: quando a lei decide, segue-se a lei; quando os dados do acervo decidem, adota-se o valor que eles sustentam, com o intervalo de incerteza; quando nem a lei nem os dados decidem, adota-se um valor central explícito, com a faixa publicada e a sensibilidade dos resultados. Nenhum valor depende de estimativas de terceiros. As fontes são a Declaração de Contas Anuais do SICONFI (estados, municípios e União), os microdados da POF 2017-18 e o Censo 2022 do IBGE e as Contas Nacionais do IBGE.

## 1. Cota-parte sobre as compras estaduais: decisão jurídica

**Decisão:** o IBS das compras do Estado entra na base sobre a qual se calcula a cota-parte de 25% dos municípios. Não é um cenário, é a regra do modelo.

**Fundamento.** O art. 149-C da Constituição destina o produto do IBS sobre as aquisições da administração direta, autarquias e fundações ao ente contratante. O art. 106, III, da LC 227/2026 inclui esse valor na receita inicial do ente, e os arts. 107 a 111 o levam à Receita-Base. O art. 118 da mesma lei parte da Receita-Base do Estado e, no § 3º, deduz dela a parcela dos municípios, a do art. 158, IV, "b", da Constituição, que é de 25% do IBS "distribuído aos Estados"; o art. 128 trata da repartição entre os municípios. Nenhum desses dispositivos exclui as compras da base da cota-parte, e as exceções que a lei prevê para as compras são só duas: a dispensa de licitação presencial (arts. 472, parágrafo único, I, e 473, § 2º) e, apenas quanto ao redutor, as alíquotas nacionalmente uniformes e o Simples/MEI (art. 472, parágrafo único, II e III). Onde a lei não abre exceção, a base é a Receita-Base inteira.

**Revisão.** Só mudaria se o Comitê Gestor regulamentar de forma diferente, hipótese que nenhum dispositivo lido sugere.

## 2. Elasticidade-renda do consumo: ε = 0,80

**O que é.** Quanto o consumo cresce quando a renda cresce. Com ε = 1 o consumo seria proporcional à renda e os municípios mais ricos pesariam mais do que devem no rateio do destino próprio. O consumo esperado de um município é a população multiplicada pelo consumo esperado de cada família, que cresce com a renda elevada a ε. A renda de cada município é aproximada por uma lognormal com a média e a mediana do Censo 2022.

**Evidência (microdados da POF 2017-18, 58.033 unidades de consumo).** O consumo somado dos microdados reproduz a tabela 1.1.13 do IBGE com razão 1,0000 nas 27 UFs, usando a fórmula oficial da Memória de Cálculo. As estimativas:

| Método | ε |
|---|---|
| Entre famílias (MQO log-log, ponderado) | 0,751 (EP 0,005) |
| Entre 20 faixas de renda per capita | 0,738 |
| Entre 54 grupos de UF e situação (urbano/rural) | 0,866 (EP 0,016) |
| Entre 557 estratos amostrais da POF | 0,866 (EP 0,015) |
| Regiões, entre famílias | de 0,63 (Norte) a 0,77 |
| Variável instrumental (escolaridade da pessoa de referência) | 1,03 (descartada) |

**Por que 0,80.** A estimativa entre famílias (0,75) é um limite inferior: o erro de medida da renda e a renda transitória enviesam o coeficiente para baixo. A estimativa entre localidades (0,87, idêntica com 54 grupos e com 557 estratos) elimina esse viés, mas pode ter viés para cima, porque as áreas de renda mais alta têm também preços mais altos, o que eleva renda e consumo nominais juntos. Os dois limites se justificam, portanto, por razões opostas e conhecidas. Adota-se o ponto médio, 0,80, e publica-se a faixa de 0,75 a 0,87. O resultado quase não depende da escolha dentro da faixa: trocar 0,80 por 0,75 ou 0,87 muda a variação média do coeficiente municipal em cerca de 1 ponto percentual. A variável instrumental foi descartada porque o valor obtido (1,03) é implausível e a hipótese de exclusão é violada: a escolaridade afeta o consumo também por preferências.

**Limitações.** O valor é único, mas a curva não tem elasticidade constante (de 0,47 nos 20% mais pobres a 0,89 na faixa de 50% a 80%), e a lognormal é uma aproximação da distribuição de renda municipal.

## 3. Peso das compras no IBS subnacional: θ_M = 41,6% (municipal) e θ_E = 6,0% (estadual)

**O que é.** Parcela do IBS de cada esfera que vem das compras do próprio governo (e vai ao ente que comprou), em vez do consumo das famílias (e do critério de destino). Define o quanto o rateio segue a despesa da prefeitura em vez da renda dos moradores.

**Derivação.** O art. 370 da LC 214 manda calibrar o redutor das compras para que a receita seja neutra: o IBS e a CBS sobre as compras públicas devem render o que os tributos antigos rendiam sobre as mesmas operações. O art. 473 destina esse produto ao comprador, com a alíquota do comprador fixada na soma de IBS e CBS (§ 1º). Logo, o IBS que o Estado ou município recebe sobre suas compras equivale aos tributos antigos embutidos nelas: ICMS e ISS e também PIS, Cofins e IPI. A carga média dos tributos antigos sobre o gasto final é τ = (R + F) ÷ (C_fam + f × C_gov), onde R é o bolo subnacional (ICMS líquido, ISS e FECOP, DCA 2025: R$ 1.020 bi), F é a receita de PIS, Cofins e IPI (DCA da União 2025: R$ 666 bi), C_fam é o consumo das famílias (Contas Nacionais 2025: R$ 8.081 bi) e C_gov são as compras estaduais e municipais da DCA I-D (R$ 738 bi, média de 2024 e 2025 a preços de 2025; seção 5), e f é a fração delas que carrega a carga média. A receita de compras é X = τ × f × C_gov, e a parte de famílias do IBS subnacional é R − X, dividida entre as esferas pelas alíquotas de referência (α_E = 85,1%, α_M = 14,9%). Daí θ_M = X_M ÷ (X_M + α_M (R − X)) e θ_E = X_E ÷ (X_E + α_E (R − X)).

**Como se estima f.** f é a fração das compras que carrega a carga média dos tributos antigos. Dois testes com dados oficiais (`data/estima-fracao-compras-carga.py`) a estimam. O primeiro compara a carga de impostos sobre produtos da cesta que a administração pública compra com a da cesta das famílias, nas Tabelas de Recursos e Usos 2023 do IBGE (carga de IPI, ICMS e outros impostos por grupo de produtos; composição do consumo intermediário da atividade "Administração, defesa, saúde e educação públicas" e do consumo das famílias). As compras do governo carregam 4% a 9% mais imposto que o consumo das famílias, porque o governo compra mais energia, comunicações e serviços financeiros e quase nenhum aluguel, que não paga imposto; a variante que exclui o grupo financeiro (cujos "outros impostos" incluem o IOF, que a reforma não substitui) dá 1,04 e a que o inclui, 1,09 (cesta de custeio). Como a mesma medida vale nas duas pontas, o que ela não capta (a cascata de tributos nos insumos) afeta ambas por igual. O segundo teste verifica se a proxy tem o tamanho certo: o consumo intermediário da administração pública (R$ 583 bi em 2023, R$ 679 bi em 2025 pelo PIB nominal) está a 3% do custeio da proxy (elementos 3.3.90.* da DCA I-D, média de 2024 e 2025 a preços de 2025, de Estados, municípios e União 2025: R$ 658 bi). O produto dos dois testes dá f entre 1,06 e 1,10.

**Valor adotado.** Como f é uma fração, adota-se f = 1,0 como valor central e publica-se a faixa de 0,8 a 1,0. O limite inferior cobre o que os testes não captam: a cascata de tributos nos insumos (que pode diferir entre as cestas), a classificação das despesas na DCA (parte de 3.3.90.39 pode não ser compra tributável) e o fato de os dois testes serem nacionais. Em versão anterior usava-se 0,8, ponto médio de uma faixa de 0,6 a 1,0 sem amparo em dados; a evidência exclui a metade inferior dessa faixa. A tabela mostra a sensibilidade, na leitura legal (o comprador recebe também o equivalente à CBS) e na leitura restritiva (só a parte subnacional):

Leitura legal (federal incluída):

| f | τ | X (R$ bi) | θ_M | θ_E |
|---|---|---|---|---|
| 0.80 | 19,4% | 115 | 36,0% | 4,8% |
| 0.85 | 19,4% | 121 | 37,5% | 5,1% |
| 0.90 | 19,3% | 128 | 38,9% | 5,4% |
| 0.95 | 19,2% | 135 | 40,3% | 5,7% |
| 1.00 | 19,1% | 141 | 41,6% | 6,0% |

Leitura restritiva (só tributos subnacionais), como limite inferior:

| f | τ | X (R$ bi) | θ_M | θ_E |
|---|---|---|---|---|
| 0.80 | 11,8% | 69 | 24,5% | 2,8% |
| 0.85 | 11,7% | 73 | 25,6% | 3,0% |
| 0.90 | 11,7% | 77 | 26,7% | 3,2% |
| 0.95 | 11,6% | 81 | 27,8% | 3,3% |
| 1.00 | 11,6% | 85 | 28,8% | 3,5% |

**Por que a leitura legal.** O art. 473, § 1º, II, "b", fixa a alíquota estadual do IBS na soma das alíquotas de IBS e CBS após o redutor; o valor arrecadado a essa alíquota é, portanto, IBS extinto destinado ao Estado contratante (art. 106, III, da LC 227). A leitura restritiva ignora a parcela federal, que a lei também direciona ao comprador. **Revisão.** Quando o Poder Executivo e o Comitê Gestor divulgarem o redutor do art. 370, f pode ser substituído por valor oficial. O script `data/calibra-peso-compras.py` recalcula tudo.

## 4. Teto de compras por habitante: percentil 99 nacional (R$ 10.233)

**O que é.** Alguns municípios, em geral pequenos e financiados por royalties ou compensações minerais, têm compras por habitante muito acima dos demais, (valores atípicos por erro de classificação, como Quinta do Sol/PR, são tratados antes, pela regra da seção 5). O teto limita o peso de cada município ao valor do percentil 99. Sem ele, um único município (Presidente Kennedy/ES) teria o peso intra-UF 343% maior, e o rateio da UF passaria a depender dele.

**Evidência de robustez.** Variar o percentil de 95% a 99,5% muda pouco o resultado:

| Percentil | Teto (R$/hab.) | Média das diferenças vs. p99 | Máxima diferença | Correlação de postos |
|---|---|---|---|---|
| sem teto | — | 0,47% | 343,1% | 0,99979 |
| 99,5% | 11.536 | 0,11% | 10,6% | 0,99999 |
| **99%** | **10.233** | — | — | — |
| 97,5% | 8.461 | 0,33% | 15,0% | 0,99992 |
| 95% | 6.994 | 0,95% | 27,4% | 0,99960 |

(Diferenças no peso final do município no rateio do IBS próprio da UF, já combinados consumo e compras.) O percentil 99 é a winsorização padrão de 1% e fica no centro de um intervalo em que a ordenação dos municípios é praticamente invariante. O teto limita 56 municípios e retira 0,7% das compras totais. **Limitação.** Valores extremos podem ser reais (royalties), e o teto subestima esses casos.

## 5. Outros tratamentos

Municípios sem dado utilizável em nenhum dos dois anos (14, entre sem informação, valor zero ou negativo e dado inconsistente) recebem a mediana per capita da UF vezes a população. A regra de inconsistência é objetiva e geral: compras acima de 90% da despesa total liquidada (`LIM_COMPRAS_DESPESA` em `data/rateio_consumo_compras.py`). Uma prefeitura não pode gastar quase tudo em compras, porque a folha de pessoal responde por cerca de 40% a 50% da despesa dos municípios. O único caso é Quinta do Sol/PR: 95% da despesa em 3.3.90.39 e nenhum gasto de pessoal registrado, o que indica folha classificada como serviço de terceiros. Os municípios com compras per capita muito altas, mas com folha de pessoal normal (Presidente Kennedy/ES, com 74%, e os de royalties), não são tocados por essa regra: o teto do percentil 99 cuida deles. O Distrito Federal não separa as esferas: as compras do ente distrital entram na esfera estadual. O peso das compras no IBS estadual é calibrado pela mesma equação do municipal (θ_E).

## 5-B. Anos usados: média de 2024 e 2025

**Decisão.** As compras de cada ente são a média de 2024 e 2025, a preços de 2025 (PIB nominal), calculada por `data/build-compras-media.py`; se só um dos anos tem dado válido, usa-se esse ano. **Fundamento.** O ano-base do modelo é 2025, mas (i) nenhum dos dois anos cobre todos os entes (2025 tem 74 municípios sem dado, por entrega atrasada; 2024 tem 24); (ii) a ordenação das compras per capita entre os dois anos tem correlação de postos de apenas 0,88, porque investimento e obras vêm em ondas; e (iii) 2024 foi ano de eleição municipal, com mais obras, e 2025 o primeiro ano de mandato, de modo que cada ano isolado enviesa o rateio em um sentido. A média dos dois cobre metade do ciclo eleitoral e preenche as lacunas, e a imputação pela mediana da UF cai de 31 para 14 municípios. **Limitação.** Dois anos ainda não cobrem o ciclo completo de quatro anos; quando a DCA de 2026 for publicada, a média pode ser ampliada, o que o script faz sem alteração de método.

## 5-A. Composição da proxy de compras (elementos de despesa da DCA I-D)

**Regra.** Entram os elementos de despesa liquidada que correspondem a aquisição onerosa de bens e serviços de pessoa jurídica pela administração: 3.3.90.30, .32, .33 (passagens e locomoção), .34 (terceirização de mão de obra contabilizada como pessoal, nos termos da LRF), .35, .37, .39, .40 e, no investimento, 4.4.90.35, .39, .40, .51, .52 e .61. Ficam fora pessoal, juros, transferências sem contraprestação (3.3.50, 3.3.60, 3.3.40/41), serviços de pessoa física (3.3.90.36, pessoa física não é contribuinte em regra), obrigações tributárias, sentenças e exercícios anteriores. **Fundamento.** O art. 473 da LC 214 destina ao comprador o imposto das operações em que a administração adquire bens e serviços de contribuintes; subvenção e transferência não são fornecimento oneroso.

**Testes de sensibilidade (coleta em `data/collect-compras-complementares-dca.py`).** A composição vigente soma R$ 488 bi nos municípios e R$ 250 bi nos Estados e DF (média de 2024 e 2025 a preços de 2025). O elemento 3.3.90.39 responde por 50% do total e obras (4.4.90.51), por 18%. As variantes abaixo medem quanto muda a participação nas compras (antes de aplicar o peso θ):

| Variante | Total vs. vigente | Participação da UF: diferença média | Participação do município na UF: diferença média |
|---|---|---|---|
| sem aquisição de imóveis (4.4.90.61) | −1% | 0,5% | 0,8% |
| metade dos serviços de terceiros (3.3.90.39 e 4.4.90.39) | −27% | 3,0% | 7,6% |
| sem obras (4.4.90.51) | −15% | 3,6% | 7,9% |
| só custeio (sem investimento) | −21% | 3,8% | 9,5% |
| sem serviços de terceiros | −54% | 9,7% | 24,1% |
| **com** transferências a entidades sem fins lucrativos (3.3.50), medido com os dados de 2024 | +17% | 9,7% | 8,4% |

(A inclusão de 3.3.90.33 e .34 mudou 1,6% a 2,6% as participações por UF e 3,1% as dos municípios na UF, medido com os dados de 2024.) Como as compras respondem por cerca de 43% do peso do município, essas diferenças diluem-se no coeficiente final. **Limitação.** A DCA não separa, dentro de 3.3.90.39, o que é serviço tributável do que não é (por exemplo, contratos com organizações sociais, que alguns entes registram em 3.3.50 e outros em 3.3.90.39). A proxy trata os dois registros como aparecem; a classificação oficial só virá com a regulamentação do Comitê Gestor.

## 6. Reprodutibilidade

`data/collect-compras-dca.py`, `data/collect-tributos-federais-uniao.py`, `data/estima-elasticidade-pof.py`, `data/calibra-peso-compras.py`, `data/rateio_consumo_compras.py` (parâmetros) e a cadeia `bash data/rodar-modelo.sh tudo`. Os valores podem ser sobrescritos por variáveis de ambiente (`RATEIO_EPS`, `RATEIO_THETA_M`, `RATEIO_THETA_E`, `RATEIO_TETO_P`).
