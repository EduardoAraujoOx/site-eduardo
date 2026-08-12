# Legislação da Reforma Tributária — referências verificadas

Compilado em 11/ago/2026, para uso interno pelos scripts e páginas de estudo
deste repositório (`data/build-*.py`, `estudos/ibs-*.html`, `estudos/seguro-receita-*.html`).

**Estado desta compilação:** o Planalto (`planalto.gov.br`) esteve inacessível
(timeout/503) durante toda a sessão em que este arquivo foi montado — não foi
possível baixar o texto integral bruto das três leis diretamente da fonte
primária. Em 11/ago/2026, o autor do site enviou três arquivos com trechos
extraídos de fontes espelho (texto integral da LC 227/2026, o Título III da
LC 227/2026 — arts. 103 a 131 — e os artigos constitucionais da CF/88 com a
redação da EC 132/2023), o que permitiu confirmar literalmente praticamente
todos os dispositivos usados nos cálculos deste site. Trechos marcados
**[LITERAL]** foram conferidos palavra por palavra; trechos marcados
**[PARÁFRASE]** vêm de buscas/resumos e devem ser reconfirmados contra a fonte
primária antes de qualquer uso que exija precisão literal (ex.: citação direta
num estudo publicado).

Fontes primárias (a re-tentar quando o Planalto estiver acessível):
- EC 132/2023: https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm
- LC 214/2025: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm
- LC 227/2026: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm

---

## 1. EC 132/2023 — ADCT (Ato das Disposições Constitucionais Transitórias)

### Art. 128 — extinção gradual do ICMS/ISS
**[PARÁFRASE, uso já validado nos estudos]** A alíquota do ICMS e do ISS é
reduzida a cada ano, de 2029 a 2032, à razão de um décimo, e extinta em 2033.
Parâmetro `fa` em `data/build-ibs-projecao-nacional.py` e
`estudos/ibs-projecao-arrecadacao-*.html`.

### Art. 130 — alíquotas de referência e neutralidade
**[LITERAL]** Caput: *"Resolução do Senado Federal fixará, para todas as
esferas federativas, as alíquotas de referência dos tributos previstos nos
arts. 156-A e 195, V, da Constituição Federal, observados a forma de cálculo e
os limites previstos em lei complementar, de forma a assegurar:"*

- **Inciso I**: *"de 2027 a 2033, que a receita da União com a contribuição
  prevista no art. 195, V, e com o imposto previsto no art. 153, VIII, todos
  da Constituição Federal, seja equivalente à redução da receita"* (CBS/IS —
  neutralidade federal).
- **Inciso II**: *"de 2029 a 2033, que a receita dos Estados e do Distrito
  Federal com o imposto previsto no Art. 156-A da Constituição Federal seja
  equivalente à redução"* (do ICMS) — base da neutralidade estadual que
  fundamenta a razão bolo/PIB usada no Estudo 11.
- **Inciso III**: *"de 2029 a 2033, que a receita dos Municípios e do
  Distrito Federal com o imposto previsto no art. 156-A seja equivalente à
  redução da receita do imposto previsto no art. 156, III"* (do ISS) —
  idem, para municípios.

§4º/§5º (Teto de Referência, **[PARÁFRASE]**): compara a média 2029-2033 de
CBS+Imposto Seletivo+IBS com a média 2012-2021 de IPI+ICMS+ISS+PIS/Cofins+
IOF-seguros; se ultrapassado, reduz a alíquota a partir de 2035 — fora do
horizonte de todos os estudos deste site, não usado nos cálculos.

### Art. 131 — implementação progressiva do IBS e transição histórico→destino
**[PARÁFRASE — confirmar literal quando possível]** §1º, I-II: fixa α_a
(fração do IBS bruto pelo critério histórico) em 80% para 2029-2032 e 90%
para 2033. A partir de 2034, reduz o valor de 2033 em 1/45 a cada ano, até
zero em 2078 (100% destino) — "os 50 anos de transição" (2029-2078). Usado em
`data/build-ibs-projecao-longo-prazo.py`.

