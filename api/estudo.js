'use strict';
const L = require('./_lib');

// Entrega o texto do estudo (decifrado no servidor) apenas a leitores com sessão válida e acesso ativo.
module.exports = async (req, res) => {
  try {
    const slug = String(req.query?.slug || new URL(req.url, 'http://x').searchParams.get('slug') || '');
    if (!L.slugValido(slug)) return L.resposta(res, 404, { erro: 'nao_encontrado' });
    const email = L.lerSessao(req);
    if (!email) return L.resposta(res, 401, { erro: 'sem_acesso' });
    const leitor = await L.db.leitor(email);
    if (!leitor || leitor.status !== 'ativo') return L.resposta(res, 401, { erro: 'sem_acesso' });
    const html = L.decifrar(slug);
    await Promise.allSettled([L.db.registrarLeitura(email, slug), L.db.tocarLeitor(email)]);
    res.statusCode = 200;
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.setHeader('Cache-Control', 'private, no-store');
    res.setHeader('X-Robots-Tag', 'noindex');
    return res.end(html);
  } catch (e) {
    console.error('estudo', e.message);
    return L.resposta(res, 500, { erro: 'falha' });
  }
};
