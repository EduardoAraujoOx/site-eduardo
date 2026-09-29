# Auditoria da qualidade dos dados municipais do Paraná para o cálculo do IBS

## 1. Objetivo

Esta nota registra a auditoria realizada sobre os dados municipais utilizados no cálculo do coeficiente de participação na transição federativa e nas projeções de receita dos municípios paranaenses.

O objetivo não é avaliar a qualidade do Siconfi como sistema. A DCA/Siconfi recebe informações declaradas pelos próprios entes. O próprio Tesouro Nacional ressalta que Estados, Distrito Federal e Municípios são responsáveis pela exatidão e fidedignidade das informações encaminhadas ao Siconfi. A análise abaixo identifica, portanto, **inconsistências em registros municipais disponíveis na DCA/Siconfi quando confrontados com outras fontes oficiais**.

A auditoria tem quatro funções:

1. distinguir ausência real de informação de falha de coleta;
2. verificar a coerência da cota-parte municipal do ICMS contra os repasses informados pelo Estado do Paraná;
3. identificar valores temporalmente atípicos do ISS que exigem validação externa;
4. medir quanto essas inconsistências alteram a base de referência, o coeficiente histórico, o Seguro-Receita e as projeções municipais.

## 2. Fontes e procedimento

A base original utiliza a DCA Anexo I-C do Siconfi para ISS e cota-parte do ICMS, de 2019 a 2025.

A nova auditoria recoletou os 399 municípios do Paraná para os sete exercícios, totalizando 2.793 observações município-ano. Cada consulta passou a ser classificada como:

- **ok**: ISS e cota-parte encontrados;
- **partial**: apenas um componente encontrado;
- **absent_dca**: consulta bem-sucedida, mas contas-alvo ausentes;
- **api_error**: falha da consulta após todas as tentativas.

A ausência não é convertida automaticamente em zero.

Para a cota-parte do ICMS, cada observação municipal foi confrontada com o valor bruto de ICMS transferido ao município no Portal da Transparência do Estado do Paraná. A comparação utiliza o valor bruto porque a orientação contábil do Tesouro determina que a cota-parte do ICMS seja registrada pelo valor bruto, inclusive a parcela destinada ao Fundeb.

Na reconstrução diagnóstica, o valor total da cota-parte em cada ano continua ancorado na DCA do próprio Estado do Paraná. O Portal estadual é utilizado apenas para determinar a participação relativa de cada município nesse total:

[
CP_{m,t}
=
rac{T_{m,t}^{PR}}{sum_j T_{j,t}^{PR}}
, CP_{PR,t}^{DCA}.
]

Esse procedimento preserva o agregado estadual e corrige apenas a distribuição entre municípios.

Para o ISS, como não existe fonte estadual equivalente ao repasse do ICMS, a série da DCA continua sendo a fonte principal. Valores muito discrepantes em relação ao próprio histórico são apenas sinalizados para validação externa, sem correção automática.

## 3. Cobertura da nova coleta

A nova coleta encontrou:

- 2.730 observações completas;
- 29 respostas parciais;
- 34 observações sem as contas-alvo na primeira auditoria;
- 49 municípios que demandaram alguma imputação temporal;
- nenhum componente que permanecesse sem solução após o tratamento.

O exercício mostrou que a ausência de dados era uma fonte relevante de distorção. Em 29 municípios, a revisão inicial alterou a variação projetada para 2033 em pelo menos 10 pontos percentuais.

Exemplos:

- Jataizinho: de -33,1% para +11,1%;
- Alto Piquiri: de -33,1% para -6,8%;
- Campina da Lagoa: de -19,2% para -2,2%;
- Guaratuba: de +6,3% para -19,2%.

No caso de Guaratuba, a nova coleta recuperou cota-parte de aproximadamente R$ 22,4 milhões em 2025, valor compatível com o Portal estadual. A fotografia anterior continha cerca de R$ 5,0 milhões.

