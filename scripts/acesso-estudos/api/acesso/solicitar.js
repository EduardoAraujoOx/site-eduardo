'use strict';
const crypto = require('node:crypto');
const L = require('../_lib');

// Cadastro com aprovação automática: o acesso é liberado a quem comprova o e-mail clicando no link recebido.
module.exports = async (req, res) => {
  if (req.method !== 'POST') return L.resposta(res, 405, { erro: 'metodo' });
  try {
    const b = L.corpo(req);
    if (b.site) return L.resposta(res, 200, { ok: true });            // campo-isca preenchido por robôs
    const email = L.normEmail(b.email);
    if (!email) return L.resposta(res, 400, { erro: 'email_invalido' });
    const destino = L.slugValido(b.slug) ? `/estudos/${b.slug}.html` : '/estudos/';
    const ip = L.ipHash(req), desde = new Date(Date.now() - 3600e3).toISOString();
    const [porEmail, porIp] = await Promise.all([L.db.contarTokensEmail(email, desde), L.db.contarTokensIp(ip, desde)]);
    if (porEmail >= 3 || porIp >= 10) return L.resposta(res, 429, { erro: 'muitas_tentativas' });

    const leitor = await L.db.leitor(email);
    if (leitor && leitor.status === 'revogado') return L.resposta(res, 200, { ok: true });   // não revela o motivo
    if (!leitor) await L.db.criarLeitor(email);

    const token = crypto.randomBytes(32).toString('base64url');
    await L.db.criarToken({ hash: L.sha256(token), email, destino, ip_hash: ip, expira_em: new Date(Date.now() + 30 * 60e3).toISOString() });
    const link = `${L.SITE()}/api/acesso/entrar?t=${token}`;
    await L.enviarEmail({
      para: email, assunto: 'Seu link de acesso aos estudos',
      html: `<p>Olá,</p><p>Para abrir o estudo, clique no botão abaixo. O link vale por 30 minutos e só pode ser usado uma vez.</p><p><a href="${link}" style="background:#8a6d1d;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none">Abrir estudo</a></p><p style="color:#666;font-size:13px">Se não foi você quem pediu, ignore esta mensagem. Seu e-mail é usado apenas para liberar o acesso e registrar quais estudos foram lidos; para pedir a exclusão, entre em contato pelo site.</p>`,
      texto: `Abra o estudo (link válido por 30 minutos, uso único): ${link}\n\nSe não foi você, ignore esta mensagem.`,
    });
    if (!leitor) {   // aviso ao autor (falha aqui não impede o acesso do leitor)
      const rev = `${L.SITE()}/api/acesso/revogar?e=${L.enc(email)}&s=${L.hmac('revogar:' + email)}`;
      await L.enviarEmail({ para: L.env('AUTHOR_EMAIL', 'economista.araujo@gmail.com'), assunto: 'Novo cadastro nos estudos', html: `<p>Novo leitor cadastrado: <b>${L.esc(email)}</b>.</p><p>Para revogar o acesso: <a href="${rev}">${rev}</a></p>`, texto: `Novo leitor: ${email}\nRevogar: ${rev}` }).catch((e) => console.error('aviso_autor', e.message));
    }
    return L.resposta(res, 200, { ok: true });
  } catch (e) {
    console.error('solicitar', e.message);
    return L.resposta(res, 500, { erro: 'falha' });
  }
};
