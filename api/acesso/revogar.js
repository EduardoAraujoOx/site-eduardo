'use strict';
const L = require('../_lib');

// Link enviado só ao autor: revoga o acesso de um e-mail (confirmação em duas etapas).
module.exports = async (req, res) => {
  try {
    const src = req.method === 'POST' ? L.corpo(req) : (req.query || Object.fromEntries(new URL(req.url, 'http://x').searchParams));
    const email = L.normEmail(src.e), s = String(src.s || '');
    if (!email || !L.seguroIgual(s, L.hmac('revogar:' + email))) return L.pagina(res, 400, 'Link inválido', '<p>Link inválido.</p>');
    if (req.method === 'POST') { await L.db.statusLeitor(email, 'revogado'); return L.pagina(res, 200, 'Acesso revogado', `<p>Acesso de <b>${L.esc(email)}</b> revogado.</p>`); }
    return L.pagina(res, 200, 'Revogar acesso', `<p>Revogar o acesso de <b>${L.esc(email)}</b>?</p><form method="post" action="/api/acesso/revogar"><input type="hidden" name="e" value="${L.esc(email)}"><input type="hidden" name="s" value="${L.esc(s)}"><button type="submit">Revogar</button></form>`);
  } catch (e) { console.error('revogar', e.message); return L.pagina(res, 500, 'Erro', '<p>Erro. Tente novamente.</p>'); }
};