### Art. 132 — Seguro-Receita
**[PARÁFRASE, caput já citado nos estudos]**: do imposto apurado com base nas
alíquotas de referência (art. 130), deduzida a retenção do art. 131 §1º, será
retido 5% para distribuição aos entes com as menores razões entre (I) o valor
apurado com base nas alíquotas de referência e (II) a receita média (art.
131, §2º, I-III), limitada a 3x a média nacional por habitante da esfera.
Regulamentado por LC 227/2026 art. 117. Esse percentual de 5% permanece
constante até 2077, só caindo (linearmente, até 0% em 2097) a partir de 2078
— fora do horizonte de todos os estudos deste site.

---

## 2. LC 214/2025

### Arts. 361-365 — cálculo da alíquota de referência
**[LITERAL — confirmado 11/ago/2026 via arquivo enviado pelo autor do site]**
Para cada ano da transição (2029 a 2033), a lei fixa a alíquota de referência
(estadual e municipal, separadamente) exigindo equivalência entre (i) a razão
apurada para o(s) ano(s)-base mais recente(s) disponíveis e (ii) **"a média da
razão entre a receita de referência dos Estados [ou dos Municípios] e o PIB
nos anos de 2024 a 2026"** (redação idêntica nos §§1º/2º dos cinco artigos).
Ex., art. 361, §1º: *"A alíquota de referência do IBS estadual para 2029 será
fixada de forma que haja equivalência entre: I - a razão entre a soma dos
valores de que tratam os incisos I e III do caput deste artigo e o PIB em
2027; e II - a média da razão entre a receita de referência dos Estados e o
PIB nos anos de 2024 a 2026."* Isso **confirma literalmente e exatamente** o
método usado no Estudo 11 (`razao_referencia` = ICMS+ISS+FECOP médio /
PIB médio, 2024-2026, aplicado ao PIB projetado) — não é uma aproximação
nossa, é a fórmula legal. Regulamenta o mecanismo de neutralidade do ADCT
art. 130, II e III (acima). Base de `razao_referencia` em
`data/build-ibs-projecao-nacional.py`.

### Art. 43 — período de apuração mensal do IBS
**[PARÁFRASE, via Resolução CGIBS nº 14/2026]**: o período de apuração do IBS
é mensal.

---

## 3. LC 227/2026

### Art. 47 — obrigações do CGIBS (estimativa de arrecadação, orçamento)
**[PARÁFRASE]** incisos I-II e §1º: determina a publicação, até 31/jul de
cada ano, da estimativa de arrecadação do IBS para o exercício seguinte, da
proposta de percentual destinado ao financiamento do CGIBS, e da metodologia
de cálculo. Ver Resolução CGIBS nº 14/2026 (2027, ano-teste, alíquota 0,1%).

### Art. 51 — financiamento do CGIBS (taxa `ca`)
**[LITERAL — confirmado 11/ago/2026]**

> Art. 51. Nos exercícios financeiros de 2026 a 2032, o percentual do produto
> da arrecadação do IBS destinado ao financiamento do CGIBS de que trata o
> inciso I do caput do art. 47 desta Lei Complementar:
>
> I - será de:
> a) até 100% (cem por cento), limitado ao montante aprovado no orçamento do
> CGIBS, no exercício financeiro de 2026 [...]; e
> b) até 50% (cinquenta por cento) nos exercícios financeiros de 2027 e 2028; e
>
> II - não poderá ser superior a:
> a) 2% (dois por cento) no exercício financeiro de 2029;
> b) 1% (um por cento) no exercício financeiro de 2030;
> c) 0,67% (sessenta e sete centésimos por cento) no exercício financeiro de
> 2031; e
> d) 0,5% (cinco décimos por cento) no exercício financeiro de 2032.

