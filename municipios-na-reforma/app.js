/* Municípios na Reforma.
   Lê os mesmos JSONs do painel da reforma tributária (/data/), de modo que qualquer
   melhoria metodológica regenerada em data/ aparece aqui no mesmo deploy. Nenhum
   número de resultado é escrito à mão neste arquivo. */
(function () {
'use strict';

/* ── CONFIGURAÇÃO COMERCIAL: preencher antes da campanha ─────────────────── */
const CONFIG = {
    whatsapp: '5527988361923',   // somente dígitos com DDI e DDD, ex.: '5527999999999'
    email: '',      // ex.: 'fale@municipiosnareforma.com.br'
    gaId: '',       // ex.: 'G-XXXXXXXXXX' (Google Analytics 4), opcional
    razaoSocial: '', // ex.: 'Vertex Advisory Ltda.', aparece na política de privacidade
    cnpj: '',        // ex.: '00.000.000/0001-00'
    sensibilidade: false   // painel "Quanto este resultado depende das hipóteses?" na ficha; adiado, mude para true para reativar
};

const ANOS = ['2029', '2030', '2031', '2032', '2033'];
const ANOS_HIST = ['2019', '2020', '2021', '2022', '2023', '2024', '2025'];
const NOMES_UF = {AC:'Acre',AL:'Alagoas',AM:'Amazonas',AP:'Amapá',BA:'Bahia',CE:'Ceará',DF:'Distrito Federal',ES:'Espírito Santo',GO:'Goiás',MA:'Maranhão',MG:'Minas Gerais',MS:'Mato Grosso do Sul',MT:'Mato Grosso',PA:'Pará',PB:'Paraíba',PE:'Pernambuco',PI:'Piauí',PR:'Paraná',RJ:'Rio de Janeiro',RN:'Rio Grande do Norte',RO:'Rondônia',RR:'Roraima',RS:'Rio Grande do Sul',SC:'Santa Catarina',SE:'Sergipe',SP:'São Paulo',TO:'Tocantins'};
const UF_POR_PREFIXO = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'};

/* Municípios: sete faixas fixas, as mesmas do painel. A variação vai de −74% a +265%, e num
   degradê contínuo a cauda achataria a cor de quase todos perto do meio. */
const CLASSES = [
    {ate: -30, cor: '#9c2222', rotulo: '−30% ou menos'},
    {ate: -15, cor: '#c9524f', rotulo: '−30% a −15%'},
    {ate: -5, cor: '#e08a88', rotulo: '−15% a −5%'},
    {ate: 5, cor: '#f0efec', rotulo: '−5% a +5%'},
    {ate: 15, cor: '#7cafec', rotulo: '+5% a +15%'},
    {ate: 30, cor: '#4a8ce0', rotulo: '+15% a +30%'},
    {ate: Infinity, cor: '#1c5cab', rotulo: '+30% ou mais'}
];
const COR_RESSALVA = '#b9bec2', COR_SEM_ESFERA = '#e8ecef', ROTULO_RESSALVA = 'Sem base de 2025';
/* Estados: escala contínua divergente, vermelho ↔ cinza ↔ azul, centrada em zero. */
const COR_NEG = '#a02525', COR_MEIO = '#f0efec', COR_POS = '#1c5cab';

/* ── formatação (mesmas regras do painel) ── */
const fmtPct = v => {
    if (v == null || !isFinite(v)) return '—';
    const p = Math.round(v * 1000) / 10;                  // o sinal sai do valor já arredondado
    return (p > 0 ? '+' : p < 0 ? '−' : '') + Math.abs(p).toLocaleString('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1}) + '%';
};
const fmtPctSimples = v => Math.round(v * 100).toLocaleString('pt-BR') + '%';
const fmtPctPlain = (v, dec) => v == null ? '—' : v.toLocaleString('pt-BR', {maximumFractionDigits: dec == null ? 4 : dec}) + '%';
const clsSinal = v => v == null ? '' : v < -0.0005 ? 'neg' : v > 0.0005 ? 'pos' : '';
function fmtMoney(v) {
    if (v == null || !isFinite(v)) return '—';
    const a = Math.abs(v), s = v < 0 ? '−' : '';
    if (a >= 1e9) return s + 'R$ ' + (a / 1e9).toLocaleString('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1}) + ' bi';
    if (a >= 1e6) return s + 'R$ ' + (a / 1e6).toLocaleString('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1}) + ' mi';
    if (a >= 1e3) return s + 'R$ ' + Math.round(a / 1e3).toLocaleString('pt-BR') + ' mil';
    return s + 'R$ ' + Math.round(a).toLocaleString('pt-BR');
}
/* Valores lado a lado (2025, 2033 sem e com a reforma): duas casas em bilhões, para que 1,96 e 2,04 não virem "2,0" e "2,0". */
function fmtMoneyFino(v) {
    if (v != null && isFinite(v) && Math.abs(v) >= 1e9) return (v < 0 ? '−' : '') + 'R$ ' + (Math.abs(v) / 1e9).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' bi';
    return fmtMoney(v);
}
const fmtInt = v => Math.round(v).toLocaleString('pt-BR');
const norm = s => (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const getJSON = url => fetch(url).then(r => { if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); });

function classeDe(m) {
    if (!m) return null;
    if (m.r) return {cor: COR_RESSALVA, rotulo: ROTULO_RESSALVA};
    const p = m.v * 100;
    return CLASSES.find(c => p < c.ate) || CLASSES[CLASSES.length - 1];
}

/* ── medição da campanha (GA4 opcional) ── */
function track(evento, params) {
    try { if (typeof window.gtag === 'function') window.gtag('event', evento, params || {}); } catch (e) { /* sem medição, sem problema */ }
}
if (CONFIG.gaId) {
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    const s = document.createElement('script');
    s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(CONFIG.gaId);
    document.head.appendChild(s);
    window.gtag('js', new Date()); window.gtag('config', CONFIG.gaId);
}

/* ── estado ── */
let LISTA = [], POR_COD = {}, RESULT = null, NAC = null, AGG = {};
let ESCOPO = 'BR', NIVEL = 'uf', ATUAL = null, MAPA = null, MINI = null, graficos = [];
const MEMO = {cod: null, secao: 'historico'};
const RANK = {}, DADOS_UF = {};
let LOCAL = null, MAPA_DESTAQUE = null;
let UF_VISITANTE = null, RANK_UF = null, RANK_ORDEM = 'pct', RANK_PEQ = false;
const RANK_MAIS = {perdas: false, ganhos: false};
const CACHE_UF = new Map(), CACHE_MEMO = new Map();
let MEMO_NAC = null;
let REF_NAC = null;   // total nacional de 2025 e fator de ajuste de cada ano (índice da base)
const GEO = {muni: null, uf: null, promessa: null};

/* ── abas ── */
function mostrarVisao(v) {
    if (v === 'vertex') { preencherMunicipioForms(); renderContextoVertex(); }
    document.querySelectorAll('.view').forEach(s => s.classList.toggle('active', s.id === 'view-' + v));
    document.querySelectorAll('.tab-btn').forEach(b => {
        const on = b.dataset.view === v;
        b.classList.toggle('active', on);
        if (on) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
    });
    const dentro = !!document.querySelector('.tab-mais-lista .tab-btn.active');         // aba aberta está no menu "Mais"
    $('tabMais').classList.toggle('active', dentro);
    fecharMais();
    window.scrollTo({top: 0});
}
function fecharMais() { $('tabMaisBox').classList.remove('aberto'); $('tabMais').setAttribute('aria-expanded', 'false'); }
$('tabMais').addEventListener('click', e => {
    e.stopPropagation();
    const aberto = $('tabMaisBox').classList.toggle('aberto');
    $('tabMais').setAttribute('aria-expanded', aberto ? 'true' : 'false');
});
document.addEventListener('click', e => { if (!$('tabMaisBox').contains(e.target)) fecharMais(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') fecharMais(); });
document.querySelectorAll('.tab-btn').forEach(b => b.addEventListener('click', () => {
    mostrarVisao(b.dataset.view); track('aba', {aba: b.dataset.view});
    if (b.dataset.view === 'municipio') municipioInicial();
    if (b.dataset.view === 'memoria') { memoriaInicial(); renderMemoria(); }
    if (b.dataset.view === 'rankings') renderRankUF();
}));
document.querySelectorAll('[data-ir]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); mostrarVisao(a.dataset.ir); }));
document.querySelectorAll('[data-ancora]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const el = $(a.dataset.ancora); if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'}); }));
document.addEventListener('click', e => {   // link que abre um item recolhido da ficha e rola até ele
    const a = e.target.closest('[data-abrir]'); if (!a) return;
    e.preventDefault();
    const d = $(a.dataset.abrir); if (!d) return;
    d.open = true;
    d.scrollIntoView({behavior: 'smooth', block: 'start'});
});
document.addEventListener('click', e => {   // link de texto que age como a aba (e, se pedido, rola até a seção)
    const a = e.target.closest('[data-tab]'); if (!a) return;
    e.preventDefault();
    const b = document.querySelector('.tab-btn[data-view="' + a.dataset.tab + '"]'); if (b) b.click();
    if (a.dataset.depois) setTimeout(() => { const el = $(a.dataset.depois); if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'}); }, 80);
});

/* ── carga ── */
Promise.all([
    getJSON('/data/painel-municipios/index.json'),
    getJSON('/data/resultados-consolidados-ibs.json').catch(() => null),
    getJSON('/data/ibs-projecao-nacional.json').catch(() => null)
]).then(([idx, res, nac]) => iniciar(idx, res, nac))
  .catch(e => { console.error(e); $('dicaBusca').textContent = 'Não foi possível carregar a base de municípios. Atualize a página em instantes.'; });

function iniciar(idx, res, nac) {
    LISTA = Object.entries(idx.municipios).map(([cod, m]) => ({cod, nome: m.nome, uf: m.uf, v: m.v, r: !!m.r, chave: norm(m.nome), alt: m.an ? norm(m.an) : ''}));
    LISTA.forEach(m => { POR_COD[m.cod] = m; });
    RESULT = res; NAC = nac; REF_NAC = idx.referencia_nacional || null;
    calcularRanks();
    AGG = (res && res.variacao_municipal_por_uf_2033) || {};

    $('mapaUF').innerHTML = '<option value="BR">Brasil</option>' + Object.keys(NOMES_UF)
        .filter(u => LISTA.some(m => m.uf === u))
        .sort((a, b) => NOMES_UF[a].localeCompare(NOMES_UF[b], 'pt-BR'))
        .map(u => `<option value="${u}">${NOMES_UF[u]}</option>`).join('');
    $('mapaUF').addEventListener('change', e => { definirEscopo(e.target.value); track('mapa_uf', {uf: e.target.value}); });
    document.querySelectorAll('#toggleNivel button').forEach(b => b.addEventListener('click', () => definirEscopo('BR', b.dataset.nivel)));
    document.querySelectorAll('#toggleViz button').forEach(b => b.addEventListener('click', () => {
        const tabela = b.dataset.viz === 'tabela';
        document.querySelectorAll('#toggleViz button').forEach(x => x.classList.toggle('active', x === b));
        $('mapaWrap').hidden = tabela; $('mapaLegenda').hidden = tabela; $('mapaTabela').hidden = !tabela;
    }));

    ativarBusca($('busca'), $('sugestoes'), $('formBusca'), cod => abrirMunicipio(cod), codDoCampo);
    ativarBusca($('buscaMuni'), $('sugestoesMuni'), $('formBuscaMuni'), cod => abrirMunicipio(cod));
    ativarBusca($('buscaMemo'), $('sugestoesMemo'), $('formBuscaMemo'), cod => abrirMemoria(cod));
    $('dicaBusca').textContent = '';
    definirEscopo('BR', 'uf');
    montarRankings();
    document.querySelectorAll('#memoAbas button').forEach(b => b.addEventListener('click', () => { MEMO.secao = b.dataset.secao; renderMemoria(); }));

    carregarMalha().then(() => {
        MAPA = criarMapa($('mapaSvg'), $('mapaWrap'), $('mapaTip'), {camadaUF: true, todos: true, uf: ESCOPO, nivel: NIVEL, aoClicar: cod => abrirMunicipio(cod), aoClicarUF: uf => definirEscopo(uf, 'muni')});
        $('mapaCarregando').hidden = true; $('mapaSvg').removeAttribute('hidden');   // SVGElement não tem a propriedade hidden
        if (ATUAL || MAPA_DESTAQUE) MAPA.destacar(ATUAL || MAPA_DESTAQUE);
    }).catch(e => { console.error(e); $('mapaCarregando').textContent = 'O mapa não pôde ser carregado agora. Use a busca por município ou a lista ao lado.'; });

    const cod = new URLSearchParams(location.search).get('m');
    if (cod && POR_COD[cod]) abrirMunicipio(cod, {semUrl: true}); else iniciarLocalizacao();
    $('btnLocal').addEventListener('click', () => localizarGPS(false));
}

/* ── escopo e nível do mapa ── */
const nivelAtual = () => ESCOPO === 'BR' ? NIVEL : 'muni';
const noEscopo = () => LISTA.filter(m => ESCOPO === 'BR' || m.uf === ESCOPO);

function definirEscopo(uf, nivel) {
    ESCOPO = uf;
    if (nivel) NIVEL = nivel;
    $('mapaUF').value = uf;
    $('toggleNivel').hidden = uf !== 'BR';
    document.querySelectorAll('#toggleNivel button').forEach(b => b.classList.toggle('active', b.dataset.nivel === NIVEL));
    if (MAPA) MAPA.definir(ESCOPO, NIVEL);
    if (uf !== 'BR') municipiosDaUF(uf).catch(() => CACHE_UF.delete(uf));   // alimenta a dica do mapa com R$ e população
    renderCabecalhoMapa(); renderLegenda(); renderTabelaMapa(); renderTrilho(); renderContexto();
}

function renderCabecalhoMapa() {
    if (nivelAtual() === 'uf') {
        $('tituloMapa').textContent = 'Variação da receita municipal por estado em 2033';
        $('subMapa').textContent = 'Receita das prefeituras de cada estado (ISS mais cota-parte do ICMS), somada, contra o cenário sem a reforma. Clique num estado para ver os municípios.';
    } else {
        $('tituloMapa').textContent = ESCOPO === 'BR' ? 'Variação da receita municipal em 2033' : 'Variação da receita municipal em 2033, ' + emUF(ESCOPO);
        $('subMapa').textContent = 'Cada município colorido pela variação da própria receita contra o cenário sem a reforma. Clique para abrir a ficha, ou busque pelo nome.';
    }
}

function limiteEscala() { return Math.max(0.01, ...Object.values(AGG).filter(v => v != null).map(Math.abs)); }

function renderLegenda() {
    const alvo = $('mapaLegenda');
    if (nivelAtual() === 'uf') {
        const m = limiteEscala();
        alvo.innerHTML = `<div class="escala"><div class="escala-barra" aria-hidden="true"></div>
            <div class="escala-ticks" aria-hidden="true"><span>${fmtPct(-m)}</span><span>0</span><span>${fmtPct(m)}</span></div>
            <p class="nota">Vermelho: as prefeituras do estado, somadas, arrecadam menos do que arrecadariam sem a reforma. Azul: arrecadam mais. O valor de cada estado aparece ao passar o cursor e na lista ao lado.</p></div>`;
        return;
    }
    const escopo = noEscopo(), cont = {};
    escopo.forEach(x => { const c = classeDe(x); cont[c.rotulo] = (cont[c.rotulo] || 0) + 1; });
    const itens = CLASSES.map(c => [c.cor, c.rotulo]).concat([[COR_RESSALVA, ROTULO_RESSALVA]]);
    alvo.innerHTML = '<ul class="legenda">' + itens.map(([cor, rot]) => `<li><i style="background:${cor}"></i>${rot} <b>${fmtInt(cont[rot] || 0)}</b></li>`).join('') + '</ul>';
}

function linhasUF() {
    return Object.keys(NOMES_UF).filter(u => LISTA.some(m => m.uf === u)).map(u => {
        const ok = LISTA.filter(m => m.uf === u && !m.r), perdem = ok.filter(m => m.v < 0).length;
        return {uf: u, v: AGG[u] != null ? AGG[u] : null, perdem, n: ok.length, total: LISTA.filter(m => m.uf === u).length};
    }).sort((a, b) => (b.v != null && a.v != null) ? b.v - a.v : (b.perdem / b.n) - (a.perdem / a.n));
}

/* Contagens: o total é o de municípios do estado; as posições e a contagem de quem perde usam os que têm base de 2025 (ver a metodologia). */
const totalUF = uf => LISTA.filter(m => m.uf === uf).length;
function txtPerdem(l) {
    return `${fmtInt(l.perdem)} de ${fmtInt(l.n)} prefeituras perdem`;
}

function renderTabelaMapa() {
    const alvo = $('mapaTabela');
    if (nivelAtual() === 'uf') {
        alvo.innerHTML = `<table class="dados"><thead><tr><th>Estado</th><th>Prefeituras</th><th>Perdem em 2033</th><th>Variação agregada</th></tr></thead><tbody>`
            + linhasUF().map(l => `<tr class="clicavel" data-uf="${l.uf}"><td class="nome">${NOMES_UF[l.uf]}</td><td>${fmtInt(l.total)}</td><td>${fmtInt(l.perdem)} de ${fmtInt(l.n)} (${fmtPctSimples(l.perdem / l.n)})</td><td class="${clsSinal(l.v)}">${fmtPct(l.v)}</td></tr>`).join('') + '</tbody></table>';
        alvo.querySelectorAll('tr[data-uf]').forEach(tr => tr.addEventListener('click', () => definirEscopo(tr.dataset.uf, 'muni')));
        return;
    }
    const escopo = noEscopo(), cont = {};
    escopo.forEach(x => { const c = classeDe(x); cont[c.rotulo] = (cont[c.rotulo] || 0) + 1; });
    const itens = CLASSES.map(c => [c.cor, c.rotulo]).concat([[COR_RESSALVA, ROTULO_RESSALVA]]);
    alvo.innerHTML = `<table class="dados"><thead><tr><th>Faixa de variação em 2033</th><th>Municípios</th><th>Do total</th></tr></thead><tbody>`
        + itens.map(([cor, rot]) => `<tr><td class="nome"><i style="background:${cor};display:inline-block;width:.9rem;height:.7rem;border:1px solid rgba(0,0,0,.12);margin-right:.5rem"></i>${rot}</td><td>${fmtInt(cont[rot] || 0)}</td><td>${fmtPctSimples((cont[rot] || 0) / escopo.length)}</td></tr>`).join('') + '</tbody></table>';
}

/* Lista lateral: no Brasil, os estados pela variação agregada da receita municipal; num estado, os municípios. */
function renderTrilho() {
    const head = $('trilhoHead'), lista = $('trilhoLista');
    if (ESCOPO === 'BR') {
        head.textContent = 'Estados, do maior ganho à maior perda';
        const linhas = linhasUF();
        const max = Math.max(...linhas.map(l => Math.abs(l.v || 0)), 0.01);
        lista.innerHTML = linhas.map((l, i) => `<button type="button" class="rail-row" data-uf="${l.uf}">
            <span class="rk">${i + 1}</span><span class="nm">${NOMES_UF[l.uf]}<small>${txtPerdem(l)}</small></span>
            <span class="vl ${clsSinal(l.v)}">${fmtPct(l.v)}</span>${l.v != null ? `<i class="bar ${clsSinal(l.v)}" style="width:${Math.max(2, Math.abs(l.v) / max * 62)}%"></i>` : ''}</button>`).join('');
        lista.querySelectorAll('[data-uf]').forEach(b => b.addEventListener('click', () => { definirEscopo(b.dataset.uf, 'muni'); track('trilho_uf', {uf: b.dataset.uf}); }));
    } else {
        head.innerHTML = `<button type="button" id="voltaBR">← Brasil</button>${esc(NOMES_UF[ESCOPO])}: municípios, do maior ganho à maior perda`;
        $('voltaBR').addEventListener('click', () => definirEscopo('BR', 'uf'));
        const ok = noEscopo().filter(m => !m.r).sort((a, b) => b.v - a.v);
        const linha = (m, i) => `<button type="button" class="rail-row" data-cod="${m.cod}">
            <span class="rk">${i + 1}</span><span class="nm">${esc(m.nome)}</span>
            <span class="vl ${clsSinal(m.v)}">${fmtPct(m.v)}</span><i class="bar ${clsSinal(m.v)}" style="width:${Math.max(2, Math.min(Math.abs(m.v) / 0.6, 1) * 62)}%"></i></button>`;
        lista.innerHTML = ok.map(linha).join('');
        lista.scrollTop = 0;
        lista.querySelectorAll('[data-cod]').forEach(b => b.addEventListener('click', () => { track('trilho_municipio', {municipio: POR_COD[b.dataset.cod].nome}); abrirMunicipio(b.dataset.cod); }));
    }
}

function renderContexto() {
    const escopo = noEscopo(), ok = escopo.filter(m => !m.r), perdem = ok.filter(m => m.v < 0).length;
    const ord = ok.map(m => m.v).sort((a, b) => a - b);
    const mediana = ord.length % 2 ? ord[(ord.length - 1) / 2] : (ord[ord.length / 2 - 1] + ord[ord.length / 2]) / 2;
    const nome = ESCOPO === 'BR' ? 'No Brasil' : emUF(ESCOPO).replace(/^./, c => c.toUpperCase());
    const partes = [];
    if (ESCOPO === 'BR' && NAC && NAC.historico && NAC.projecao) {
        const h = NAC.historico[NAC.historico.length - 1], p = NAC.projecao[NAC.projecao.length - 1];
        partes.push(`<span>Bolo tributário 2025: <b>${fmtMoney(h.bolo_nominal)}</b></span>`,
            `<span>Projetado 2033: <b>${fmtMoney(p.icms_iss_residual + p.ibs_bruto)}</b></span>`,
            `<span>IBS já por destino em 2033: <b>${fmtPctPlain(p.ibs_destino_liquido / p.ibs_bruto * 100, 0)}</b> (pleno só em 2078)</span>`);
    }
    partes.push(`<span>${nome}: <b>${fmtInt(escopo.length)}</b> municípios analisados</span>`,
        `<span><b class="neg">${fmtInt(perdem)}</b> de ${fmtInt(ok.length)} municípios (<b>${fmtPctSimples(perdem / ok.length)}</b>) arrecadam menos em 2033 do que arrecadariam sem a reforma</span>`,
        `<span>Variação mediana: <b class="${clsSinal(mediana)}">${fmtPct(mediana)}</b></span>`);
    if (ESCOPO !== 'BR' && AGG[ESCOPO] != null) partes.push(`<span>Receita municipal agregada ${esc(DE_UF[ESCOPO])}: <b class="${clsSinal(AGG[ESCOPO])}">${fmtPct(AGG[ESCOPO])}</b></span>`);
    $('contexto').innerHTML = partes.join('');
}

/* ── rankings: dentro do estado, abrindo no estado do visitante ── */
const ufDoRanking = () => RANK_UF || UF_VISITANTE || (ATUAL && POR_COD[ATUAL] ? POR_COD[ATUAL].uf : null) || (ESCOPO !== 'BR' ? ESCOPO : null);

function montarRankings() {
    const ufs = Object.keys(NOMES_UF).filter(u => LISTA.some(m => m.uf === u)).sort((a, b) => NOMES_UF[a].localeCompare(NOMES_UF[b], 'pt-BR'));
    $('rankUF').innerHTML = '<option value="">Escolha um estado</option>' + ufs.map(u => `<option value="${u}">${NOMES_UF[u]}</option>`).join('');
    $('rankUF').addEventListener('change', e => selecionarRankUF(e.target.value));
    document.querySelectorAll('#rankOrdem button').forEach(b => b.addEventListener('click', () => {
        RANK_ORDEM = b.dataset.ordem;
        document.querySelectorAll('#rankOrdem button').forEach(x => x.classList.toggle('active', x === b));
        track('ranking_ordem', {ordem: RANK_ORDEM}); renderRankUF();
    }));
    $('rankPeq').addEventListener('change', e => { RANK_PEQ = e.target.checked; renderRankUF(); });
    $('maisPerdas').addEventListener('click', () => { RANK_MAIS.perdas = !RANK_MAIS.perdas; renderRankUF(); });
    $('maisGanhos').addEventListener('click', () => { RANK_MAIS.ganhos = !RANK_MAIS.ganhos; renderRankUF(); });

    $('tabUF').querySelector('tbody').innerHTML = linhasUF().map((l, i) => `<tr class="clicavel" data-uf="${l.uf}"><td>${i + 1}</td><td class="nome">${NOMES_UF[l.uf]}</td><td>${fmtInt(l.total)}</td><td>${fmtInt(l.perdem)} de ${fmtInt(l.n)} (${fmtPctSimples(l.perdem / l.n)})</td><td class="${clsSinal(l.v)}">${fmtPct(l.v)}</td></tr>`).join('');
    $('tabUF').querySelectorAll('tr[data-uf]').forEach(tr => tr.addEventListener('click', () => { selecionarRankUF(tr.dataset.uf); window.scrollTo({top: 0, behavior: 'smooth'}); }));
}

function selecionarRankUF(uf) {
    RANK_UF = uf || null;
    RANK_MAIS.perdas = RANK_MAIS.ganhos = false;
    if (uf) track('ranking_uf', {uf});
    renderRankUF();
}

async function renderRankUF() {
    const uf = ufDoRanking();
    $('rankUF').value = uf || '';
    $('rankTitulo').textContent = uf ? 'Comparar municípios em 2033, ' + emUF(uf) : 'Comparar municípios em 2033';
    $('rankVazio').hidden = !!uf; $('rankBloco').hidden = !uf; $('rankResumo').hidden = !uf;
    if (!uf) return;
    let munis;
    try { munis = await municipiosDaUF(uf); } catch (e) { CACHE_UF.delete(uf); $('rankVazio').textContent = 'Não foi possível carregar os municípios deste estado. Tente novamente em instantes.'; $('rankVazio').hidden = false; $('rankBloco').hidden = true; return; }
    if (ufDoRanking() !== uf) return;                         // o usuário já trocou de estado

    const todos = Object.entries(munis).map(([cod, m]) => {
        const cf = m.contrafactual_por_ano['2033'], pos = m.pos_por_ano['2033'];
        return {cod, nome: m.nome, pop: m.pop_media, v: m.variacao_por_ano['2033'], dif: pos - cf, ok: !m.neutro_aproximado && !m.neutro_suspeito && m.cobertura_anos >= 5};
    });
    const base = todos.filter(x => x.ok && (RANK_PEQ || x.pop >= 10000));
    const chave = RANK_ORDEM === 'rs' ? 'dif' : 'v';
    const perdas = base.filter(x => x.dif < 0).sort((a, b) => a[chave] - b[chave]);
    const ganhos = base.filter(x => x.dif > 0).sort((a, b) => b[chave] - a[chave]);

    const noEstado = LISTA.filter(m => m.uf === uf), confiaveis = noEstado.filter(m => !m.r), perdem = confiaveis.filter(m => m.v < 0).length;
    const ord = confiaveis.map(m => m.v).sort((x, y) => x - y);
    const mediana = ord.length ? (ord.length % 2 ? ord[(ord.length - 1) / 2] : (ord[ord.length / 2 - 1] + ord[ord.length / 2]) / 2) : null;
    $('rankResumo').innerHTML = [
        `<span><b>${fmtInt(noEstado.length)}</b> municípios ${esc(emUF(uf))}</span>`,
        `<span><b class="neg">${fmtInt(perdem)}</b> de ${fmtInt(confiaveis.length)} municípios (<b>${fmtPctSimples(perdem / Math.max(confiaveis.length, 1))}</b>) arrecadam menos em 2033</span>`,
        mediana != null ? `<span>Variação mediana: <b class="${clsSinal(mediana)}">${fmtPct(mediana)}</b></span>` : '',
        AGG[uf] != null ? `<span>Receita municipal agregada: <b class="${clsSinal(AGG[uf])}">${fmtPct(AGG[uf])}</b></span>` : ''
    ].join('');

    const crit = (RANK_PEQ ? 'Municípios com ao menos 5 anos de dados e base de 2025' : 'Municípios com ao menos 10 mil habitantes, 5 anos de dados e base de 2025')
        + `, ordenados por ${RANK_ORDEM === 'rs' ? 'diferença em reais por ano' : 'variação percentual'}. ${fmtInt(base.length)} de ${fmtInt(todos.length)} entram no ranking.`;
    $('rankCritPerdas').textContent = crit; $('rankCritGanhos').textContent = 'Mesmos critérios, do maior ganho para baixo.';

    const N = 10;
    const linhas = (lista, tudo) => (tudo ? lista : lista.slice(0, N)).map((m, i) => `<tr class="clicavel" data-cod="${m.cod}"><td>${i + 1}</td><td class="nome">${esc(m.nome)}</td><td class="col-pop">${fmtInt(m.pop)}</td><td class="${clsSinal(m.dif)}">${m.dif > 0 ? '+' : ''}${fmtMoney(m.dif)}</td><td class="${clsSinal(m.dif)}">${fmtPct(m.v)}</td></tr>`).join('')
        || '<tr><td colspan="5" class="vazio-td">Nenhum município nesta situação com os critérios atuais.</td></tr>';
    const preenche = (idTab, idBotao, lista, chaveMais) => {
        $(idTab).querySelector('tbody').innerHTML = linhas(lista, RANK_MAIS[chaveMais]);
        $(idTab).querySelectorAll('tr[data-cod]').forEach(tr => tr.addEventListener('click', () => { track('ranking_municipio', {municipio: POR_COD[tr.dataset.cod].nome}); abrirMunicipio(tr.dataset.cod); }));
        const b = $(idBotao);
        b.hidden = lista.length <= N;
        b.textContent = RANK_MAIS[chaveMais] ? 'Mostrar só os ' + N + ' primeiros' : 'Ver todos os ' + fmtInt(lista.length) + ' municípios';
    };
    preenche('tabPerdas', 'maisPerdas', perdas, 'perdas');
    preenche('tabGanhos', 'maisGanhos', ganhos, 'ganhos');
}

/* ── busca (padrão combobox), reaproveitada nas abas ── */
/* Município que o campo de busca da visão geral já traz escrito: o que está aberto na ficha ou o localizado. */
const emUF = uf => DE_UF[uf].replace(/^do /, 'no ').replace(/^da /, 'na ').replace(/^de /, 'em ');
const DE_UF = {AC:'do Acre',AL:'de Alagoas',AM:'do Amazonas',AP:'do Amapá',BA:'da Bahia',CE:'do Ceará',DF:'do Distrito Federal',ES:'do Espírito Santo',GO:'de Goiás',MA:'do Maranhão',MG:'de Minas Gerais',MS:'de Mato Grosso do Sul',MT:'de Mato Grosso',PA:'do Pará',PB:'da Paraíba',PE:'de Pernambuco',PI:'do Piauí',PR:'do Paraná',RJ:'do Rio de Janeiro',RN:'do Rio Grande do Norte',RO:'de Rondônia',RR:'de Roraima',RS:'do Rio Grande do Sul',SC:'de Santa Catarina',SE:'de Sergipe',SP:'de São Paulo',TO:'do Tocantins'};
const rotuloMuni = cod => POR_COD[cod].nome + ' (' + POR_COD[cod].uf + ')';
function codDoCampo(v) {
    const t = v.trim();
    if (ATUAL && t === rotuloMuni(ATUAL)) return ATUAL;
    if (LOCAL && (t === LOCAL.rotulo || t === rotuloMuni(LOCAL.cod) || !t)) return LOCAL.cod;
    return null;
}
function ativarBusca(inp, ul, form, aoEscolher, padrao) {
    inp.disabled = false;
    let sugestoes = [], ativo = -1;
    const fechar = () => { ul.hidden = true; inp.setAttribute('aria-expanded', 'false'); inp.removeAttribute('aria-activedescendant'); ativo = -1; };
    const marcar = i => {
        ativo = i;
        [...ul.children].forEach((li, k) => li.setAttribute('aria-selected', k === i ? 'true' : 'false'));
        if (i >= 0) inp.setAttribute('aria-activedescendant', ul.children[i].id); else inp.removeAttribute('aria-activedescendant');
    };
    const buscar = () => {
        const mUF = /\(\s*([a-z]{2})\s*\)\s*$/i.exec(inp.value);                      // "Vitória (ES)": o estado entre parênteses filtra, não entra no nome
        const ufFiltro = mUF && NOMES_UF[mUF[1].toUpperCase()] ? mUF[1].toUpperCase() : null;
        const q = norm(ufFiltro ? inp.value.replace(mUF[0], '') : inp.value);
        if (q.length < 2) { fechar(); return; }
        const comp = q.split(/\s+/), ufPreferida = ufFiltro || (ESCOPO !== 'BR' ? ESCOPO : UF_VISITANTE);   // entre homônimos, o do estado de quem busca vem primeiro
        sugestoes = LISTA
            .filter(m => !ufFiltro || m.uf === ufFiltro)
            .map(m => {
                const alvo = m.chave + ' ' + m.uf.toLowerCase(), alvoAlt = m.alt ? m.alt + ' ' + m.uf.toLowerCase() : '';      // o nome anterior (SICONFI) também acha o município
                if (!comp.every(c => alvo.includes(c)) && !(alvoAlt && comp.every(c => alvoAlt.includes(c)))) return null;
                return {m, ordem: m.chave === q ? 0 : m.chave.startsWith(q) ? 1 : m.chave.split(' ').some(w => w.startsWith(comp[0])) ? 2 : m.alt && (m.alt === q || m.alt.startsWith(q)) ? 2 : 3};
            })
            .filter(Boolean)
            .sort((a, b) => a.ordem - b.ordem || (b.m.uf === ufPreferida) - (a.m.uf === ufPreferida) || a.m.nome.localeCompare(b.m.nome, 'pt-BR'))
            .slice(0, 8).map(x => x.m);
        ul.innerHTML = sugestoes.length
            ? sugestoes.map((m, i) => `<li role="option" id="${ul.id}-${i}" data-cod="${m.cod}" aria-selected="false">${esc(m.nome)}<small>${m.uf}</small></li>`).join('')
            : '<li class="vazio-li" role="option" aria-disabled="true">Nenhum município encontrado. Confira a grafia.</li>';
        ul.hidden = false; inp.setAttribute('aria-expanded', 'true'); ativo = -1;
    };
    const escolher = cod => {
        fechar();
        track('busca_municipio', {municipio: POR_COD[cod].nome, uf: POR_COD[cod].uf});
        aoEscolher(cod);
    };
    inp.addEventListener('input', buscar);
    inp.addEventListener('keydown', e => {
        if (ul.hidden) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); marcar(Math.min(ativo + 1, sugestoes.length - 1)); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); marcar(Math.max(ativo - 1, 0)); }
        else if (e.key === 'Escape') { fechar(); }
    });
    ul.addEventListener('mousedown', e => {                // mousedown: o clique chega antes do blur do campo
        const li = e.target.closest('li[data-cod]');
        if (li) { e.preventDefault(); escolher(li.dataset.cod); }
    });
    inp.addEventListener('blur', () => setTimeout(fechar, 120));
    form.addEventListener('submit', e => {
        e.preventDefault();
        const cod = padrao && ativo < 0 && padrao(inp.value);       // campo ainda com o município localizado: é esse mesmo
        if (cod) { escolher(cod); return; }
        if (!sugestoes.length) buscar();
        const alvo = sugestoes[ativo >= 0 ? ativo : 0];
        if (alvo) escolher(alvo.cod);
    });
}

/* ── dica do município: mesmo molde da dica do estado (nome, número, contexto, posição, convite) ── */
function calcularRanks() {
    const porUF = {};
    LISTA.filter(m => !m.r).forEach(m => (porUF[m.uf] = porUF[m.uf] || []).push(m));
    Object.values(porUF).forEach(arr => { arr.sort((a, b) => b.v - a.v); arr.forEach((m, i) => { RANK[m.cod] = {pos: i + 1, n: arr.length}; }); });
}

function tipMunicipio(m) {
    if (m.r) return `<b>${esc(m.nome)} · ${m.uf}</b><small>Sem estimativa: não há base de 2025 utilizável (ver a metodologia).</small><em>Clique para ver a ficha →</em>`;
    const d = DADOS_UF[m.uf] && DADOS_UF[m.uf][m.cod];
    const dif = d ? d.pos_por_ano['2033'] - d.contrafactual_por_ano['2033'] : null;
    const rk = RANK[m.cod];
    return `<b>${esc(m.nome)} · ${m.uf}</b><span class="v ${clsSinal(m.v)}">${fmtPct(m.v)}</span><small>da receita em 2033, contra o cenário sem a reforma</small>`
        + (d ? `<small>${fmtMoney(Math.abs(dif))} por ano ${dif < 0 ? 'a menos' : 'a mais'} · ${fmtInt(d.pop_media)} habitantes</small>` : '')
        + (rk ? `<small>${fmtInt(rk.pos)}º entre ${fmtInt(rk.n)} municípios de ${m.uf} com base de 2025${totalUF(m.uf) > rk.n ? ' (de ' + fmtInt(totalUF(m.uf)) + ')' : ''}</small>` : '')
        + '<em>Clique para ver a ficha →</em>';
}

/* ── abertura no município de quem chega ──
   Três fontes, da mais à menos precisa: localização do navegador (já autorizada, ou pedida
   no botão), e estimativa pela conexão (/api/geo, só na Vercel). A localização do navegador
   é resolvida aqui mesmo, contra a malha municipal, sem enviar coordenadas a ninguém.
   A sugestão nunca abre a ficha sozinha: leva o mapa à UF, contorna o município e deixa o nome dele no campo de busca. */
function definirUFVisitante(uf) {
    UF_VISITANTE = uf;
    if (!RANK_UF && $('view-rankings').classList.contains('active')) renderRankUF();
}

function iniciarLocalizacao() {
    const viaConexao = () => getJSON('/api/geo').then(g => {
        if (!g || g.country !== 'BR' || !g.city) return;
        const alvo = norm(g.city), achados = LISTA.filter(m => m.uf === g.uf && (m.chave === alvo || m.alt === alvo));
        if (NOMES_UF[g.uf]) definirUFVisitante(g.uf);
        if (achados.length === 1) sugerirLocal(achados[0].cod, 'conexao');
        else if (NOMES_UF[g.uf] && !ATUAL && ESCOPO === 'BR') definirEscopo(g.uf, 'muni');   // cidade não identificada: ao menos abre no estado
    }).catch(() => { /* fora da Vercel não há estimativa: tudo certo */ });
    try {
        if (navigator.permissions && navigator.geolocation) {
            navigator.permissions.query({name: 'geolocation'}).then(r => { if (r.state === 'granted') localizarGPS(true); else viaConexao(); }).catch(viaConexao);
        } else viaConexao();
    } catch (e) { viaConexao(); }
}

function localizarGPS(silencioso) {
    const msg = t => { if (!silencioso) $('localMsg').textContent = t; };
    if (!navigator.geolocation) { msg('Seu navegador não informa a localização. Busque pelo nome.'); return; }
    msg('Localizando…');
    navigator.geolocation.getCurrentPosition(pos => {
        carregarMalha().then(() => {
            const cod = municipioNaCoordenada(pos.coords.longitude, pos.coords.latitude);
            if (cod && POR_COD[cod]) { $('localMsg').textContent = ''; sugerirLocal(cod, 'gps'); }
            else msg('Não encontramos um município brasileiro nesse ponto. Busque pelo nome.');
        }).catch(() => msg('O mapa não pôde ser carregado agora. Busque pelo nome.'));
    }, () => msg('Não foi possível obter a localização. Busque pelo nome.'), {timeout: 10000, maximumAge: silencioso ? 600000 : 0});   // clique do usuário pede a posição atual
}

let CAIXAS = null;
function municipioNaCoordenada(lon, lat) {
    if (!CAIXAS) CAIXAS = GEO.muni.features.map(f => {                       // caixa envolvente de cada município, calculada uma vez
        let x0 = 181, x1 = -181, y0 = 91, y1 = -91;
        const varre = c => { if (typeof c[0] === 'number') { if (c[0] < x0) x0 = c[0]; if (c[0] > x1) x1 = c[0]; if (c[1] < y0) y0 = c[1]; if (c[1] > y1) y1 = c[1]; } else c.forEach(varre); };
        varre(f.geometry.coordinates);
        return [x0, y0, x1, y1];
    });
    const feats = GEO.muni.features;
    for (let i = 0; i < feats.length; i++) {
        const b = CAIXAS[i];
        if (lon < b[0] || lon > b[2] || lat < b[1] || lat > b[3]) continue;
        if (d3.geoContains(feats[i], [lon, lat])) return feats[i].properties.cod;
    }
    return null;
}

function sugerirLocal(cod, origem) {
    if (ATUAL || (LOCAL && LOCAL.origem === 'gps' && origem !== 'gps')) return;      // quem já escolheu um município, ou já tem posição precisa, não é atropelado
    const m = POR_COD[cod];
    definirUFVisitante(m.uf);
    const anterior = LOCAL && LOCAL.rotulo;                                        // a posição precisa do GPS substitui a estimativa pela conexão
    LOCAL = {cod, origem};
    MAPA_DESTAQUE = cod;
    if (ESCOPO !== m.uf) definirEscopo(m.uf, 'muni');
    if (MAPA) MAPA.destacar(cod);
    track('local_sugerido', {origem, municipio: m.nome, uf: m.uf});
    LOCAL.rotulo = m.nome;                                                         // o campo de busca já abre com o município; quem mora em outro digita por cima
    const campo = $('busca');
    if (!campo.value || campo.value === anterior) campo.value = m.nome;
}

/* A aba Município nunca abre vazia: usa o município localizado; sem cidade, a capital do estado estimado. */
const CAPITAIS = {AC:'1200401',AL:'2704302',AM:'1302603',AP:'1600303',BA:'2927408',CE:'2304400',ES:'3205309',GO:'5208707',MA:'2111300',MG:'3106200',MS:'5002704',MT:'5103403',PA:'1501402',PB:'2507507',PE:'2611606',PI:'2211001',PR:'4106902',RJ:'3304557',RN:'2408102',RO:'1100205',RR:'1400100',RS:'4314902',SC:'4205407',SE:'2800308',SP:'3550308',TO:'1721000'};
function municipioInicial() {
    if (ATUAL) return;
    const cod = LOCAL ? LOCAL.cod : (UF_VISITANTE && CAPITAIS[UF_VISITANTE]);
    if (cod && POR_COD[cod]) abrirMunicipio(cod, {semUrl: true});
}

$('busca').addEventListener('focus', e => { if (LOCAL && e.target.value === LOCAL.rotulo) e.target.select(); });

/* ── mapa ── */
function carregarMalha() {
    if (GEO.promessa) return GEO.promessa;
    if (typeof d3 === 'undefined') return Promise.reject(new Error('d3 indisponível'));
    GEO.promessa = Promise.all([getJSON('/data/malha-municipios.json'), getJSON('/data/malha-uf.json').catch(() => null)]).then(([muni, uf]) => {
        muni.features.forEach(f => { f.properties.uf = UF_POR_PREFIXO[f.properties.cod.slice(0, 2)]; });
        GEO.muni = muni; GEO.uf = uf;
    });
    GEO.promessa.catch(() => { GEO.promessa = null; });
    return GEO.promessa;
}

function luminancia(hex) {
    const c = d3.color(hex); const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
}

/* Um mapa independente por instância: o principal (estados e municípios) e o minimapa da ficha (só a UF). */
function criarMapa(svgEl, wrapEl, tipEl, opt) {
    const W = 900;
    const feats = opt.todos ? GEO.muni.features : GEO.muni.features.filter(f => f.properties.uf === opt.uf);
    const ctl = {uf: null, nivel: null, cod: null};
    const svg = d3.select(svgEl); svg.selectAll('*').remove();
    const gMuni = svg.append('g');
    const paths = gMuni.selectAll('path').data(feats).enter().append('path')
        .attr('data-cod', d => d.properties.cod)
        .attr('fill', d => { const c = classeDe(POR_COD[d.properties.cod]); return c ? c.cor : COR_SEM_ESFERA; });

    let gUF = null, pathsUF = null, rotulos = null, escalaUF = null;
    if (opt.camadaUF && GEO.uf) {
        const m = limiteEscala();
        escalaUF = d3.scaleLinear().domain([-m, 0, m]).range([COR_NEG, COR_MEIO, COR_POS]).interpolate(d3.interpolateRgb).clamp(true);
        const corUF = uf => AGG[uf] != null ? escalaUF(AGG[uf]) : COR_SEM_ESFERA;
        gUF = svg.append('g');
        pathsUF = gUF.selectAll('path').data(GEO.uf.features).enter().append('path').attr('class', 'uf')
            .attr('data-uf', d => d.properties.uf).attr('fill', d => corUF(d.properties.uf));
        rotulos = gUF.selectAll('text').data(GEO.uf.features).enter().append('text').attr('class', 'uf-rotulo')
            .text(d => d.properties.uf)
            .attr('fill', d => luminancia(corUF(d.properties.uf)) > 0.32 ? '#1f2a55' : '#fff');
    }

    ctl.definir = (uf, nivel) => {
        const nv = uf === 'BR' ? (gUF ? nivel : 'muni') : 'muni';
        ctl.uf = uf; ctl.nivel = nv;
        const visivel = d => uf === 'BR' || d.properties.uf === uf;
        const H = Math.round(W * (nv === 'uf' || uf === 'BR' ? 0.92 : 0.8));
        const alvo = nv === 'uf' ? GEO.uf.features : feats.filter(visivel);
        const proj = d3.geoMercator().fitSize([W, H], {type: 'FeatureCollection', features: alvo});
        const gen = d3.geoPath().projection(proj);
        svg.attr('viewBox', '0 0 ' + W + ' ' + H);
        gMuni.style('display', nv === 'muni' ? null : 'none');
        if (gUF) gUF.style('display', nv === 'uf' ? null : 'none');
        if (nv === 'muni') paths.style('display', d => visivel(d) ? null : 'none').attr('d', d => visivel(d) ? gen(d) : null);
        else {
            pathsUF.attr('d', gen);
            rotulos.attr('x', d => gen.centroid(d)[0]).attr('y', d => gen.centroid(d)[1]);
        }
        if (ctl.cod) ctl.destacar(ctl.cod);
    };
    ctl.destacar = cod => {
        ctl.cod = cod;
        paths.classed('sel', false);
        if (cod) paths.filter(d => d.properties.cod === cod).classed('sel', true).raise();
    };

    const toque = window.matchMedia && matchMedia('(pointer: coarse)').matches;
    const alvoDe = el => el && el.tagName === 'path' ? el : null;
    if (!toque) {
        svgEl.addEventListener('mousemove', e => {
            const p = alvoDe(e.target);
            if (!p) { tipEl.classList.remove('on'); return; }
            const cod = p.getAttribute('data-cod'), uf = p.getAttribute('data-uf');
            if (uf) {
                const ok = LISTA.filter(m => m.uf === uf && !m.r), perdem = ok.filter(m => m.v < 0).length;
                tipEl.innerHTML = AGG[uf] == null
                    ? `<b>${esc(NOMES_UF[uf])}</b><small>Sem esfera municipal própria: o Distrito Federal não entra na projeção municipal.</small>`
                    : `<b>${esc(NOMES_UF[uf])}</b><span class="v ${clsSinal(AGG[uf])}">${fmtPct(AGG[uf])}</span><small>receita das prefeituras somada, em 2033, contra o cenário sem a reforma</small><small>${txtPerdem({perdem, n: ok.length, total: totalUF(uf)})}</small><em>Clique para ver os municípios →</em>`;
            } else {
                const m = POR_COD[cod];
                tipEl.innerHTML = m ? tipMunicipio(m) : '<b>Sem esfera municipal própria</b><small>Este território não entra na projeção municipal.</small>';
            }
            const r = wrapEl.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
            const w = tipEl.offsetWidth, h = tipEl.offsetHeight;
            tipEl.style.left = Math.max(6, x + 16 + w > r.width ? x - w - 16 : x + 16) + 'px';
            tipEl.style.top = Math.min(Math.max(6, y - h / 2), r.height - h - 6) + 'px';
            tipEl.classList.add('on');
        });
        svgEl.addEventListener('mouseleave', () => tipEl.classList.remove('on'));
    }
    svgEl.addEventListener('click', e => {
        const p = alvoDe(e.target); if (!p) return;
        const cod = p.getAttribute('data-cod'), uf = p.getAttribute('data-uf');
        if (uf) { if (AGG[uf] != null && opt.aoClicarUF) { track('clique_mapa_uf', {uf}); opt.aoClicarUF(uf); } return; }
        if (!cod || !POR_COD[cod]) return;
        track('clique_mapa', {municipio: POR_COD[cod].nome, uf: POR_COD[cod].uf});
        opt.aoClicar(cod);
    });
    ctl.definir(opt.uf, opt.nivel || 'muni');
    return ctl;
}

/* ── ficha do município ── */
async function abrirMunicipio(cod, opt) {
    opt = opt || {};
    const base = POR_COD[cod];
    ATUAL = cod;
    mostrarVisao('municipio');
    const rotulo = base.nome + ' (' + base.uf + ')';
    $('busca').value = rotulo; $('buscaMuni').value = rotulo;
    if (!opt.semUrl) { const u = new URL(location.href); u.searchParams.set('m', cod); history.replaceState(null, '', u); }
    if (ESCOPO !== base.uf) definirEscopo(base.uf, 'muni');
    if (MAPA) MAPA.destacar(cod);
    const corpo = $('fichaCorpo');
    corpo.innerHTML = '<p class="nota" role="status">Carregando a ficha de ' + esc(base.nome) + '…</p>';
    let m;
    try { m = (await municipiosDaUF(base.uf))[cod]; } catch (e) { CACHE_UF.delete(base.uf); m = null; }
    if (ATUAL !== cod) return;                              // o usuário já escolheu outro município
    if (!m) { corpo.innerHTML = '<p class="aviso">Não foi possível carregar os dados deste município. Tente novamente em instantes.</p>'; return; }
    renderFicha(cod, base, m);
}

function municipiosDaUF(uf) {
    if (!CACHE_UF.has(uf)) CACHE_UF.set(uf, getJSON('/data/painel-municipios/' + uf + '.json').then(j => { DADOS_UF[uf] = j.municipios; return j.municipios; }));
    return CACHE_UF.get(uf);
}

function coefTilesHtml(m) {
    return `<div class="coef-grid">
        <div class="coef"><span>Participação neutra, 2025</span><b>${fmtPctPlain(m.coef_neutro_pct)}</b><small>A fatia deste ente hoje, sem a reforma: o ponto de partida da comparação.</small></div>
        <div class="coef"><span>Coeficiente histórico (φ<sup>CPT</sup>)</span><b>${fmtPctPlain(m.coef_cpt_pct)}</b><small>Média de 8 anos (2019–2026, com 2026 pelo RREO até agosto) de ISS e cota-parte do ICMS do próprio ente. É o critério que ainda pesa mais até 2033. <a href="#" data-abrir="detHist">Ver a receita usada →</a></small></div>
        <div class="coef"><span>Coeficiente de destino (φ<sup>dest</sup>)</span><b>${fmtPctPlain(m.coef_pleno_pct)}</b><small>Baseado em consumo (renda × POF) e compras públicas. Pesa cerca de 10% em 2033; por inteiro, só em 2078.</small></div>
    </div>`;
}

function seguroCardHtml(repasse, posByYear) {
    const v2033 = (repasse && repasse['2033']) || 0;
    const recebeAlgumAno = ANOS.some(a => ((repasse && repasse[a]) || 0) > 1);
    if (!recebeAlgumAno) {
        return `<div class="seguro-card"><div class="seguro-label">Seguro-Receita (ADCT art. 132)</div><div class="seguro-value muted">Não recebe</div>
            <div class="seguro-note">Em 2029–2033, a receita deste ente pelo critério de destino fica acima do nível de nivelamento em todos os anos do período; não há repasse.</div></div>`;
    }
    if (v2033 <= 1) {
        return `<div class="seguro-card recebe"><div class="seguro-label">Seguro-Receita (ADCT art. 132)</div><div class="seguro-value muted">Não recebe em 2033</div>
            <div class="seguro-note">Recebeu repasse em anos anteriores da transição, mas deixa de receber a partir de 2033: a receita própria pelo critério de destino alcançou o nível de nivelamento daquele ano.</div></div>`;
    }
    const total2033 = posByYear && posByYear['2033'];
    const share = total2033 ? v2033 / total2033 * 100 : null;
    const anos = ANOS.filter(a => (repasse[a] || 0) > 1).map(a => a + ': ' + fmtMoney(repasse[a])).join(' · ');
    return `<div class="seguro-card recebe"><div class="seguro-label">Seguro-Receita (ADCT art. 132)</div><div class="seguro-value">${fmtMoney(v2033)}</div>
        <div class="seguro-note">Repasse bruto em 2033${share != null ? ' (' + share.toLocaleString('pt-BR', {maximumFractionDigits: 1}) + '% da receita projetada do município naquele ano)' : ''}. Série: ${anos}. Veja a memória de cálculo para o nível de nivelamento de cada ano.</div></div>`;
}

/* Anos preenchidos fora da DCA (RREO anual ou estimativa a partir do ano anterior): uma frase que diz de onde veio cada componente. */
function origemAnosTxt(historico) {
    const como = {rreo: 'pelo RREO do ano', estimativa_serie: 'por estimativa pela série do município (anos vizinhos, com o crescimento do estado)'};
    const frases = [];
    ANOS_HIST.forEach(a => {
        const o = historico && historico[a] && historico[a].origem; if (!o) return;
        const porFonte = {};
        [['ISS', o.iss, o.descartado && o.descartado.iss], ['cota-parte', o.cota, o.descartado && o.descartado.cota]].forEach(([nome, f, desc]) => {
            if (f && f !== 'dca') (porFonte[f] = porFonte[f] || []).push(nome + (desc ? '*' : ''));
        });
        const partes = Object.keys(porFonte).map(f => `${porFonte[f].join(' e ')} ${como[f]}`);
        if (partes.length) frases.push(`${a}: ${partes.join('; ')}`);
    });
    if (!frases.length) return '';
    const algumDesc = ANOS_HIST.some(a => historico[a] && historico[a].origem && historico[a].origem.descartado && (historico[a].origem.descartado.iss || historico[a].origem.descartado.cota));
    return ' Anos preenchidos fora da DCA do município, que não traz o dado: ' + frases.join('. ') + '.' + (algumDesc ? ' * O valor da fonte oficial destoava da série do próprio município e foi descartado.' : '');
}

/* Selo do ano preenchido fora da DCA do município. */
function seloAno(h) {
    const o = h && h.origem; if (!o) return '';
    const fontes = [o.iss, o.cota].filter(x => x && x !== 'dca');
    return fontes.length ? (fontes.every(x => x === 'rreo') ? ' (RREO)' : ' (est.)') + (o.descartado && (o.descartado.iss || o.descartado.cota) ? '*' : '') : '';
}

function historicoTableHtml(historico, est26) {
    // Mesma conta da lei (LC 227, art. 115, §2º), linha a linha: valor declarado, fator de ajuste do ano e valor em R$ de 2025; depois a média e a divisão pelo total nacional.
    // Sem o fator (base antiga), cai para a tabela só em R$ de 2025.
    const fat = REF_NAC && REF_NAC.fatores_ajuste;
    const todos = ANOS_HIST.map(a => historico && historico[a]).concat([est26]).filter(Boolean);
    const maior = Math.max(0, ...todos.map(h => h.total_reais_2025 || 0));
    const mi = maior >= 5e6, div = mi ? 1e6 : 1e3, dec = mi ? 1 : 0;
    const f = v => (v / div).toLocaleString('pt-BR', {minimumFractionDigits: dec, maximumFractionDigits: dec});
    const bi = v => (v / 1e9).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    let soma = {iss: 0, cota: 0}, faltou = false;
    const linha = (rot, h, a, cls) => {
        if (h) { soma.iss += h.iss_reais_2025 || 0; soma.cota += h.cota_parte_reais_2025 || 0; } else faltou = true;
        const fa = fat && a != null ? fat[a] : null;
        const nom = k => h ? f(fa ? h[k] / fa : h[k]) : '—';        // valor declarado: o ajustado dividido pelo fator
        const c = k => `<td class="num">${h ? f(h[k]) : '—'}</td>`;
        if (!fat) return `<tr${cls ? ' class="' + cls + '"' : ''}><td>${rot}</td>${c('iss_reais_2025')}${c('cota_parte_reais_2025')}${c('total_reais_2025')}</tr>`;
        return `<tr${cls ? ' class="' + cls + '"' : ''}><td>${rot}</td><td class="num">${nom('iss_reais_2025')}</td><td class="num">${nom('cota_parte_reais_2025')}</td><td class="num">${nom('total_reais_2025')}</td>`
            + `<td class="num">${a == null ? 'n.a.' : (fa ? fa.toLocaleString('pt-BR', {minimumFractionDigits: 3, maximumFractionDigits: 3}) : '—')}</td>${c('total_reais_2025')}</tr>`;
    };
    const rows = ANOS_HIST.map(a => linha(a + seloAno(historico && historico[a]), historico ? historico[a] : null, a)).join('')
        + linha(est26 && est26.origem === 'rreo' ? '2026 (RREO)' : '2026 (est.)', est26, null, 'est');
    const n = ANOS_HIST.length + 1, media = (soma.iss + soma.cota) / n;
    const cab = fat ? '<th>Ano</th><th class="num">ISS</th><th class="num">Cota-parte do ICMS</th><th class="num">Referência</th><th class="num">Fator</th><th class="num">R$ de 2025</th>'
                    : '<th>Ano</th><th class="num">ISS</th><th class="num">Cota-parte do ICMS</th><th class="num">Total</th>';
    const rodape = fat
        ? `<tr class="media"><td colspan="5">Média da referência ajustada, 2019–2026</td><td class="num">${f(media)}</td></tr>`
          + `<tr class="rodape"><td colspan="5">Arrecadação nacional de referência em 2025 (R$ bilhões)</td><td class="num">${bi(REF_NAC.total_br_2025)}</td></tr>`
          + `<tr class="media"><td colspan="5">Coeficiente histórico (φ<sup>CPT</sup>)</td><td class="num">${fmtPctPlain(media / REF_NAC.total_br_2025 * 100, 5)}</td></tr>`
        : `<tr class="media"><td>Média 2019–2026</td><td class="num">${f(soma.iss / n)}</td><td class="num">${f(soma.cota / n)}</td><td class="num">${f(media)}</td></tr>`;
    return `<div class="table-wrap"><table class="dados tab-hist"><thead><tr>${cab}</tr></thead><tbody>${rows}${rodape}</tbody></table></div>
        <p class="nota">Valores em R$ ${mi ? 'milhões' : 'mil'}; a última coluna está em reais de 2025.${fat ? ' O fator de ajuste corrige cada ano pela variação nominal da arrecadação total de ICMS e ISS do país (LC 227, art. 115, §2º), e a referência do ano é o valor declarado vezes esse fator.' : ''}${faltou ? ' Ano sem dado entra como zero na média.' : ''}${origemAnosTxt(historico)}${est26 ? (est26.origem === 'rreo' ? ' 2026, já em reais de 2025: ISS observado no RREO de setembro de 2025 a agosto de 2026; cota-parte de 2025 ajustada pelo crescimento de janeiro a agosto, também do RREO.' : ' 2026, já em reais de 2025: este município não publica o Anexo 3 do RREO; mantém a posição relativa de 2025 no estado.') : ''}</p>`;
}

function renderFicha(cod, base, m) {
    graficos.forEach(g => g.destroy()); graficos = [];
    if (GSENS) { GSENS.destroy(); GSENS = null; }
    const ok = LISTA.filter(x => !x.r).sort((a, b) => b.v - a.v);
    const posBR = ok.findIndex(x => x.cod === cod) + 1;
    const naUF = ok.filter(x => x.uf === base.uf);
    const posUF = naUF.findIndex(x => x.cod === cod) + 1;

    const pos33 = m.pos_por_ano['2033'], cf33 = m.contrafactual_por_ano['2033'];
    const dif33 = pos33 - cf33, v33 = m.variacao_por_ano['2033'];
    const sinal = clsSinal(v33);

    let aviso = '';
    if (m.neutro_suspeito) aviso = '<strong>Dado a conferir.</strong> O valor declarado ao SICONFI para 2025 diverge de forma incompatível da série histórica deste município, o que sugere falha de preenchimento na fonte. Os números são exibidos com cautela e não entram nos rankings.';
    else if (m.neutro_aproximado) aviso = '<strong>Estimativa aproximada.</strong> Este município não tem registro individualizado de ISS e cota-parte do ICMS para 2025 no SICONFI, e a participação de 2025 foi aproximada pela média de sete anos. Leia os números como ordem de grandeza.';
    else if (m.cobertura_anos < 5) aviso = '<strong>Série curta.</strong> Há apenas ' + m.cobertura_anos + ' anos de dados históricos para este município, abaixo do mínimo recomendado de 5. Os números são menos estáveis.';

    const neutra = Math.abs(v33) <= 0.0005;
    const lado = v33 < 0 ? 'a menos' : 'a mais';
    const nomeSeg = esc(base.nome);
    const selo = neutra ? 'Receita estável' : v33 < 0 ? 'Perda estimada' : 'Ganho estimado';
    const frase = neutra
        ? `Em 2033, a receita de <b>${nomeSeg}</b> fica praticamente igual à que teria sem a reforma.`
        : `Em 2033, <b>${nomeSeg}</b> deve arrecadar <b>${fmtMoney(Math.abs(dif33))} ${lado} por ano</b> do que arrecadaria sem a reforma.`;

    const linhas = ANOS.map(a => {
        const v = m.variacao_por_ano[a], d = m.pos_por_ano[a] - m.contrafactual_por_ano[a];
        return `<tr><td>${a}</td><td>${fmtMoneyFino(m.contrafactual_por_ano[a])}</td><td>${fmtMoneyFino(m.pos_por_ano[a])}</td><td class="${clsSinal(v)}">${fmtMoney(d)}</td><td class="${clsSinal(v)}">${fmtPct(v)}</td></tr>`;
    }).join('');

    const posicao = m.neutro_aproximado || m.neutro_suspeito
        ? '<p class="nota">Posição nos rankings indisponível para municípios com ressalva de dados.</p>'
        : `<div class="pos-grid">
            <div class="pos-item"><b>${fmtInt(posUF)}º</b><span>entre ${fmtInt(naUF.length)} municípios ${DE_UF[base.uf]} com base de 2025${totalUF(base.uf) > naUF.length ? ' (de ' + fmtInt(totalUF(base.uf)) + ')' : ''}</span></div>
            <div class="pos-item"><b>${fmtInt(posBR)}º</b><span>entre ${fmtInt(ok.length)} municípios do Brasil com base de 2025${LISTA.length > ok.length ? ' (de ' + fmtInt(LISTA.length) + ')' : ''}</span></div>
        </div><p class="nota">Do maior ganho (1º) à maior perda, na variação da receita em 2033.</p>`;

    $('fichaCorpo').innerHTML = `
        <div class="ficha-top">
            <div>
                <h2 id="fichaTitulo" tabindex="-1">${nomeSeg}<small>${base.uf}</small></h2>
                <p class="ficha-meta">${esc(NOMES_UF[base.uf])} · ${fmtInt(m.pop_media)} habitantes<span class="meta-fonte"> (média 2019–2026, IBGE)</span></p>
            </div>
            <div class="ficha-acoes">
                <button class="btn btn-ghost btn-sm" type="button" id="btnCopiar">Copiar link</button>
                <button class="btn btn-ghost btn-sm" type="button" id="btnImprimir">Imprimir / salvar PDF</button>
            </div>
        </div>
        ${aviso ? `<div class="aviso" role="note">${aviso}</div>` : ''}
        <div class="faixa">
            <div class="faixa-main ${sinal}">
                <div class="fm-num"><em class="selo">${selo}</em><span>Efeito da reforma na receita em 2033</span><b>${fmtPct(v33)}</b></div>
                <div class="fm-txt"><p class="frase">${frase}</p>
                <small>Compara os dois cenários do mesmo ano. <a href="#" data-tab="metodologia" data-depois="met-5">Como ler →</a></small></div>
            </div>
            <div class="kpi"><span>Receita em 2025</span><b>${fmtMoneyFino(m.pre_2025)}</b></div>
            <div class="kpi"><span>2033 sem a reforma</span><b>${fmtMoneyFino(cf33)}</b></div>
            <div class="kpi destaque"><span>2033 com a reforma</span><b>${fmtMoneyFino(pos33)}</b></div>
        </div>
        <div class="panel accent"><h3>Para onde vai a arrecadação</h3><p class="panel-sub">Receita realizada até 2025 e projetada de 2029 a 2033, com e sem a reforma, em R$ de 2025.</p>
            <div class="canvas-box canvas-serie"><canvas id="gSerie" role="img" aria-label="Gráfico de linhas com a receita histórica de 2019 a 2025 e a projeção de 2029 a 2033 com e sem a reforma. Os mesmos valores estão na tabela ano a ano, em Detalhes do cálculo."></canvas></div>
</div>
        <div class="panel accent">
            <div class="panel-head"><div><h3>De onde vem a receita</h3><p class="panel-sub">Quanto ainda vem do ISS e da cota-parte do ICMS e quanto já vem do IBS, de 2029 a 2033.</p></div>
                <div class="comp-controles">
                    <div class="toggle" id="compModo" role="group" aria-label="Unidade"><button type="button" data-modo="pct" class="active">%</button><button type="button" data-modo="rs">R$</button></div>
                    <div class="toggle" id="compViz" role="group" aria-label="Forma"><button type="button" data-viz="grafico" class="active">Gráfico</button><button type="button" data-viz="tabela">Tabela</button></div>
                </div></div>
            <div class="canvas-box" id="compBox"><canvas id="gComp" role="img" aria-label="Gráfico de barras empilhadas com a composição da receita projetada de 2029 a 2033: ISS e cota-parte do ICMS residuais, IBS pelo critério histórico, IBS por destino e Seguro-Receita. Os mesmos valores estão na aba Tabela."></canvas></div>
            <div class="table-wrap" id="compTabela" hidden></div>
            <p class="nota nota-grafico">* Inclui a cota-parte dos municípios: na parte histórica, a cota-parte do ICMS que o município já recebia; no destino, os 25% do IBS do estado repassados às prefeituras. <a href="#" data-tab="metodologia" data-depois="met-3">Entenda →</a></p>
        </div>
        <div class="panel accent" id="painelSens" hidden>
            <h3>Quanto este resultado depende das hipóteses?</h3>
            <p class="panel-sub">O modelo faz duas escolhas: qual ano define a fatia do município no cenário sem reforma e quanto de IBS ele recebe pelo consumo no destino. Aqui as duas variam.</p>
            <p class="leitura" id="sensTexto"></p>
            <div class="canvas-box canvas-sens"><canvas id="gSens" role="img" aria-label="Gráfico de linhas com a variação projetada da receita de 2029 a 2033 em diferentes anos-base, com a faixa entre o menor e o maior resultado."></canvas></div>
            <details class="sens-ajuste">
                <summary>Ajustar as hipóteses e ver como ler</summary>
                <div class="sens-ctl"><span class="sens-lab" id="sensChipsLab">O cenário sem reforma mantém a fatia do município em:</span>
                    <div class="sens-chips" id="sensChips" role="group" aria-labelledby="sensChipsLab"></div>
                    <p class="nota">2025 é a referência central e fica sempre ligada; 2026 é estimado.</p></div>
                <div class="sens-ctl"><label for="sensErro">Margem de erro do consumo no destino</label>
                    <div class="sens-slider"><input type="range" id="sensErro" min="0" max="30" step="0.5" value="10"><span id="sensErroValor"></span><button type="button" class="btn btn-ghost btn-sm" id="sensErroReset">Margem medida</button></div></div>
                <p class="nota">Cada linha usa um ano-base com o destino no valor central; a faixa sombreada vai do menor ao maior resultado entre todos os cenários, incluindo o destino reduzido e aumentado pela margem de erro. Não é um intervalo de confiança. A margem é a medida para o estado, aplicada ao destino do município; o Seguro-Receita fica no valor central.</p>
            </details>
        </div>
        <div class="ficha-grid ficha-contexto">
            <div class="panel"><h3>Como ${nomeSeg} se compara</h3><p class="panel-sub">Posição na variação da receita em 2033.</p>${posicao}</div>
            <div class="panel"><h3>${nomeSeg} no mapa ${DE_UF[base.uf]}</h3><p class="panel-sub">Contornado; a cor mostra a variação em 2033.</p>
                <div class="map-wrapper" id="miniWrap"><svg id="miniSvg" role="img" aria-label="Mapa dos municípios ${DE_UF[base.uf]} com ${nomeSeg} contornado."></svg><div class="map-tip" id="miniTip" role="tooltip"></div></div></div>
        </div>
        <div class="detalhes">
            <h3 class="detalhes-tit">Detalhes do cálculo</h3>
            <details><summary>Ano a ano, 2029–2033</summary>
                <div class="table-wrap"><table class="dados"><thead><tr><th>Ano</th><th>Sem a reforma</th><th>Com a reforma</th><th>Diferença</th><th>Variação</th></tr></thead><tbody>${linhas}</tbody></table></div></details>
            <details id="detCoef"><summary>Coeficientes de participação</summary>
                <p class="panel-sub">Os critérios que, ponderados pelo cronograma do ADCT, definem a fatia deste município no IBS.</p>${coefTilesHtml(m)}</details>
            <details><summary>Seguro-Receita</summary>
                <p class="panel-sub">Repasse compensatório para entes cuja receita pelo critério de destino fica abaixo do nível de nivelamento.</p>${seguroCardHtml(m.repasse_seguro_receita_por_ano, m.pos_por_ano)}</details>
            <details id="detHist"><summary>Receita histórica: ISS e cota-parte do ICMS</summary>
                <p class="panel-sub">São as receitas do próprio município usadas no cálculo: o ISS que ele arrecada e a cota-parte do ICMS que recebe do estado (SICONFI, DCA). A média dos oito anos, com 2026 pelo RREO até agosto, é a base do coeficiente histórico. <a href="#" data-abrir="detCoef">Ver o coeficiente histórico →</a></p>${historicoTableHtml(m.historico_por_ano, m.estimativa_2026)}</details>
            <button type="button" class="memo-link" id="btnMemoria">Ver a memória de cálculo deste município →</button>
        </div>
        <p class="print-credito">Municípios na Reforma, iniciativa da Vertex Advisory · municipiosnareforma.com.br${CONFIG.email ? ' · ' + CONFIG.email : ''}</p>`;

    $('btnMemoria').addEventListener('click', () => { track('abrir_memoria', {municipio: base.nome}); abrirMemoria(cod); });
    $('btnCopiar').addEventListener('click', e => {
        const url = location.origin + location.pathname + '?m=' + cod;
        (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(() => { e.target.textContent = 'Link copiado'; }, () => { prompt('Copie o link:', url); });
        track('copiar_link', {municipio: base.nome});
    });
    $('btnImprimir').addEventListener('click', () => { track('imprimir_ficha', {municipio: base.nome}); window.print(); });
    desenharGraficos(m);
    iniciarSens(cod, base, m);
    carregarMalha().then(() => {
        if (ATUAL !== cod || !$('miniSvg')) return;
        MINI = criarMapa($('miniSvg'), $('miniWrap'), $('miniTip'), {camadaUF: false, todos: false, uf: base.uf, nivel: 'muni', aoClicar: c => abrirMunicipio(c)});
        MINI.destacar(cod);
    }).catch(() => { const w = $('miniWrap'); if (w) w.innerHTML = '<p class="nota">O mapa não pôde ser carregado agora.</p>'; });
    $('fichaTitulo').focus({preventScroll: true});
}

/* ── sensibilidade: o mesmo teste do painel dos estados, agora por município ──
   Com a reforma = residual×ref + histórico×φCPT×(1−ca) + destino×φdest×(1±erro) + repasse×(1−ca);
   sem a reforma = ref × bolo projetado, em que ref é a fatia do município no ano-base escolhido. Com ref de 2025 e destino
   central, reproduz a variação publicada. A fatia de cada ano é a de 2025 (coef_neutro) escalada pela receita real do
   município naquele ano em relação a 2025 (série deflacionada da ficha; 2026 é a estimativa). A margem de erro do destino
   é a medida para a UF (sensibilidade-uf.json). */
let GSENS = null, SENS_UF = null, SENS_P = null;
const SENSM = {refs: ['2019', '2025', '2026'], erro: null};
const SENS_ESTILO = {'2019': ['#9c3d3d', [2, 4]], '2020': ['#8a6d3b', [10, 3, 2, 3]], '2021': ['#6b4c9a', [6, 3]], '2022': ['#00799a', [3, 3]],
    '2023': ['#b5651d', [12, 4]], '2024': ['#7a7a7a', [1, 3]], '2026': ['#2e7d32', [8, 4]]};
const fmtV = v => {
    if (v == null || !isFinite(v)) return '—';
    const p = Math.round(v * 10000) / 100;
    return (p > 0 ? '+' : p < 0 ? '−' : '') + Math.abs(p).toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + '%';
};
const fmtErro = e => (e * 100).toLocaleString('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1}) + '%';

function sensRefs(m) {
    const h = m.historico_por_ano || {}, h25 = h['2025'] && h['2025'].total_reais_2025, out = {};
    if (!h25) return out;
    const c0 = m.coef_neutro_pct / 100;
    ANOS_HIST.forEach(a => { if (h[a] && h[a].total_reais_2025 > 0) out[a] = c0 * h[a].total_reais_2025 / h25; });
    if (m.estimativa_2026 && m.estimativa_2026.total_reais_2025 > 0) out['2026'] = c0 * m.estimativa_2026.total_reais_2025 / h25;
    out['2025'] = c0;
    return out;
}
function sensVar(P, refKey, mult, ano) {
    const s = P.nac[ano], ref = P.ref[refKey];
    const pos = s.icms_iss_residual * ref + s.ibs_historico * P.cpt * (1 - s.ca) + s.ibs_destino_liquido * P.pleno * (1 + mult) + (P.rep[ano] || 0) * (1 - s.ca);
    return pos / (ref * s.bolo_projetado) - 1;
}
function sensCalc(P, refs, erro) {
    const linhas = {};
    refs.forEach(r => { linhas[r] = ANOS.map(a => ({lo: sensVar(P, r, -erro, a), c: sensVar(P, r, 0, a), hi: sensVar(P, r, erro, a)})); });
    const banda = ANOS.map((a, i) => { const vs = refs.flatMap(r => [linhas[r][i].lo, linhas[r][i].c, linhas[r][i].hi]); return {min: Math.min(...vs), max: Math.max(...vs)}; });
    return {linhas, banda};
}
/* Quanto o destino teria de diferir do estimado para a variação central (ref. 2025) ser zero; negativo = menor. */
function sensVirada(P, ano) {
    const s = P.nac[ano], ref = P.ref['2025'];
    const alvo = ref * s.bolo_projetado - s.icms_iss_residual * ref - s.ibs_historico * P.cpt * (1 - s.ca) - (P.rep[ano] || 0) * (1 - s.ca);
    const dest = s.ibs_destino_liquido * P.pleno;
    return dest > 0 ? alvo / dest - 1 : null;
}

function iniciarSens(cod, base, m) {
    const caixa = $('painelSens');
    if (!CONFIG.sensibilidade || !caixa || !NAC || !NAC.projecao || typeof Chart === 'undefined') return;
    const ref = sensRefs(m);
    if (!ref['2025'] || !(m.coef_neutro_pct > 0)) return;
    SENS_UF = SENS_UF || getJSON('/data/sensibilidade-uf.json').catch(() => null);
    SENS_UF.then(d => {
        if (ATUAL !== cod || !$('painelSens')) return;
        const u = d && d.por_uf && d.por_uf[base.uf];
        if (!u) return;
        const nac = {}; NAC.projecao.forEach(r => { nac[String(r.ano)] = r; });
        if (!ANOS.every(a => nac[a])) return;
        SENS_P = {nac, ref, cpt: m.coef_cpt_pct / 100, pleno: m.coef_pleno_pct / 100, rep: m.repasse_seguro_receita_por_ano || {}, medido: u.incerteza_rel, nome: base.nome};
        SENSM.erro = null;
        SENSM.refs = ['2019', '2025', '2026'].filter(r => ref[r]);
        $('sensChips').innerHTML = Object.keys(ref).sort().map(r =>
            `<button type="button" class="sens-chip" data-ref="${r}" aria-pressed="false">${r}${r === '2026' ? ' (est.)' : ''}</button>`).join('');
        document.querySelectorAll('#sensChips .sens-chip').forEach(b => b.addEventListener('click', () => {
            const r = b.dataset.ref; if (r === '2025') return;
            SENSM.refs = SENSM.refs.includes(r) ? SENSM.refs.filter(x => x !== r) : SENSM.refs.concat(r);
            track('sens_ano_base', {municipio: base.nome, ano: r}); desenharSens();
        }));
        $('sensErro').addEventListener('input', e => { SENSM.erro = Number(e.target.value) / 100; desenharSens(); });
        $('sensErroReset').addEventListener('click', () => { SENSM.erro = null; desenharSens(); });
        $('painelSens').hidden = false;
        desenharSens();
    });
}

function desenharSens() {
    const P = SENS_P; if (!P || !$('gSens')) return;
    if (!SENSM.refs.includes('2025')) SENSM.refs = SENSM.refs.concat('2025');
    const refs = SENSM.refs.slice().sort(), erro = SENSM.erro == null ? P.medido : SENSM.erro;
    const calc = sensCalc(P, refs, erro), i = ANOS.length - 1, a = ANOS[i];
    const c = calc.linhas['2025'][i].c, b = calc.banda[i], eps = 0.00005;
    document.querySelectorAll('#sensChips .sens-chip').forEach(x => x.setAttribute('aria-pressed', refs.includes(x.dataset.ref) ? 'true' : 'false'));
    $('sensErro').value = String(Math.round(erro * 1000) / 10);
    $('sensErroValor').textContent = '±' + fmtErro(erro);
    $('sensErroReset').disabled = SENSM.erro == null;

    const nome = esc(P.nome), cruza = b.min <= eps && b.max >= -eps;
    const v = sensVirada(P, a);
    let frase = b.min > eps ? `Em ${a}, mesmo com outros anos-base e outro consumo no destino, <b>${nome} segue com ganho</b>: de ${fmtV(b.min)} a ${fmtV(b.max)}.`
        : b.max < -eps ? `Em ${a}, mesmo com outros anos-base e outro consumo no destino, <b>${nome} segue com perda</b>: de ${fmtV(b.min)} a ${fmtV(b.max)}.`
        : `Em ${a}, o resultado de ${nome} vai de <b>${fmtV(b.min)} a ${fmtV(b.max)}</b> conforme as hipóteses: <b>o sinal depende delas</b>.`;
    frase += ` Variação central: ${fmtV(c)}.`;
    if (v != null && v > -1) {
        const q = Math.abs(v) * 100;
        frase += ` Para zerar a variação, o consumo no destino teria de ser ${q > 100 ? 'maior que o dobro do' : q.toLocaleString('pt-BR', {maximumFractionDigits: 0}) + '% ' + (v > 0 ? 'maior' : 'menor') + ' que o'} estimado (margem medida: ±${fmtErro(P.medido)}).`;
    }
    $('sensTexto').innerHTML = frase;

    const pc = x => Math.round(x * 10000) / 100;
    const linha = {borderWidth: 2, tension: 0.1, pointRadius: 0, pointHoverRadius: 5, pointBorderWidth: 2, pointBorderColor: '#fff', hitRadius: 14};
    const ds = [
        {label: 'Faixa entre os cenários', data: calc.banda.map(x => pc(x.max)), borderWidth: 0, pointRadius: 0, pointHoverRadius: 0, hitRadius: 0, backgroundColor: 'rgba(31,42,85,.14)', fill: '+1', tension: 0.1},
        {label: 'min', data: calc.banda.map(x => pc(x.min)), borderWidth: 0, pointRadius: 0, pointHoverRadius: 0, hitRadius: 0, fill: false, tension: 0.1}
    ];
    refs.filter(r => r !== '2025').forEach(r => {
        const e = SENS_ESTILO[r] || ['#7a7a7a', [3, 3]];
        ds.push(Object.assign({label: 'Base ' + r + (r === '2026' ? ' (est.)' : ''), data: calc.linhas[r].map(x => pc(x.c)), borderColor: e[0], backgroundColor: e[0], borderDash: e[1]}, linha, {borderWidth: 1.8}));
    });
    ds.push(Object.assign({label: 'Base 2025 (a do painel)', data: calc.linhas['2025'].map(x => pc(x.c)), borderColor: '#1f2a55', backgroundColor: '#1f2a55', pointBackgroundColor: '#1f2a55', pointRadius: 4}, linha, {pointRadius: 4, borderWidth: 3}));

    const estreito = $('gSens').parentElement.clientWidth < 520;
    if (GSENS) GSENS.destroy();
    GSENS = new Chart($('gSens'), {
        type: 'line', data: {labels: ANOS, datasets: ds},
        options: {responsive: true, maintainAspectRatio: false, interaction: {mode: 'index', intersect: false},
            plugins: {legend: {position: 'bottom', labels: {boxWidth: 26, boxHeight: 2, padding: estreito ? 10 : 16, color: '#141414', font: {size: 11}, filter: it => it.text !== 'min'}},
                tooltip: {filter: it => it.dataset.label !== 'min' && it.dataset.label !== 'Faixa entre os cenários', callbacks: {label: c => ' ' + c.dataset.label + ': ' + fmtV(c.parsed.y / 100)}}},
            scales: {y: {grid: {color: ctx => ctx.tick && ctx.tick.value === 0 ? '#8a98a3' : '#e9edf0', drawTicks: false}, border: {display: false}, grace: '10%',
                    ticks: {callback: x => (x > 0 ? '+' : x < 0 ? '−' : '') + Math.abs(x).toLocaleString('pt-BR', {maximumFractionDigits: 1}) + (x === 0 ? '' : '%'), color: '#6b6b6b', font: {size: 11}, padding: 8}},
                x: {grid: {display: false}, border: {color: '#c8d0d6'}, ticks: {font: {size: 11}, color: '#6b6b6b', padding: 6}}}}
    });
}

const COMP_ROTULOS = [['origem', 'ISS e cota-parte do ICMS residuais', '#858384'], ['cpt', 'IBS pelo critério histórico*', '#1f2a55'], ['destino', 'IBS por destino*', '#cfad56'], ['seguro', 'Seguro-Receita', '#2f7f7a']];

function desenharGraficos(m) {
    const tabelaComp = pct => {
        const cab = ANOS.map(a => `<th>${a}</th>`).join('');
        const corpo = COMP_ROTULOS.map(([k, rot]) => `<tr><td>${rot}</td>${ANOS.map(a => {
            const r = m.componentes_por_ano[a] || {}, tot = (r.origem || 0) + (r.cpt || 0) + (r.destino || 0) + (r.seguro || 0), v = r[k] || 0;
            return `<td>${pct ? (tot ? (v / tot * 100).toLocaleString('pt-BR', {maximumFractionDigits: 1}) + '%' : '—') : fmtMoney(v)}</td>`;
        }).join('')}</tr>`).join('');
        return `<table class="dados"><thead><tr><th>Categoria</th>${cab}</tr></thead><tbody>${corpo}</tbody></table>`;
    };
    let modo = 'pct';
    $('compTabela').innerHTML = tabelaComp(true);
    document.querySelectorAll('#compViz button').forEach(b => b.addEventListener('click', () => {
        const tab = b.dataset.viz === 'tabela';
        document.querySelectorAll('#compViz button').forEach(x => x.classList.toggle('active', x === b));
        $('compBox').hidden = tab; $('compTabela').hidden = !tab;
    }));

    if (typeof Chart === 'undefined') {
        document.querySelectorAll('.canvas-box').forEach(b => { b.innerHTML = '<p class="nota">O gráfico não pôde ser carregado. Os valores estão nas tabelas.</p>'; });
        document.querySelectorAll('#compViz button')[1] && document.querySelectorAll('#compViz button')[1].click();
        return;
    }
    const mi = v => v == null ? null : v / 1e6;
    const eixoR$ = {ticks: {callback: v => 'R$ ' + v.toLocaleString('pt-BR') + ' mi', color: '#55576a'}, grid: {color: '#ecebe5'}, beginAtZero: true};
    const tip = {callbacks: {label: c => c.parsed.y == null ? null : ' ' + c.dataset.label + ': ' + fmtMoney(c.parsed.y * 1e6)}};
    Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
    // Mesma solução do painel original: o eixo vai de 2019 a 2025 e segue direto para 2029–2033, sem espaço para 2026–2028
    // (o modelo não projeta esses anos), e os dois cenários partem do valor de 2025, de onde o contrafactual é construído.
    const rotulos = ANOS_HIST.concat(ANOS);
    const estreito = $('gSerie').parentElement.clientWidth < 520;      // no celular, todos os anos, na diagonal e menores (como no painel dos estados)
    const hist = rotulos.map(a => ANOS_HIST.includes(a) && m.historico_por_ano[a] ? mi(m.historico_por_ano[a].total_reais_2025) : null);
    const cenario = serie => rotulos.map(a => a === '2025' ? mi(m.pre_2025) : (ANOS.includes(a) && serie[a] != null ? mi(serie[a]) : null));
    // Desenho do painel dos estados: linha fina, ponto de 4 px com anel de 2 px na cor da superfície (continua legível onde as séries
    // se tocam), área de acerto folgada para o toque, grade só na horizontal e sem eixo vertical.
    const linha = {borderWidth: 2, spanGaps: false, tension: 0.1, pointRadius: 4, pointHoverRadius: 6, pointBorderWidth: 2, pointBorderColor: '#fff', hitRadius: 14};
    graficos.push(new Chart($('gSerie'), {
        type: 'line',
        data: {labels: rotulos, datasets: [
            Object.assign({label: 'Realizado (2019–2025)', data: hist, borderColor: '#1f2a55', backgroundColor: '#1f2a55', pointBackgroundColor: '#1f2a55'}, linha),
            Object.assign({label: 'Projeção com a reforma', data: cenario(m.pos_por_ano), borderColor: '#b8922f', backgroundColor: 'rgba(207,173,86,.18)', pointBackgroundColor: '#b8922f', fill: '+1'}, linha),
            Object.assign({label: 'Cenário sem a reforma', data: cenario(m.contrafactual_por_ano), borderColor: '#6b6b6b', backgroundColor: '#6b6b6b', pointBackgroundColor: '#6b6b6b', borderDash: [5, 4], fill: false}, linha)
        ]},
        options: {responsive: true, maintainAspectRatio: false, interaction: {mode: 'index', intersect: false},
            plugins: {legend: {position: 'bottom', labels: {usePointStyle: false, boxWidth: 26, boxHeight: 2, padding: 16, color: '#141414', font: {size: 11}}}, tooltip: tip},
            scales: {y: {grid: {color: '#e9edf0', drawTicks: false}, border: {display: false}, beginAtZero: false, grace: '8%', ticks: {callback: v => fmtMoney(v * 1e6), color: '#6b6b6b', font: {size: 11}, padding: 8}},
                x: {grid: {display: false}, border: {color: '#c8d0d6'}, ticks: {maxRotation: estreito ? 55 : 0, minRotation: estreito ? 55 : 0, autoSkip: false, font: {size: estreito ? 10 : 11}, color: '#6b6b6b', padding: 6}}}}
    }));
    const desenhaComp = () => {
        const pct = modo === 'pct';
        const tot = ANOS.map(a => { const r = m.componentes_por_ano[a]; return r.origem + r.cpt + r.destino + r.seguro; });
        const serie = k => ANOS.map((a, i) => pct ? (tot[i] ? m.componentes_por_ano[a][k] / tot[i] * 100 : 0) : mi(m.componentes_por_ano[a][k]));
        if (graficos[1]) { graficos[1].destroy(); graficos.pop(); }
        graficos.push(new Chart($('gComp'), {
            type: 'bar',
            data: {labels: ANOS, datasets: COMP_ROTULOS.map(([k, rot, cor]) => ({label: rot, data: serie(k), backgroundColor: cor}))},
            options: {responsive: true, maintainAspectRatio: false, interaction: {mode: 'index', intersect: false},
                plugins: {legend: {position: 'bottom', labels: {boxWidth: 12}},
                    tooltip: {callbacks: {label: c => ' ' + c.dataset.label + ': ' + (pct ? c.parsed.y.toLocaleString('pt-BR', {maximumFractionDigits: 1}) + '%' : fmtMoney(c.parsed.y * 1e6))}}},
                scales: {x: {stacked: true, grid: {display: false}},
                    y: pct ? {stacked: true, max: 100, ticks: {callback: v => v + '%', color: '#55576a'}, grid: {color: '#ecebe5'}} : Object.assign({stacked: true}, eixoR$)}}
        }));
    };
    desenhaComp();
    document.querySelectorAll('#compModo button').forEach(b => b.addEventListener('click', () => {
        modo = b.dataset.modo;
        document.querySelectorAll('#compModo button').forEach(x => x.classList.toggle('active', x === b));
        $('compTabela').innerHTML = tabelaComp(modo === 'pct');
        desenhaComp();
    }));
}

/* ── memória de cálculo (portada do painel) ── */
function memoriaInicial() {
    if (MEMO.cod) return;
    const cod = ATUAL || (LOCAL && LOCAL.cod) || (UF_VISITANTE && CAPITAIS[UF_VISITANTE]);
    if (cod && POR_COD[cod]) { MEMO.cod = cod; $('buscaMemo').value = rotuloMuni(cod); }
}
function abrirMemoria(cod, secao) {
    MEMO.cod = cod;
    if (secao) MEMO.secao = secao;
    $('buscaMemo').value = POR_COD[cod].nome + ' (' + POR_COD[cod].uf + ')';
    mostrarVisao('memoria');
    renderMemoria();
}

function dadosMemoria(uf) {
    if (!CACHE_MEMO.has(uf)) {
        const p = Promise.all([
            MEMO_NAC ? Promise.resolve(MEMO_NAC) : getJSON('/data/memoria-calculo/nacional.json'),
            getJSON('/data/memoria-calculo/' + uf + '.json')
        ]).then(([nac, memo]) => { MEMO_NAC = nac; window.MemoriaCalculo.definirNacional(nac); return memo; });
        p.catch(() => CACHE_MEMO.delete(uf));
        CACHE_MEMO.set(uf, p);
    }
    return CACHE_MEMO.get(uf);
}

/* ── cadastro: abre a memória de cálculo ──
   Só entra em cena quando /api/lead informa que o armazenamento está configurado na Vercel.
   Sem isso (prévia, outro servidor, variáveis ausentes) a memória fica aberta a todos, de modo
   que o cadastro nunca vira uma porta fechada por falha técnica. */
const CHAVE_CADASTRO = 'mnr-cadastro-v1', VERSAO_TERMOS = '2026-10';
let CADASTRO_ATIVO = false, CADASTRO_PULADO = false;
getJSON('/api/lead').then(r => { CADASTRO_ATIVO = !!(r && r.ativo); }).catch(() => { /* sem função: memória aberta */ });
function jaCadastrado() { try { return !!localStorage.getItem(CHAVE_CADASTRO); } catch (e) { return false; } }
function lembrarCadastro() { try { localStorage.setItem(CHAVE_CADASTRO, String(Date.now())); } catch (e) { /* sem armazenamento, pede de novo na próxima vez */ } }
const precisaCadastro = () => CADASTRO_ATIVO && !CADASTRO_PULADO && !jaCadastrado();
const EMAIL_OK = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function renderCadastro() {
    const base = MEMO.cod ? POR_COD[MEMO.cod] : null;
    $('memoConteudo').innerHTML = `<div class="panel accent cadastro">
        <h3>Cadastro gratuito para abrir a memória de cálculo</h3>
        <p class="panel-sub">A memória mostra, com os números intermediários, como cada coeficiente foi obtido, para que a conta possa ser refeita e conferida. O acesso é livre; o cadastro nos ajuda a saber quem usa o painel e a avisar quando o modelo for atualizado.</p>
        <form id="formCadastro" class="form-cad" novalidate>
            <div class="campo"><label for="cadNome">Nome completo</label><input id="cadNome" name="nome" autocomplete="name" required></div>
            <div class="campo"><label for="cadEmail">E-mail</label><input id="cadEmail" name="email" type="email" autocomplete="email" required></div>
            <div class="campo"><label for="cadCargo">Cargo ou função</label><input id="cadCargo" name="cargo" autocomplete="organization-title" required></div>
            <div class="campo"><label for="cadVinculo">Vínculo</label><select id="cadVinculo" name="vinculo"><option>Prefeitura</option><option>Câmara municipal</option><option>Governo estadual</option><option>Consultoria ou empresa</option><option>Imprensa ou academia</option><option>Outro</option></select></div>
            <div class="campo campo-largo"><label for="cadMunicipio">Município ou órgão</label><input id="cadMunicipio" name="municipio" autocomplete="off" value="${base ? esc(base.nome + ' (' + base.uf + ')') : ''}"></div>
            <input class="isca" type="text" name="site" tabindex="-1" autocomplete="off" aria-hidden="true">
            <label class="aceite"><input type="checkbox" name="aceite_privacidade" required><span>Li e aceito a <a href="#" data-ir-priv>política de privacidade</a>.</span></label>
            <label class="aceite"><input type="checkbox" name="aceite_contato"><span>Aceito receber contato da Vertex Advisory sobre a reforma tributária e os serviços para prefeituras (opcional).</span></label>
            <div class="form-acoes"><button class="btn btn-gold" type="submit">Abrir a memória de cálculo</button><span class="nota" id="cadMsg" role="status"></span></div>
        </form></div>`;
    const f = $('formCadastro'), msg = $('cadMsg');
    f.querySelector('[data-ir-priv]').addEventListener('click', e => { e.preventDefault(); mostrarVisao('privacidade'); });
    f.addEventListener('submit', async e => {
        e.preventDefault();
        const d = Object.fromEntries(new FormData(f).entries());
        const erros = [];
        const marca = (campo, ok) => { const el = f.elements[campo]; if (el) el.setAttribute('aria-invalid', ok ? 'false' : 'true'); if (!ok) erros.push(campo); };
        marca('nome', (d.nome || '').trim().length >= 3);
        marca('email', EMAIL_OK.test((d.email || '').trim()));
        marca('cargo', (d.cargo || '').trim().length >= 2);
        msg.dataset.erro = '1';
        if (erros.length) { msg.textContent = 'Confira os campos marcados.'; f.elements[erros[0]].focus(); return; }
        if (!f.elements.aceite_privacidade.checked) { msg.textContent = 'Para continuar, aceite a política de privacidade.'; f.elements.aceite_privacidade.focus(); return; }
        const botao = f.querySelector('button[type=submit]');
        botao.disabled = true; msg.dataset.erro = '0'; msg.textContent = 'Enviando…';
        try {
            const r = await fetch('/api/lead', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({
                nome: d.nome, email: d.email, cargo: d.cargo, vinculo: d.vinculo, municipio: d.municipio, site: d.site || '',
                municipio_cod: base ? MEMO.cod : '', uf: base ? base.uf : '',
                origem: 'memoria:' + MEMO.secao,
                utm: [...new URLSearchParams(location.search)].filter(([k]) => k.indexOf('utm_') === 0).map(([k, v]) => k + '=' + v).join('&'),
                aceite_privacidade: true, aceite_contato: !!f.elements.aceite_contato.checked, versao_termos: VERSAO_TERMOS
            })});
            if (!r.ok) throw new Error('lead ' + r.status);
            lembrarCadastro();
            track('cadastro', {origem: 'memoria', municipio: base ? base.nome : '', vinculo: d.vinculo, contato: !!f.elements.aceite_contato.checked});
            renderMemoria();
        } catch (err) {
            console.error(err);
            botao.disabled = false; msg.dataset.erro = '1';
            msg.innerHTML = 'Não foi possível enviar agora. Tente de novo, ou <button type="button" class="link-btn" id="cadPular">abra a memória mesmo assim</button>.';
            $('cadPular').addEventListener('click', () => { CADASTRO_PULADO = true; renderMemoria(); });
        }
    });
}

function renderMemoria() {
    document.querySelectorAll('#memoAbas button').forEach(b => b.classList.toggle('active', b.dataset.secao === MEMO.secao));
    const alvo = $('memoConteudo');
    const barrada = precisaCadastro();
    $('memoAbas').hidden = barrada;
    if (barrada) { renderCadastro(); return; }
    if (!MEMO.cod) return;
    const cod = MEMO.cod, base = POR_COD[cod];
    alvo.innerHTML = '<div class="panel"><p class="nota" role="status">Carregando os dados do município…</p></div>';
    Promise.all([dadosMemoria(base.uf), municipiosDaUF(base.uf)]).then(([memo, munis]) => {
        if (MEMO.cod !== cod || !$('view-memoria').classList.contains('active')) return;
        const m = munis[cod];
        if (!m) throw new Error('município ausente');
        let corpo;
        if (MEMO.secao === 'historico') {
            corpo = window.MemoriaCalculo.historico({
                historico: Object.assign({}, m.historico_por_ano, m.estimativa_2026 ? {'2026': m.estimativa_2026} : {}), origem2026: m.estimativa_2026 ? m.estimativa_2026.origem : null,
                campoTotal: 'total_reais_2025', coefPublicado: m.coef_cpt_pct, fatores: REF_NAC ? REF_NAC.fatores_ajuste : null,
                descricaoReferencia: 'Para o município, a receita de referência é o ISS bruto declarado ao SICONFI mais a cota-parte de ICMS recebida do estado.',
                colunas: [{rotulo: 'ISS bruto', campo: 'iss_reais_2025'}, {rotulo: '+ Cota-parte de ICMS', campo: 'cota_parte_reais_2025'}, {rotulo: '= Referência', campo: 'total_reais_2025', total: true}]
            });
        } else if (MEMO.secao === 'destino') {
            corpo = window.MemoriaCalculo.destinoMuni(memo.refs, m, cod);
        } else {
            corpo = window.MemoriaCalculo.seguro(memo.seguro_municipios[cod] || null, m.receita_media_referencia, 'municipal');
        }
        alvo.innerHTML = `<p class="memo-ente">Memória de cálculo de<b>${esc(base.nome)} (${base.uf})</b></p>` + corpo +
            '<p class="nota" style="margin-top:.9rem">Os valores desta página vêm da mesma execução que alimenta as demais abas. Para a descrição das fontes e das fórmulas, veja a aba Metodologia.</p>';
    }).catch(e => { console.error(e); alvo.innerHTML = '<div class="panel"><p class="aviso">Não foi possível carregar a memória de cálculo deste município. Tente novamente em instantes.</p></div>'; });
}

/* ── contato ──
   Os links só existem quando WhatsApp ou e-mail estão configurados no topo deste arquivo.
   A mensagem já leva o município e o número da ficha, para que o contato chegue qualificado. */
function contatoBotoes(alvo, base, resumo, local) {
    const assunto = base ? 'Diagnóstico da reforma tributária: ' + base.nome + '/' + base.uf : 'Diagnóstico da reforma tributária para a minha prefeitura';
    const texto = base
        ? 'Olá! Escrevo da Prefeitura de ' + base.nome + '/' + base.uf + '. Vi no Municípios na Reforma que a variação estimada da receita em 2033 é ' + resumo + ', frente ao cenário sem a reforma, e gostaria de conversar sobre o diagnóstico da reforma tributária para o município. Meu nome e cargo: '
        : 'Olá! Vim pelo Municípios na Reforma e gostaria de conversar sobre o diagnóstico da reforma tributária para a minha prefeitura. Meu nome, cargo e município: ';
    const rotulo = base ? 'Pedir diagnóstico de ' + base.nome : null;
    const html = [];
    if (CONFIG.whatsapp) html.push(`<a class="btn btn-gold btn-sm" data-contato="whatsapp" href="https://wa.me/${CONFIG.whatsapp}?text=${encodeURIComponent(texto)}" rel="noopener" target="_blank">${rotulo ? esc(rotulo) + ' pelo WhatsApp' : 'Falar pelo WhatsApp'}</a>`);
    if (CONFIG.email) html.push(`<a class="btn ${CONFIG.whatsapp ? 'btn-ghost' : 'btn-gold'} btn-sm" data-contato="email" href="mailto:${CONFIG.email}?subject=${encodeURIComponent(assunto)}&body=${encodeURIComponent(texto)}">${rotulo && !CONFIG.whatsapp ? esc(rotulo) : 'Enviar e-mail'}</a>`);
    if (!html.length && base) html.push('<a class="btn btn-gold btn-sm" href="#" data-ir="vertex">Falar com a Vertex</a>');
    alvo.innerHTML = html.join('');
    alvo.querySelectorAll('[data-contato]').forEach(a => a.addEventListener('click', () => track('clique_contato', {canal: a.dataset.contato, municipio: base ? base.nome : 'geral', local: local || 'aba'})));
    alvo.querySelectorAll('[data-ir]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); track('clique_contato', {canal: 'aba_vertex', municipio: base ? base.nome : 'geral', local: local || 'aba'}); if (a.dataset.ir === 'vertex') irParaContato(base, resumo); else mostrarVisao(a.dataset.ir); }));
}
contatoBotoes($('botoesContato'), null);

/* Botão flutuante do WhatsApp: o canal comercial fica fora das fichas e dos dados. A mensagem leva o município em foco. */
function iniciarZap() {
    const zap = $('zap');
    if (!CONFIG.whatsapp) return;
    zap.hidden = false;
    const mensagem = () => {
        const m = municipioEmFoco();
        return m ? 'Olá! Vim pelo painel Municípios na Reforma e gostaria de conversar sobre o diagnóstico da reforma tributária para ' + m.nome + '/' + m.uf + '.'
                 : 'Olá! Vim pelo painel Municípios na Reforma e gostaria de conversar sobre o diagnóstico da reforma tributária para a minha prefeitura.';
    };
    const atualizar = () => { zap.href = 'https://wa.me/' + CONFIG.whatsapp + '?text=' + encodeURIComponent(mensagem()); };
    atualizar();
    ['pointerdown', 'focus', 'mouseover'].forEach(ev => zap.addEventListener(ev, atualizar));      // o link já sai atualizado no toque ou no clique
    zap.addEventListener('click', () => { atualizar(); const m = municipioEmFoco(); track('clique_contato', {canal: 'whatsapp', municipio: m ? m.nome : 'geral', local: 'flutuante'}); });
}

/* ── formulários: pedido de informações sobre os serviços e cadastro do livro ──
   Mandam um e-mail de texto por /api/contato. Só aparecem quando a função informa que o envio está
   configurado na Vercel (RESEND_API_KEY e CONTATO_PARA); antes disso o portal não promete nada. */
let CONTATO_ATIVO = false;
const T_FORM = {contato: Date.now(), livro: Date.now()};   // tempo desde o carregamento da página, para a armadilha de robôs (nunca reiniciado, para não descartar quem usa preenchimento automático)
const MSG_PADRAO = 'Gostaria de receber informações sobre os serviços da Vertex Advisory para a minha prefeitura.';
let MSG_AUTO = '';

const municipioEmFoco = () => {
    const cod = ATUAL || (LOCAL && LOCAL.cod);
    return cod && POR_COD[cod] ? POR_COD[cod] : null;
};
iniciarZap();
function preencherMunicipioForms() {
    const m = municipioEmFoco();
    if (!m) return;
    ['ctMunicipio', 'livMunicipio'].forEach(id => { const el = $(id); if (el && !el.value) el.value = m.nome + ' (' + m.uf + ')'; });
}
/* Uma linha com o número do município em foco abre a seção de serviços: o dado vem antes da oferta. */
function renderContextoVertex() {
    const el = $('contextoVertex'), m = municipioEmFoco();
    if (!m || m.r) { el.hidden = true; el.innerHTML = ''; return; }
    el.innerHTML = `<span><b>${esc(m.nome)} (${m.uf})</b>: variação estimada de <b class="${clsSinal(m.v)}">${fmtPct(m.v)}</b> da receita em 2033, contra o cenário sem a reforma.</span> <button type="button" class="link-btn" id="verFichaVertex">Ver a ficha →</button>`;
    el.hidden = false;
    $('verFichaVertex').addEventListener('click', () => abrirMunicipio(m.cod));
}

function abrirContato(opcoes) {
    const f = $('formContato');
    f.hidden = false; $('btnServico').setAttribute('aria-expanded', 'true');
    if (!$('ctMsg').value) { $('ctMsg').value = MSG_PADRAO; MSG_AUTO = MSG_PADRAO; }
    preencherMunicipioForms();
    if (opcoes && opcoes.rolar) f.scrollIntoView({behavior: 'smooth', block: 'center'});
    if (!(opcoes && opcoes.semFoco)) $('ctNome').focus({preventScroll: true});
}
/* O botão "Pedir diagnóstico" da ficha chega aqui: município e variação já vão na mensagem. */
function irParaContato(base, resumo) {
    mostrarVisao('vertex');
    if (base) {
        $('ctMunicipio').value = base.nome + ' (' + base.uf + ')';
        const msg = 'Olá! Escrevo da Prefeitura de ' + base.nome + '/' + base.uf + '. Vi no Municípios na Reforma que a variação estimada da receita em 2033 é ' + resumo + ', frente ao cenário sem a reforma, e gostaria de conversar sobre o diagnóstico da reforma tributária para o município.';
        if (!$('ctMsg').value || $('ctMsg').value === MSG_AUTO) { $('ctMsg').value = msg; MSG_AUTO = msg; }
    }
    abrirContato({rolar: true, semFoco: false});
}
function mostrarFormularios() {
    $('livroEmBreve').hidden = true; $('servicoEmBreve').hidden = true;    // os formulários estão sempre abertos; sem o e-mail ativo, o envio sai pelo WhatsApp
}

function ligarFormulario(form, msgEl, tipo, aoEnviar) {
    form.addEventListener('submit', async e => {
        e.preventDefault();
        const d = Object.fromEntries(new FormData(form).entries());
        const erros = [];
        const marca = (campo, ok) => { const el = form.elements[campo]; if (el) el.setAttribute('aria-invalid', ok ? 'false' : 'true'); if (!ok) erros.push(campo); };
        marca('nome', (d.nome || '').trim().length >= 3);
        marca('email', EMAIL_OK.test((d.email || '').trim()));
        if (tipo === 'contato') marca('mensagem', (d.mensagem || '').trim().length >= 5);
        msgEl.dataset.erro = '1';
        if (erros.length) { msgEl.textContent = 'Confira os campos marcados.'; form.elements[erros[0]].focus(); return; }
        if (!form.elements.aceite_privacidade.checked) { msgEl.textContent = 'Para continuar, aceite a política de privacidade.'; form.elements.aceite_privacidade.focus(); return; }
        if (!CONTATO_ATIVO && CONFIG.whatsapp) {                   // canal de e-mail ainda não ativo: a mensagem sai pelo WhatsApp, já escrita
            const linhas = tipo === 'livro'
                ? ['Olá! Quero receber o sumário e as informações de lançamento do livro "Modernização Tributária Municipal no Brasil".']
                : ['Olá! ' + (d.mensagem || '').trim()];
            linhas.push('Nome: ' + d.nome.trim(), 'E-mail: ' + d.email.trim());
            if (d.telefone) linhas.push('Telefone: ' + d.telefone.trim());
            if (d.cargo) linhas.push('Cargo: ' + d.cargo.trim());
            if (d.municipio) linhas.push('Município ou órgão: ' + d.municipio.trim());
            const url = 'https://wa.me/' + CONFIG.whatsapp + '?text=' + encodeURIComponent(linhas.join('\n'));
            track(tipo === 'livro' ? 'livro_cadastro' : 'contato_enviado', {municipio: d.municipio || '', canal: 'whatsapp'});
            window.open(url, '_blank', 'noopener');
            form.innerHTML = '<p class="form-ok" role="status"><strong>Quase lá.</strong> Abrimos o WhatsApp com os seus dados já escritos: é só tocar em enviar. Se a conversa não abriu, <a href="' + url + '" target="_blank" rel="noopener">toque aqui para abri-la</a>.</p>';
            return;
        }
        const botao = form.querySelector('button[type=submit]');
        botao.disabled = true; msgEl.dataset.erro = '0'; msgEl.textContent = 'Enviando…';
        try {
            const r = await fetch('/api/contato', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({
                tipo, nome: d.nome, email: d.email, cargo: d.cargo || '', telefone: d.telefone || '', municipio: d.municipio || '', mensagem: d.mensagem || '',
                interesse: d.interesse || '', site: d.site || '', t: Date.now() - T_FORM[tipo], origem: tipo === 'livro' ? 'livro' : 'aba_vertex',
                utm: [...new URLSearchParams(location.search)].filter(([k]) => k.indexOf('utm_') === 0).map(([k, v]) => k + '=' + v).join('&'),
                aceite_privacidade: true
            })});
            if (!r.ok) throw new Error('contato ' + r.status);
            track(tipo === 'livro' ? 'livro_cadastro' : 'contato_enviado', {municipio: d.municipio || '', interesse: d.interesse || ''});
            aoEnviar(d);
        } catch (err) {
            console.error(err);
            botao.disabled = false; msgEl.dataset.erro = '1';
            msgEl.textContent = 'Não foi possível enviar agora. Tente de novo em instantes.';
        }
    });
}

function iniciarFormularios() {
    ligarFormulario($('formLivro'), $('livMsg'), 'livro', d => {
        $('formLivro').innerHTML = '<p class="form-ok" role="status"><strong>Cadastro recebido.</strong> Você vai receber o sumário do livro e as informações do lançamento em ' + esc(d.email) + '.</p>';
    });
    ligarFormulario($('formContato'), $('ctMsgStatus'), 'contato', d => {
        $('formContato').innerHTML = '<p class="form-ok" role="status"><strong>Solicitação enviada.</strong> A Vertex responde no e-mail ' + esc(d.email) + '.</p>';
    });
    $('btnServico').addEventListener('click', () => {
        if ($('formContato').hidden) { track('servico_abrir', {}); abrirContato({}); }
        else { $('formContato').hidden = true; $('btnServico').setAttribute('aria-expanded', 'false'); }
    });
    getJSON('/api/contato').then(r => { CONTATO_ATIVO = !!(r && r.ativo); }).catch(() => { /* sem função: formulários ficam fora */ }).then(mostrarFormularios);
}
iniciarFormularios();
$('btnVoltar').addEventListener('click', () => mostrarVisao('visao-geral'));
/* Ao imprimir, os detalhes do cálculo saem abertos; depois voltam ao estado em que estavam. */
let ABERTOS_ANTES = null;
window.addEventListener('beforeprint', () => { const ds = [...document.querySelectorAll('.detalhes details')]; ABERTOS_ANTES = ds.map(d => d.open); ds.forEach(d => { d.open = true; }); });
window.addEventListener('afterprint', () => { if (ABERTOS_ANTES) [...document.querySelectorAll('.detalhes details')].forEach((d, i) => { d.open = ABERTOS_ANTES[i]; }); ABERTOS_ANTES = null; });
if (CONFIG.razaoSocial) $('privControlador').textContent = CONFIG.razaoSocial + (CONFIG.cnpj ? ' (CNPJ ' + CONFIG.cnpj + ')' : '');
if (CONFIG.email) $('privContato').textContent = CONFIG.email;
if (CONFIG.gaId) $('privAnalytics').textContent = 'Este portal usa o Google Analytics 4 para medir audiência de forma agregada (páginas vistas, cliques nos botões de contato, uso do mapa). O Google define cookies para isso; você pode bloqueá-los no navegador sem perder nenhuma função do portal.';
})();