## 4. Confronto DCA municipal x Portal do Estado

Depois da correção dos nomes e da coleta, as 2.793 observações município-ano foram integralmente confrontadas.

Classificação:

| Situação | Observações |
|---|---:|
| Diferença de até 5% | 2.646 |
| Diferença entre 5% e 20% | 87 |
| Cota-parte ausente na DCA | 44 |
| Divergência entre 20% e 100% | 14 |
| Divergência superior a 100% | 2 |

Assim, aproximadamente 94,7% das observações ficam a até 5% da fonte estadual. O resultado é favorável à utilização geral da DCA, mas identifica um subconjunto pequeno e materialmente relevante de registros problemáticos.

Quinze municípios apresentam ao menos uma divergência superior a 20% em algum exercício: Barbosa Ferraz, Guaraqueçaba, Icaraíma, Itambaracá, Jandaia do Sul, Kaloré, Marumbi, Ourizona, Quinta do Sol, Rio Branco do Sul, Santo Antônio do Paraíso, São José das Palmeiras, Tamarana, Terra Boa e Virmond.

### 4.1 Barbosa Ferraz

Em 2025, a DCA municipal registra aproximadamente R$ 0,42 milhão de cota-parte do ICMS. O Portal do Estado registra cerca de R$ 13,94 milhões. A diferença é próxima de -97%.

Esse registro fazia a receita de referência de 2025 ficar artificialmente baixa e produzia uma variação projetada de aproximadamente +488% em 2033.

Com a cota-parte reconstruída a partir da fonte estadual, a base de 2025 passa de aproximadamente R$ 2,49 milhões para R$ 16,06 milhões. A projeção de 2033 passa de +487,8% para aproximadamente **+2,1%**.

Este caso demonstra que um outlier aparentemente econômico pode ser quase integralmente produzido por uma inconsistência cadastral/contábil na base.

### 4.2 Guaraqueçaba

Em 2025, a DCA municipal registra aproximadamente R$ 46,65 milhões de cota-parte do ICMS, enquanto o Portal do Estado registra cerca de R$ 15,52 milhões. A diferença supera 200%.

A reconstrução da cota-parte reduz a base de referência utilizada no exercício de aproximadamente R$ 70,55 milhões para R$ 39,40 milhões. A variação projetada para 2033 passa de -64,6% para aproximadamente **-47,8%**.

O caso, contudo, ainda não está encerrado. O ISS declarado em 2025 é de aproximadamente R$ 23,81 milhões, contra mediana de apenas R$ 0,52 milhão nos demais anos observados. A razão é superior a 45 vezes. Esse valor foi mantido no cenário auditado até que seja validado em fonte externa.

Guaraqueçaba ilustra a necessidade de combinar **validação cruzada entre fontes** e **testes temporais de plausibilidade**.

### 4.3 Pontal do Paraná

Pontal do Paraná permanece como forte outlier positivo, aproximadamente +119,6% em 2033, mesmo após a reconciliação.

Ao contrário dos casos anteriores, os valores elevados de cota-parte de 2020 e 2021 observados na DCA, aproximadamente R$ 52,7 milhões e R$ 65,8 milhões, aparecem com os mesmos valores no Portal do Estado. A anomalia estatística, portanto, não decorre de divergência entre as duas fontes.

Esse é um exemplo importante para o método: a auditoria não deve eliminar automaticamente observações extremas. Quando duas fontes oficiais independentes convergem, o valor deve ser preservado e sua causa econômica ou institucional investigada separadamente.

### 4.4 Padrão compatível com registro líquido de Fundeb

A auditoria encontrou 35 observações cuja cota-parte registrada na DCA é praticamente 20% inferior ao valor bruto do Portal estadual.

Esse padrão é consistente com a hipótese de que, em parte dos registros, o valor líquido após a retenção de 20% para o Fundeb tenha sido informado em campo que deveria refletir a receita bruta.

