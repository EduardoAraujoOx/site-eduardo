/* Cadastro de quem pede a memória de cálculo.
   Função de borda da Vercel que recebe o formulário e grava no Supabase pela API REST.
   As chaves ficam nas variáveis de ambiente do projeto (SUPABASE_URL e SUPABASE_ANON_KEY),
   nunca no navegador nem no repositório. A tabela aceita só inserção para essa chave
   (ver _src/municipios-na-reforma/leads-schema.sql), então, mesmo que a chave vazasse,
   ninguém conseguiria ler os cadastros por ela.
   GET devolve {ativo}: o portal só pede cadastro quando as variáveis estão configuradas,
   e sem elas a memória de cálculo continua aberta a todos. */
export const config = { runtime: 'edge' };

const resposta = (corpo, status) => new Response(JSON.stringify(corpo), {
    status: status || 200,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
});
const texto = (v, max) => String(v == null ? '' : v).trim().slice(0, max);
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export default async function handler(request) {
    const url = process.env.SUPABASE_URL, chave = process.env.SUPABASE_ANON_KEY;
    const ativo = Boolean(url && chave);
    if (request.method === 'GET') return resposta({ ativo });
    if (request.method !== 'POST') return resposta({ erro: 'metodo' }, 405);
    if (!ativo) return resposta({ erro: 'nao_configurado' }, 503);

    const origem = request.headers.get('origin');                 // só aceita o próprio portal
    if (origem) { try { if (new URL(origem).host !== request.headers.get('host')) return resposta({ erro: 'origem' }, 403); } catch (e) { return resposta({ erro: 'origem' }, 403); } }

    let b;
    try { b = await request.json(); } catch (e) { return resposta({ erro: 'json' }, 400); }
    if (b && b.site) return resposta({ ok: true });                // campo-isca: robô preenche, gente não

    const lead = {
        nome: texto(b.nome, 120),
        email: texto(b.email, 160).toLowerCase(),
        cargo: texto(b.cargo, 120),
        vinculo: texto(b.vinculo, 40),
        municipio: texto(b.municipio, 120),
        municipio_cod: texto(b.municipio_cod, 7),
        uf: texto(b.uf, 2).toUpperCase(),
        origem: texto(b.origem, 60),
        utm: texto(b.utm, 300),
        aceite_privacidade: b.aceite_privacidade === true,
        aceite_contato: b.aceite_contato === true,
        versao_termos: texto(b.versao_termos, 20)
    };
    if (lead.nome.length < 3 || !EMAIL.test(lead.email) || lead.cargo.length < 2) return resposta({ erro: 'dados' }, 400);
    if (!lead.aceite_privacidade) return resposta({ erro: 'aceite' }, 400);

    const r = await fetch(url.replace(/\/$/, '') + '/rest/v1/leads', {
        method: 'POST',
        headers: { apikey: chave, authorization: 'Bearer ' + chave, 'content-type': 'application/json', prefer: 'return=minimal' },
        body: JSON.stringify(lead)
    });
    if (!r.ok) return resposta({ erro: 'gravacao' }, 502);
    return resposta({ ok: true });
}
