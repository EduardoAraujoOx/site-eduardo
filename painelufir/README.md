# painelufir.vercel.app

Cópia autocontida do painel (`/painel-reforma-tributaria.html` na raiz do
repositório), com seus dados e imagens copiados para dentro desta pasta,
para ser publicada como um projeto Vercel **separado** do site pessoal —
em vez de um endereço extra sobre o mesmo projeto "site-eduardo", o que
misturaria o site pessoal com o painel da Sefaz-ES sob o mesmo domínio.

## Deploy (uma vez)

1. Em vercel.com, **Add New → Project**.
2. Importe o repositório `EduardoAraujoOx/site-eduardo`.
3. Em **Root Directory**, selecione a pasta `painelufir`.
4. Em **Project Name**, use `painelufir` (define o domínio
   `painelufir.vercel.app`).
5. Framework: **Other** (é HTML/CSS/JS estático, sem build).
6. Deploy.

A cada novo push nesta pasta (`painelufir/`), a Vercel publica
automaticamente uma nova versão.

## Manter atualizado

Este é um espelho estático, não um link simbólico. Ao atualizar
`/painel-reforma-tributaria.html` ou os dados em `/data/*.json` na raiz do
repositório, replique manualmente aqui (ou peça para o Claude replicar):

- `index.html` ← `painel-reforma-tributaria.html`
- `data/resultados-consolidados-ibs.json`
- `data/ibs-projecao-nacional.json`
- `data/painel-estados.json`
- `data/painel-municipios/` (pasta inteira: `index.json` + um arquivo por UF)
- `data/malha-municipios.json` (malha do mapa municipal)
- `data/memoria-calculo/` (pasta inteira: `nacional.json` + um arquivo por UF)
- `data/faixa-phi-dest-estados.json` (faixa entre os quatro métodos de coeficiente de destino)
- `images/brasao-es.png`, `images/brasao-es-branco.png`

Diferenças propositais em relação ao arquivo original, e apenas estas três:

- `<link rel="canonical">` e `og:url` apontam para `https://painelufir.vercel.app/`,
  o endereço do próprio deploy.
- `og:image` e `twitter:image` são servidos por este deploy
  (`/images/brasao-es.png`), não pelo site pessoal.

O conteúdo é idêntico ao da raiz. O painel é autossuficiente: a aba
Metodologia descreve fontes e fórmulas sem remeter a nenhuma página fora
deste deploy, então não há links a converter.
