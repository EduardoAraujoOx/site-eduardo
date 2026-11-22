/* Radar de notícias da reforma tributária: lê feeds RSS/Atom de fontes selecionadas, deixa só o que trata do tema
   e devolve título, fonte, data e link. Não guarda nem reproduz o texto das matérias: o leitor vai ao veículo de origem.
   Roda na borda da Vercel (sem DOMParser), por isso o leitor de XML é pequeno e feito à mão.
   Para trocar as fontes, edite FEEDS e VEICULOS abaixo; o restante não muda. */

/* ── fontes ── */
// Feeds de cobertura geral: só entram as notícias que passam no filtro de assunto.
export const FEEDS = [
    {id: 'senado', nome: 'Agência Senado', tipo: 'congresso', url: 'https://www12.senado.leg.br/noticias/rss'},
    {id: 'camara', nome: 'Agência Câmara', tipo: 'congresso', url: 'https://www.camara.leg.br/noticias/rss/ultimas-noticias'},
    {id: 'receita', nome: 'Receita Federal', tipo: 'governo', url: 'https://www.gov.br/receitafederal/pt-br/assuntos/noticias/RSS'},
    {id: 'agenciabrasil', nome: 'Agência Brasil', tipo: 'imprensa', url: 'https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml'},
    {id: 'jota', nome: 'JOTA', tipo: 'imprensa', url: 'https://www.jota.info/feed'},
    {id: 'conjur', nome: 'Conjur', tipo: 'imprensa', url: 'https://conjur.com.br/feed/'},
    {id: 'poder360', nome: 'Poder360', tipo: 'imprensa', url: 'https://www.poder360.com.br/feed/'}
];

// Buscas no Google Notícias, que devolve só links. Com `veiculo`, todo resultado é daquele órgão (a busca restringe o endereço);
// sem ele, cada resultado só é aceito se o veículo estiver em VEICULOS. `semFiltro` dispensa o filtro de assunto, para fontes que só tratam do tema.
const gn = consulta => 'https://news.google.com/rss/search?hl=pt-BR&gl=BR&ceid=BR:pt-419&q=' + encodeURIComponent(consulta);
export const BUSCAS = [
    {id: 'gn-cgibs', url: gn('IBS site:cgibs.gov.br when:60d'), veiculo: {nome: 'Comitê Gestor do IBS', tipo: 'cgibs'}, semFiltro: true},
    {id: 'gn-fazenda', url: gn('reforma tributária site:gov.br/fazenda when:30d'), veiculo: {nome: 'Ministério da Fazenda', tipo: 'governo'}},
    {id: 'gn-planalto', url: gn('reforma tributária site:gov.br/planalto when:30d'), veiculo: {nome: 'Presidência da República', tipo: 'governo'}},
    {id: 'gn-congresso', url: gn('reforma tributária (site:camara.leg.br OR site:senado.leg.br) when:30d')},
    {id: 'gn-entes', url: gn('reforma tributária (site:cnm.org.br OR site:fnp.org.br OR site:comsefaz.org.br) when:30d')},
    {id: 'gn-imprensa', url: gn('"reforma tributária" (IBS OR CBS OR CGIBS OR "Comitê Gestor") when:7d')},
    {id: 'gn-municipios', url: gn('"reforma tributária" (municípios OR prefeituras OR ISS) when:14d')}
];

// Veículos aceitos nas buscas, por domínio (sem "www."). O tipo define o filtro da página.
export const VEICULOS = {
    'senado.leg.br': {nome: 'Agência Senado', tipo: 'congresso'},
    'camara.leg.br': {nome: 'Agência Câmara', tipo: 'congresso'},
    'cnm.org.br': {nome: 'CNM', tipo: 'entes'},
    'fnp.org.br': {nome: 'FNP', tipo: 'entes'},
    'comsefaz.org.br': {nome: 'Comsefaz', tipo: 'entes'},
    'valor.globo.com': {nome: 'Valor Econômico', tipo: 'imprensa'},
    'g1.globo.com': {nome: 'g1', tipo: 'imprensa'},
    'oglobo.globo.com': {nome: 'O Globo', tipo: 'imprensa'},
    'folha.uol.com.br': {nome: 'Folha de S.Paulo', tipo: 'imprensa'},
    'estadao.com.br': {nome: 'Estadão', tipo: 'imprensa'},
    'cnnbrasil.com.br': {nome: 'CNN Brasil', tipo: 'imprensa'},
    'poder360.com.br': {nome: 'Poder360', tipo: 'imprensa'},
    'jota.info': {nome: 'JOTA', tipo: 'imprensa'},
    'conjur.com.br': {nome: 'Conjur', tipo: 'imprensa'},
    'agenciabrasil.ebc.com.br': {nome: 'Agência Brasil', tipo: 'imprensa'},
    'infomoney.com.br': {nome: 'InfoMoney', tipo: 'imprensa'},
    'exame.com': {nome: 'Exame', tipo: 'imprensa'},
    'bloomberglinea.com.br': {nome: 'Bloomberg Línea', tipo: 'imprensa'},
    'correiobraziliense.com.br': {nome: 'Correio Braziliense', tipo: 'imprensa'},
    'gazetadopovo.com.br': {nome: 'Gazeta do Povo', tipo: 'imprensa'},
    'nexojornal.com.br': {nome: 'Nexo', tipo: 'imprensa'},
    'migalhas.com.br': {nome: 'Migalhas', tipo: 'imprensa'}
};