Confirma **exatamente** o parâmetro `ca` já usado nos estudos para 2029-2032
(2,00% / 1,00% / 0,67% / 0,50%). A lei só fixa teto explícito até 2032 — o
valor de 2033 em diante (mantido em 0,50%, com `estimated: true` no código)
continua sendo extrapolação nossa, não uma exigência legal, mas é a hipótese
mais razoável (piso já atingido em 2032, sem indicação de queda adicional).

### Arts. 105-111 — apuração da Receita-Base (cadeia completa)
**[LITERAL — confirmado 11/ago/2026]** O Capítulo II do Título III define,
em cadeia, como se chega à Receita-Base de cada ente:

> Art. 105, parágrafo único. A Receita-Base de cada ente federativo
> corresponde à receita inicial, apurada nos termos do art. 106, após os
> ajustes de que tratam os arts. 107 a 111 desta Lei Complementar.
>
> Art. 109. De 2029 a 2077, serão retidos do produto da arrecadação do IBS
> destinada a cada Estado e Município e ao Distrito Federal, nos termos do
> art. 108 desta Lei Complementar: I - de 2029 a 2032, 80% (oitenta por
> cento); II - em 2033, 90% (noventa por cento); e III - de 2034 a 2077,
> percentual correspondente ao aplicado em 2033, reduzido à razão de 1/45
> (um quarenta e cinco avos) por ano.
>
> Art. 110. De 2029 a 2096, serão retidos [...], após a retenção de que trata
> o art. 109 [...]: I - de 2029 a 2077, 5% (cinco por cento); e II - de 2078
> a 2096, o percentual [...] reduzido à razão de 1/20 (um vinte avos) por
> ano.
>
> Art. 111. Considera-se Receita-Base de cada Estado e Município e do
> Distrito Federal o produto da arrecadação apurado nos termos do art. 108,
> **após as retenções de que tratam os arts. 109 e 110** desta Lei
> Complementar [...].

**Confirma exatamente** os parâmetros α_a (art. 109 → 80%/2029-2032, 90%/2033,
-1/45 ao ano/2034-2077) e ρ (art. 110 → 5%/2029-2077, -1/20 ao ano/2078-2096)
já usados em `data/build-ibs-projecao-longo-prazo.py` e
`data/build-seguro-receita-repasses.py`, sem nenhuma divergência. E **resolve
definitivamente** a dúvida sobre a natureza da Receita-Base: ela é apurada
**depois** de retirados tanto o bolo histórico (art. 109) quanto o bolo do
Seguro-Receita (art. 110) — ou seja, é especificamente a parcela **destino**
que fica retida com o ente (φ^dest), não o IBS total do ente.

### Arts. 114-116 — critério histórico (transição)
**[LITERAL — confirmado 11/ago/2026]** Definem o Coeficiente de Participação
de Transição, base do `φ^CPT` usado em `coeficientes-uf.json`, validado
contra a Nota Técnica nº 02/2026 (SEFAZ-ES). O ponto central, art. 115,
caput, incisos I e III:

> I - para os Estados: a) a arrecadação com o ICMS, **após a aplicação do
> disposto na alínea "a" do inciso IV do caput do art. 158 da Constituição
> Federal** [...];
> [...]
> III - para os Municípios: a) a arrecadação do imposto de que trata o
> inciso III do caput do art. 156 [ISS]; e b) **a parcela creditada na forma
> da alínea "a" do inciso IV do caput do art. 158** da Constituição Federal
> [a cota-parte de ICMS já recebida pelo Município].

Isso confirma literalmente o relato do contato do autor do site (seção 5
abaixo): o φ^CPT de cada Estado já é apurado **líquido** da cota-parte de
ICMS que ele repassa aos seus Municípios (art. 158, IV, "a"), e o φ^CPT de
cada Município já **inclui** a cota-parte de ICMS que ele efetivamente
recebe. A divisão estado/município do histórico está, portanto, embutida no
próprio coeficiente — nenhum ajuste adicional é necessário nem correto.
**Importante:** essa cota-parte histórica (art. 158, IV, "a", §1º) usa o
critério **antigo do ICMS** — 65% no mínimo por valor adicionado + até 35%
por lei estadual —, diferente do critério **novo** do IBS-destino (art. 158,
IV, "b", §2º — população/educação/ambiental/igualitário, ver CF art. 158
abaixo). São dois critérios de cota-parte municipal diferentes, cada um
aplicável a uma fatia diferente da receita.

