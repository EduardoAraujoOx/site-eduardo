# Separação: Municípios na Reforma e Painel Vertex

## Estrutura preparada

- **Municípios na Reforma:** conserva domínio, marca, projeções e fluxo GA4 existentes. A versão desta revisão retira apresentação comercial, livro, formulários e cadastro para a memória de cálculo.
- **Painel Vertex:** cópia independente preparada em `/workspace/painel-vertex`, com marca e cores Vertex, serviços e livro, configuração própria de domínio, publicação e métricas. Origem: commit `4d026e3c9c4618eca5df2776e3cc45b001b1a9aa` deste repositório.
- **Modelo e resultados:** o processamento continua em `site-eduardo/data`. O portal Vertex consulta os JSONs públicos em `https://municipiosnareforma.com.br/data/`. Assim, uma atualização dos resultados na origem abastece os dois painéis. O cabeçalho CORS dos dados públicos é explícito; cadastros e funções de envio não são compartilhados entre domínios.

O novo repositório leva somente o painel e suas funções, não o site pessoal, os demais projetos ou o histórico completo deste monorepositório. Seu README documenta build, domínios, serviços opcionais e testes de comparação.

## Validação

- Build Node do Vertex, com domínio de produção simulado derivado das variáveis Vercel.
- Testes de desktop e celular dos dois painéis: mapa, busca, ficha, gráfico e memória de cálculo.
- Comparação dos dados das séries do gráfico: valores idênticos entre os dois painéis.
- No Vertex, pedidos analíticos usam a origem comum; APIs de contato e cadastro permanecem no domínio próprio. O fluxo GA4 do Municípios na Reforma não é reutilizado.
- No portal independente, testes de consentimento, recusa, revogação e ausência de formulários comerciais passaram. Projeções e bases de dados não foram alteradas nesta revisão.

## Pendências reais de acesso e identificação

1. A integração GitHub permite editar este repositório, mas recusou criar `EduardoAraujoOx/painel-vertex`: `Resource not accessible by integration`, confirmado também por HTTP 403 na API REST. A cópia foi preservada como repositório Git local e arquivo ZIP. O proprietário precisa criar o repositório privado vazio e informar a URL; o envio deve ser tentado com as permissões existentes e, se necessário, o acesso do aplicativo GitHub ao novo repositório precisa ser concedido.
2. Não há autenticação Vercel nesta sessão. A API informou ausência de token. Depois de enviar o código ao GitHub, o proprietário pode importar o repositório em **Add New → Project**; o `vercel.json` da cópia já define o build e `public/`. A Vercel atribui o domínio provisório. Um domínio próprio pode ser definido depois com `SITE_URL` e **Settings → Domains**.
3. Falta definir quem assume a identificação de responsável pelo Municípios na Reforma e qual contato deve aparecer na política de privacidade. Por isso, **a identificação atual de controlador foi preservada nessa política nesta revisão**. A publicação da remoção completa da Vertex depende de substituir essa identificação por informação confirmada pelo proprietário.

A revisão permanece em rascunho enquanto esses pontos de identificação e publicação são concluídos. Não há migração ou exclusão de registros de cadastros; serviços comerciais existentes devem ser configurados no novo projeto com suas próprias variáveis de ambiente.