// Convites, cursos e eventos de divulgação não são notícia da reforma; ficam de fora, salvo se tratarem de audiência, consulta ou ato oficial.
const PROMO = /inscri[cç]|capacit|curso\b|webinar|workshop|palestra|treinamento|jornada\b|semin[aá]rio|simp[oó]sio|encontro\b|promove\b|mentoria|\blive\b|oficina|roda de conversa|fórum\b|forum\b/i;
const OFICIAL = /audi[eê]ncia p[uú]blica|consulta p[uú]blica|medida provis[oó]ria|portaria|resolu[cç][aã]o|decreto|regulament|prazo|aprova|sanciona|publica/i;
const JANELA_DIAS = 30, MAXIMO = 80, ESPERA_MS = 4000, TAM_MAX = 1.5e6;

/* ── texto ── */
const sem = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const ENTIDADES = {amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' '};
const decodifica = s => s.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, e) => {
    if (e[0] === '#') {
        const n = e[1].toLowerCase() === 'x' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
        return n > 0 && n < 0x110000 ? String.fromCodePoint(n) : '';
    }
    return ENTIDADES[e.toLowerCase()] ?? m;
});
const limpa = s => decodifica(String(s || '').replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();

/* O assunto: reforma tributária e seus nomes próprios. "CBS" sozinha pode ser a rede americana, então exige contexto tributário. */
const NUCLEO = /reforma tributaria|\bibs\b|\bcgibs\b|comite gestor do (ibs|imposto)|imposto sobre bens e servicos|contribuicao sobre bens e servicos|\blc 2(14|27)\b|lei complementar (n[o.]? ?)?2(14|27)\b|imposto seletivo|split payment|cashback (do|da|tributario)|seguro-receita|\bec 132\b|emenda constitucional (n[o.]? ?)?132\b|transicao tributaria/;
const CBS = /\bcbs\b/, CONTEXTO_CBS = /tribut|imposto|\bibs\b|reforma|aliquota|nota fiscal|receita federal/;
const MUNICIPAL = /municip|prefeit|\biss\b|\biptu\b|cota-parte|\bfpm\b|\bfnp\b|\bcnm\b|\bcgibs\b/;

export function relevancia(titulo, resumo) {
    const t = sem(titulo), r = sem(resumo);
    const bate = s => NUCLEO.test(s) || (CBS.test(s) && CONTEXTO_CBS.test(s));
    if (bate(t)) return 2;
    return bate(r) ? 1 : 0;
}
export const ehMunicipal = (titulo, resumo) => MUNICIPAL.test(sem(titulo + ' ' + resumo));

/* ── leitor de feeds (RSS 2.0 e Atom) ── */
const campo = (bloco, nome) => {
    const m = bloco.match(new RegExp('<' + nome + '(?:\\s[^>]*)?>([\\s\\S]*?)</' + nome + '>', 'i'));
    return m ? m[1] : '';
};
export function leFeed(xml) {
    const blocos = xml.match(/<(item|entry)[\s>][\s\S]*?<\/\1>/gi) || [];
    return blocos.map(b => {
        let link = limpa(campo(b, 'link'));
        if (!link) {   // Atom: o endereço fica no atributo href
            const a = b.match(/<link\b[^>]*\brel=["']alternate["'][^>]*\bhref=["']([^"']+)["']/i) || b.match(/<link\b[^>]*\bhref=["']([^"']+)["']/i);
            link = a ? decodifica(a[1]) : '';
        }
        const data = limpa(campo(b, 'pubDate') || campo(b, 'dc:date') || campo(b, 'published') || campo(b, 'updated'));
        const fonte = b.match(/<source\b[^>]*\burl=["']([^"']+)["'][^>]*>([\s\S]*?)<\/source>/i);
        return {
            titulo: limpa(campo(b, 'title')),
            link,
            resumo: limpa(campo(b, 'description') || campo(b, 'summary') || campo(b, 'content:encoded')).slice(0, 600),
            data: Number.isFinite(Date.parse(data)) ? new Date(data).toISOString() : '',
            fonteUrl: fonte ? decodifica(fonte[1]) : '',
            fonteNome: fonte ? limpa(fonte[2]) : ''
        };
    }).filter(i => i.titulo && /^https:\/\//i.test(i.link));
}

const dominio = url => { try { return new URL(url).hostname.replace(/^www\./, '').toLowerCase(); } catch (_) { return ''; } };
const veiculoDe = host => {
    for (const d in VEICULOS) if (host === d || host.endsWith('.' + d)) return VEICULOS[d];
    return null;
};
// O Google Notícias põe o nome do veículo ao fim do título ("Título - Valor Econômico"), e alguns órgãos repetem o próprio nome ("Título — Planalto").
const ORGAOS = /\s[—–-]\s(?:Receita Federal|Minist[eé]rio da Fazenda|Governo Federal|Planalto|Presid[eê]ncia da Rep[uú]blica|Senado Not[ií]cias?|Secretaria de Comunica[cç][aã]o Social)\s*$/i;
const limpaTitulo = (titulo, nomes) => {
    for (const n of nomes) if (n) {
        const fim = ' - ' + n;
        if (titulo.toLowerCase().endsWith(fim.toLowerCase())) { titulo = titulo.slice(0, -fim.length); break; }
    }
    return titulo.replace(ORGAOS, '').trim();
};
const chave = titulo => sem(titulo).replace(/[^a-z0-9]+/g, ' ').trim().slice(0, 90);

/* ── coleta ── */
async function baixa(url) {
    const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), ESPERA_MS);
    try {
        const r = await fetch(url, {
            signal: ctl.signal, redirect: 'follow',
            headers: {'user-agent': 'Mozilla/5.0 (compatible; MunicipiosNaReforma-radar; +https://municipiosnareforma.com.br)', accept: 'application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.5'}
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const texto = await r.text();
        if (texto.length > TAM_MAX) throw new Error('feed grande demais');
        return texto;
    } finally { clearTimeout(t); }
}

export async function coletar(agora = Date.now()) {
    const limite = agora - JANELA_DIAS * 864e5;
    const fontes = [
        ...FEEDS.map(f => ({...f, geral: true})),
        ...BUSCAS.map(b => ({...b, geral: false}))
    ];
    const resultados = await Promise.allSettled(fontes.map(async f => ({f, itens: leFeed(await baixa(f.url))})));
    const itens = [], falhas = [];
    resultados.forEach((r, i) => {
        if (r.status === 'rejected') { falhas.push(fontes[i].id + ' (' + (r.reason && r.reason.name === 'AbortError' ? 'demorou demais' : (r.reason && r.reason.message) || 'erro') + ')'); return; }
        const {f, itens: lidos} = r.value;
        for (const it of lidos) {
            const quando = Date.parse(it.data);
            if (!Number.isFinite(quando) || quando < limite || quando > agora + 36e5) continue;
            let veiculo, url = it.link, titulo = it.titulo;
            if (f.geral) { veiculo = {nome: f.nome, tipo: f.tipo}; titulo = limpaTitulo(titulo, []); }
            else {
                veiculo = f.veiculo || veiculoDe(dominio(it.fonteUrl));
                if (!veiculo) continue;      // veículo fora da lista de fontes
                titulo = limpaTitulo(titulo, [it.fonteNome, veiculo.nome]);
            }
            const rel = f.semFiltro ? 2 : relevancia(titulo, f.geral ? it.resumo : '');
            if (!rel || titulo.length < 25) continue;      // título curto demais é página institucional, não notícia
            if (PROMO.test(titulo) && !OFICIAL.test(titulo)) continue;
            itens.push({
                titulo, fonte: veiculo.nome, tipo: veiculo.tipo, url, publicado_em: it.data,
                municipal: ehMunicipal(titulo, f.geral ? it.resumo : ''), forte: rel === 2
            });
        }
    });
    // Sem repetição (mesmo título ou mesmo endereço); entre repetidas, vale a de fonte oficial e a mais recente.
    const peso = {cgibs: 0, governo: 1, congresso: 2, entes: 3, imprensa: 4};
    itens.sort((a, b) => (peso[a.tipo] - peso[b.tipo]) || (Date.parse(b.publicado_em) - Date.parse(a.publicado_em)));
    const vistos = new Set(), unicos = [];
    for (const it of itens) {
        const k = chave(it.titulo), u = it.url.split('#')[0];
        if (vistos.has('t' + k) || vistos.has('u' + u)) continue;
        vistos.add('t' + k); vistos.add('u' + u); unicos.push(it);
    }
    unicos.sort((a, b) => Date.parse(b.publicado_em) - Date.parse(a.publicado_em));
    return {
        atualizado_em: new Date(agora).toISOString(),
        janela_dias: JANELA_DIAS,
        fontes: [...new Set([...FEEDS.map(f => f.nome), ...Object.values(VEICULOS).map(v => v.nome)])].sort((a, b) => a.localeCompare(b, 'pt-BR')),
        falhas,
        itens: unicos.slice(0, MAXIMO)
    };
}
