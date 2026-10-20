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
    gaId: 'G-JYFYHLBRP9', // ID público do GA4. A coleta só começa na produção, após consentimento.
    razaoSocial: '', // nome do controlador dos dados, exibido na política de privacidade
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
    if (window.MnrMedicao) window.MnrMedicao.registrar(evento, params);
}
if (window.MnrMedicao) window.MnrMedicao.iniciar(CONFIG.gaId);

/* ── estado ── */
let LISTA = [], POR_COD = {}, RESULT = null, NAC = null, AGG = {};
let grafSerie = null;
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
    document.querySelectorAll('.view').forEach(s => s.classList.toggle('active', s.id === 'view-' + v));
    document.querySelectorAll('.tab-btn').forEach(b => {
        const on = b.dataset.view === v;
        b.classList.toggle('active', on);
        if (on) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
    });
    const dentro = !!document.querySelector('.tab-mais-lista .tab-btn.active');         // aba aberta está no menu "Mais"
    $('tabMais').classList.toggle('active', dentro);
    fecharMais();
    const ativa = document.querySelector('.tab-btn.active'); if (ativa && $('navAtual')) $('navAtual').textContent = ativa.textContent;
    fecharMenu();
    window.scrollTo({top: 0});
}
function fecharMenu() { const n = $('tabnav'); if (n) n.classList.remove('aberto'); const t = $('navToggle'); if (t) t.setAttribute('aria-expanded', 'false'); }
if ($('navToggle')) $('navToggle').addEventListener('click', e => {
    e.stopPropagation();
    const aberto = $('tabnav').classList.toggle('aberto');
    $('navToggle').setAttribute('aria-expanded', aberto ? 'true' : 'false');
});
document.addEventListener('click', e => { if ($('tabnav') && !$('tabnav').contains(e.target)) fecharMenu(); });
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
        if (UF_VISITANTE) MAPA.destacarUF(UF_VISITANTE);
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
        lista.querySelectorAll('[data-cod]').forEach(b => b.addEventListener('click', () => { track('trilho_municipio', {municipio_codigo: b.dataset.cod}); abrirMunicipio(b.dataset.cod); }));
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
        $(idTab).querySelectorAll('tr[data-cod]').forEach(tr => tr.addEventListener('click', () => { track('ranking_municipio', {municipio_codigo: tr.dataset.cod}); abrirMunicipio(tr.dataset.cod); }));
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
        track('busca_municipio', {municipio_codigo: cod, uf: POR_COD[cod].uf});
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
    if (MAPA) MAPA.destacarUF(uf);
    if (!RANK_UF && $('view-rankings').classList.contains('active')) renderRankUF();
}

