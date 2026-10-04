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

## 3. Peso das compras no IBS subnacional: θ_M = 36,7% (municipal) e θ_E = 4,6% (estadual)

**O que é.** Parcela do IBS de cada esfera que vem das compras do próprio governo (e vai ao ente que comprou), em vez do consumo das famílias (e do critério de destino). Define o quanto o rateio segue a despesa da prefeitura em vez da renda dos moradores.

**Derivação.** O art. 370 da LC 214 manda calibrar o redutor das compras para que a receita seja neutra: o IBS e a CBS sobre as compras públicas devem render o que os tributos antigos rendiam sobre as mesmas operações. O art. 473 destina esse produto ao comprador, com a alíquota do comprador fixada na soma de IBS e CBS (§ 1º). Logo, o IBS que o Estado ou município recebe sobre suas compras equivale aos tributos antigos embutidos nelas: ICMS e ISS e também PIS, Cofins e IPI. A carga média dos tributos antigos sobre o gasto final é τ = (R + F) ÷ (C_fam + f × C_gov), onde R é o bolo subnacional (ICMS líquido, ISS e FECOP, DCA 2025: R$ 1.020 bi), F é a receita de PIS, Cofins e IPI (DCA da União 2024, levada a 2025 pelo crescimento do PIB nominal: R$ 660 bi), C_fam é o consumo das famílias (Contas Nacionais 2025: R$ 8.081 bi) e C_gov são as compras estaduais e municipais da DCA I-D (R$ 743 bi em 2025), e f é a fração delas que carrega a carga média. A receita de compras é X = τ × f × C_gov, e a parte de famílias do IBS subnacional é R − X, dividida entre as esferas pelas alíquotas de referência (α_E = 85,1%, α_M = 14,9%). Daí θ_M = X_M ÷ (X_M + α_M (R − X)) e θ_E = X_E ÷ (X_E + α_E (R − X)).

**O que os dados não resolvem: f.** Depende do redutor oficial e da composição das compras (as de serviços tendem a ter carga antiga menor que as de bens). Dado o intervalo [0,6; 1,0], adota-se o ponto médio, f = 0,8. A tabela mostra a sensibilidade, na leitura legal (o comprador recebe também o equivalente à CBS) e na leitura restritiva (só a parte subnacional):

Leitura legal (federal incluída):

| f | τ | X (R$ bi) | θ_M | θ_E |
|---|---|---|---|---|
| 0.6 | 19,7% | 88 | 30,1% | 3,4% |
| 0.7 | 19,5% | 102 | 33,5% | 4,0% |
| 0.8 | 19,4% | 115 | 36,7% | 4,6% |
| 0.9 | 19,2% | 128 | 39,6% | 5,1% |
| 1.0 | 19,0% | 141 | 42,3% | 5,7% |

Leitura restritiva (só tributos subnacionais), como limite inferior:

| f | τ | X (R$ bi) | θ_M | θ_E |
|---|---|---|---|---|
| 0.6 | 12,0% | 53 | 20,1% | 2,0% |
| 0.7 | 11,9% | 62 | 22,7% | 2,4% |
| 0.8 | 11,8% | 70 | 25,1% | 2,7% |
| 0.9 | 11,7% | 78 | 27,4% | 3,0% |
| 1.0 | 11,6% | 86 | 29,5% | 3,3% |

**Por que a leitura legal.** O art. 473, § 1º, II, "b", fixa a alíquota estadual do IBS na soma das alíquotas de IBS e CBS após o redutor; o valor arrecadado a essa alíquota é, portanto, IBS extinto destinado ao Estado contratante (art. 106, III, da LC 227). A leitura restritiva ignora a parcela federal, que a lei também direciona ao comprador. **Revisão.** Quando o Poder Executivo e o Comitê Gestor divulgarem o redutor do art. 370, f pode ser substituído por valor oficial. O script `data/calibra-peso-compras.py` recalcula tudo.

## 4. Teto de compras por habitante: percentil 99 nacional (R$ 9.879)

**O que é.** Alguns municípios, em geral pequenos e financiados por royalties ou compensações minerais, têm compras por habitante muito acima dos demais, e outros têm valores atípicos na DCA (Quinta do Sol/PR, com 95% da despesa classificada como compras). O teto limita o peso de cada município ao valor do percentil 99. Sem ele, um único município (Presidente Kennedy/ES) teria o coeficiente de destino 296% maior, e o rateio da UF passaria a depender dele.

**Evidência de robustez.** Variar o percentil de 95% a 99,5% muda pouco o resultado:

| Percentil | Teto (R$/hab.) | Média das diferenças vs. p99 | Máxima diferença | Correlação de postos |
|---|---|---|---|---|
| sem teto | — | 0,23% | 163,2% | 0,99987 |
| 99,5% | 11.901 | 0,08% | 11,0% | 0,99998 |
| **99%** | **9.879** | — | — | — |
| 97,5% | 8.165 | 0,16% | 9,3% | 0,99997 |
| 95% | 6.808 | 0,42% | 16,7% | 0,99984 |

O percentil 99 é a winsorização padrão de 1% e fica no centro de um intervalo em que a ordenação dos municípios é praticamente invariante. O teto limita 56 municípios e retira 0,5% das compras totais. **Limitação.** Valores extremos podem ser reais (royalties), e o teto subestima esses casos.

## 5. Outros tratamentos

Municípios sem dado utilizável na DCA (24 sem informação e 6 com valor zero ou negativo) recebem a mediana per capita da UF vezes a população. O Distrito Federal não separa as esferas: as compras do ente distrital entram na esfera estadual. O peso das compras no IBS estadual é calibrado pela mesma equação do municipal (θ_E).

## 6. Reprodutibilidade

`data/collect-compras-dca.py`, `data/collect-tributos-federais-uniao.py`, `data/estima-elasticidade-pof.py`, `data/calibra-peso-compras.py`, `data/rateio_consumo_compras.py` (parâmetros) e a cadeia `bash data/rodar-modelo.sh tudo`. Os valores podem ser sobrescritos por variáveis de ambiente (`RATEIO_EPS`, `RATEIO_THETA_M`, `RATEIO_THETA_E`, `RATEIO_TETO_P`).