A hipótese não deve ser tratada como causa comprovada para cada ente sem inspeção contábil individual. Ainda assim, o padrão é economicamente e contabilmente relevante porque a orientação do Tesouro determina o registro bruto das receitas de cota-parte, com a destinação ao Fundeb registrada separadamente.

## 5. Efeito sobre o coeficiente e sobre a projeção

Um resultado importante é que a reconciliação da cota-parte produz alterações relativamente pequenas no **coeficiente histórico agregado de cada município**, porque esse coeficiente utiliza uma média de sete exercícios. Nenhum município apresentou mudança absoluta superior a 0,001 ponto percentual no CPT apenas com essa reconstrução.

Isso não significa que o problema seja irrelevante. A fotografia de 2025 é usada como referência no cenário contrafactual. Uma inconsistência concentrada justamente em 2025 pode mudar fortemente a base comparativa e, consequentemente, a variação percentual atribuída à reforma.

Seis municípios tiveram alteração superior a 10% na base de 2025 somente com a reconstrução da cota-parte. Barbosa Ferraz é o caso extremo, com aumento de aproximadamente 546% na base reconstruída.

Depois de reconciliar a cota-parte e recalcular nacionalmente o Seguro-Receita:

- 9 municípios têm nova alteração superior a 10 pontos percentuais em relação à projeção já corrigida para faltantes;
- os outliers com variação absoluta superior a 30% caem de 6 para 4;
- Barbosa Ferraz deixa de ser outlier;
- Pontal do Paraná permanece em aproximadamente +119,6%;
- Saudade do Iguaçu permanece em aproximadamente +57,2%;
- São Carlos do Ivaí permanece em aproximadamente +32,8%;
- Guaraqueçaba permanece em aproximadamente -47,8%, ainda sob investigação por causa do ISS.

## 6. Sinais de anomalia no ISS

Um filtro temporal conservador sinalizou 22 observações de ISS para verificação externa. O critério marca valores anuais superiores a cinco vezes ou inferiores a 20% da mediana dos demais anos observados.

Entre os casos mais relevantes estão:

- Guaraqueçaba, 2025: 45,5 vezes a mediana dos demais anos;
- Nossa Senhora das Graças, 2025: 7,4 vezes;
- Miraselva, 2025: 6,5 vezes;
- Itaipulândia, 2022: 6,3 vezes;
- São João do Caiuá, 2020: apenas 1,5% da mediana dos demais anos;
- Terra Boa, 2021: aproximadamente 2,1% da mediana.

Esses sinais não são tratados como erros. Eles definem uma fila de validação contra o Portal Informação para Todos/SIM-AM do TCE-PR ou outra fonte contábil oficial.

## 7. Auditoria do ente estadual

A mesma verificação foi aplicada ao governo do Estado do Paraná.

A recoleta direta do Siconfi reproduziu exatamente os valores já utilizados no modelo para ICMS bruto, FECOP e outras deduções em todos os anos de 2019 a 2025.

A cota-parte declarada pelo Estado também apresenta forte consistência com a soma dos repasses brutos do Portal estadual:

| Ano | DCA Estado | Soma Portal PR | Diferença |
|---|---:|---:|---:|
| 2020 | R$ 7,709 bi | R$ 7,715 bi | -0,08% |
| 2021 | R$ 9,560 bi | R$ 9,560 bi | ~0,00% |
| 2022 | R$ 10,222 bi | R$ 10,222 bi | ~0,00% |
| 2023 | R$ 11,338 bi | R$ 11,336 bi | +0,02% |
| 2024 | R$ 12,694 bi | R$ 12,701 bi | -0,06% |
| 2025 | R$ 13,247 bi | R$ 13,192 bi | +0,42% |

Em 2019, a coluna específica de transferências constitucionais não aparece na resposta atual da DCA estadual; o modelo já utiliza, nesse caso, o fallback teórico de 25% do ICMS.