function iniciarLocalizacao() {
    const viaConexao = () => getJSON('/api/geo').then(g => {
        if (!g || g.country !== 'BR' || !g.city) return;
        const alvo = norm(g.city), achados = LISTA.filter(m => m.uf === g.uf && (m.chave === alvo || m.alt === alvo));
        if (NOMES_UF[g.uf]) definirUFVisitante(g.uf);
        if (achados.length === 1) sugerirLocal(achados[0].cod, 'conexao');
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
    if (MAPA) MAPA.destacar(cod);                                                  // o mapa continua no Brasil; o município fica marcado para quando o usuário abrir o estado
    track('local_sugerido', {origem, municipio_codigo: cod, uf: m.uf});
    LOCAL.rotulo = m.nome;                                                         // o campo de busca já abre com o município; quem mora em outro digita por cima
    const campo = $('busca');
    if (!campo.value || campo.value === anterior) campo.value = m.nome;
}

/* A aba Município nunca abre vazia: usa o município localizado; sem cidade, a capital do estado estimado. */
const CAPITAIS = {AC:'1200401',AL:'2704302',AM:'1302603',AP:'1600303',BA:'2927408',CE:'2304400',ES:'3205309',GO:'5208707',MA:'2111300',MG:'3106200',MS:'5002704',MT:'5103403',PA:'1501402',PB:'2507507',PE:'2611606',PI:'2211001',PR:'4106902',RJ:'3304557',RN:'2408102',RO:'1100205',RR:'1400100',RS:'4314902',SC:'4205407',SE:'2800308',SP:'3550308',TO:'1721000'};
function municipioInicial() {
    if (ATUAL) return;
    const cod = LOCAL ? LOCAL.cod : (UF_VISITANTE && CAPITAIS[UF_VISITANTE]);
    if (cod && POR_COD[cod]) abrirMunicipio(cod, {semUrl: true, semEscopo: true});
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
            .attr('fill', d => luminancia(corUF(d.properties.uf)) > 0.32 ? '#062254' : '#fff');
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
    ctl.destacarUF = uf => {   // contorna, no mapa do Brasil, o estado de quem chega, sem mudar o que o mapa mostra
        if (!pathsUF) return;
        pathsUF.classed('sua', d => d.properties.uf === uf).filter('.sua').raise();
        rotulos.raise();   // as siglas continuam por cima do contorno
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
        track('clique_mapa', {municipio_codigo: cod, uf: POR_COD[cod].uf});
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
    if (ESCOPO !== base.uf && !opt.semEscopo) definirEscopo(base.uf, 'muni');
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
        <div class="coef"><span>Participação de referência, 2025</span><b>${fmtPctPlain(m.coef_neutro_pct)}</b><small>A fatia deste ente em 2025, sem a reforma: é a base do cenário sem reforma.</small></div>
        <div class="coef"><span>Coeficiente histórico</span><b>${fmtPctPlain(m.coef_cpt_pct)}</b><small>Razão entre a receita média de referência do ente (ISS e cota-parte do ICMS, média de 2019 a 2026, com 2026 estimado) e a de todos os entes (LC 227/2026, arts. 114 e 115). Rege 80% do IBS até 2032 e 90% em 2033. <a href="#" data-abrir="detHist">Ver a receita usada →</a></small></div>
        <div class="coef"><span>Coeficiente de destino</span><b>${fmtPctPlain(m.coef_pleno_pct)}</b><small>Estimativa do painel, baseada no consumo estimado (população e renda, com a POF), nas compras da prefeitura e na cota-parte do IBS estadual. Rege 19% do IBS até 2032 e 9,5% em 2033, depois da retenção do Seguro-Receita; por inteiro, só em 2078.</small></div>
    </div>`;
}

function seguroCardHtml(repasse, posByYear) {
    const v2033 = (repasse && repasse['2033']) || 0;
    const recebeAlgumAno = ANOS.some(a => ((repasse && repasse[a]) || 0) > 1);
    if (!recebeAlgumAno) {
        return `<div class="seguro-card"><div class="seguro-label">Seguro-Receita (ADCT art. 132)</div><div class="seguro-value muted">Não recebe</div>
            <div class="seguro-note">Em 2029–2033, a razão entre o IBS que este ente receberia pelo critério de destino e a sua receita média de referência fica acima do nível de nivelamento em todos os anos; não há repasse.</div></div>`;
    }
    if (v2033 <= 1) {
        return `<div class="seguro-card recebe"><div class="seguro-label">Seguro-Receita (ADCT art. 132)</div><div class="seguro-value muted">Não recebe em 2033</div>
            <div class="seguro-note">Recebeu repasse em anos anteriores da transição, mas deixa de receber a partir de 2033: a razão entre o IBS pelo critério de destino e a receita média de referência alcançou o nível de nivelamento daquele ano.</div></div>`;
    }
    const total2033 = posByYear && posByYear['2033'];
    const share = total2033 ? v2033 / total2033 * 100 : null;
    const anos = ANOS.filter(a => (repasse[a] || 0) > 1).map(a => a + ': ' + fmtMoney(repasse[a])).join(' · ');
    return `<div class="seguro-card recebe"><div class="seguro-label">Seguro-Receita (ADCT art. 132)</div><div class="seguro-value">${fmtMoney(v2033)}</div>
        <div class="seguro-note">Repasse bruto em 2033, antes da dedução do financiamento do CGIBS${share != null ? ', equivalente a ' + share.toLocaleString('pt-BR', {maximumFractionDigits: 1}) + '% da receita projetada do município no mesmo ano' : ''}. Série (bruta, em R$ de 2025): ${anos}. Veja a memória de cálculo para o nível de nivelamento de cada ano.</div></div>`;
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
          + `<tr class="media"><td colspan="5">Coeficiente histórico</td><td class="num">${fmtPctPlain(media / REF_NAC.total_br_2025 * 100, 5)}</td></tr>`
        : `<tr class="media"><td>Média 2019–2026</td><td class="num">${f(soma.iss / n)}</td><td class="num">${f(soma.cota / n)}</td><td class="num">${f(media)}</td></tr>`;
    return `<div class="table-wrap"><table class="dados tab-hist"><thead><tr>${cab}</tr></thead><tbody>${rows}${rodape}</tbody></table></div>
        <p class="nota">Valores em R$ ${mi ? 'milhões' : 'mil'}; a última coluna está em reais de 2025.${fat ? ' O fator de ajuste corrige cada ano pela variação nominal da arrecadação total de ICMS e ISS do país (LC 227, art. 115, §2º), e a referência do ano é o valor declarado vezes esse fator.' : ''}${origemAnosTxt(historico)}${est26 ? (est26.origem === 'rreo' ? ' 2026, já em reais de 2025: ISS observado no RREO de setembro de 2025 a agosto de 2026; cota-parte de 2025 ajustada pelo crescimento de janeiro a agosto, também do RREO.' : ' 2026, já em reais de 2025: este município não publica o Anexo 3 do RREO; mantém a posição relativa de 2025 no estado.') : ''}</p>`;
}

/* ── participação histórica: a fatia do município na arrecadação nacional, ano a ano, contra a média que vira o coeficiente histórico ── */
function pctAdapt(v) {
    if (v == null || !isFinite(v)) return '—';
    const d = Math.abs(v) < 0.01 ? 5 : Math.abs(v) < 0.1 ? 4 : Math.abs(v) < 1 ? 3 : 2;
    return v.toLocaleString('pt-BR', {minimumFractionDigits: d, maximumFractionDigits: d}) + '%';
}

function partDados(m) {
    if (!REF_NAC || !REF_NAC.total_br_2025 || m.coef_cpt_pct == null) return null;
    const tb = REF_NAC.total_br_2025, h = m.historico_por_ano || {};
    const valores = ANOS_HIST.map(a => h[a] ? h[a].total_reais_2025 / tb * 100 : null);
    const est = m.estimativa_2026 ? m.estimativa_2026.total_reais_2025 / tb * 100 : null;
    const s25 = valores[valores.length - 1];
    return {valores, est, coef: m.coef_cpt_pct, s25, rreo: !!(m.estimativa_2026 && m.estimativa_2026.origem === 'rreo')};
}

/* Texto que explica o porquê: compara a fatia de 2025 (a do cenário sem reforma) com a média de 2019 a 2026 (a do coeficiente histórico). */
function explicaParticipacao(nome, d) {
    const fecho = ' O resultado de 2033 também depende do critério de destino e do Seguro-Receita, mostrados nos blocos abaixo.';
    if (d.s25 == null) return `Este município não tem o dado de 2025 no SICONFI, então não dá para comparar a fatia atual com a média. O painel usa a própria média como aproximação da fatia de 2025, e por isso o critério histórico, aqui, quase não altera o ponto de partida.` + fecho;
    const r = d.coef / d.s25, vezes = r.toLocaleString('pt-BR', {maximumFractionDigits: 1});
    const base = `Em 2025, a fatia de ${nome} na arrecadação nacional de ICMS e ISS foi de ${pctAdapt(d.s25)}. A média de 2019 a 2026 é de ${pctAdapt(d.coef)}`;
    const regra = ' É essa média, e não o valor de 2025, que vira o coeficiente histórico, e em 2033 cerca de 90% do IBS ainda é repartido por ele. O cenário sem a reforma, ao contrário, mantém a fatia de 2025.';
    if (r > 1.15) return `${base}, ${vezes} vez${r >= 2 ? 'es' : ''} a de 2025.${regra} Por isso a reforma preserva uma fatia maior do que o município tem hoje, e o critério histórico puxa o resultado para cima. Se o nível de 2025 for um novo patamar, o município ganha em relação ao cenário sem reforma; se a receita voltar ao patamar anterior, o ganho diminui ou desaparece.` + fecho;
    if (r < 0.87) return `${base}, abaixo da fatia de 2025.${regra} Por isso a reforma devolve uma fatia menor do que o município tem hoje, e o critério histórico puxa o resultado para baixo. Se o nível de 2025 for um novo patamar, o município perde em relação ao cenário sem reforma; se for um pico passageiro, o efeito é menor.` + fecho;
    return `${base}, parecida com a de 2025.${regra} Por isso o critério histórico quase não altera o ponto de partida do município.` + fecho;
}

function painelParticipacaoHtml(m, base) {
    const d = partDados(m); if (!d) return '';
    return `<div class="panel" id="painelPart"><h3>O coeficiente histórico</h3>
        <p class="panel-sub">O coeficiente histórico rege 90% do IBS em 2033 (80% entre 2029 e 2032) e é a fatia que o município teve, em média, na receita de referência nacional (ISS e cota-parte do ICMS) de 2019 a 2026. O gráfico compara a fatia de cada ano com essa média.</p>
        <div class="canvas-box canvas-part"><canvas id="gPart" role="img" aria-label="Gráfico de linhas com a participação de ${esc(base.nome)} na arrecadação nacional de 2019 a 2025, a estimativa de 2026 e a média de 2019 a 2026, que é o coeficiente histórico. Os valores estão na tabela da receita de referência, em Detalhes do cálculo."></canvas></div>
        <p class="leitura">${esc(explicaParticipacao(base.nome, d))}</p>
        <p class="nota nota-grafico"><a href="#" data-abrir="detHist">Ver a conta, ano a ano, na tabela da receita de referência →</a></p>
    </div>`;
}

function desenhaParticipacao(m) {
    const d = partDados(m), cv = $('gPart'); if (!d || !cv) return;
    const rotulos = ANOS_HIST.concat(['2026']);
    const estreito = cv.parentElement.clientWidth < 520;
    const todos = d.valores.concat([d.est, d.coef]).filter(v => v != null);
    const lo = Math.min(...todos), hi = Math.max(...todos), dig = Math.abs(hi) < 0.01 ? 5 : Math.abs(hi) < 0.1 ? 4 : Math.abs(hi) < 1 ? 3 : 2;
    const obs = d.valores.concat([null]);
    const est = ANOS_HIST.map((a, i) => i === ANOS_HIST.length - 1 ? d.s25 : null).concat([d.est]);
    const media = rotulos.map(() => d.coef);
    const rotuloEst = d.rreo ? '2026 (estimada pelo RREO até agosto)' : '2026 (estimada)';
    const linha = {borderWidth: 2.5, tension: 0.1, spanGaps: false, hitRadius: 14};
    // rótulos com o valor em cada ponto (no celular, alternando acima e abaixo para não se sobreporem)
    const valoresNosPontos = {id: 'valoresNosPontos', afterDatasetsDraw(chart) {
        const c = chart.ctx; c.save(); c.font = (estreito ? '600 9px' : '600 11px') + " 'Inter', system-ui, sans-serif"; c.fillStyle = '#141414'; c.textAlign = 'center';
        [0, 1].forEach(di => chart.getDatasetMeta(di).data.forEach((pt, i) => {
            const v = chart.data.datasets[di].data[i]; if (v == null || (di === 1 && i < rotulos.length - 1)) return;
            const abaixo = estreito ? i % 2 === 1 : (di === 1);
            c.textBaseline = abaixo ? 'top' : 'bottom'; c.fillText(pctAdapt(v), pt.x, pt.y + (abaixo ? 9 : -9));
        })); c.restore();
    }};
    GPART = new Chart(cv, {
        type: 'line', plugins: [valoresNosPontos],
        data: {labels: rotulos, datasets: [
            Object.assign({label: 'Participação em cada ano', data: obs, borderColor: '#062254', backgroundColor: '#062254', pointBackgroundColor: '#062254', pointBorderColor: '#fff', pointBorderWidth: 2, pointRadius: 4.5, pointHoverRadius: 6}, linha),
            Object.assign({label: rotuloEst, data: est, borderColor: '#062254', borderDash: [5, 4], backgroundColor: '#fff', pointBackgroundColor: ctx => ctx.dataIndex === rotulos.length - 1 ? '#fff' : 'rgba(0,0,0,0)', pointBorderColor: ctx => ctx.dataIndex === rotulos.length - 1 ? '#062254' : 'rgba(0,0,0,0)', pointBorderWidth: 2, pointRadius: ctx => ctx.dataIndex === rotulos.length - 1 ? 5.5 : 0, pointHoverRadius: 6}, linha),
            {label: 'Coeficiente histórico: ' + pctAdapt(d.coef), data: media, borderColor: '#0f508e', borderWidth: 2, borderDash: [7, 5], pointRadius: 0, pointHitRadius: 0, fill: false}
        ]},
        options: {responsive: true, maintainAspectRatio: false, interaction: {mode: 'index', intersect: false}, layout: {padding: {top: 16, bottom: 12, right: 30}},
            plugins: {legend: {position: 'bottom', labels: {boxWidth: 26, boxHeight: 2, padding: 14, color: '#141414', font: {size: 11}}},
                tooltip: {callbacks: {label: c => c.parsed.y == null ? null : ' ' + c.dataset.label + ': ' + pctAdapt(c.parsed.y)}}},
            scales: {y: {grace: '12%', grid: {color: '#e9edf0', drawTicks: false}, border: {display: false}, ticks: {maxTicksLimit: 5, color: '#6b6b6b', font: {size: 11}, padding: 8,
                        callback: v => v.toLocaleString('pt-BR', {minimumFractionDigits: dig, maximumFractionDigits: dig}) + '%'}},
                x: {grid: {display: false}, border: {color: '#c8d0d6'}, ticks: {autoSkip: false, maxRotation: estreito ? 55 : 0, minRotation: estreito ? 55 : 0, font: {size: estreito ? 10 : 11}, color: '#6b6b6b', padding: 6}}}}
    });
}

/* Leitura em português do que o gráfico mostra, montada por regras a partir dos números do município. */
/* O repasse bruto do Seguro-Receita (o que o fundo paga) e o efetivo (o que entra na receita, depois da dedução do CGIBS) diferem em até 2%.
   As comparações com o cenário sem reforma usam o efetivo, que é o valor que está somado à receita com reforma. */
const seguroEfetivo = (m, ano) => { const c = m.componentes_por_ano && m.componentes_por_ano[ano]; return c && c.seguro != null ? c.seguro : ((m.repasse_seguro_receita_por_ano || {})[ano] || 0); };

/* Decomposição da diferença anual em quatro fontes, com a mesma base do modelo (build-resultados-consolidados): o cenário sem reforma é dividido
   nas mesmas parcelas da receita com reforma, e cada fonte é o que a receita com reforma tem a mais ou a menos que a sua parcela.
   histórico = IBS pelo critério histórico, antes do CGIBS, menos a parcela do cenário sem reforma (s·λ·C);
   destino = IBS por destino, antes do CGIBS, menos a parcela depois da retenção do Seguro-Receita (s·(1−λ)·(1−ρ)·C);
   Seguro-Receita = repasse recebido menos a retenção de 5% que todos sofrem (ρ·s·(1−λ)·C);
   CGIBS = dedução sobre os três blocos. A soma é igual a pos − cenário sem reforma. */
function decomposicaoEfeito(m, ano) {
    const p = NAC && NAC.projecao && NAC.projecao.find(r => String(r.ano) === String(ano));
    const c = m.componentes_por_ano && m.componentes_por_ano[ano];
    if (!p || !c || !p.ibs_bruto || p.alpha_a == null) return null;
    const C = m.contrafactual_por_ano[ano], s = p.sa, l = p.alpha_a, ca = p.ca, rho = p.ibs_seguro_receita / (p.ibs_bruto * (1 - l));
    const hist = c.cpt / (1 - ca) - s * l * C;
    const dest = c.destino / (1 - ca) - s * (1 - l) * (1 - rho) * C;
    const seg = c.seguro / (1 - ca) - rho * s * (1 - l) * C;
    const cg = -ca * (c.cpt + c.destino + c.seguro) / (1 - ca);
    const resto = m.pos_por_ano[ano] - C - (hist + dest + seg + cg);   // ICMS e ISS remanescentes: zero por construção; guarda contra mudança do modelo
    return {C, ca, partes: [
        {k: 'hist', nome: 'Critério histórico', ref: 'o critério histórico', dica: 'O coeficiente histórico contra a participação de 2025.', v: hist},
        {k: 'dest', nome: 'Critério de destino', ref: 'o critério de destino', dica: 'O coeficiente de destino contra a participação de 2025, depois da retenção de 5% do Seguro-Receita.', v: dest},
        {k: 'seg', nome: 'Seguro-Receita', ref: 'o Seguro-Receita', dica: 'O repasse recebido menos a retenção de 5% que todos os entes sofrem.', v: seg},
        {k: 'cg', nome: 'Financiamento do CGIBS', ref: 'o financiamento do CGIBS', dica: 'A dedução sobre o IBS do município, limitada a ' + (ca * 100).toLocaleString('pt-BR', {maximumFractionDigits: 2}) + '% em ' + ano + '.', v: cg}
    ], resto};
}
function decompHtml(m, ano) {
    const d = decomposicaoEfeito(m, ano);
    if (!d || Math.abs(d.resto) > Math.max(1e4, Math.abs(d.C) * 1e-6)) return '';
    const total = d.partes.reduce((a, x) => a + x.v, 0), max = Math.max(...d.partes.map(x => Math.abs(x.v)), 1);
    const maior = d.partes.slice().sort((a, b) => Math.abs(b.v) - Math.abs(a.v))[0];
    const linha = x => {
        const w = Math.abs(x.v) / max * 50, cls = x.v < 0 ? 'neg' : 'pos';
        return `<li><div class="dc-nome"><b>${x.nome}</b><small>${x.dica}</small></div>
            <div class="dc-barra" aria-hidden="true"><span class="${cls}" style="width:${w.toFixed(1)}%;${x.v < 0 ? 'right:50%' : 'left:50%'}"></span></div>
            <div class="dc-valor ${cls}">${x.v > 0 ? '+' : ''}${fmtMoney(x.v)}<small>${fmtPct(x.v / d.C)} do cenário sem reforma</small></div></li>`;
    };
    return `<ul class="decomp" role="list">${d.partes.map(linha).join('')}</ul>
        <div class="dc-total"><span>Diferença anual em ${ano}</span><b class="${total < 0 ? 'neg' : 'pos'}">${total > 0 ? '+' : ''}${fmtMoney(total)}</b></div>
        <p class="leitura">O maior componente é ${maior.ref}, que ${maior.v < 0 ? 'reduz' : 'soma'} ${fmtMoney(Math.abs(maior.v))} à receita do ano em relação ao cenário sem reforma.</p>`;
}

function leituraMunicipio(m, base) {
    const nome = '<b>' + esc(base.nome) + '</b>';
    const v29 = m.variacao_por_ano['2029'], v33 = m.variacao_por_ano['2033'];
    const dif33 = m.pos_por_ano['2033'] - m.contrafactual_por_ano['2033'];
    const rep = m.repasse_seguro_receita_por_ano || {};
    const seg33 = rep['2033'] || 0;
    const pos33 = m.pos_por_ano['2033'], neutra = Math.abs(v33) <= 0.0005, perde = v33 < 0;
    const segEf33 = seguroEfetivo(m, '2033');
    const depende = seg33 > 0 && v33 > 0.0005 && segEf33 > dif33;
    // Resposta à pergunta do título, em poucas linhas: o resultado de 2033 e, se for o caso, de que ele depende.
    const lead = [`Em 2033, a receita projetada de ${nome} alcança ${fmtMoneyFino(pos33)}, já incluindo a parcela de 25% do IBS estadual que cabe aos municípios. ` + (neutra
        ? 'Esse valor é praticamente igual ao do cenário sem reforma.'
        : `Esse valor é ${fmtPct(Math.abs(v33)).replace(/^[+−]/, '')} ${perde ? 'inferior' : 'superior'} ao cenário sem reforma, o equivalente a ${perde ? 'uma perda' : 'um ganho'} anual de ${fmtMoney(Math.abs(dif33))}.`)];
    if (depende) lead.push(`Esse resultado depende do Seguro-Receita, o repasse compensatório do Comitê Gestor: sem ele, a receita ficaria ${fmtMoney(segEf33 - dif33)} abaixo do cenário sem reforma.`);
    // O restante explica como ler o gráfico; no celular fica recolhido.
    const resto = ['O gráfico apresenta os efeitos estimados da reforma tributária do consumo sobre as receitas municipais. As projeções consideram a substituição gradual do ISS e do ICMS pelo IBS e comparam os resultados com um cenário sem reforma.'];
    if (Math.abs(v29) > 0.0005 || Math.abs(v33) > 0.0005) resto.push(`O efeito começa em ${fmtPct(v29)} em 2029 e chega a ${fmtPct(v33)} em 2033, de modo que a transição vai ${Math.abs(v33) > Math.abs(v29) ? 'ampliando' : 'reduzindo'} a diferença.`);
    if (seg33 > 0) resto.push(`${nome} recebe ${fmtMoney(seg33)} do Seguro-Receita em 2033${depende ? ', mais do que o ganho' : ''}; o repasse compensatório do Comitê Gestor já está incluído nos números, depois da dedução do financiamento do CGIBS.`);
    else resto.push(`${nome} não recebe Seguro-Receita no período, e o resultado vem da repartição do IBS pelos coeficientes.`);
    // A ressalva de que são estimativas fica sempre à vista, junto da resposta, mesmo quando o restante está recolhido.
    const ressalva = 'São estimativas que dependem das hipóteses do modelo' + (CONFIG.sensibilidade ? '; a seção sobre sensibilidade, mais abaixo, mostra a faixa de resultados.' : '. Os critérios e as fontes estão em Detalhes do cálculo e na Metodologia.');
    const par = l => l.map(t => '<p>' + t + '</p>').join('');
    return `<div class="leitura-corpo"><div class="leitura-lead">${par(lead)}<p class="leitura-ressalva">${ressalva}</p></div>
        <details class="leitura-mais" id="leituraMais"><summary>Como ler este gráfico</summary><div class="leitura-resto">${par(resto)}<p class="como-ler"><a href="#" data-tab="metodologia" data-depois="met-5">Como ler os dois cenários →</a></p></div></details></div>`;
}

/* Marcador do município no mini-mapa: um ponto com o nome, sobre o contorno (que sozinho quase não se vê num estado inteiro). */
let PIN = null;
function marcarPin() {
    const wrap = $('miniWrap'), svg = $('miniSvg');
    if (!PIN || !wrap || !svg) return;
    const path = svg.querySelector('path[data-cod="' + PIN.cod + '"]');
    wrap.querySelectorAll('.pin-muni').forEach(n => n.remove());
    if (!path) return;
    const r = path.getBoundingClientRect(), w = wrap.getBoundingClientRect();
    const pin = document.createElement('div'); pin.className = 'pin-muni';
    pin.innerHTML = '<span class="pin-rotulo"></span><span class="pin-ponto"></span>';
    pin.firstChild.textContent = PIN.nome;
    pin.style.left = (r.left - w.left + r.width / 2) + 'px'; pin.style.top = (r.top - w.top + r.height / 2) + 'px';
    wrap.appendChild(pin);
}
window.addEventListener('resize', () => { if (PIN) marcarPin(); });

function renderFicha(cod, base, m) {
    graficos.forEach(g => g.destroy()); graficos = []; grafSerie = null;
    if (GSENS) { GSENS.destroy(); GSENS = null; }
    if (GPART) { GPART.destroy(); GPART = null; }
    const ok = LISTA.filter(x => !x.r).sort((a, b) => b.v - a.v);
    const posBR = ok.findIndex(x => x.cod === cod) + 1;
    const naUF = ok.filter(x => x.uf === base.uf);
    const posUF = naUF.findIndex(x => x.cod === cod) + 1;

    const pos33 = m.pos_por_ano['2033'], cf33 = m.contrafactual_por_ano['2033'];
    const dif33 = pos33 - cf33, v33 = m.variacao_por_ano['2033'];
    const sinal = clsSinal(v33);

    let aviso = '';
    if (m.neutro_suspeito) aviso = '<strong>Dado a conferir.</strong> O valor declarado ao SICONFI para 2025 diverge de forma incompatível da série histórica deste município, o que sugere falha de preenchimento na fonte. Os números são exibidos com cautela e não entram nos rankings.';
    else if (m.neutro_aproximado) aviso = '<strong>Estimativa aproximada.</strong> Este município não tem registro individualizado de ISS e cota-parte do ICMS para 2025 no SICONFI, e a participação de 2025 foi aproximada pelo próprio coeficiente histórico (média de 2019 a 2026). Leia os números como ordem de grandeza.';
    else if (m.cobertura_anos < 5) aviso = '<strong>Série curta.</strong> Há apenas ' + m.cobertura_anos + ' anos de dados históricos para este município, abaixo do mínimo recomendado de 5. Os números são menos estáveis.';

    const seg33 = (m.repasse_seguro_receita_por_ano || {})['2033'] || 0;
    const painelSeguro = seg33 > 0 ? `<div class="panel" id="painelSeguro"><h3>Seguro-Receita</h3><p class="panel-sub">O fundo equivale a 5% do IBS que não é distribuído pelo critério histórico e é repartido entre os entes de menor razão entre o IBS pelo destino e a receita média de referência, até igualar essa razão.</p>${seguroCardHtml(m.repasse_seguro_receita_por_ano, m.pos_por_ano)}</div>` : '';
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
            <div class="pos-item"><b>${fmtInt(posUF)}º</b><span>entre ${fmtInt(naUF.length)} municípios ${DE_UF[base.uf]}: à frente de ${Math.round((naUF.length - posUF) / naUF.length * 100)}% deles</span></div>
            <div class="pos-item"><b>${fmtInt(posBR)}º</b><span>entre ${fmtInt(ok.length)} municípios do Brasil: à frente de ${Math.round((ok.length - posBR) / ok.length * 100)}% deles</span></div>
        </div><p class="nota">Do maior ganho (1º) à maior perda, na variação da receita em 2033.</p>`;

    $('fichaCorpo').innerHTML = `
        <div class="ficha-top">
            <div>
                <h2 id="fichaTitulo" tabindex="-1">${nomeSeg}<small>${base.uf}</small></h2>
                <p class="ficha-meta">${esc(NOMES_UF[base.uf])} · <span title="Média 2019–2026, IBGE">${fmtInt(m.pop_media)} habitantes</span></p>
            </div>
            <div class="ficha-acoes">
                <button class="btn btn-ghost btn-sm" type="button" id="btnCopiar">Copiar link</button>
                <button class="btn btn-ghost btn-sm" type="button" id="btnImprimir">Imprimir / salvar PDF</button>
            </div>
        </div>
        ${aviso ? `<div class="aviso" role="note">${aviso}</div>` : ''}
        <nav class="cap-nav" aria-label="Seções desta página"><a href="#cap-resultado">Resultado</a><a href="#cap-porque">Por quê</a><a href="#cap-compara">Comparação</a><a href="#cap-detalhes">Cálculo</a></nav>
        <div class="panel accent panel-grafico" id="cap-resultado">
            <h3 class="sr-only">Para onde vai a arrecadação</h3>
            <div class="canvas-box canvas-serie"><canvas id="gSerie" role="img" aria-label="Gráfico de linhas com a receita realizada em 2025 e a projeção de 2029 a 2033 com e sem a reforma. Os mesmos valores estão na tabela ano a ano, em Detalhes do cálculo."></canvas></div>
            <p class="nota-serie">Valores em R$ de 2025. Linha tracejada: cenário sem a reforma. Faixa cinza: 2026 a 2028, sem projeção. O eixo vertical não começa em zero, para destacar a diferença entre os cenários.</p>
            <div class="ano-sel" id="anoSel" role="group" aria-label="Ano em destaque no gráfico"><span>Ver o ano</span>${ANOS.map(a => `<button type="button" data-ano="${a}" aria-pressed="${a === '2033'}">${a}</button>`).join('')}</div>
            <div class="efeito-linha" id="efeitoLinha" aria-live="polite"></div>
            <div class="leitura-dados"><h4>Como a reforma tributária afeta a receita de ${nomeSeg}?</h4>${leituraMunicipio(m, base)}</div>
        </div>
        ${painelSeguro}
        <h3 class="capitulo" id="cap-porque">Por que o resultado é este</h3>
        <div class="panel" id="painelDecomp" hidden><h3 id="decompTit">O que explica a diferença</h3><p class="panel-sub">A diferença entre a receita com e sem reforma vem de quatro fontes. Cada barra mostra quanto uma delas soma ou subtrai, no ano escolhido no gráfico.</p><div id="decompCorpo"></div></div>
        ${painelParticipacaoHtml(m, base)}
        <div class="panel">
            <div class="panel-head"><div><h3>De onde vem a receita</h3><p class="panel-sub">Quanto ainda vem do ISS e da cota-parte do ICMS e quanto já vem do IBS, de 2029 a 2033.</p></div>
                <div class="comp-controles">
                    <div class="toggle" id="compModo" role="group" aria-label="Unidade"><button type="button" data-modo="pct" class="active">%</button><button type="button" data-modo="rs">R$</button></div>
                    <div class="toggle" id="compViz" role="group" aria-label="Forma"><button type="button" data-viz="grafico" class="active">Gráfico</button><button type="button" data-viz="tabela">Tabela</button></div>
                </div></div>
            <div class="canvas-box" id="compBox"><canvas id="gComp" role="img" aria-label="Gráfico de barras empilhadas com a composição da receita projetada de 2029 a 2033: ISS e cota-parte do ICMS residuais, IBS pelo critério histórico, IBS por destino e Seguro-Receita. Os mesmos valores estão na aba Tabela."></canvas></div>
            <div class="table-wrap" id="compTabela" hidden></div>
            <p class="nota nota-grafico">* Inclui a cota-parte dos municípios: no critério histórico, a cota-parte do ICMS que o município já recebia; no critério de destino, os 25% do IBS do estado repassados às prefeituras. <a href="#" data-tab="metodologia" data-depois="met-3">Entenda →</a></p>
        </div>
        <div class="panel" id="painelSens" hidden>
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
        <h3 class="capitulo" id="cap-compara">Como ${nomeSeg} se compara</h3>
        <div class="ficha-grid ficha-contexto">
            <div class="panel"><h3>Posição no ranking</h3><p class="panel-sub">Posição na variação da receita em 2033.</p>${posicao}</div>
            <div class="panel"><h3>${nomeSeg} no mapa ${DE_UF[base.uf]}</h3><p class="panel-sub">Contornado; a cor mostra a variação em 2033.</p>
                <div class="map-wrapper" id="miniWrap"><svg id="miniSvg" role="img" aria-label="Mapa dos municípios ${DE_UF[base.uf]} com ${nomeSeg} contornado."></svg><div class="map-tip" id="miniTip" role="tooltip"></div></div></div>
        </div>
        <div class="detalhes" id="cap-detalhes">
            <h3 class="detalhes-tit">Detalhes do cálculo</h3>
            <details><summary>Ano a ano, 2029–2033</summary>
                <div class="table-wrap"><table class="dados"><thead><tr><th>Ano</th><th>Sem a reforma</th><th>Com a reforma</th><th>Diferença</th><th>Variação</th></tr></thead><tbody>${linhas}</tbody></table></div></details>
            <details id="detCoef"><summary>Coeficientes: histórico e de destino</summary>
                <p class="panel-sub">O coeficiente histórico e o de destino, ponderados pelo cronograma do ADCT (o histórico rege 80% do IBS até 2032 e 90% em 2033; o de destino, o que sobra depois do Seguro-Receita: 19% e 9,5%), definem a fatia deste município no IBS. A participação de referência de 2025 não entra nessa fatia: é a base do cenário sem reforma.</p>${coefTilesHtml(m)}</details>
            ${seg33 > 0 ? '' : `<details><summary>Seguro-Receita</summary>
                <p class="panel-sub">O fundo equivale a 5% do IBS que não é distribuído pelo critério histórico e é repartido entre os entes de menor razão entre o IBS pelo destino e a receita média de referência, até igualar essa razão.</p>${seguroCardHtml(m.repasse_seguro_receita_por_ano, m.pos_por_ano)}</details>`}
            <details id="detHist"><summary>Receita de referência: ISS e cota-parte do ICMS</summary>
                <p class="panel-sub">É a receita de referência do município, na definição da lei (LC 227/2026, art. 115): o ISS que ele arrecada e a cota-parte do ICMS que recebe do estado (SICONFI, DCA). A média dos oito anos de 2019 a 2026, com 2026 estimado, é a base do coeficiente histórico. <a href="#" data-abrir="detCoef">Ver o coeficiente histórico →</a></p>${historicoTableHtml(m.historico_por_ano, m.estimativa_2026)}</details>
            <button type="button" class="memo-link" id="btnMemoria">Ver a memória de cálculo deste município →</button>
        </div>
        <div class="panel proximos" id="cap-proximos"><h3>E agora?</h3><p class="panel-sub">Leve este resultado adiante ou acompanhe os próximos passos da reforma.</p>
            <div class="acoes-fim"><button class="btn btn-gold" type="button" id="btnPdf">Salvar em PDF</button><button class="btn btn-ghost" type="button" id="btnCompartilhar">Compartilhar</button><a class="btn btn-ghost" href="#" data-tab="agenda">Ver os prazos da reforma</a>${CONFIG.whatsapp ? `<a class="btn btn-ghost" data-contato="whatsapp" href="https://wa.me/${CONFIG.whatsapp}?text=${encodeURIComponent('Olá! Vim pelo painel Municípios na Reforma e tenho uma pergunta sobre ' + base.nome + '/' + base.uf + '.')}" target="_blank" rel="noopener">Enviar uma pergunta ou correção</a>` : ''}</div></div>
        <p class="print-credito">Municípios na Reforma · municipiosnareforma.com.br${CONFIG.email ? ' · ' + CONFIG.email : ''}</p>`;

    $('btnMemoria').addEventListener('click', () => { track('abrir_memoria', {municipio_codigo: cod}); abrirMemoria(cod); });
    document.querySelectorAll('#cap-proximos [data-contato]').forEach(a => a.addEventListener('click', () => track('clique_contato', {canal: a.dataset.contato, municipio_codigo: cod, local: 'ficha'})));
    $('btnCopiar').addEventListener('click', e => {
        const url = location.origin + location.pathname + '?m=' + cod;
        (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(() => { e.target.textContent = 'Link copiado'; }, () => { prompt('Copie o link:', url); });
        track('copiar_link', {municipio_codigo: cod});
    });
    $('btnImprimir').addEventListener('click', () => { track('imprimir_ficha', {municipio_codigo: cod}); window.print(); });
    $('btnPdf').addEventListener('click', () => { track('imprimir_ficha', {municipio_codigo: cod}); window.print(); });
    $('btnCompartilhar').addEventListener('click', () => {
        const url = location.origin + location.pathname + '?m=' + cod, texto = base.nome + ': ' + fmtPct(v33) + ' na receita em 2033 com a reforma tributária (estimativa).';
        track('compartilhar', {municipio_codigo: cod});
        if (navigator.share) navigator.share({title: 'Municípios na Reforma', text: texto, url}).catch(() => {});
        else window.open('https://wa.me/?text=' + encodeURIComponent(texto + ' ' + url), '_blank', 'noopener');
    });
    const efeitoAno = ano => {
        const v = m.variacao_por_ano[ano], d = m.pos_por_ano[ano] - m.contrafactual_por_ano[ano], sg = (m.repasse_seguro_receita_por_ano || {})[ano] || 0;
        const neu = Math.abs(v) <= 0.0005, cls = clsSinal(v);
        const tag = sg > 0 && v > 0.0005 && seguroEfetivo(m, ano) > d ? '<span class="tag-seg">Depende do Seguro-Receita</span>' : sg > 0 ? '<span class="tag-seg tag-seg-leve">Recebe Seguro-Receita</span>' : '';
        return `<div class="efeito ${cls}"><em class="selo">${neu ? 'Receita estável' : v < 0 ? 'Perda estimada' : 'Ganho estimado'}</em><b>${fmtPct(v)}</b><span>em ${ano}</span><span>${neu ? '' : (d > 0 ? '+' : '') + fmtMoney(d) + ' ao ano'}</span>${tag}</div>`;
    };
    const selecionarAno = ano => {
        $('efeitoLinha').innerHTML = efeitoAno(ano);
        document.querySelectorAll('#anoSel button').forEach(b => b.setAttribute('aria-pressed', b.dataset.ano === ano));
        if (grafSerie) { grafSerie.anoSel = ano; grafSerie.draw(); }
        const dh = decompHtml(m, ano), pd = $('painelDecomp');
        if (pd) { pd.hidden = !dh; $('decompCorpo').innerHTML = dh; $('decompTit').textContent = 'O que explica a diferença em ' + ano; }
    };
    document.querySelectorAll('#anoSel button').forEach(b => b.addEventListener('click', () => selecionarAno(b.dataset.ano)));
    const mais = $('leituraMais'), larga = matchMedia('(min-width: 900px)');
    if (mais) { mais.open = larga.matches; larga.onchange = e => { mais.open = e.matches; }; }
    desenharGraficos(m, selecionarAno);
    selecionarAno('2033');
    iniciarSens(cod, base, m);
    carregarMalha().then(() => {
        if (ATUAL !== cod || !$('miniSvg')) return;
        MINI = criarMapa($('miniSvg'), $('miniWrap'), $('miniTip'), {camadaUF: false, todos: false, uf: base.uf, nivel: 'muni', aoClicar: c => abrirMunicipio(c)});
        MINI.destacar(cod);
        PIN = {cod, nome: base.nome}; requestAnimationFrame(marcarPin);
    }).catch(() => { const w = $('miniWrap'); if (w) w.innerHTML = '<p class="nota">O mapa não pôde ser carregado agora.</p>'; });
    $('fichaTitulo').focus({preventScroll: true});
}

/* ── sensibilidade: o mesmo teste do painel dos estados, agora por município ──
   Com a reforma = residual×ref + histórico×φCPT×(1−ca) + destino×φdest×(1±erro) + repasse×(1−ca);
   sem a reforma = ref × bolo projetado, em que ref é a fatia do município no ano-base escolhido. Com ref de 2025 e destino
   central, reproduz a variação publicada. A fatia de cada ano é a de 2025 (coef_neutro) escalada pela receita real do
   município naquele ano em relação a 2025 (série deflacionada da ficha; 2026 é a estimativa). A margem de erro do destino
   é a medida para a UF (sensibilidade-uf.json). */
let GSENS = null, GPART = null, SENS_UF = null, SENS_P = null;
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
            track('sens_ano_base', {municipio_codigo: cod, ano: r}); desenharSens();
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
    ds.push(Object.assign({label: 'Base 2025 (a do painel)', data: calc.linhas['2025'].map(x => pc(x.c)), borderColor: '#062254', backgroundColor: '#062254', pointBackgroundColor: '#062254', pointRadius: 4}, linha, {pointRadius: 4, borderWidth: 3}));

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

const COMP_ROTULOS = [['origem', 'ISS e cota-parte do ICMS residuais', '#858384'], ['cpt', 'IBS pelo critério histórico*', '#0f508e'], ['destino', 'IBS por destino*', '#6aa8dd'], ['seguro', 'Seguro-Receita', '#249266']];

function desenharGraficos(m, aoEscolherAno) {
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
    // O eixo traz só o 2025 realizado (de onde o contrafactual é construído) e segue direto para 2029–2033, sem espaço para 2026–2028
    // (o modelo não projeta esses anos). A série de 2019 a 2025 fica em Detalhes do cálculo: no mesmo gráfico, ela triplica a
    // amplitude do eixo e achata a diferença entre os cenários, que é o que a página quer mostrar.
    const rotulos = ['2025'].concat(ANOS);
    const estreito = $('gSerie').parentElement.clientWidth < 520;      // no celular, todos os anos, na diagonal e menores (como no painel dos estados)
    const cenario = serie => rotulos.map(a => a === '2025' ? mi(m.pre_2025) : (ANOS.includes(a) && serie[a] != null ? mi(serie[a]) : null));
    // Desenho do painel dos estados: linha fina, ponto de 4 px com anel de 2 px na cor da superfície (continua legível onde as séries
    // se tocam), área de acerto folgada para o toque, grade só na horizontal e sem eixo vertical.
    const linha = {borderWidth: 2, spanGaps: false, tension: 0.1, pointRadius: 4, pointHoverRadius: 6, pointBorderWidth: 2, pointBorderColor: '#fff', hitRadius: 14};
    // Rótulos diretos no lugar da legenda: o valor de cada cenário em 2033 e o de 2025, ao lado dos pontos.
    const rotulosDiretos = {id: 'rotulosDiretos',
        beforeDatasetsDraw(chart) {   // faixa dos anos sem projeção (2026 a 2028), para o salto do eixo não parecer continuidade
            const ctx = chart.ctx, ca = chart.chartArea, i25 = rotulos.indexOf('2025');
            if (i25 < 0 || !rotulos[i25 + 1]) return;
            const x0 = chart.scales.x.getPixelForValue(i25), x1 = chart.scales.x.getPixelForValue(i25 + 1);
            ctx.save(); ctx.fillStyle = 'rgba(107,107,107,.08)'; ctx.fillRect(x0, ca.top, x1 - x0, ca.bottom - ca.top);
            ctx.restore();
        },
        afterDatasetsDraw(chart) {
            const ctx = chart.ctx, fs = estreito ? 11 : 12, ult = rotulos.length - 1, i25 = rotulos.indexOf('2025');
            const texto = (x, y, t, cor, peso, tam, al) => { ctx.font = peso + ' ' + tam + 'px Inter, system-ui, sans-serif'; ctx.fillStyle = cor; ctx.textAlign = al || 'left'; ctx.fillText(t, x, y); };
            ctx.save();
            const pos = chart.getDatasetMeta(0).data[ult], cf = chart.getDatasetMeta(1).data[ult], p25 = chart.getDatasetMeta(0).data[i25];
            if (pos && cf) {
                const ganha = pos.y <= cf.y, v = m.variacao_por_ano['2033'];
                const blocoPos = ganha ? [pos.y - 16, pos.y - 4] : [pos.y + 14, pos.y + 26], blocoCf = ganha ? [cf.y + 14, cf.y + 26] : [cf.y - 16, cf.y - 4];
                texto(pos.x + 10, blocoPos[0], fmtMoneyFino(m.pos_por_ano['2033']), '#8a6508', 700, fs); texto(pos.x + 10, blocoPos[1], 'com a reforma', '#8a6508', 500, fs - 1);
                texto(cf.x + 10, blocoCf[0], fmtMoneyFino(m.contrafactual_por_ano['2033']), '#555', 700, fs); texto(cf.x + 10, blocoCf[1], 'sem a reforma', '#555', 500, fs - 1);
                if (Math.abs(v) > 0.0005) {   // colchete com a diferença entre os dois cenários em 2033
                    const cor = v < 0 ? '#a02525' : '#1c5cab', topo = Math.min(pos.y, cf.y), base = Math.max(pos.y, cf.y);
                    ctx.strokeStyle = cor; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(pos.x + 6, topo); ctx.lineTo(pos.x + 6, base); ctx.stroke();
                    texto(pos.x + 10, base + 44, fmtPct(v), cor, 800, fs + 1);
                }
            }
            const iSel = rotulos.indexOf(chart.anoSel || '2033');
            if (iSel > 0 && iSel < ult) {   // ano escolhido no meio da série: guia vertical e colchete com a diferença
                const a = chart.getDatasetMeta(0).data[iSel], b = chart.getDatasetMeta(1).data[iSel];
                if (a && b) {
                    const cor = m.variacao_por_ano[rotulos[iSel]] < 0 ? '#a02525' : '#1c5cab';
                    ctx.setLineDash([3, 4]); ctx.strokeStyle = '#b9c1c8'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(a.x, chart.chartArea.top); ctx.lineTo(a.x, chart.chartArea.bottom); ctx.stroke(); ctx.setLineDash([]);
                    ctx.strokeStyle = cor; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(a.x, b.y); ctx.stroke();
                    ctx.fillStyle = '#fff'; ctx.strokeStyle = cor; ctx.lineWidth = 2.5;
                    [a, b].forEach(pt => { ctx.beginPath(); ctx.arc(pt.x, pt.y, 6, 0, 7); ctx.fill(); ctx.stroke(); });
                }
            }
            if (p25) { const y = Math.min(p25.y + 20, chart.chartArea.bottom - 14); texto(p25.x + 10, y, fmtMoneyFino(m.pre_2025), '#062254', 700, fs); texto(p25.x + 10, y + 12, 'realizado em 2025', '#062254', 500, fs - 1); }
            ctx.restore();
        }};
    grafSerie = new Chart($('gSerie'), {
        type: 'line',
        data: {labels: rotulos, datasets: [
            Object.assign({label: 'Projeção com a reforma', data: cenario(m.pos_por_ano), borderColor: '#b8860b', backgroundColor: 'rgba(252,187,27,.2)', pointBackgroundColor: '#b8860b', fill: '+1'}, linha),
            Object.assign({label: 'Cenário sem a reforma', data: cenario(m.contrafactual_por_ano), borderColor: '#6b6b6b', backgroundColor: '#6b6b6b', pointBackgroundColor: '#6b6b6b', borderDash: [5, 4], fill: false}, linha)
        ]},
        options: {responsive: true, maintainAspectRatio: false, interaction: {mode: 'index', intersect: false},
            onClick: (ev, _, chart) => { const el = chart.getElementsAtEventForMode(ev, 'index', {intersect: false}, false)[0]; if (el && el.index > 0 && aoEscolherAno) aoEscolherAno(rotulos[el.index]); },
            plugins: {legend: {display: false}, tooltip: tip},
            layout: {padding: {right: estreito ? 90 : 104}},
            scales: {y: {grid: {color: '#e9edf0', drawTicks: false}, border: {display: false}, beginAtZero: false, grace: '12%', ticks: {maxTicksLimit: 6, callback: v => fmtMoney(v * 1e6), color: '#6b6b6b', font: {size: 11}, padding: 8}},
                x: {grid: {display: false}, border: {color: '#c8d0d6'}, ticks: {maxRotation: estreito ? 55 : 0, minRotation: estreito ? 55 : 0, autoSkip: false, font: {size: estreito ? 10 : 11}, color: '#6b6b6b', padding: 6}}}}
        , plugins: [rotulosDiretos]
    });
    graficos.push(grafSerie);
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
    desenhaParticipacao(m);
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
                aceite_privacidade: true, versao_termos: VERSAO_TERMOS
            })});
            if (!r.ok) throw new Error('lead ' + r.status);
            lembrarCadastro();
            track('cadastro', {origem: 'memoria', municipio_codigo: base ? base.cod : ''});
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


/* Botão flutuante do WhatsApp: canal de contato fora das fichas e dos dados. A mensagem leva o município em foco. */
function iniciarZap() {
    const zap = $('zap');
    if (!CONFIG.whatsapp) return;
    zap.hidden = false;
    const mensagem = () => {
        const m = municipioEmFoco();
        return m ? 'Olá! Vim pelo painel Municípios na Reforma e tenho uma pergunta sobre ' + m.nome + '/' + m.uf + '.'
                 : 'Olá! Vim pelo painel Municípios na Reforma e tenho uma pergunta.';
    };
    const atualizar = () => { zap.href = 'https://wa.me/' + CONFIG.whatsapp + '?text=' + encodeURIComponent(mensagem()); };
    atualizar();
    ['pointerdown', 'focus', 'mouseover'].forEach(ev => zap.addEventListener(ev, atualizar));      // o link já sai atualizado no toque ou no clique
    zap.addEventListener('click', () => { atualizar(); const m = municipioEmFoco(); track('clique_contato', {canal: 'whatsapp', municipio_codigo: m ? m.cod : '', local: 'flutuante'}); });
}


const municipioEmFoco = () => {
    const cod = ATUAL || (LOCAL && LOCAL.cod);
    return cod && POR_COD[cod] ? POR_COD[cod] : null;
};
iniciarZap();
$('btnVoltar').addEventListener('click', () => mostrarVisao('visao-geral'));
/* Ao imprimir, os detalhes do cálculo saem abertos; depois voltam ao estado em que estavam. */
let ABERTOS_ANTES = null;
window.addEventListener('beforeprint', () => { const ds = [...document.querySelectorAll('.detalhes details')]; ABERTOS_ANTES = ds.map(d => d.open); ds.forEach(d => { d.open = true; }); });
window.addEventListener('afterprint', () => { if (ABERTOS_ANTES) [...document.querySelectorAll('.detalhes details')].forEach((d, i) => { d.open = ABERTOS_ANTES[i]; }); ABERTOS_ANTES = null; });
if (CONFIG.razaoSocial) $('privControlador').textContent = CONFIG.razaoSocial + (CONFIG.cnpj ? ' (CNPJ ' + CONFIG.cnpj + ')' : '');
if (CONFIG.email) $('privContato').textContent = CONFIG.email;
})();
