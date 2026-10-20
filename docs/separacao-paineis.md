# Separação: Municípios na Reforma e Painel Vertex

## Estrutura preparada

- **Municípios na Reforma:** conserva domínio, marca, projeções e fluxo GA4 existentes. A versão desta revisão retira apresentação comercial, livro, formulários e cadastro para a memória de cálculo.
- **Painel Vertex:** cópia independente preparada em `/workspace/painel-vertex`, com marca e cores Vertex, serviços e livro, configuração própria de domínio, publicação e métricas. Origem: commit `4d026e3c9c4618eca5df2776e3cc45b001b1a9aa` deste repositório.
- **Modelo e resultados:** o processamento continua em `site-eduardo/data`. O portal Vertex consulta os JSONs públicos em `https://municipiosnareforma.com.br/data/`. Assim, uma atualização dos resultados na origem abastece os dois painéis. O cabeçalho CORS dos dados públicos é explícito; cadastros e funções de envio não são compartilhados entre domínios.

O novo repositório leva somente o painel e suas funções, não o site pessoal, os demais projetos ou o histórico completo deste monorepositório. Seu README documenta build, domínios, serviços opcionais e testes de comparação.

## Validação

- Build Node do Vertex com o endereço publicado `https://painelvertex.vercel.app`, canonical, compartilhamento e configuração de produção verificados; página e assets servidos por HTTP local.
- Testes de desktop e celular dos dois painéis: mapa, busca, ficha, gráfico e memória de cálculo.
- Comparação dos dados das séries do gráfico: valores idênticos entre os dois painéis.
- No Vertex, pedidos analíticos usam a origem comum; APIs de contato e cadastro permanecem no domínio próprio. O fluxo GA4 do Municípios na Reforma não é reutilizado.
- No portal independente, testes de consentimento, recusa, revogação e ausência de formulários comerciais passaram. Projeções e bases de dados não foram alteradas nesta revisão.

- Na primeira versão publicada, testes reais em computador e celular passaram para mapa, busca de São Francisco do Conde, gráfico e memória; séries numéricas idênticas às do Municípios na Reforma em produção. Nenhum formulário ou evento de medição foi enviado pelos testes.

## Repositório independente

O painel está no repositório privado `EduardoAraujoOx/painel-vertex`, branch `main`. O endereço escolhido pelo proprietário é `https://painelvertex.vercel.app`, sem hífen; responde HTTP 200 e os metadados, a configuração e o sitemap publicados já usam esse endereço. O repositório e o ZIP de recuperação foram alinhados com essa escolha.

## Pendências reais de publicação e identificação

1. Embora o site já esteja publicado no endereço escolhido, a Vercel bloqueou a atualização automática do commit `aba8cd3` com `Deployment was blocked`. Esse commit mantém o endereço sem hífen na configuração do repositório. O motivo detalhado e a liberação das atualizações devem ser consultados no painel autenticado da Vercel; a sessão não possui autenticação para essa operação. A versão atualmente publicada já usa o endereço escolhido.
2. Falta definir quem assume a identificação de responsável pelo Municípios na Reforma e qual contato deve aparecer na política de privacidade. Por isso, **a identificação atual de controlador foi preservada nessa política nesta revisão**. A publicação da remoção completa da Vertex depende de substituir essa identificação por informação confirmada pelo proprietário.

A revisão permanece em rascunho enquanto esses pontos de identificação e publicação são concluídos. Não há migração ou exclusão de registros de cadastros; serviços comerciais existentes devem ser configurados no novo projeto com suas próprias variáveis de ambiente.
