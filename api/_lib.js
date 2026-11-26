'use strict';
// Utilidades do acesso por cadastro aos estudos. Os arquivos que começam com "_" não viram rotas na Vercel.
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const env = (k, d) => process.env[k] || d;
const SITE = () => env('SITE_URL') || (env('VERCEL_URL') ? 'https://' + env('VERCEL_URL') : 'https://www.eduardoreisaraujo.com.br');
const sha256 = (s) => crypto.createHash('sha256').update(s).digest('hex');
const hmac = (s) => crypto.createHmac('sha256', env('SESSION_SECRET', '')).update(s).digest('base64url');
const seguroIgual = (a, b) => { const x = Buffer.from(String(a)), y = Buffer.from(String(b)); return x.length === y.length && crypto.timingSafeEqual(x, y); };
const enc = encodeURIComponent;
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const normEmail = (e) => {
  e = String(e || '').trim().toLowerCase();
  return e.length <= 254 && /^[^\s@"<>(),;:\\]{1,64}@[a-z0-9.-]+\.[a-z]{2,}$/.test(e) && !e.includes('..') ? e : null;
};
const dirCifrado = () => [path.join(process.cwd(), '_cifrado'), path.join(__dirname, '..', '_cifrado')].find((d) => fs.existsSync(d));
const slugValido = (s) => typeof s === 'string' && /^[a-z0-9-]{1,80}$/.test(s) && !!dirCifrado() && fs.existsSync(path.join(dirCifrado(), s + '.json'));

function corpo(req) {
  let b = req.body;
  if (typeof b === 'string') { try { b = JSON.parse(b); } catch (e) { b = Object.fromEntries(new URLSearchParams(b)); } }
  return b && typeof b === 'object' ? b : {};
}
function ipHash(req) {
  const ip = String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || '').split(',')[0].trim();
  return sha256(ip + '|' + env('SESSION_SECRET', ''));
}
function resposta(res, status, obj) {
  res.statusCode = status; res.setHeader('Content-Type', 'application/json; charset=utf-8'); res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(obj));
}
function pagina(res, status, titulo, html) {
  res.statusCode = status; res.setHeader('Content-Type', 'text/html; charset=utf-8'); res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Robots-Tag', 'noindex');
  res.end(`<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>${esc(titulo)}</title>
<style>:root{--bg:#f7f6f2;--fg:#1c1c1c;--card:#fff;--bd:#d9d6cc;--ac:#8a6d1d}@media(prefers-color-scheme:dark){:root{--bg:#14161a;--fg:#ece9e1;--card:#1c1f25;--bd:#33373f;--ac:#d4b25c}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,sans-serif}main{max-width:520px;margin:0 auto;padding:3rem 1rem}
.c{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:1.25rem}button{padding:.65rem 1.1rem;font-size:1rem;border:0;border-radius:6px;background:var(--ac);color:#fff;cursor:pointer}a{color:var(--ac)}</style></head><body><main><div class="c">${html}</div></main></body></html>`);
}

// ---- sessão (cookie assinado)
const COOKIE = 'er_sessao';
const DIAS = 30;
function criarSessao(email) {
  const p = Buffer.from(JSON.stringify({ e: email, x: Date.now() + DIAS * 864e5 })).toString('base64url');
  return p + '.' + hmac('sessao:' + p);
}
function cookieSessao(valor) { return `${COOKIE}=${valor}; Path=/; Max-Age=${DIAS * 86400}; HttpOnly; Secure; SameSite=Lax`; }
function lerSessao(req) {
  const m = String(req.headers.cookie || '').match(new RegExp('(?:^|;\\s*)' + COOKIE + '=([^;]+)'));
  if (!m || !env('SESSION_SECRET')) return null;
  const [p, s] = m[1].split('.');
  if (!p || !s || !seguroIgual(s, hmac('sessao:' + p))) return null;
  try { const o = JSON.parse(Buffer.from(p, 'base64url').toString()); return o.x > Date.now() ? o.e : null; } catch (e) { return null; }
}

