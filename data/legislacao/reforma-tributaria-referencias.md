# Legislação da Reforma Tributária — referências verificadas

Compilado em 11/ago/2026, para uso interno pelos scripts e páginas de estudo
deste repositório (`data/build-*.py`, `estudos/ibs-*.html`, `estudos/seguro-receita-*.html`).

**Estado desta compilação:** o Planalto (`planalto.gov.br`) esteve inacessível
(timeout/503) durante toda a sessão em que este arquivo foi montado — não foi
possível baixar o texto integral bruto das três leis. O que segue é uma
coletânea dos artigos especificamente verificados e citados nos estudos deste
site até agora, não um espelho completo das leis. Trechos marcados **[LITERAL]**
foram conferidos palavra por palavra (colados pelo autor do site ou extraídos
de fontes espelho confiáveis); trechos marcados **[PARÁFRASE]** vêm de buscas/
resumos e devem ser reconfirmados contra a fonte primária antes de qualquer uso
que exija precisão literal (ex.: citação direta num estudo publicado).

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
**[PARÁFRASE — texto integral não obtido nesta sessão]** Para cada ano da
transição (2029-2033), a alíquota de referência do IBS estadual e municipal é
fixada de forma a equivaler à média da razão entre a receita de referência
(ICMS+ISS+FECOP) e o PIB nos anos de 2024 a 2026 — regulamenta o mecanismo de
neutralidade do ADCT art. 130, II e III (acima). Base de `razao_referencia`
em `data/build-ibs-projecao-nacional.py`.

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
**[PARÁFRASE]** Alínea "b" do inciso I autoriza, para 2027 especificamente,
destinação de até 50% da arrecadação do IBS ao financiamento do CGIBS (ano-
teste, valores irrisórios em R$). Para os anos da transição (2029-2033), os
parâmetros já usados nos estudos (`ca`: 2,00% em 2029, decrescendo a 0,50%
em 2032-2033, mantido nesse piso daí em diante) vêm de outro dispositivo do
mesmo artigo — texto exato ainda não confirmado nesta sessão.

### Arts. 114-116 — critério histórico (transição)
**[PARÁFRASE]** Definem o Coeficiente de Participação de Transição (CPT),
base do `φ^CPT` usado em `coeficientes-uf.json`, validado contra a Nota
Técnica nº 02/2026 (SEFAZ-ES). Conforme relato direto (não uma citação legal,
ver seção 4 abaixo), o CPT de cada estado já é líquido da cota-parte
municipal — a divisão estado/município desse coeficiente já embute a
cota-parte, sem necessidade de aplicá-la de novo.

### Art. 117 — Seguro-Receita (regulamentação)
**[PARÁFRASE]** "Da distribuição complementar para os entes federativos com
maior perda de participação relativa na receita": nivelamento sequencial
entre os entes de menor razão entre (I) IBS-destino recebido e (II) receita
média de referência ajustada (art. 115, limitada a 3x a média per capita da
esfera). Implementado em `data/build-seguro-receita-repasses.py`. Pela mesma
lógica do art. 114-116, a receita média de referência de cada ente já é
líquida de cota-parte municipal.

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

**Nota importante para o modelo:** o caput fala em "Receita-Base de cada
Estado apurada nos termos do art. 111" (texto do art. 111 ainda não obtido) —
não fica explícito, só por este artigo, se essa Receita-Base é a soma de
todos os "tipos de IBS" (histórico + destino + Seguro-Receita) ou só a
parcela destino. Combinado com os arts. 114-117 (que já tratam separadamente
histórico e Seguro-Receita, cada um com sua própria apuração por esfera), a
leitura mais consistente é que a Receita-Base do art. 111/118 é
especificamente a parcela **destino**, e é sobre ELA que os 25% de cota-parte
municipal (art. 158, IV, "b", CF) incidem — não sobre o total do IBS estadual.
Isso precisa de confirmação lendo o art. 111 antes de qualquer mudança de
código baseada nele.

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

**[PARÁFRASE — via agregador jurídico, não confirmado direto no Planalto
nesta sessão]**

- **Inciso IV**: 25% do produto da arrecadação: a) do ICMS estadual; b) do
  IBS (art. 156-A) distribuída aos Estados — **a mesma fração de 25% já
  histórica do ICMS**, agora também aplicada ao IBS.
- **§2º**: os critérios do inciso IV, "b" (a mesma lista do art. 128 da LC
  227/2026 acima: 80% população / 10% educação-equidade / 5% ambiental / 5%
  igualitário).

**Implicação para os estudos (ainda não implementada, pendente confirmação
do art. 111 da LC 227/2026):** hoje, a divisão estado/município do φ^dest
(coeficiente de destino) em `coeficientes-uf.json`/Estudo 06/Estudo 12 vem da
estimativa de Gobetti e Monteiro (IPEA, 2023) — anterior à própria EC
132/2023, portanto anterior a este dispositivo. Se a Receita-Base do art. 111
for de fato só a parcela destino (ver nota no art. 118 acima), a divisão
correta seria 25% município / 75% estado, fixa e nacionalmente uniforme, em
vez da estimativa do Gobetti. **Não implementado ainda — decisão pendente do
autor do site.**

---

## 5. Relato direto (contato do autor do site, ago/2026) — não é fonte legal

Resumo da mensagem recebida (contexto no histórico da conversa, não citável
como fonte primária num estudo): a partir de 2029 existem "3 tipos de IBS"
(1 — Transição/histórico, 2 — Seguro-Receita, 3 — IBS Destino); os tipos 1 e 2
já têm coeficiente líquido de cota-parte municipal (não precisa aplicar de
novo); só o tipo 3 passa pela cota-parte do art. 128/158 CF; o CGIBS manda
direto ao município, sem passar pelo estado. Consistente com o que os arts.
114-118/128 (acima) sugerem, mas os arts. 114-117 não confirmam isso
explicitamente por si só (ver nota no art. 118).
