/* Estimativa de município pela conexão do visitante, usada só para SUGERIR a ficha na abertura.
   Função de borda da Vercel: lê os cabeçalhos que a própria plataforma injeta e devolve
   cidade e UF ao navegador de quem pediu. Nada é gravado nem enviado a terceiros.
   Só existe quando o projeto é publicado na Vercel com a pasta municipios-na-reforma como
   raiz; em qualquer outro caso o portal simplesmente não sugere nada. */
export const config = { runtime: 'edge' };

export default function handler(request) {
    const h = request.headers;
    const decodifica = v => { try { return decodeURIComponent(v || ''); } catch (e) { return ''; } };
    const corpo = {
        country: h.get('x-vercel-ip-country') || '',
        uf: (h.get('x-vercel-ip-country-region') || '').toUpperCase(),
        city: decodifica(h.get('x-vercel-ip-city'))
    };
    return new Response(JSON.stringify(corpo), {
        headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'private, no-store' }
    });
}