// ---- banco (Supabase REST, chave de serviço)
async function sb(rota, { method = 'GET', body, prefer = 'return=minimal', headers = {} } = {}) {
  const base = env('SUPABASE_URL'), key = env('SUPABASE_SERVICE_ROLE_KEY');
  if (!base || !key) throw new Error('banco_nao_configurado');
  const r = await fetch(base + '/rest/v1/' + rota, { method, headers: { apikey: key, Authorization: 'Bearer ' + key, 'Content-Type': 'application/json', Prefer: prefer, ...headers }, body: body ? JSON.stringify(body) : undefined });
  if (!r.ok) throw new Error('banco_' + r.status + ':' + (await r.text()).slice(0, 200));
  return r;
}
const contar = async (rota) => { const r = await sb(rota + '&select=email&limit=1', { prefer: 'count=exact' }); const m = /\/(\d+)$/.exec(r.headers.get('content-range') || ''); return m ? +m[1] : 0; };
const db = global.__DB_MOCK__ || {
  contarTokensEmail: (email, desde) => contar(`acesso_tokens?email=eq.${enc(email)}&criado_em=gte.${enc(desde)}`),
  contarTokensIp: (ip, desde) => contar(`acesso_tokens?ip_hash=eq.${ip}&criado_em=gte.${enc(desde)}`),
  leitor: async (email) => (await (await sb(`acesso_leitores?email=eq.${enc(email)}&select=email,status`)).json())[0] || null,
  criarLeitor: (email) => sb('acesso_leitores?on_conflict=email', { method: 'POST', body: { email }, prefer: 'resolution=ignore-duplicates,return=minimal' }),
  statusLeitor: (email, status) => sb(`acesso_leitores?email=eq.${enc(email)}`, { method: 'PATCH', body: { status } }),
  tocarLeitor: (email) => sb(`acesso_leitores?email=eq.${enc(email)}`, { method: 'PATCH', body: { ultimo_acesso: new Date().toISOString() } }),
  criarToken: (t) => sb('acesso_tokens', { method: 'POST', body: t }),
  consumirToken: async (hash) => (await (await sb(`acesso_tokens?hash=eq.${hash}&usado_em=is.null&expira_em=gt.${enc(new Date().toISOString())}`, { method: 'PATCH', body: { usado_em: new Date().toISOString() }, prefer: 'return=representation' })).json())[0] || null,
  tokenValido: async (hash) => (await (await sb(`acesso_tokens?hash=eq.${hash}&usado_em=is.null&expira_em=gt.${enc(new Date().toISOString())}&select=email,destino`)).json())[0] || null,
  registrarLeitura: (email, slug) => sb('acesso_log', { method: 'POST', body: { email, slug } }),
};

// ---- e-mail (Resend)
async function enviarEmail({ para, assunto, html, texto }) {
  // Gmail (senha de app) tem prioridade; sem ele, usa o Resend.
  if (env('GMAIL_USER') && env('GMAIL_APP_PASSWORD')) {
    const nodemailer = require('nodemailer');
    const t = nodemailer.createTransport({ host: env('SMTP_HOST', 'smtp.gmail.com'), port: +env('SMTP_PORT', '465'), secure: true, auth: { user: env('GMAIL_USER'), pass: env('GMAIL_APP_PASSWORD') } });
    await t.sendMail({ from: `"Eduardo Reis Araújo" <${env('GMAIL_USER')}>`, to: para, subject: assunto, html, text: texto });
    return;
  }
  const chave = env('RESEND_API_KEY');
  if (!chave) throw new Error('email_nao_configurado');
  const r = await fetch(env('RESEND_API_URL', 'https://api.resend.com/emails'), {
    method: 'POST', headers: { Authorization: 'Bearer ' + chave, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: env('MAIL_FROM', 'Eduardo Reis Araújo <acesso@eduardoreisaraujo.com.br>'), to: [para], subject: assunto, html, text: texto }),
  });
  if (!r.ok) throw new Error('email_' + r.status + ':' + (await r.text()).slice(0, 200));
}

// ---- conteúdo cifrado
const chaves = new Map(), htmls = new Map();
function decifrar(slug) {
  if (htmls.has(slug)) return htmls.get(slug);
  const senha = env('ESTUDOS_SENHA');
  if (!senha) throw new Error('senha_nao_configurada');
  const p = JSON.parse(fs.readFileSync(path.join(dirCifrado(), slug + '.json'), 'utf8'));
  const chave = crypto.pbkdf2Sync(senha, Buffer.from(p.salt, 'base64'), p.iter, 32, 'sha256');
  const buf = Buffer.from(p.ct, 'base64'), tag = buf.subarray(buf.length - 16);
  const d = crypto.createDecipheriv('aes-256-gcm', chave, Buffer.from(p.iv, 'base64')); d.setAuthTag(tag);
  const html = Buffer.concat([d.update(buf.subarray(0, buf.length - 16)), d.final()]).toString('utf8');
  htmls.set(slug, html); return html;
}

module.exports = { env, SITE, sha256, hmac, seguroIgual, enc, esc, normEmail, slugValido, corpo, ipHash, resposta, pagina, criarSessao, cookieSessao, lerSessao, db, enviarEmail, decifrar };