### Art. 117 — Seguro-Receita (regulamentação)
**[LITERAL — confirmado 11/ago/2026]** "Da distribuição complementar para os
entes federativos com maior perda de participação relativa na receita":
nivelamento sequencial entre os entes de menor razão entre:

> I - a média, nos 12 (doze) meses anteriores, da receita mensal do IBS
> apurada com base nas alíquotas de referência, nos termos do art. 108 desta
> Lei Complementar, **após a aplicação do disposto na alínea "b" do inciso IV
> do caput do art. 158** da Constituição Federal; e
>
> II - a receita média de referência ajustada, calculada nos termos dos §§
> 3º a 6º deste artigo [receita média de referência do art. 115, limitada a
> 3x a média per capita da esfera].

Implementado em `data/build-seguro-receita-repasses.py`. **Nuance
importante, ainda não refletida no código:** diferente do histórico (que já
nasce líquido/bruto de cota-parte por natureza do próprio dado-fonte, ver
arts. 114-116 acima), aqui é a **própria lei** que manda calcular o
numerador da razão do Estado **já líquido** dos 25% que serão repassados aos
Municípios via cota-parte do IBS-destino (art. 158, IV, "b"). Ou seja, o
nivelamento do Seguro-Receita compara Estados e Municípios **cada um já com
sua fatia líquida/recebida da cota-parte**, não a receita bruta do IBS-destino
estadual antes da partilha. Isso é consistente com a leitura de que φ^dest
deveria ser calculado por esfera (estado vs. município) já considerando a
cota-parte — mas não da forma que o Estudo 06/12 fazem hoje (ver "Implicação
para os estudos" abaixo).

### Art. 118 — Receita-Base do Estado (dedução e repasse da cota-parte municipal)
**[LITERAL — colado pelo autor do site, 11/ago/2026]**

> Art. 118. A Receita-Base de cada Estado apurada nos termos do art. 111 desta
> Lei Complementar:
>
> I - será acrescida das multas punitivas e dos juros de mora sobre elas
> incidentes na hipótese em que o ente federativo tenha promovido a
> fiscalização nos termos dos §§ 1º e 2º do art. 4º desta Lei Complementar;
>
> II - será deduzida, a cada período de determinação do montante do produto
> da arrecadação a ser distribuído:
>
> a) do montante correspondente à compensação ou ao ressarcimento do saldo
> credor de ICMS do respectivo Estado;
>
> b) do montante correspondente à compensação devida pelo Estado em função da
> existência em estoque, em 31 de dezembro de 2032, de mercadoria sujeita ao
> regime de substituição tributária relativamente ao ICMS; e
>
> c) do montante correspondente à devolução específica de IBS a pessoas
> físicas, nos termos previstos em lei estadual.
>
> [...]
>
> § 2º Do montante apurado na forma do caput deste artigo, será deduzida a
> parcela destinada ao Fundo de Combate à Pobreza do Estado, no percentual
> previsto na respectiva legislação.
>
> § 3º Do montante apurado na forma do § 2º deste artigo, será deduzida a
> parcela pertencente aos Municípios do Estado, nos termos da alínea "b" do
> inciso IV do caput do art. 158 da Constituição Federal, a qual será
> distribuída nos termos do art. 128 desta Lei Complementar.
>
> § 4º Do montante apurado na forma do § 3º deste artigo e do valor destinado
> ao Fundo de Combate à Pobreza do Estado, serão deduzidos:
>
> I - o percentual previsto no inciso II do caput do art. 212-A da
> Constituição Federal destinado ao Fundo de Manutenção e Desenvolvimento da
> Educação Básica e de Valorização dos Profissionais da Educação (Fundeb); e
>
> II - o percentual destinado ao financiamento do CGIBS.
>
> § 5º Os valores apurados na forma do § 3º deste artigo e os valores
> destinados ao Fundo de Combate à Pobreza, após as deduções a que se refere
> o § 4º deste artigo, serão transferidos aos Estados, no prazo estabelecido
> no § 3º do art. 104 desta Lei Complementar.
>
> § 8º O CGIBS deverá distribuir, de forma segregada, os recursos de que
> trata este artigo.

