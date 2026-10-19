# Ficha municipal explorável

A nova interface está integrada ao portal e recebe o mesmo objeto municipal usado
pela ficha existente. Está disponível como prévia; o visual atual continua sendo o
padrão. O objetivo é comparar a experiência com os mesmos dados antes de ativá-la
para todos os visitantes.

## Avaliar a prévia

No endereço da implantação escolhida, abra `/?m=2929206&visual=novo` para São
Francisco do Conde. Na própria ficha, **Experimentar nova ficha** e **Voltar ao
visual atual** alternam a opção. A busca continua selecionando qualquer município
da base e conserva o parâmetro durante a navegação. Copiar/compartilhar conserva a
opção do visual. Acrescentar o parâmetro ao domínio de produção só terá efeito
depois que estes arquivos forem implantados nesse domínio.

Para desenvolvimento local, use o build documentado do portal:

```bash
cd municipios-na-reforma
sh ../scripts/copiar-dados-portal.sh
python3 -m http.server 8000 --bind 127.0.0.1
```

O script copia apenas os dados necessários para a pasta ignorada
`municipios-na-reforma/data/`. O servidor estático não implementa as funções
Vercel de cadastro/contato; não use envios de formulário como teste local. Mapas
e gráficos existentes carregam D3/Chart.js dos CDNs já utilizados pelo portal.

## Manutenção entre Codex e Claude Code

Trabalhar em branches e revisar a mesma alteração no GitHub evita cópias
concorrentes de `app.js`. Antes de retomar, conferir `git status`, a referência
remota e o diff; preservar trabalho local e não substituir arquivos inteiros
para aplicar esta interface.

- `ficha-explorador.js`: renderização SVG, seleção de ano, lentes, tabela,
  reprodução, composição, CSV e limpeza dos eventos/timers da instância.
- `ficha-explorador.css`: regras isoladas sob `.ficha-explorador`; ajustes do
  contêiner original ficam sob `.com-explorador` e `.ficha-preview-nova`.
- `app.js`: monta e destrói a instância durante a troca de município; pausa ao
  sair da aba e redesenha ao voltar. O gráfico de composição existente usa uma
  referência própria, sem depender da posição de outro gráfico no array.
- `index.html`: carrega os novos arquivos antes de `app.js`, com versões nas URLs.
- `scripts/testar-ficha-explorador.py`: verificação funcional com o portal real.

O módulo público é `window.FichaExplorador`:

```js
const instancia = FichaExplorador.montar(elemento, {
    municipio: objetoDaBase,
    nome: nomeDoMunicipio
});
// montar retorna null se a linha não tiver os campos necessários.
instancia?.pausar();
instancia?.atualizar();
instancia?.destruir();
```

A implementação não altera os JSONs, coletores, coeficientes, consultas de backend
ou fórmulas. As diferenças e os percentuais exibidos derivam das mesmas séries da
ficha. A composição conserva as cores dos componentes no gráfico original.
O resumo identifica o Seguro-Receita bruto; a composição identifica o efetivo.
A série histórica reproduz os valores da base. Não se desenha uma linha sobre a
lacuna 2026–2028. Valores negativos têm sinal e escala próprios; valores nulos ou
incompletos impedem a montagem opcional e deixam a ficha padrão disponível.

Os elementos do gráfico aceitam seleção intencional por clique/arraste e o
controle de tempo funciona por toque e teclado. A reprodução para ao trocar de
aba/município, sair da página, ocultar a janela ou imprimir. O gráfico não muda
por mero movimento do mouse. Os eventos globais usam `AbortController`, liberado
na destruição. O WhatsApp flutuante fica oculto na prévia para não cobrir o
conteúdo; as ações de contato do portal continuam disponíveis ao fim da ficha.

## Validação

Requer Python com Playwright e Chromium. O navegador pode ser indicado por
`--chromium`. Se necessário, instale as ferramentas de desenvolvimento:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

Esses comandos não são necessários se as ferramentas já estiverem no ambiente.

```bash
node --check municipios-na-reforma/app.js
node --check municipios-na-reforma/ficha-explorador.js
python3 scripts/testar-ficha-explorador.py
```

O teste inicia seu próprio servidor e usa a pasta `data/` da raiz sem copiar ou
alterar a base. As APIs locais de cadastro e geolocalização são simuladas; não
são enviados formulários, mensagens ou eventos para serviços de produção.
Opcionalmente, `--bibliotecas DIRETORIO` usa cópias locais de
`chart.umd.min.js` (Chart.js 4.4.4) e `d3.min.js` (D3 7.9.0), e `--fontes DIRETORIO`
usa `inter.woff2` e `montserrat.woff2`. Sem esses argumentos, os gráficos usam os
CDNs da página; as fontes não são requisito funcional. As capturas e o CSV da
execução ficam em `artifacts/ficha-explorador/`, caminho ignorado pelo Git.

A execução cobre computador e celular, seleção por mouse/toque/teclado,
reprodução e seu ciclo de vida, troca de município pela busca, sinais de perda,
escala do impacto, exportação reconciliada com a base, composição existente,
linhas zeradas/incompletas, imutabilidade do objeto de entrada, retorno ao visual
atual e recuperação quando o script opcional não carrega.

## Implantação

Esta alteração deve ser revisada numa implantação de prévia do projeto Vercel
existente, cujo diretório raiz é `municipios-na-reforma`. O build continua
`sh ../scripts/copiar-dados-portal.sh`; nenhuma dependência de produção foi
adicionada. Ainda não torna o visual novo o padrão. Para um lançamento posterior,
revisar primeiro o seletor `FichaExplorador.ativo()`, a acessibilidade e as
capturas com dados de municípios distintos. O link sem `visual=novo` mantém o
visual existente.
