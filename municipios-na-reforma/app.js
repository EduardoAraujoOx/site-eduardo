/* Municípios na Reforma.
   Lê os mesmos JSONs do painel da reforma tributária (/data/), de modo que qualquer
   melhoria metodológica regenerada em data/ aparece aqui no mesmo deploy. Nenhum
   número de resultado é escrito à mão neste arquivo. */
(function () {
'use strict';

/* ── CONFIGURAÇÃO COMERCIAL: preencher antes da campanha ─────────────────── */
const CONFIG = {
    whatsapp: '',   // somente dígitos com DDI e DDD, ex.: '5527999999999'
    email: '',      // ex.: 'fale@municipiosnareforma.com.br'
    gaId: ''        // ex.: 'G-XXXXXXXXXX' (Google Analytics 4), opcional
};

const ANOS = ['2029', '2030', '2031', '2032', '2033'];
const ANOS_HIST = ['2019', '2020', '2021', '2022', '2023', '2024', '2025'];
const NOMES_UF = {AC:'Acre',AL:'Alagoas',AM:'Amazonas',AP:'Amapá',BA:'Bahia',CE:'Ceará',DF:'Distrito Federal',ES:'Espírito Santo',GO:'Goiás',MA:'Maranhão',MG:'Minas Gerais',MS:'Mato Grosso do Sul',MT:'Mato Grosso',PA:'Pará',PB:'Paraíba',PE:'Pernambuco',PI:'Piauí',PR:'Paraná',RJ:'Rio de Janeiro',RN:'Rio Grande do Norte',RO:'Rondônia',RR:'Roraima',RS:'Rio Grande do Sul',SC:'Santa Catarina',SE:'Sergipe',SP:'São Paulo',TO:'Tocantins'};
const UF_POR_PREFIXO = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'};

/* Sete faixas fixas, as mesmas do painel: a variação vai de −74% a +265%, e num
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
const COR_RESSALVA = '#b9bec2', COR_SEM_ESFERA = '#e8ecef', ROTULO_RESSALVA = 'Sem dado confiável';

/* ── formatação (mesmas regras do painel) ── */
const fmtPct = v => {
    if (v == null || !isFinite(v)) return '—';
    const p = Math.round(v * 1000) / 10;                  // o sinal sai do valor já arredondado
    return (p > 0 ? '+' : p < 0 ? '−' : '') + Math.abs(p).toLocaleString('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1}) + '%';
};
const fmtPctSimples = v => Math.round(v * 100).toLocaleString('pt-BR') + '%';
const clsSinal = v => v == null ? '' : v < -0.0005 ? 'neg' : v > 0.0005 ? 'pos' : '';
function fmtMoney(v) {
    if (v == null || !isFinite(v)) return '—';
    const a = Math.abs(v), s = v < 0 ? '−' : '';
    if (a >= 1e9) return s + 'R$ ' + (a / 1e9).toLocaleString('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1}) + ' bi';
    if (a >= 1e6) return s + 'R$ ' + (a / 1e6).toLocaleString('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1}) + ' mi';
    if (a >= 1e3) return s + 'R$ ' + Math.round(a / 1e3).toLocaleString('pt-BR') + ' mil';
    return s + 'R$ ' + Math.round(a).toLocaleString('pt-BR');
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
let LISTA = [], POR_COD = {}, RESULT = null;
let ESCOPO = 'BR', ATUAL = null, MAPA = null, MINI = null, graficos = [];
const CACHE_UF = new Map();
const GEO = {dados: null, promessa: null};

/* ── abas ── */
function mostrarVisao(v) {
    document.querySelectorAll('.view').forEach(s => s.classList.toggle('active', s.id === 'view-' + v));
    document.querySelectorAll('.tab-btn').forEach(b => {
        const on = b.dataset.view === v;
        b.classList.toggle('active', on);
        if (on) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
    });
    window.scrollTo({top: 0});
}
document.querySelectorAll('.tab-btn').forEach(b => b.addEventListener('click', () => { mostrarVisao(b.dataset.view); track('aba', {aba: b.dataset.view}); }));
document.querySelectorAll('[data-ir]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); mostrarVisao(a.dataset.ir); }));

/* ── carga ── */
Promise.all([getJSON('/data/painel-municipios/index.json'), getJSON('/data/resultados-consolidados-ibs.json').catch(() => null)])
    .then(([idx, res]) => iniciar(idx, res))
    .catch(e => { console.error(e); $('dicaBusca').textContent = 'Não foi possível carregar a base de municípios. Atualize a página em instantes.'; });

function iniciar(idx, res) {
    LISTA = Object.entries(idx.municipios).map(([cod, m]) => ({cod, nome: m.nome, uf: m.uf, v: m.v, r: !!m.r, chave: norm(m.nome)}));
    LISTA.forEach(m => { POR_COD[m.cod] = m; });
    RESULT = res;

    $('mapaUF').innerHTML = '<option value="BR">Brasil</option>' + Object.keys(NOMES_UF)
        .sort((a, b) => NOMES_UF[a].localeCompare(NOMES_UF[b], 'pt-BR'))
        .map(u => `<option value="${u}">${NOMES_UF[u]}</option>`).join('');
    $('mapaUF').addEventListener('change', e => { definirEscopo(e.target.value); track('mapa_uf', {uf: e.target.value}); });
    document.querySelectorAll('#toggleViz button').forEach(b => b.addEventListener('click', () => {
        const tabela = b.dataset.viz === 'tabela';
        document.querySelectorAll('#toggleViz button').forEach(x => x.classList.toggle('active', x === b));
        $('mapaWrap').hidden = tabela; $('mapaLegenda').hidden = tabela; $('mapaTabela').hidden = !tabela;
    }));

    ativarBusca($('busca'), $('sugestoes'), $('formBusca'));
    ativarBusca($('buscaMuni'), $('sugestoesMuni'), $('formBuscaMuni'));
    $('dicaBusca').textContent = 'Base com ' + fmtInt(LISTA.length) + ' municípios. Comece a digitar e escolha na lista.';
    definirEscopo('BR');
    montarRankings();

    carregarMalha().then(() => {
        MAPA = criarMapa($('mapaSvg'), $('mapaWrap'), $('mapaTip'), {todos: true, uf: ESCOPO, aoClicar: cod => abrirMunicipio(cod)});
        $('mapaCarregando').hidden = true; $('mapaSvg').removeAttribute('hidden');   // SVGElement não tem a propriedade hidden
        if (ATUAL) MAPA.destacar(ATUAL);
    }).catch(() => { $('mapaCarregando').textContent = 'O mapa não pôde ser carregado agora. Use a busca por município ou a lista ao lado.'; });

    const cod = new URLSearchParams(location.search).get('m');
    if (cod && POR_COD[cod]) abrirMunicipio(cod, {semUrl: true});
}

/* ── escopo (Brasil ou UF) ── */
function definirEscopo(uf) {
    ESCOPO = uf;
    $('mapaUF').value = uf;
    if (MAPA) MAPA.definirUF(uf);
    renderLegenda(); renderTrilho(); renderContexto();
}

function noEscopo() { return LISTA.filter(m => ESCOPO === 'BR' || m.uf === ESCOPO); }

function renderLegenda() {
    const escopo = noEscopo(), cont = {};
    escopo.forEach(m => { const c = classeDe(m); cont[c.rotulo] = (cont[c.rotulo] || 0) + 1; });
    const itens = CLASSES.map(c => [c.cor, c.rotulo]).concat([[COR_RESSALVA, ROTULO_RESSALVA]]);
    $('mapaLegenda').innerHTML = itens.map(([cor, rot]) => `<li><i style="background:${cor}"></i>${rot} <b>${fmtInt(cont[rot] || 0)}</b></li>`).join('');
    $('mapaTabela').innerHTML = `<table class="dados"><thead><tr><th>Faixa de variação em 2033</th><th>Municípios</th><th>Do total</th></tr></thead><tbody>`
        + itens.map(([cor, rot]) => `<tr><td class="nome"><i style="background:${cor};display:inline-block;width:.9rem;height:.7rem;border:1px solid rgba(0,0,0,.12);margin-right:.5rem"></i>${rot}</td><td>${fmtInt(cont[rot] || 0)}</td><td>${fmtPctSimples((cont[rot] || 0) / escopo.length)}</td></tr>`).join('') + '</tbody></table>';
}

/* Lista lateral: no Brasil, os estados pela variação agregada da receita municipal; num estado, os municípios. */
function renderTrilho() {
    const head = $('trilhoHead'), lista = $('trilhoLista');
    if (ESCOPO === 'BR') {
        head.textContent = 'Estados, do maior ganho à maior perda';
        const agg = RESULT && RESULT.variacao_municipal_por_uf_2033;
        const linhas = Object.keys(NOMES_UF).filter(u => LISTA.some(m => m.uf === u)).map(u => {
            const ok = LISTA.filter(m => m.uf === u && !m.r), perdem = ok.filter(m => m.v < 0).length;
            return {uf: u, v: agg && agg[u] != null ? agg[u] : null, perdem, n: ok.length};
        }).sort((a, b) => agg ? b.v - a.v : (b.perdem / b.n) - (a.perdem / a.n));
        const max = Math.max(...linhas.map(l => Math.abs(l.v || 0)), 0.01);
        lista.innerHTML = linhas.map((l, i) => `<button type="button" class="rail-row" data-uf="${l.uf}">
            <span class="rk">${i + 1}</span><span class="nm">${NOMES_UF[l.uf]}<small>${fmtInt(l.perdem)} de ${fmtInt(l.n)} prefeituras perdem</small></span>
            <span class="vl ${clsSinal(l.v)}">${fmtPct(l.v)}</span>${l.v != null ? `<i class="bar ${clsSinal(l.v)}" style="width:${Math.max(2, Math.abs(l.v) / max * 62)}%"></i>` : ''}</button>`).join('');
        lista.querySelectorAll('[data-uf]').forEach(b => b.addEventListener('click', () => { definirEscopo(b.dataset.uf); track('trilho_uf', {uf: b.dataset.uf}); }));
    } else {
        head.innerHTML = `<button type="button" id="voltaBR">← Brasil</button>${esc(NOMES_UF[ESCOPO])}: municípios, do maior ganho à maior perda`;
        $('voltaBR').addEventListener('click', () => definirEscopo('BR'));
        const ok = noEscopo().filter(m => !m.r).sort((a, b) => b.v - a.v);
        const sem = noEscopo().filter(m => m.r).sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
        const linha = (m, i) => `<button type="button" class="rail-row${m.r ? ' semdado' : ''}" data-cod="${m.cod}">
            <span class="rk">${m.r ? '' : i + 1}</span><span class="nm">${esc(m.nome)}${m.r ? '<small>sem dado confiável</small>' : ''}</span>
            <span class="vl ${m.r ? '' : clsSinal(m.v)}">${m.r ? '—' : fmtPct(m.v)}</span>${m.r ? '' : `<i class="bar ${clsSinal(m.v)}" style="width:${Math.max(2, Math.min(Math.abs(m.v) / 0.6, 1) * 62)}%"></i>`}</button>`;
        lista.innerHTML = ok.map(linha).join('') + sem.map(linha).join('');
        lista.scrollTop = 0;
        lista.querySelectorAll('[data-cod]').forEach(b => b.addEventListener('click', () => { track('trilho_municipio', {municipio: POR_COD[b.dataset.cod].nome}); abrirMunicipio(b.dataset.cod); }));
    }
}

function renderContexto() {
    const escopo = noEscopo(), ok = escopo.filter(m => !m.r), perdem = ok.filter(m => m.v < 0).length;
    const ord = ok.map(m => m.v).sort((a, b) => a - b);
    const mediana = ord.length % 2 ? ord[(ord.length - 1) / 2] : (ord[ord.length / 2 - 1] + ord[ord.length / 2]) / 2;
    const agg = RESULT && RESULT.variacao_municipal_por_uf_2033;
    const nome = ESCOPO === 'BR' ? 'No Brasil' : 'Em ' + NOMES_UF[ESCOPO];
    const partes = [
        `<span>${nome}: <b>${fmtInt(escopo.length)}</b> municípios analisados</span>`,
        `<span><b class="neg">${fmtInt(perdem)}</b> de ${fmtInt(ok.length)} com dados confiáveis (<b>${fmtPctSimples(perdem / ok.length)}</b>) arrecadam menos em 2033 do que arrecadariam sem a reforma</span>`,
        `<span>Variação mediana: <b class="${clsSinal(mediana)}">${fmtPct(mediana)}</b></span>`
    ];
    if (ESCOPO !== 'BR' && agg && agg[ESCOPO] != null) partes.push(`<span>Receita municipal agregada de ${esc(NOMES_UF[ESCOPO])}: <b class="${clsSinal(agg[ESCOPO])}">${fmtPct(agg[ESCOPO])}</b></span>`);
    $('contexto').innerHTML = partes.join('');
}

/* ── rankings ── */
function montarRankings() {
    const agg = RESULT && RESULT.variacao_municipal_por_uf_2033;
    const linhas = Object.keys(NOMES_UF).filter(u => LISTA.some(m => m.uf === u)).map(u => {
        const ok = LISTA.filter(m => m.uf === u && !m.r), perdem = ok.filter(m => m.v < 0).length;
        return {uf: u, v: agg && agg[u] != null ? agg[u] : null, perdem, n: ok.length, total: LISTA.filter(m => m.uf === u).length};
    }).sort((a, b) => agg ? b.v - a.v : (b.perdem / b.n) - (a.perdem / a.n));
    $('tabUF').querySelector('tbody').innerHTML = linhas.map((l, i) => `<tr class="clicavel" data-uf="${l.uf}"><td>${i + 1}</td><td class="nome">${NOMES_UF[l.uf]}</td><td>${fmtInt(l.total)}</td><td>${fmtInt(l.perdem)} de ${fmtInt(l.n)} (${fmtPctSimples(l.perdem / l.n)})</td><td class="${clsSinal(l.v)}">${fmtPct(l.v)}</td></tr>`).join('');
    $('tabUF').querySelectorAll('tr[data-uf]').forEach(tr => tr.addEventListener('click', () => { definirEscopo(tr.dataset.uf); mostrarVisao('visao-geral'); }));

    const d = RESULT && RESULT.destaques_municipios_2033;
    const cr = RESULT && RESULT.criterios_destaque_municipal;
    if (!d) { ['tabPerdas', 'tabGanhos'].forEach(id => { $(id).querySelector('tbody').innerHTML = '<tr><td colspan="4" class="vazio-td">Ranking indisponível no momento.</td></tr>'; }); return; }
    if (cr) $('critRank').textContent = `Municípios com ao menos ${fmtInt(cr.populacao_min)} habitantes e ${cr.cobertura_anos_min} anos de dados, sem ressalva de qualidade, do maior para o menor impacto.`;
    const corpo = lista => lista.map(m => `<tr class="clicavel" data-cod="${m.cod}"><td class="nome">${esc(m.nome)}<small>${m.uf}</small></td><td>${fmtMoney(m.contrafactual_2033)}</td><td>${fmtMoney(m.pos_2033)}</td><td class="${clsSinal(m.variacao_2033)}">${fmtPct(m.variacao_2033)}</td></tr>`).join('');
    $('tabPerdas').querySelector('tbody').innerHTML = corpo(d.maiores_perdas);
    $('tabGanhos').querySelector('tbody').innerHTML = corpo(d.maiores_ganhos);
    ['tabPerdas', 'tabGanhos'].forEach(id => $(id).querySelectorAll('tr[data-cod]').forEach(tr => tr.addEventListener('click', () => abrirMunicipio(tr.dataset.cod))));
}

/* ── busca (padrão combobox), reaproveitada nas duas abas ── */
function ativarBusca(inp, ul, form) {
    inp.disabled = false;
    let sugestoes = [], ativo = -1;
    const fechar = () => { ul.hidden = true; inp.setAttribute('aria-expanded', 'false'); inp.removeAttribute('aria-activedescendant'); ativo = -1; };
    const marcar = i => {
        ativo = i;
        [...ul.children].forEach((li, k) => li.setAttribute('aria-selected', k === i ? 'true' : 'false'));
        if (i >= 0) inp.setAttribute('aria-activedescendant', ul.children[i].id); else inp.removeAttribute('aria-activedescendant');
    };
    const buscar = () => {
        const q = norm(inp.value);
        if (q.length < 2) { fechar(); return; }
        const comp = q.split(/\s+/);
        sugestoes = LISTA
            .map(m => {
                const alvo = m.chave + ' ' + m.uf.toLowerCase();
                if (!comp.every(c => alvo.includes(c))) return null;
                return {m, ordem: m.chave.startsWith(q) ? 0 : m.chave.split(' ').some(w => w.startsWith(comp[0])) ? 1 : 2};
            })
            .filter(Boolean)
            .sort((a, b) => a.ordem - b.ordem || a.m.nome.localeCompare(b.m.nome, 'pt-BR'))
            .slice(0, 8).map(x => x.m);
        ul.innerHTML = sugestoes.length
            ? sugestoes.map((m, i) => `<li role="option" id="${ul.id}-${i}" data-cod="${m.cod}" aria-selected="false">${esc(m.nome)}<small>${m.uf}</small></li>`).join('')
            : '<li class="vazio-li" role="option" aria-disabled="true">Nenhum município encontrado. Confira a grafia.</li>';
        ul.hidden = false; inp.setAttribute('aria-expanded', 'true'); ativo = -1;
    };
    const escolher = cod => {
        fechar();
        track('busca_municipio', {municipio: POR_COD[cod].nome, uf: POR_COD[cod].uf});
        abrirMunicipio(cod);
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
        if (!sugestoes.length) buscar();
        const alvo = sugestoes[ativo >= 0 ? ativo : 0];
        if (alvo) escolher(alvo.cod);
    });
}

/* ── mapa ── */
function carregarMalha() {
    if (GEO.promessa) return GEO.promessa;
    if (typeof d3 === 'undefined') return Promise.reject(new Error('d3 indisponível'));
    GEO.promessa = getJSON('/data/malha-municipios.json').then(geo => {
        geo.features.forEach(f => { f.properties.uf = UF_POR_PREFIXO[f.properties.cod.slice(0, 2)]; });
        GEO.dados = geo; return geo;
    });
    GEO.promessa.catch(() => { GEO.promessa = null; });
    return GEO.promessa;
}

/* Um mapa independente por instância: o principal (Brasil inteiro) e o minimapa da ficha (só a UF). */
function criarMapa(svgEl, wrapEl, tipEl, opt) {
    const feats = opt.todos ? GEO.dados.features : GEO.dados.features.filter(f => f.properties.uf === opt.uf);
    const W = 900;
    const ctl = {uf: null, cod: null};
    d3.select(svgEl).selectAll('*').remove();
    const paths = d3.select(svgEl).append('g').selectAll('path').data(feats).enter().append('path')
        .attr('data-cod', d => d.properties.cod)
        .attr('fill', d => { const c = classeDe(POR_COD[d.properties.cod]); return c ? c.cor : COR_SEM_ESFERA; });

    ctl.definirUF = uf => {
        ctl.uf = uf;
        const visivel = d => uf === 'BR' || d.properties.uf === uf;
        const alvo = feats.filter(visivel);
        const H = Math.round(W * (uf === 'BR' ? 0.92 : 0.8));
        const proj = d3.geoMercator().fitSize([W, H], {type: 'FeatureCollection', features: alvo});
        const gen = d3.geoPath().projection(proj);
        d3.select(svgEl).attr('viewBox', '0 0 ' + W + ' ' + H);
        paths.style('display', d => visivel(d) ? null : 'none').attr('d', d => visivel(d) ? gen(d) : null);
        if (ctl.cod) ctl.destacar(ctl.cod);
    };
    ctl.destacar = cod => {
        ctl.cod = cod;
        paths.classed('sel', false);
        paths.filter(d => d.properties.cod === cod).classed('sel', true).raise();
    };

    const toque = window.matchMedia && matchMedia('(pointer: coarse)').matches;
    const codDe = alvo => alvo && alvo.tagName === 'path' ? alvo.getAttribute('data-cod') : null;
    if (!toque) {
        svgEl.addEventListener('mousemove', e => {
            const cod = codDe(e.target);
            if (!cod) { tipEl.classList.remove('on'); return; }
            const m = POR_COD[cod];
            tipEl.innerHTML = !m
                ? '<b>Sem esfera municipal própria</b><small>Este território não entra na projeção municipal.</small>'
                : `<b>${esc(m.nome)} · ${m.uf}</b>` + (m.r
                    ? '<small>Sem dado confiável: a participação de 2025 tem ressalva na fonte.</small><em>Clique para ver a ficha →</em>'
                    : `<span class="v ${clsSinal(m.v)}">${fmtPct(m.v)}</span><small>em 2033, contra o cenário sem a reforma</small><em>Clique para ver a ficha →</em>`);
            const r = wrapEl.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
            const w = tipEl.offsetWidth, h = tipEl.offsetHeight;
            tipEl.style.left = Math.max(6, x + 16 + w > r.width ? x - w - 16 : x + 16) + 'px';
            tipEl.style.top = Math.min(Math.max(6, y - h / 2), r.height - h - 6) + 'px';
            tipEl.classList.add('on');
        });
        svgEl.addEventListener('mouseleave', () => tipEl.classList.remove('on'));
    }
    svgEl.addEventListener('click', e => {
        const cod = codDe(e.target);
        if (!cod || !POR_COD[cod]) return;
        track('clique_mapa', {municipio: POR_COD[cod].nome, uf: POR_COD[cod].uf});
        opt.aoClicar(cod);
    });
    ctl.definirUF(opt.uf);
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
    if (ESCOPO !== base.uf) definirEscopo(base.uf);
    if (MAPA) MAPA.destacar(cod);
    const corpo = $('fichaCorpo');
    corpo.innerHTML = '<p class="nota" role="status">Carregando a ficha de ' + esc(base.nome) + '…</p>';
    let m;
    try {
        if (!CACHE_UF.has(base.uf)) CACHE_UF.set(base.uf, getJSON('/data/painel-municipios/' + base.uf + '.json').then(j => j.municipios));
        m = (await CACHE_UF.get(base.uf))[cod];
    } catch (e) { CACHE_UF.delete(base.uf); m = null; }
    if (ATUAL !== cod) return;                              // o usuário já escolheu outro município
    if (!m) { corpo.innerHTML = '<p class="aviso">Não foi possível carregar os dados deste município. Tente novamente em instantes.</p>'; return; }
    renderFicha(cod, base, m);
}

function renderFicha(cod, base, m) {
    graficos.forEach(g => g.destroy()); graficos = [];
    const ok = LISTA.filter(x => !x.r).sort((a, b) => b.v - a.v);
    const posBR = ok.findIndex(x => x.cod === cod) + 1;
    const naUF = ok.filter(x => x.uf === base.uf);
    const posUF = naUF.findIndex(x => x.cod === cod) + 1;

    const pos33 = m.pos_por_ano['2033'], cf33 = m.contrafactual_por_ano['2033'];
    const dif33 = pos33 - cf33, v33 = m.variacao_por_ano['2033'];
    const sinal = clsSinal(v33);
    const seg = ANOS.map(a => m.repasse_seguro_receita_por_ano[a] || 0);
    const temSeguro = seg.some(x => x > 0);

    let aviso = '';
    if (m.neutro_suspeito) aviso = '<strong>Dado a conferir.</strong> O valor declarado ao SICONFI para 2025 diverge de forma incompatível da série histórica deste município, o que sugere falha de preenchimento na fonte. Os números são exibidos com cautela e não entram nos rankings.';
    else if (m.neutro_aproximado) aviso = '<strong>Estimativa aproximada.</strong> Este município não tem registro individualizado de ISS e cota-parte do ICMS para 2025 no SICONFI, e a participação de 2025 foi aproximada pela média de sete anos. Leia os números como ordem de grandeza.';
    else if (m.cobertura_anos < 5) aviso = '<strong>Série curta.</strong> Há apenas ' + m.cobertura_anos + ' anos de dados históricos para este município, abaixo do mínimo recomendado de 5. Os números são menos estáveis.';

    const lado = v33 < -0.0005 ? 'a menos' : 'a mais';
    const leitura = Math.abs(v33) > 0.0005
        ? `Em 2033, a receita de ${esc(base.nome)} proveniente de ISS e cota-parte do ICMS (já substituídos pelo IBS) é estimada em <strong>${fmtMoney(pos33)}</strong>, contra <strong>${fmtMoney(cf33)}</strong> que a prefeitura teria sem a reforma: <strong>${fmtMoney(Math.abs(dif33))} por ano</strong> ${lado}.`
        : `Em 2033, a receita de ${esc(base.nome)} é estimada em <strong>${fmtMoney(pos33)}</strong>, praticamente igual ao cenário sem a reforma.`;
    const nota = v33 < -0.0005
        ? 'Perda estimada não é destino: ela depende de decisões de orçamento, de arrecadação própria e de legislação local que ainda podem ser tomadas.'
        : 'Ganho estimado também exige planejamento: a receita de destino depende de consumo e de compras públicas que variam, e a projeção precisa ser acompanhada.';

    const linhas = ANOS.map((a, i) => {
        const v = m.variacao_por_ano[a], d = m.pos_por_ano[a] - m.contrafactual_por_ano[a];
        return `<tr><td>${a}</td><td>${fmtMoney(m.contrafactual_por_ano[a])}</td><td>${fmtMoney(m.pos_por_ano[a])}</td><td class="${clsSinal(v)}">${fmtMoney(d)}</td><td class="${clsSinal(v)}">${fmtPct(v)}</td>${temSeguro ? `<td>${seg[i] > 0 ? fmtMoney(seg[i]) : '—'}</td>` : ''}</tr>`;
    }).join('');

    $('fichaCorpo').innerHTML = `
        <button type="button" class="voltar" id="btnVoltar">← Voltar ao mapa</button>
        <div class="ficha-top">
            <div>
                <h2 id="fichaTitulo" tabindex="-1">${esc(base.nome)}<small>${base.uf}</small></h2>
                <p class="ficha-meta">${esc(NOMES_UF[base.uf])} · população média de ${fmtInt(m.pop_media)} habitantes (IBGE, 2019–2026)</p>
            </div>
            <div class="ficha-acoes">
                <button class="btn btn-ghost btn-sm" type="button" id="btnCopiar">Copiar link</button>
                <button class="btn btn-ghost btn-sm" type="button" id="btnImprimir">Imprimir / salvar PDF</button>
            </div>
        </div>
        ${aviso ? `<div class="aviso" role="note">${aviso}</div>` : ''}
        <div class="veredito ${sinal}">
            <div class="grande">${fmtPct(v33)}<small>variação da receita em 2033</small></div>
            <div><p>${leitura}</p><p>${nota}</p></div>
        </div>
        <div class="kpis">
            <div class="kpi"><span>Receita de referência 2025</span><b>${fmtMoney(m.pre_2025)}</b><small>ISS mais cota-parte do ICMS, em R$ de 2025</small></div>
            <div class="kpi"><span>Sem a reforma, 2033</span><b>${fmtMoney(cf33)}</b><small>Regras antigas e fatia de 2025</small></div>
            <div class="kpi"><span>Com a reforma, 2033</span><b>${fmtMoney(pos33)}</b><small>Com o cronograma do ADCT aplicado</small></div>
            <div class="kpi"><span>Diferença por ano, 2033</span><b class="${sinal}">${fmtMoney(dif33)}</b><small>Projeção menos cenário sem reforma</small></div>
        </div>
        ${temSeguro ? `<div class="seguro" role="note"><strong>Seguro-Receita.</strong> No cenário do modelo, o município recebe repasse do Seguro-Receita, de ${fmtMoney(Math.min(...seg.filter(x => x > 0)))} no primeiro ano com repasse a ${fmtMoney(Math.max(...seg))} no maior ano. O valor já está incluído na projeção acima.</div>` : ''}
        <div class="ficha-grid">
            <div class="panel"><h3>Receita ao longo do tempo</h3><p class="panel-sub">Histórico declarado e projeção com e sem a reforma, em R$ de 2025.</p>
                <div class="canvas-box"><canvas id="gSerie" role="img" aria-label="Gráfico de linhas com a receita histórica de 2019 a 2025 e a projeção de 2029 a 2033 com e sem a reforma. Os mesmos valores estão na tabela ao lado."></canvas></div></div>
            <div class="panel"><h3>De onde vem a receita com a reforma</h3><p class="panel-sub">Composição da projeção, por componente, em R$ de 2025.</p>
                <div class="canvas-box"><canvas id="gComp" role="img" aria-label="Gráfico de barras empilhadas com a composição da receita projetada de 2029 a 2033: tributos atuais residuais, IBS pelo critério histórico, IBS por destino e Seguro-Receita."></canvas></div></div>
        </div>
        <div class="ficha-grid">
            <div class="panel"><h3>${esc(base.nome)} entre os municípios de ${esc(NOMES_UF[base.uf])}</h3><p class="panel-sub">Variação da receita em 2033. O município está contornado; passe o cursor sobre os vizinhos.</p>
                <div class="map-wrapper" id="miniWrap"><svg id="miniSvg" role="img" aria-label="Mapa dos municípios de ${esc(NOMES_UF[base.uf])} com ${esc(base.nome)} contornado."></svg><div class="map-tip" id="miniTip" role="tooltip"></div></div></div>
            <div class="panel"><h3>Ano a ano, 2029–2033</h3><p class="panel-sub">Receita estimada com e sem a reforma, e a diferença entre as duas.</p>
                <div class="table-wrap"><table class="dados">
                    <thead><tr><th>Ano</th><th>Sem a reforma</th><th>Com a reforma</th><th>Diferença</th><th>Variação</th>${temSeguro ? '<th>Seguro-Receita</th>' : ''}</tr></thead>
                    <tbody>${linhas}</tbody></table></div></div>
        </div>
        <div class="posicao">
            ${m.neutro_aproximado || m.neutro_suspeito ? '<span>Posição nos rankings indisponível para municípios com ressalva de dados.</span>' : `
            <span>Variação em 2033: <b>${fmtInt(posBR)}º</b> entre os ${fmtInt(ok.length)} municípios do país com dados confiáveis, do maior ganho à maior perda.</span>
            <span>Em ${base.uf}: <b>${fmtInt(posUF)}º</b> entre ${fmtInt(naUF.length)}.</span>`}
        </div>
        <div class="cta-ficha">
            <p><strong>Quer o diagnóstico completo de ${esc(base.nome)}?</strong> A Vertex Advisory monta o relatório individual, com plano de ação para o orçamento e capacitação da equipe.</p>
            <div class="botoes" id="ctaFichaBotoes" style="margin:0"></div>
        </div>`;

    $('btnVoltar').addEventListener('click', () => mostrarVisao('visao-geral'));
    $('btnCopiar').addEventListener('click', e => {
        const url = location.origin + location.pathname + '?m=' + cod;
        (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(() => { e.target.textContent = 'Link copiado'; }, () => { prompt('Copie o link:', url); });
        track('copiar_link', {municipio: base.nome});
    });
    $('btnImprimir').addEventListener('click', () => { track('imprimir_ficha', {municipio: base.nome}); window.print(); });
    contatoBotoes($('ctaFichaBotoes'), base);
    desenharGraficos(m);
    carregarMalha().then(() => {
        if (ATUAL !== cod || !$('miniSvg')) return;
        MINI = criarMapa($('miniSvg'), $('miniWrap'), $('miniTip'), {todos: false, uf: base.uf, aoClicar: c => abrirMunicipio(c)});
        MINI.destacar(cod);
    }).catch(() => { const w = $('miniWrap'); if (w) w.innerHTML = '<p class="nota">O mapa não pôde ser carregado agora.</p>'; });
    $('fichaTitulo').focus({preventScroll: true});
}

function desenharGraficos(m) {
    if (typeof Chart === 'undefined') { document.querySelectorAll('.canvas-box').forEach(b => { b.innerHTML = '<p class="nota">O gráfico não pôde ser carregado. Os valores estão na tabela.</p>'; }); return; }
    const mi = v => v == null ? null : v / 1e6;
    const eixoR$ = {ticks: {callback: v => 'R$ ' + v.toLocaleString('pt-BR') + ' mi', color: '#55576a'}, grid: {color: '#ecebe5'}, beginAtZero: true};
    const tip = {callbacks: {label: c => ' ' + c.dataset.label + ': ' + fmtMoney(c.parsed.y * 1e6)}};
    Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
    const rotulos = ANOS_HIST.concat(['2026', '2027', '2028'], ANOS);
    const hist = rotulos.map(a => m.historico_por_ano[a] ? mi(m.historico_por_ano[a].total_reais_2025) : null);
    const cf = rotulos.map(a => m.contrafactual_por_ano[a] != null ? mi(m.contrafactual_por_ano[a]) : null);
    const pos = rotulos.map(a => m.pos_por_ano[a] != null ? mi(m.pos_por_ano[a]) : null);
    graficos.push(new Chart($('gSerie'), {
        type: 'line',
        data: {labels: rotulos, datasets: [
            {label: 'Histórico declarado', data: hist, borderColor: '#1f2a55', backgroundColor: '#1f2a55', borderWidth: 3, pointRadius: 3, spanGaps: false},
            {label: 'Sem a reforma', data: cf, borderColor: '#858384', backgroundColor: '#858384', borderDash: [6, 5], borderWidth: 3, pointRadius: 3, spanGaps: false},
            {label: 'Com a reforma', data: pos, borderColor: '#b8922f', backgroundColor: '#b8922f', borderWidth: 4, pointRadius: 4, spanGaps: false}
        ]},
        options: {responsive: true, maintainAspectRatio: false, interaction: {mode: 'index', intersect: false},
            plugins: {legend: {position: 'bottom', labels: {usePointStyle: true, boxWidth: 8}}, tooltip: tip}, scales: {y: eixoR$, x: {grid: {display: false}}}}
    }));
    const comp = k => ANOS.map(a => mi(m.componentes_por_ano[a][k]));
    graficos.push(new Chart($('gComp'), {
        type: 'bar',
        data: {labels: ANOS, datasets: [
            {label: 'ISS e ICMS residuais', data: comp('origem'), backgroundColor: '#858384'},
            {label: 'IBS pelo critério histórico', data: comp('cpt'), backgroundColor: '#1f2a55'},
            {label: 'IBS por destino', data: comp('destino'), backgroundColor: '#cfad56'},
            {label: 'Seguro-Receita', data: comp('seguro'), backgroundColor: '#2f7f7a'}
        ]},
        options: {responsive: true, maintainAspectRatio: false, interaction: {mode: 'index', intersect: false},
            plugins: {legend: {position: 'bottom', labels: {boxWidth: 12}}, tooltip: tip}, scales: {x: {stacked: true, grid: {display: false}}, y: Object.assign({stacked: true}, eixoR$)}}
    }));
}

/* ── contato ──
   Os links só existem quando WhatsApp ou e-mail estão configurados no topo deste arquivo. */
function contatoBotoes(alvo, base) {
    const assunto = base ? 'Diagnóstico da reforma tributária: ' + base.nome + '/' + base.uf : 'Diagnóstico da reforma tributária para a minha prefeitura';
    const texto = base
        ? 'Olá! Vi a estimativa de ' + base.nome + '/' + base.uf + ' no Municípios na Reforma e gostaria de conversar sobre o diagnóstico da reforma tributária para a prefeitura.'
        : 'Olá! Vim pelo Municípios na Reforma e gostaria de conversar sobre o diagnóstico da reforma tributária para a minha prefeitura.';
    const html = [];
    if (CONFIG.whatsapp) html.push(`<a class="btn btn-gold btn-sm" data-contato="whatsapp" href="https://wa.me/${CONFIG.whatsapp}?text=${encodeURIComponent(texto)}" rel="noopener" target="_blank">Falar pelo WhatsApp</a>`);
    if (CONFIG.email) html.push(`<a class="btn ${CONFIG.whatsapp ? 'btn-ghost' : 'btn-gold'} btn-sm" data-contato="email" href="mailto:${CONFIG.email}?subject=${encodeURIComponent(assunto)}&body=${encodeURIComponent(texto)}">Enviar e-mail</a>`);
    alvo.innerHTML = html.join('') || '<span class="nota">Canal de contato em configuração.</span>';
    alvo.querySelectorAll('[data-contato]').forEach(a => a.addEventListener('click', () => track('clique_contato', {canal: a.dataset.contato, municipio: base ? base.nome : 'geral'})));
}
contatoBotoes($('botoesContato'), null);
})();