**Confirmado (art. 111, acima):** a Receita-Base de que trata o caput deste
artigo é, de fato, especificamente a parcela **destino** do IBS estadual —
apurada após as retenções do histórico (art. 109) e do Seguro-Receita (art.
110). É sobre ELA, depois do Fundo de Combate à Pobreza (§2º), que incide a
cota-parte municipal de 25% (§3º: *"será deduzida a parcela pertencente aos
Municípios do Estado, nos termos da alínea 'b' do inciso IV do caput do art.
158 [...], a qual será distribuída nos termos do art. 128"*) — não sobre o
IBS estadual total. O art. 119 (Município) e o art. 120 (DF), por
contraste, **não têm** dedução de cota-parte equivalente — confirma que só o
Estado repassa cota-parte ao Município, nunca o contrário.

### Art. 128 — critérios de distribuição da cota-parte municipal
**[LITERAL — colado pelo autor do site, 11/ago/2026]**

> Art. 128. O CGIBS transferirá aos Municípios o valor a eles pertencente nos
> termos da alínea "b" do inciso IV do caput do art. 158 da Constituição
> Federal, e retido nos termos do § 3º do art. 118 desta Lei Complementar,
> observados os seguintes critérios de distribuição previstos no § 2º do
> art. 158 da Constituição Federal:
>
> I - 80% (oitenta por cento) na proporção da população;
>
> II - 10% (dez por cento) com base em indicadores de melhoria nos resultados
> de aprendizagem e de aumento da equidade, considerado o nível
> socioeconômico dos educandos, de acordo com o que dispuser lei estadual;
>
> III - 5% (cinco por cento) com base em indicadores de preservação
> ambiental, de acordo com o que dispuser lei estadual;
>
> IV - 5% (cinco por cento) em montantes iguais para todos os Municípios do
> Estado.
>
> § 1º Do montante destinado a cada Município, nos termos do caput deste
> artigo serão deduzidos:
>
> I - o percentual previsto no inciso II do caput do art. 212-A da
> Constituição Federal destinado ao Fundeb; e
>
> II - o percentual destinado ao financiamento do CGIBS.
>
> § 2º O valor apurado na forma do caput deste artigo, após as deduções a que
> se refere o § 1º deste artigo, será transferido ao Município no prazo
> estabelecido no § 3º do art. 104 desta Lei Complementar.

**Confirma o relato do contato do autor do site:** o CGIBS transfere direto
ao Município ("O CGIBS transferirá aos Municípios..."), sem o Estado como
intermediário — diferente da sistemática do ICMS/cota-parte tradicional.

---

## 4. CF/88, art. 158 (redação dada pela EC 132/2023)

**[LITERAL — confirmado 11/ago/2026, via arquivo enviado pelo autor do site]**

> Art. 158. Pertencem aos Municípios: [...]
>
> IV - 25% (vinte e cinco por cento):
> a) do produto da arrecadação do imposto do Estado sobre operações relativas
> à circulação de mercadorias [...] [ICMS];
> b) do produto da arrecadação do imposto previsto no art. 156-A [IBS]
> distribuída aos Estados.
>
> § 1º As parcelas [...] mencionadas no inciso IV, "a" [ICMS], serão
> creditadas conforme os seguintes critérios: I - 65% (sessenta e cinco por
> cento), no mínimo, na proporção do valor adicionado [...]; II - até 35%
> (trinta e cinco por cento), de acordo com o que dispuser lei estadual,
> observada [...] a distribuição de, no mínimo, 10 pontos percentuais com
> base em indicadores de melhoria [...] educação [...].
>
> § 2º As parcelas [...] mencionadas no inciso IV, "b" [IBS-destino], serão
> creditadas conforme os seguintes critérios: I - 80% (oitenta por cento) na
> proporção da população; II - 10% (dez por cento) com base em indicadores de
> melhoria nos resultados de aprendizagem e de aumento da equidade [...];
> III - 5% (cinco por cento) com base em indicadores de preservação
> ambiental [...]; IV - 5% (cinco por cento) em montantes iguais para todos
> os Municípios do Estado.

