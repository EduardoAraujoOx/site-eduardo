# Radar de notícias da reforma tributária

A aba **Notícias** do portal Municípios na Reforma lista links de notícias recentes sobre a reforma tributária. Ela mostra só título, fonte, data e link; o texto da matéria fica no veículo de origem.

## Como funciona

A página chama `/api/noticias` (`municipios-na-reforma/api/noticias.js`), uma função de borda da Vercel. A função lê os feeds RSS ou Atom das fontes, deixa só o que trata do tema, tira repetições e devolve uma lista em JSON. A resposta fica no cache da rede por uma hora (`s-maxage=3600`), e por mais um dia como cópia reserva se a renovação falhar (`stale-while-revalidate` e `stale-if-error`). Na prática, a lista se renova a cada hora, quando alguém abre a aba, sem agendador, sem armazenamento e sem commits no repositório.

Toda a lógica está em `municipios-na-reforma/api/_noticias-core.js`. O arquivo começa com as listas de fontes, que são o único lugar a editar para trocar a seleção.

- `FEEDS`: feeds de cobertura geral (Agência Senado, Agência Câmara, Receita Federal, Agência Brasil, JOTA, Conjur, Poder360). Só entra a notícia que passa no filtro de assunto.
- `BUSCAS`: buscas no Google Notícias, que devolvem links. Servem para o Comitê Gestor do IBS, o Ministério da Fazenda, a Presidência, as entidades de municípios (CNM, FNP, Comsefaz) e a imprensa. Um resultado de imprensa só é aceito se o veículo estiver em `VEICULOS`.
- `VEICULOS`: os veículos aceitos nas buscas, por domínio, com o nome exibido e o tipo (`cgibs`, `governo`, `congresso`, `entes` ou `imprensa`).

## Filtro de assunto

Uma notícia entra quando o título (ou, nos feeds gerais, o resumo) cita reforma tributária, IBS, CGIBS, Comitê Gestor do IBS, LC 214 ou 227, Imposto Seletivo, split payment, Seguro-Receita e termos próximos. "CBS" só vale com contexto tributário, porque também é uma rede de TV. Convites, cursos e eventos de divulgação (inscrições, webinars, seminários, "promove encontro") ficam de fora, salvo se tratarem de audiência, consulta pública ou ato oficial. A janela é de 30 dias, com no máximo 80 itens. Os ajustes estão em `NUCLEO`, `PROMO` e `OFICIAL`.

## Limites conhecidos

- Parte dos links de imprensa passa pelo Google Notícias antes de abrir o veículo, porque o Google não informa o endereço direto.
- Alguns sites bloqueiam leitores automáticos (o feed do Valor Econômico, por exemplo, recusa o acesso direto; o Valor entra pelas buscas). Uma fonte que falha não derruba as outras: ela aparece em `falhas` na resposta.
- O feed da CNM e o da Comsefaz não foram lidos diretamente (acesso recusado em teste); eles entram pela busca no Google Notícias.
- Na produção, os feeds diretos da Agência Câmara e do Poder360 passam do prazo de 4 s por feed (a Vercel lê de outros endereços de rede); por isso a espera máxima é de 4 s: a renovação da lista, que acontece em paralelo, não demora mais que isso. A busca `gn-congresso` cobre Câmara e Senado pelo Google Notícias, e a resposta traz as fontes que falharam em `falhas`, com o motivo, para diagnóstico.
- A seleção é automática. Não há revisão humana de cada item, e a página diz que listar não significa endossar.

## Teste local

A coleta roda em Node 22 sem alterações:

    node --input-type=module -e "import {coletar} from './municipios-na-reforma/api/_noticias-core.js'; const d = await coletar(); console.log(d.itens.length, d.falhas)"

Para ver a aba, sirva a pasta `municipios-na-reforma` e responda `/api/noticias` com `api/noticias.js`, ou use `vercel dev`.

## Medição

O clique em uma notícia gera o evento `noticia_clique`, só com o tipo da fonte (veja `docs/municipios-seo-medicao.md`).
