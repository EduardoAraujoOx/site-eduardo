/* Formulários do portal (contato com a Vertex e cadastro do livro).
   Função de borda da Vercel: recebe o formulário e manda um e-mail de texto para o endereço
   configurado, pela API do Resend (plano gratuito). O endereço de destino e a chave ficam nas
   variáveis de ambiente do projeto (RESEND_API_KEY e CONTATO_PARA), nunca no navegador nem no
   repositório. Opcional: com SUPABASE_URL e SUPABASE_ANON_KEY, também grava a linha na tabela
   leads, para montar listas (ver _src/municipios-na-reforma/leads-schema.sql).
   GET devolve {ativo}: o portal só mostra os formulários quando as variáveis existem. */
export const config = { runtime: 'edge' };

const resposta = (corpo, status) => new Response(JSON.stringify(corpo), {
    status: status || 200,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
});
const texto = (v, max) => String(v == null ? '' : v).replace(/\r/g, '').trim().slice(0, max);
const umaLinha = (v, max) => texto(v, max).replace(/\s*\n+\s*/g, ' ');
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const ROTULO = { contato: 'Contato com a Vertex', livro: 'Cadastro do livro (pré-lançamento)' };

export default async function handler(request) {
    const chave = process.env.RESEND_API_KEY, destino = process.env.CONTATO_PARA;
    const ativo = Boolean(chave && destino);
    if (request.method === 'GET') return resposta({ ativo });
    if (request.method !== 'POST') return resposta({ erro: 'metodo' }, 405);
    if (!ativo) return resposta({ erro: 'nao_configurado' }, 503);

    const origem = request.headers.get('origin');                 // só aceita o próprio portal
    if (origem) { try { if (new URL(origem).host !== request.headers.get('host')) return resposta({ erro: 'origem' }, 403); } catch (e) { return resposta({ erro: 'origem' }, 403); } }

    let b;
    try { b = await request.json(); } catch (e) { return resposta({ erro: 'json' }, 400); }
    if (!b || b.site) return resposta({ ok: true });               // campo-isca: robô preenche, gente não
    if (Number(b.t) < 2500) return resposta({ ok: true });         // formulário enviado rápido demais para um humano

    const tipo = b.tipo === 'livro' ? 'livro' : 'contato';
    const d = {
        tipo,
        nome: umaLinha(b.nome, 120),
        email: umaLinha(b.email, 160).toLowerCase(),
        telefone: umaLinha(b.telefone, 40),
        cargo: umaLinha(b.cargo, 120),
        municipio: umaLinha(b.municipio, 120),
        mensagem: texto(b.mensagem, 2000),
        aceite: b.aceite_privacidade === true,
        pagina: umaLinha(b.origem, 80),
        utm: umaLinha(b.utm, 300)
    };
    if (d.nome.length < 3 || !EMAIL.test(d.email)) return resposta({ erro: 'dados' }, 400);
    if (tipo === 'contato' && d.mensagem.length < 5) return resposta({ erro: 'dados' }, 400);
    if (!d.aceite) return resposta({ erro: 'aceite' }, 400);

    const linhas = [
        ROTULO[tipo], '',
        'Nome: ' + d.nome,
        'E-mail: ' + d.email,
        d.telefone ? 'Telefone: ' + d.telefone : null,
        d.cargo ? 'Cargo: ' + d.cargo : null,
        d.municipio ? 'Município ou órgão: ' + d.municipio : null,
        tipo === 'livro' ? 'Pediu: sumário do livro e informações do lançamento' : null,
        d.mensagem ? '\nMensagem:\n' + d.mensagem : null,
        '', 'Aceitou a política de privacidade: sim',
        d.pagina ? 'Origem: ' + d.pagina : null,
        d.utm ? 'Campanha: ' + d.utm : null
    ].filter(x => x !== null).join('\n');

    const envio = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { authorization: 'Bearer ' + chave, 'content-type': 'application/json' },
        body: JSON.stringify({
            from: process.env.CONTATO_DE || 'Municípios na Reforma <onboarding@resend.dev>',
            to: [destino],
            reply_to: d.email,
            subject: '[Municípios na Reforma] ' + (tipo === 'livro' ? 'Livro: ' : 'Contato: ') + d.nome + (d.municipio ? ' (' + d.municipio + ')' : ''),
            text: linhas
        })
    }).catch(() => null);
    if (!envio || !envio.ok) return resposta({ erro: 'envio' }, 502);

    const url = process.env.SUPABASE_URL, anon = process.env.SUPABASE_ANON_KEY;   // lista opcional; falha aqui não derruba o envio
    if (url && anon) {
        await fetch(url.replace(/\/$/, '') + '/rest/v1/leads', {
            method: 'POST',
            headers: { apikey: anon, authorization: 'Bearer ' + anon, 'content-type': 'application/json', prefer: 'return=minimal' },
            body: JSON.stringify({ nome: d.nome, email: d.email, cargo: d.cargo, municipio: d.municipio, origem: 'form:' + tipo, tipo, telefone: d.telefone, mensagem: d.mensagem, utm: d.utm, aceite_privacidade: true, aceite_contato: tipo === 'livro', versao_termos: '2026-10' })
        }).catch(() => null);
    }
    return resposta({ ok: true });
}