**Ponto central confirmado:** são **dois critérios de cota-parte municipal
totalmente diferentes**, aplicados a bases diferentes. O ICMS (§1º) segue o
critério tradicional, majoritariamente por **valor adicionado** (65% mínimo)
— reflete onde a atividade econômica ocorre. O IBS-destino (§2º) segue um
critério **novo**, majoritariamente por **população** (80%) — não tem
relação com o local de consumo dentro do Estado. É o mesmo critério do art.
128 da LC 227/2026 (idêntico, ver seção 3 acima).

### Implicação para os estudos — achado estrutural (não implementado, decisão pendente do autor do site)

Com os arts. 105-120 da LC 227/2026 e o art. 158 da CF/88 lidos por inteiro,
dá para fechar a questão que ficou em aberto: **o mecanismo legal não calcula
um φ^dest por Município.** Ele funciona assim, para a fatia destino:

1. O art. 108 apura, operação a operação, a receita de destino de cada
   **Estado** (é aqui que entra o conceito de "destino" — o local da
   operação, art. 106, §1º, II). Não há apuração de destino por Município
   nessa etapa; o Município só aparece nas mesmas regras do art. 106-108,
   como um ente equivalente ao Estado (a lei trata "Estado, Distrito Federal
   e Município" em paralelo o tempo todo em relação a bens/serviços cuja
   competência de destino é municipal — ISS/serviços — mas a fatia de
   **IBS de competência estadual** distribuída aos Municípios não vem de
   uma apuração de destino municipal; vem da cota-parte).
2. A Receita-Base do Estado (art. 111 = pós-retenção histórico + Seguro-
   Receita, isto é, especificamente destino) é reduzida pelo Fundo de
   Combate à Pobreza e então, por força do art. 118, §3º c/c art. 158, IV,
   "b", 25% dela é separada e repassada aos Municípios do Estado — **não
   proporcionalmente a onde o consumo ocorreu dentro do Estado**, e sim
   pelos critérios do art. 128/158 §2º: 80% população, 10% educação-
   equidade, 5% ambiental, 5% igualitário entre Municípios.

Ou seja: **a fatia municipal do IBS-destino não é "o IBS que o Município
teria arrecadado como destino", é uma redistribuição do bolo destino
estadual por população/educação/ambiente** — um critério redistributivo, não
um critério de destino per se. Isso é estruturalmente diferente do que a
estimativa de Gobetti e Monteiro (IPEA, 2023) tenta capturar (que é uma
participação relativa estado/município na base tributável, no espírito de
"quem geraria mais IBS-destino se fosse cobrado separadamente"), e também
diferente de simplesmente aplicar 25%/75% sobre o φ^dest já calculado por
esfera nos estudos.

**Primeira correção, 11/ago/2026 (parcialmente superada — ver abaixo).**
Estudo 06, Estudo 03 (ES), Estudo 12 e a extensão de longo prazo trocaram o
`φ^dest_município` (que vinha da variação relativa específica por UF de
Gobetti e Monteiro, Tabela 2 do paper) por **25% fixo do `φ^dest_estado` da
mesma UF** — só a fração de cota-parte (CF art. 158, IV, "b"; LC 227/2026
arts. 118, §3º, e 128), mantendo Gobetti e Monteiro como fonte do
`φ^dest_estado`.

