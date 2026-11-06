/* Radar de notícias: devolve os links de notícias recentes sobre a reforma tributária, vindos de fontes selecionadas.
   A coleta (api/_noticias-core.js) roda aqui, na borda da Vercel, e a resposta fica no cache da rede por uma hora:
   quem abre a aba depois disso recebe a cópia pronta, e a primeira visita de cada hora renova a lista. */
import {coletar} from './_noticias-core.js';

export const config = {runtime: 'edge'};

const CABECALHO = {'content-type': 'application/json; charset=utf-8'};

export default async function handler(request) {
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('{"erro":"metodo"}', {status: 405, headers: {...CABECALHO, 'cache-control': 'no-store'}});
    try {
        const dados = await coletar();
        // Tudo falhou ou nada passou no filtro: não vale guardar no cache, para a próxima visita tentar de novo.
        if (!dados.itens.length) return new Response(JSON.stringify({...dados, erro: 'sem_itens'}), {status: 503, headers: {...CABECALHO, 'cache-control': 'no-store'}});
        return new Response(JSON.stringify(dados), {headers: {...CABECALHO, 'cache-control': 'public, s-maxage=3600, stale-while-revalidate=86400, stale-if-error=86400'}});
    } catch (e) {
        return new Response('{"erro":"falha"}', {status: 502, headers: {...CABECALHO, 'cache-control': 'no-store'}});
    }
}