O diagnóstico é, portanto, de que o problema relevante está principalmente na **alocação e escrituração municipal**, não nos agregados utilizados para o ente estadual.

## 8. Protocolo metodológico proposto

A experiência do Paraná sugere que estudos que utilizem a DCA para construir coeficientes municipais adotem uma rotina de auditoria anterior à estimação.

### 8.1 Hierarquia de fontes

Para a cota-parte do ICMS:

1. utilizar o DCA estadual para determinar o total agregado da transferência;
2. utilizar a base do Estado transferidor para determinar o rateio entre municípios;
3. utilizar a DCA municipal como fonte de validação, e não como única fonte do rateio quando houver inconsistência.

Para o ISS:

1. utilizar a DCA municipal como fonte principal;
2. realizar teste de completude;
3. realizar teste temporal de plausibilidade;
4. confrontar casos sinalizados com TCE/SIM-AM, prestação de contas ou outra fonte oficial.

### 8.2 Ausência não é zero

O pipeline deve distinguir explicitamente:

- valor observado igual a zero;
- conta ausente;
- resposta parcial;
- falha de coleta;
- valor imputado.

A transformação silenciosa de qualquer uma dessas categorias em zero pode enviesar diretamente a média histórica.

### 8.3 Regras automáticas de consistência

Recomenda-se incorporar ao processo de validação, entre outras, as seguintes regras:

- DCA municipal x transferência informada pelo Estado;
- alerta quando cota-parte DCA estiver próxima de 80% do valor bruto transferido;
- comparação da soma das cotas municipais com o total estadual;
- identificação de saltos ou quedas muito acentuadas em ISS e transferências;
- exigência de confirmação em segunda fonte antes da substituição de um valor observado.

### 8.4 Trilha de auditoria

Cada valor utilizado no coeficiente deve carregar uma classificação de proveniência, por exemplo:

- observado na fonte primária;
- confirmado em segunda fonte;
- reconstruído a partir do agregado estadual;
- imputado temporalmente;
- pendente de validação.

Isso permite reproduzir a estimativa e identificar quais resultados dependem de tratamento de dados.

## 9. Contribuição potencial do estudo

A qualidade da informação deixa de ser apenas uma limitação do exercício e passa a constituir um resultado substantivo.

A transição do IBS vincula, por décadas, parcela relevante da repartição a receitas históricas declaradas pelos entes. Dessa forma, erros de escrituração, omissões ou classificações inconsistentes podem deixar de ser apenas problemas estatísticos e passar a ter consequências distributivas.

O caso do Paraná mostra que uma auditoria simples, baseada na reconciliação entre a DCA e os registros do ente transferidor, consegue identificar e corrigir parte dessas distorções antes de calcular os coeficientes.

Uma recomendação institucional decorrente é a criação de procedimentos automáticos de pré-validação dos dados usados nos coeficientes da transição, com alertas aos entes quando houver divergência material entre transferências registradas pelo ente transferidor e pelo recebedor, além de mecanismo de retificação antes da consolidação definitiva da base histórica.

## Referências institucionais para a auditoria

- Siconfi/STN, DCA e regras de preenchimento: https://www.siconfi.tesouro.gov.br/siconfi/pages/public/conteudo/conteudo.jsf?id=42
- Siconfi/STN, responsabilidade dos entes pela exatidão e fidedignidade das informações: https://www.siconfi.tesouro.gov.br/siconfi/pages/public/conteudo/conteudo.jsf?id=49103
- STN, orientação de registro bruto da cota-parte ICMS, inclusive Fundeb: https://conteudo.tesouro.gov.br/manuais/index.php?Itemid=675&catid=664&id=1316&option=com_content&view=article
- Portal da Transparência do Estado do Paraná, repasses aos municípios: https://www4.pr.gov.br/Gestao/portaldatransparencia/repasses/
- TCE-PR, Portal Informação para Todos, dados do SIM-AM: https://pit.tce.pr.gov.br/Dados/DadosConsulta/Consolidado