**Achado adicional, mesma data:** essa correção capturava só a cota-parte,
não a segunda perna do problema. **LC 214/2025, art. 361** fixa, separada e
independentemente, uma "alíquota de referência **estadual**" (inciso I) e
uma "alíquota de referência **municipal**" (inciso II) — não uma derivada da
outra. E o próprio Gobetti e Monteiro, na Carta de Conjuntura 60 (IPEA, 28
ago. 2023, p. 3), descrevem o efeito redistributivo como a combinação de
**três** mudanças, não duas: *"i) substituição do ICMS por um imposto
estadual no destino; ii) redistribuição da cota-parte municipal do imposto
estadual com base em novos critérios [...]; e iii) substituição do ISS por
um imposto municipal de base ampla e também cobrado no destino."* O item
(iii) — a parcela municipal do IBS, sucessora do ISS, cobrada no destino e
pertencente diretamente ao Município (não uma cota-parte de nada) — não
tinha nenhuma contrapartida no modelo com 25% fixo. Reproduzido de:
`swgobetti@gmail.com`; Gobetti, S. W.; Monteiro, P. K. *Impactos
redistributivos da reforma tributária: estimativas atualizadas.* Carta de
Conjuntura n. 60, Nota de Conjuntura 18. IPEA, 28 ago. 2023. Disponível em
<https://repositorio.ipea.gov.br/bitstreams/079492a6-d88a-42ac-bd75-127454c35f23/download>.

**Segunda correção, ago/2026 (vigente).** O site passou a usar uma
estimativa própria e independente do coeficiente de destino — POF
2017-2018 × Censo 2022 (<a href="/estudos/ibs-destino-pof-censo.html">Estudo
13</a>) —, aplicada às duas esferas a partir da MESMA participação da UF no
consumo nacional (φ_UF), já que a parcela estadual e a municipal do IBS
incidem sobre a mesma base (LC 214/2025 art. 361 confirma que "IBS
estadual" e "IBS municipal" são duas alíquotas de referência sobre a mesma
base de consumo, não bases diferentes):

$$\text{Estado}_{UF} = \varphi_{UF} \times 0{,}75\,\frac{r_E}{r_E+r_M}
\qquad
\text{Município}_{UF} = \varphi_{UF} \times \left(\frac{r_M + 0{,}25\,r_E}{r_E+r_M}\right)$$

onde $r_E$ e $r_M$ são as alíquotas de referência estadual e municipal
(LC 214/2025 art. 361). O fator $0{,}75$/$0{,}25$ é a cota-parte municipal
do IBS estadual (mesma base legal acima). Gobetti e Monteiro (IPEA, 2023)
deixou de ser insumo do modelo em qualquer esfera — permanece só como
fonte de comparação nos Estudos 07 e 13.

Arquivos alterados: `estudos/ibs-projecao-arrecadacao-br.html`,
`estudos/ibs-projecao-arrecadacao-es.html`,
`estudos/ibs-projecao-longo-prazo.html`,
`data/build-rateio-destino-municipios.py`,
`data/build-seguro-receita-repasses.py`,
`data/build-seguro-receita-repasses-longo-prazo.py`,
`data/build-phi-dest-pof-censo.py` (fonte de φ_UF, `data/phi-dest-pof-censo.json`).

**Rateio entre municípios individuais de uma mesma UF** (Estudo 12,
inalterado pela segunda correção): usa o critério do art. 128 — 80%
população + 5% igualitário (valores exatos da lei, usando
`data/populacao-municipios-media-2019-2026.json`, IBGE) + 10%
educação-equidade + 5% ambiental (art. 128, incisos II e III — dependem de
indicadores fixados por lei estadual; nenhum Estado regulamentou ainda,
então são aproximados pelo mesmo critério populacional do inciso I). Na
prática: 95% população + 5% igualitário, até que algum Estado regulamente
os 15% restantes.

