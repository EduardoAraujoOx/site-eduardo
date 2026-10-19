# Google e estatísticas do Municípios na Reforma

O Search Console mostra **cliques vindos da busca do Google**, impressões, consultas e posição média. O Google Analytics 4 (GA4) mostra **visitas e ações dentro do site**, como consultas de municípios e cliques no WhatsApp. São contas gratuitas e complementares.

O ID de medição configurado em `CONFIG.gaId`, no `app.js`, é `G-JYFYHLBRP9`. A coleta depende da publicação desta configuração, do aceite do visitante e dos ajustes do fluxo Web descritos abaixo. A administração das propriedades Google é feita pelo proprietário; nenhuma senha ou chave privada precisa ser compartilhada. Para desligar a integração no código, deixe `CONFIG.gaId` vazio.

## 1. Criar e verificar o Search Console

1. Entre em [Google Search Console](https://search.google.com/search-console/welcome) com a conta Google que administrará o site.
2. Escolha **Domínio** e informe `municipiosnareforma.com.br`, sem `https://` e sem caminho.
3. Copie o valor TXT fornecido pelo Google, que começa com `google-site-verification=`. Ele é público.
4. O DNS do domínio está no **Registro.br** (servidores `d.sec.dns.br` e `e.sec.dns.br`, conferidos em 19/10/2026). No [Registro.br](https://registro.br/), abra o domínio, entre em **DNS → Editar zona** e acrescente um registro **TXT** na raiz do domínio. Deixe o campo de nome em branco para a raiz; se a interface pedir o nome completo, use `municipiosnareforma.com.br`. Cole o valor do Google e salve. Preserve os registros que já existem, inclusive outros TXT; não troque os servidores DNS.
5. Volte ao Search Console e clique em **Verificar**. Se o TXT ainda não tiver propagado, tente novamente depois. Mantenha o registro após a verificação.
6. Em **Sitemaps**, envie `https://municipiosnareforma.com.br/sitemap.xml`.
7. Em **Inspeção de URL**, inspecione `https://municipiosnareforma.com.br/`. Após publicar as correções de SEO, teste a URL publicada e solicite a indexação.

**Alternativa sem alterar DNS:** crie uma propriedade **Prefixo do URL** para `https://municipiosnareforma.com.br/` e selecione **Tag HTML**. Envie a tag pública `<meta name="google-site-verification" content="…">` para adicioná-la ao `<head>` de `index.html`. Depois da publicação, clique em Verificar. Essa alternativa verifica esse prefixo; a propriedade Domínio cobre também os subdomínios e protocolos. O método TXT da propriedade Domínio não é substituído por uma meta tag.

Para acompanhar a marca: abra **Desempenho → Resultados da pesquisa**, filtre consultas como `municipios na reforma` e `municípios na reforma` e observe cliques, impressões, CTR e posição média. Compare períodos equivalentes quando houver dados suficientes. Posição média não é uma posição fixa para todas as pessoas e buscas.

## 2. Criar o Google Analytics 4

1. Entre em [Google Analytics](https://analytics.google.com/) e crie uma conta/propriedade chamada **Municípios na Reforma**. Se já houver uma conta, use **Administrador → Criar → Propriedade**.
2. Escolha o fuso horário do Brasil correspondente a **São Paulo** e a moeda **Real brasileiro (BRL)**.
3. Crie um **fluxo de dados Web** para `https://municipiosnareforma.com.br`, nomeando-o como **Site Municípios na Reforma**.
4. Nos detalhes do fluxo, **desative Medição otimizada / Enhanced measurement**. O portal envia seus próprios eventos; a captura automática de links poderia incluir mensagens pré-preenchidas do WhatsApp e duplicar contagens. Mantenha desativadas a coleta de dados fornecidos pelo usuário e a associação a recursos de publicidade.
5. Copie o **ID de medição**, que começa com `G-`. Envie apenas esse identificador público. Não é necessário colar outro snippet do Google no HTML.
6. O ID informado já foi preenchido em `gaId`, no início de `municipios-na-reforma/app.js`. Antes de publicar pela revisão habitual do projeto, confirme o ajuste de Medição otimizada do passo 4. Não há segredo de servidor nem variável de ambiente obrigatória para esse ID. Ao trocar de propriedade, substitua esse campo pelo novo ID de medição.
7. No domínio de produção, abra uma janela privativa, aceite a medição e consulte um município. Confira a visita e os eventos no relatório **Tempo real** do GA4. Teste também **Continuar sem medição**: nesse caso, a tag Google não deve ser carregada.

O banner só aparece com ID válido **no domínio de produção**. Não há coleta nas prévias da Vercel nem no desenvolvimento local. Antes da autorização, cliques são descartados e nenhuma tag GA4 é carregada. A escolha é lembrada por até 180 dias. Para alterá-la, abra **Política de privacidade → Alterar preferência de medição**. Revogar remove os cookies GA4 conhecidos e recarrega a página sem a biblioteca.

As contagens começam com a instalação; o GA4 não recupera as visitas anteriores. Recusa de consentimento e bloqueadores reduzem a audiência medida. A confirmação real na propriedade exige o ID correto, a publicação e a conferência pelo proprietário; os testes locais não comprovam recebimento pelo Google.

## 3. O que consultar no GA4

- **Aquisição de tráfego:** origem das visitas, incluindo busca orgânica, acesso direto e referências de outros sites.
- **Eventos:** quantidade de ações em cada recurso. Eventos representam ações; uma mesma pessoa pode clicar várias vezes.
- **Explorações:** comparação de municípios consultados e canais de contato. Em **Administrador → Definições personalizadas**, crie dimensões de escopo **Evento** para os parâmetros desejados: `municipio_codigo`, `uf`, `aba`, `canal` e `local`. Elas passam a servir aos relatórios após a criação e o processamento.

| Evento | Significado |
| --- | --- |
| `page_view` | Carregamento de página após autorização; não é disparado para cada troca de aba |
| `busca_municipio` | Município selecionado na busca; usa código IBGE e UF |
| `clique_mapa`, `trilho_municipio`, `ranking_municipio` | Seleção de município no mapa ou nas listas |
| `aba` | Troca de aba, identificada pelo parâmetro `aba` |
| `copiar_link`, `compartilhar`, `imprimir_ficha` | Uso de compartilhamento ou impressão da ficha |
| `clique_contato` | Clique em um canal, como WhatsApp; não confirma envio de mensagem |
| `contato_enviado`, `livro_cadastro` | Formulário concluído no portal; com `canal=whatsapp`, significa abertura da conversa, não envio confirmado. Com `canal=formulario`, a API de envio respondeu com sucesso |
| `cadastro`, `abrir_memoria` | Cadastro concluído ou abertura da memória de cálculo |

O código permite apenas nomes de eventos e parâmetros conhecidos. Não envia nome, e-mail, telefone, mensagem ou outros campos livres dos formulários ao GA4. Municípios são identificados pelo código público do IBGE, evitando confusão entre cidades homônimas. A URL medida conserva apenas o parâmetro municipal numérico `m`; parâmetros arbitrários, UTM e fragmentos são descartados. O referenciador mantém apenas a origem, sem caminho ou consulta. A origem de busca continua podendo ser identificada pelo domínio de referência; campanhas UTM não são detalhadas por esta integração.

## 4. O que as correções de SEO resolvem

- O nome da marca e a apresentação do serviço passam a existir em texto no HTML inicial, com título principal e explicação legível sem executar JavaScript.
- O dado estruturado `WebSite` informa ao Google o nome preferido do site e o domínio canônico. Isso ajuda a interpretar a identidade; não garante posição na busca.
- O `robots.txt` deixa de bloquear os JSONs usados para renderizar o painel. Os arquivos continuam públicos e recebem `X-Robots-Tag: noindex` para não virarem resultados independentes. A página HTML continua indexável.
- O sitemap continua apontando para a página canônica real. Não são geradas milhares de páginas municipais sem conteúdo próprio.

A indexação e a posição dependem do Google. Após publicar, acompanhe o Search Console durante as próximas semanas. Links contextuais em seus perfis e sites oficiais, usando o nome da marca, também ajudam a descoberta. Não há promessa de primeiro lugar nem compra de links.

## Validação da alteração

Execute `node --check municipios-na-reforma/medicao.js` e `node --check municipios-na-reforma/app.js`.

O teste `python scripts/testar-seo-medicao.py` usa Playwright/Chromium, lê dados do próprio repositório e baixa apenas as versões fixas de Chart.js e D3 para um cache local na primeira execução. Pode receber `--assets-dir CAMINHO` com esses dois arquivos já disponíveis. As páginas de produção e a tag Google são simuladas localmente; não há envio de estatísticas nem formulários ao site real. Verifica SEO estático, painel em desktop e celular, consentimento, recusa, revogação e descarte de parâmetros privados.

Referências oficiais: [nome do site no Google](https://developers.google.com/search/docs/appearance/site-names), [SEO com JavaScript e recursos bloqueados](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics), [verificar propriedade no Search Console](https://support.google.com/webmasters/answer/9008080), [configurar GA4](https://support.google.com/analytics/answer/9304153).
