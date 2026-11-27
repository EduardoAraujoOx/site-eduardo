'use strict';
const L = require('../_lib');

// GET mostra um botão (evita que verificadores de links de e-mail consumam o token); POST valida e abre a sessão.
module.exports = async (req, res) => {
  try {
    if (req.method === 'GET') {
      const t = String(req.query?.t || new URL(req.url, 'http://x').searchParams.get('t') || '');
      const ok = t && await L.db.tokenValido(L.sha256(t));
      if (!ok) return L.pagina(res, 400, 'Link inválido', '<p><b>Link inválido ou expirado.</b></p><p>Volte à <a href="/estudos/">lista de estudos</a> e peça um novo link.</p>');
      return L.pagina(res, 200, 'Abrir estudo', `<p>Confirme para abrir o estudo.</p><form method="post" action="/api/acesso/entrar"><input type="hidden" name="t" value="${L.esc(t)}"><button type="submit">Abrir estudo</button></form>`);
    }
    if (req.method !== 'POST') return L.resposta(res, 405, { erro: 'metodo' });
    const t = String(L.corpo(req).t || '');
    const tk = t && await L.db.consumirToken(L.sha256(t));
    if (!tk) return L.pagina(res, 400, 'Link inválido', '<p><b>Link inválido, expirado ou já utilizado.</b></p><p>Volte à <a href="/estudos/">lista de estudos</a> e peça um novo link.</p>');
    const leitor = await L.db.leitor(tk.email);
    if (!leitor || leitor.status !== 'ativo') return L.pagina(res, 403, 'Acesso indisponível', '<p>Este acesso não está disponível. Para esclarecimentos, entre em contato com o autor pela <a href="/#contato">seção de contato</a>.</p>');
    await L.db.tocarLeitor(tk.email).catch(() => {});
    res.statusCode = 303;
    res.setHeader('Set-Cookie', L.cookieSessao(L.criarSessao(tk.email)));
    res.setHeader('Location', /^\/estudos\/[a-z0-9-]*(\.html)?$/.test(tk.destino || '') ? tk.destino : '/estudos/');
    res.setHeader('Cache-Control', 'no-store');
    return res.end();
  } catch (e) {
    console.error('entrar', e.message);
    return L.pagina(res, 500, 'Erro', '<p>Não foi possível concluir agora. Tente novamente em instantes.</p>');
  }
};