**Terceira correção, ago/2026 (vigente).** A segunda correção aproximava
$r_E$/$r_M$ pela razão real ICMS/ISS de um único ano (2025). O texto do
art. 361, §§1º/2º, manda algo mais específico: *"a média da razão entre a
receita de referência [dos Estados / dos Municípios] e o PIB nos anos de
2024 a 2026"* — não uma razão entre dois totais de um ano só. $r_E$/$r_M$
passaram a ser calculados como a média, entre 2024 e 2025 (dois anos
fechados; 2026 fica de fora por ainda estar incompleto na data de cálculo
— decisão do autor do site, 12/ago/2026), da razão (receita de
referência/PIB) de cada esfera: receita de referência dos Estados =
ICMS + FECOP; dos Municípios = ISS (SICONFI/STN DCA Anexo I-C; PIB nominal
de `data/macro-parametros.json`). O cálculo é feito uma única vez em
`data/build-phi-dest-pof-censo.py` (função `compute_frac_estado_muni`) e
gravado em `data/phi-dest-pof-censo.json` (`frac_estado_pct`,
`frac_muni_pct`) — os seis consumidores (3 páginas HTML + 3 scripts
Python) leem esses dois campos em vez de recalcular a razão localmente.
Resultado: $r_E$/$r_M$ (antes da cota-parte) foi de 85,06%/14,94% (só
2025, sem FECOP) para 85,41%/14,59% (média 2024-2025, com FECOP incluído
em $r_E$ — mesmo tratamento que o Estudo 11 já dá ao FECOP na receita de
referência combinada); a fração final aplicada a φ_UF foi de
63,7971%/36,2029% para 64,0573%/35,9427% (estado/município). Efeito no
Espírito Santo: φ_ES^dest (estado) subiu de 1,1000% para 1,1045%.

Datasets regenerados: `data/phi-dest-pof-censo.json`,
`data/rateio-destino-municipios.json`, `data/seguro-receita-repasses.json`,
`data/seguro-receita-repasses-longo-prazo.json`.

**Pendência conhecida:** o ano de 2026 ainda fica de fora da média (só
2024-2025), então $r_E$/$r_M$ não são, ainda, o triênio 2024-2026 completo
que o art. 361 usa para fixar a alíquota de referência definitiva de 2029.
Quando o DCA de 2026 fechar (2027), recalcular incluindo o terceiro ano.
Também permanece em aberto a possibilidade de, no futuro, desmembrar o
Estudo 11 numa trajetória separada por esfera (hoje só projeta uma receita
de referência combinada) para dar mais precisão a $r_E$/$r_M$ nos anos
projetados (2029 em diante) — hoje a fração é fixa a partir da base
2024-2025 e não evolui com a trajetória.

---

## 5. Relato direto (contato do autor do site, ago/2026) — não é fonte legal

Resumo da mensagem recebida (contexto no histórico da conversa, não citável
como fonte primária num estudo): a partir de 2029 existem "3 tipos de IBS"
(1 — Transição/histórico, 2 — Seguro-Receita, 3 — IBS Destino); os tipos 1 e 2
já têm coeficiente líquido de cota-parte municipal (não precisa aplicar de
novo); só o tipo 3 passa pela cota-parte do art. 128/158 CF; o CGIBS manda
direto ao município, sem passar pelo estado. **Confirmado pela leitura
literal dos arts. 105-120 (seção 3 acima):** o tipo 1 (art. 115, I "a" vs.
III "b") já é líquido/creditado por natureza do dado-fonte; o tipo 2 (art.
117, I) usa expressamente a receita "após a aplicação" da cota-parte b) do
art. 158; e o tipo 3 é exatamente a Receita-Base do art. 111/118 §3º, de onde
saem os 25% do art. 128. O único ponto do relato que a leitura da lei
qualifica melhor é o "CGIBS manda direto ao município": tecnicamente o art.
118, §3º diz que a parcela municipal é **deduzida da Receita-Base do
Estado** e "distribuída nos termos do art. 128" — o art. 128 confirma que
quem executa essa distribuição é o próprio CGIBS ("O CGIBS transferirá aos
Municípios [...]"), então o Estado nunca chega a ter esse valor em caixa; a
transferência é direta, como relatado.
