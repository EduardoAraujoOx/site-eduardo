# Separação: Municípios na Reforma e Painel Vertex

## Estrutura preparada

- **Municípios na Reforma:** conserva domínio, marca, projeções e fluxo GA4 existentes. A versão desta revisão retira apresentação comercial, livro, formulários e cadastro para a memória de cálculo.
- **Painel Vertex:** cópia independente preparada em `/workspace/painel-vertex`, com marca e cores Vertex, serviços e livro, configuração própria de domínio, publicação e métricas. Origem: commit `4d026e3c9c4618eca5df2776e3cc45b001b1a9aa` deste repositório.
- **Modelo e resultados:** o processamento continua em `site-eduardo/data`. O portal Vertex consulta os JSONs públicos em `https://municipiosnareforma.com.br/data/`. Assim, uma atualização dos resultados na origem abastece os dois painéis. O cabeçalho CORS dos dados públicos é explícito; cadastros e funções de envio não são compartilhados entre domínios.

O novo repositório leva somente o painel e suas funções, não o site pessoal, os demais projetos ou o histórico completo deste monorepositório. Seu README documenta build, domínios, serviços opcionais e testes de comparação.

## Validação

- Build Node do Vertex com o endereço publicado `https://painel-vertex.vercel.app`, canonical, compartilhamento e configuração de produção verificados; página e assets servidos por HTTP local.
- Testes de desktop e celular dos dois painéis: mapa, busca, ficha, gráfico e memória de cálculo.
- Comparação dos dados das séries do gráfico: valores idênticos entre os dois painéis.
- No Vertex, pedidos analíticos usam a origem comum; APIs de contato e cadastro permanecem no domínio próprio. O fluxo GA4 do Municípios na Reforma não é reutilizado.
- No portal independente, testes de consentimento, recusa, revogação e ausência de formulários comerciais passaram. Projeções e bases de dados não foram alteradas nesta revisão.

- Na primeira versão publicada, testes reais em computador e celular passaram para mapa, busca de São Francisco do Conde, gráfico e memória; séries numéricas idênticas às do Municípios na Reforma em produção. Nenhum formulário ou evento de medição foi enviado pelos testes.

## Repositório independente

O proprietário criou o repositório privado `EduardoAraujoOx/painel-vertex` e publicou a primeira versão em `https://painel-vertex.vercel.app`. O acesso Git foi verificado. O commit `e48751b8d037c50839da82474cff1b3d1dc190d9` da branch `main` corrige o endereço nos metadados, links de compartilhamento e configuração. Essa atualização ainda aguarda liberação do deploy pela Vercel. O projeto mantém um ZIP de recuperação atualizado.

## Pendências reais de publicação e identificação

1. O site publicado responde HTTP 200 em `https://painel-vertex.vercel.app`. A Vercel marcou o deploy do commit `e48751b` como `Deployment was blocked`; a produção ainda aponta o canonical, a imagem de compartilhamento e a configuração para o endereço sem hífen. Não há autenticação Vercel nesta sessão para consultar o motivo detalhado ou liberar a publicação. O proprietário precisa consultar o bloqueio no painel autenticado e liberar a atualização pelo fluxo indicado pela Vercel.
2. Falta definir quem assume a identificação de responsável pelo Municípios na Reforma e qual contato deve aparecer na política de privacidade. Por isso, **a identificação atual de controlador foi preservada nessa política nesta revisão**. A publicação da remoção completa da Vertex depende de substituir essa identificação por informação confirmada pelo proprietário.

A revisão permanece em rascunho enquanto esses pontos de identificação e publicação são concluídos. Não há migração ou exclusão de registros de cadastros; serviços comerciais existentes devem ser configurados no novo projeto com suas próprias variáveis de ambiente.
