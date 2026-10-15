/* Municípios na Reforma — Vertex Advisory.
   Lê os mesmos JSONs do painel da reforma tributária (/data/painel-municipios/),
   de modo que qualquer melhoria metodológica regenerada em data/ aparece aqui
   no mesmo deploy. Nenhum número de resultado é escrito à mão neste arquivo. */
(function () {
'use strict';

/* ── CONFIGURAÇÃO COMERCIAL: preencher antes da campanha ─────────────────── */
const CONFIG = {
    whatsapp: '',   // somente dígitos com DDI e DDD, ex.: '5527999999999'
    email: '',      // ex.: 'contato@seudominio.com.br'
    gaId: ''        // ex.: 'G-XXXXXXXXXX' (Google Analytics 4), opcional
};

const ANOS = ['2029', '2030', '2031', '2032', '2033'];
const ANOS_HIST = ['2019', '2020', '2021', '2022', '2023', '2024', '2025'];
const NOMES_UF = {AC:'Acre',AL:'Alagoas',AM:'Amazonas',AP:'Amapá',BA:'Bahia',CE:'Ceará',ES:'Espírito Santo',GO:'Goiás',MA:'Maranhão',MG:'Minas Gerais',MS:'Mato Grosso do Sul',MT:'Mato Grosso',PA:'Pará',PB:'Paraíba',PE:'Pernambuco',PI:'Piauí',PR:'Paraná',RJ:'Rio de Janeiro',RN:'Rio Grande do Norte',RO:'Rondônia',RR:'Roraima',RS:'Rio Grande do Sul',SC:'Santa Catarina',SE:'Sergipe',SP:'São Paulo',TO:'Tocantins'};

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
let LISTA = [];                       // [{cod, nome, uf, v, r, chave}]
let POR_COD = {};
const CACHE_UF = new Map();
let graficos = [];

/* ── carga ── */
fetch('/data/painel-municipios/index.json')
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(j => {
        LISTA = Object.entries(j.municipios).map(([cod, m]) => ({cod, nome: m.nome, uf: m.uf, v: m.v, r: !!m.r, chave: norm(m.nome)}));
        LISTA.forEach(m => { POR_COD[m.cod] = m; });
        montarNumeros(); montarPanorama(); ativarBusca();
        const cod = new URLSearchParams(location.search).get('m');
        if (cod && POR_COD[cod]) abrirMunicipio(cod, {rolar: true, semUrl: true});
    })
    .catch(() => { $('dicaBusca').textContent = 'Não foi possível carregar a base de municípios. Atualize a página em instantes.'; });

function carregarUF(uf) {
    if (CACHE_UF.has(uf)) return CACHE_UF.get(uf);
    const p = fetch('/data/painel-municipios/' + uf + '.json').then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(j => j.municipios);
    p.catch(() => CACHE_UF.delete(uf));
    CACHE_UF.set(uf, p);
    return p;
}

/* ── faixa de números e panorama: calculados da própria base ── */
function montarNumeros() {
    const ok = LISTA.filter(m => !m.r);
    const perdem = ok.filter(m => m.v < 0).length;
    const ord = ok.map(m => m.v).sort((a, b) => a - b);
    const mediana = ord.length % 2 ? ord[(ord.length - 1) / 2] : (ord[ord.length / 2 - 1] + ord[ord.length / 2]) / 2;
    $('stPerdem').textContent = fmtPctSimples(perdem / ok.length);
    $('stMediana').textContent = fmtPct(mediana);
    $('stTotal').textContent = fmtInt(LISTA.length);
    $('dicaBusca').textContent = 'Base com ' + fmtInt(LISTA.length) + ' municípios. Comece a digitar e escolha na lista.';
}

function montarPanorama() {
    const porUF = {};
    LISTA.filter(m => !m.r).forEach(m => { const u = porUF[m.uf] || (porUF[m.uf] = {n: 0, perdem: 0}); u.n++; if (m.v < 0) u.perdem++; });
    $('ufGrid').innerHTML = Object.entries(porUF)
        .map(([uf, u]) => ({uf, n: u.n, p: u.perdem / u.n}))
        .sort((a, b) => b.p - a.p)
        .map(u => `<div class="uf-row" role="listitem" title="${esc(NOMES_UF[u.uf] || u.uf)}: ${fmtInt(u.n * u.p)} de ${fmtInt(u.n)} municípios">
            <b>${u.uf}</b><div class="uf-bar" aria-hidden="true"><i style="width:${(u.p * 100).toFixed(1)}%"></i></div><span>${fmtPctSimples(u.p)}</span></div>`).join('');
}

/* ── busca (padrão combobox) ── */
let sugestoes = [], ativo = -1;
function ativarBusca() {
    const inp = $('busca'), ul = $('sugestoes');
    inp.disabled = false;
    const fechar = () => { ul.hidden = true; inp.setAttribute('aria-expanded', 'false'); ativo = -1; };
    const marcar = i => {
        ativo = i;
        [...ul.children].forEach((li, k) => li.setAttribute('aria-selected', k === i ? 'true' : 'false'));
        if (i >= 0) inp.setAttribute('aria-activedescendant', 'sug-' + i); else inp.removeAttribute('aria-activedescendant');
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
            ? sugestoes.map((m, i) => `<li role="option" id="sug-${i}" data-cod="${m.cod}" aria-selected="false">${esc(m.nome)}<small>${m.uf}</small></li>`).join('')
            : '<li class="vazio" role="option" aria-disabled="true">Nenhum município encontrado. Confira a grafia.</li>';
        ul.hidden = false; inp.setAttribute('aria-expanded', 'true'); ativo = -1;
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
    $('formBusca').addEventListener('submit', e => {
        e.preventDefault();
        if (!sugestoes.length) buscar();
        const alvo = sugestoes[ativo >= 0 ? ativo : 0];
        if (alvo) escolher(alvo.cod);
    });
    function escolher(cod) {
        inp.value = POR_COD[cod].nome + ' (' + POR_COD[cod].uf + ')';
        fechar();
        track('busca_municipio', {municipio: POR_COD[cod].nome, uf: POR_COD[cod].uf});
        abrirMunicipio(cod, {rolar: true});
    }
}

/* ── ficha do município ── */
async function abrirMunicipio(cod, opt) {
    opt = opt || {};
    const base = POR_COD[cod];
    const secao = $('ficha'), corpo = $('fichaCorpo');
    secao.hidden = false;
    corpo.innerHTML = '<p class="nota" role="status">Carregando a ficha de ' + esc(base.nome) + '…</p>';
    if (opt.rolar) secao.scrollIntoView({behavior: 'smooth', block: 'start'});
    if (!opt.semUrl) { const u = new URL(location.href); u.searchParams.set('m', cod); history.replaceState(null, '', u); }
    let m;
    try { m = (await carregarUF(base.uf))[cod]; } catch (e) { m = null; }
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
    if (m.neutro_suspeito) aviso = '<strong>Dado a conferir.</strong> O valor declarado ao SICONFI para 2025 diverge de forma incompatível da série histórica deste município, o que sugere falha de preenchimento na fonte. Os números abaixo são exibidos com cautela e não entram nos rankings.';
    else if (m.neutro_aproximado) aviso = '<strong>Estimativa aproximada.</strong> Este município não tem registro individualizado de ISS e cota-parte do ICMS para 2025 no SICONFI, e a participação de 2025 foi aproximada pela média de sete anos. Leia os números como ordem de grandeza.';
    else if (m.cobertura_anos < 5) aviso = '<strong>Série curta.</strong> Há apenas ' + m.cobertura_anos + ' anos de dados históricos para este município, abaixo do mínimo recomendado de 5. Os números são menos estáveis.';

    const leitura = v33 < -0.0005
        ? `Em 2033, a receita de ${esc(base.nome)} proveniente de ISS e cota-parte do ICMS (já substituídos pelo IBS) é estimada em <strong>${fmtMoney(pos33)}</strong>, contra <strong>${fmtMoney(cf33)}</strong> que a prefeitura teria sem a reforma: <strong>${fmtMoney(Math.abs(dif33))} por ano</strong> a menos.`
        : v33 > 0.0005
        ? `Em 2033, a receita de ${esc(base.nome)} proveniente de ISS e cota-parte do ICMS (já substituídos pelo IBS) é estimada em <strong>${fmtMoney(pos33)}</strong>, contra <strong>${fmtMoney(cf33)}</strong> que a prefeitura teria sem a reforma: <strong>${fmtMoney(Math.abs(dif33))} por ano</strong> a mais.`
        : `Em 2033, a receita de ${esc(base.nome)} é estimada em <strong>${fmtMoney(pos33)}</strong>, praticamente igual ao cenário sem a reforma.`;
    const nota = v33 < -0.0005
        ? 'Perda estimada não é destino: ela depende de decisões de orçamento, de arrecadação própria e de legislação local que ainda podem ser tomadas.'
        : 'Ganho estimado também exige planejamento: a receita de destino depende de consumo e de compras públicas que variam, e a projeção precisa ser acompanhada.';

    const linhas = ANOS.map((a, i) => {
        const v = m.variacao_por_ano[a], d = m.pos_por_ano[a] - m.contrafactual_por_ano[a];
        return `<tr><td>${a}</td><td>${fmtMoney(m.contrafactual_por_ano[a])}</td><td>${fmtMoney(m.pos_por_ano[a])}</td><td class="${clsSinal(v)}">${fmtMoney(d)}</td><td class="${clsSinal(v)}">${fmtPct(v)}</td>${temSeguro ? `<td>${seg[i] > 0 ? fmtMoney(seg[i]) : '—'}</td>` : ''}</tr>`;
    }).join('');

    $('fichaCorpo').innerHTML = `
        <div class="ficha-top">
            <div>
                <h2 id="fichaTitulo" tabindex="-1">${esc(base.nome)}<small>${base.uf}</small></h2>
                <p class="ficha-meta">${esc(NOMES_UF[base.uf] || base.uf)} · população média de ${fmtInt(m.pop_media)} habitantes (IBGE, 2019–2026)</p>
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
            <div class="kpi"><span>Sem a reforma, 2033</span><b>${fmtMoney(cf33)}</b><small>Cenário de regras antigas e fatia de 2025</small></div>
            <div class="kpi"><span>Com a reforma, 2033</span><b>${fmtMoney(pos33)}</b><small>Já com o cronograma do ADCT aplicado</small></div>
            <div class="kpi"><span>Diferença por ano, 2033</span><b class="${sinal}">${fmtMoney(dif33)}</b><small>Projeção menos cenário sem reforma</small></div>
        </div>
        ${temSeguro ? `<div class="seguro" role="note"><strong>Seguro-Receita.</strong> No cenário do modelo, o município recebe repasse do Seguro-Receita, de ${fmtMoney(Math.min(...seg.filter(x => x > 0)))} no primeiro ano com repasse a ${fmtMoney(Math.max(...seg))} no maior ano. O valor já está incluído na projeção acima.</div>` : ''}
        <div class="graficos">
            <div class="painel"><h3>Receita ao longo do tempo</h3><p class="sub">Histórico declarado e projeção com e sem a reforma, em R$ de 2025.</p>
                <div class="canvas-box"><canvas id="gSerie" role="img" aria-label="Gráfico de linhas com a receita histórica de 2019 a 2025 e a projeção de 2029 a 2033 com e sem a reforma. Os mesmos valores estão na tabela abaixo."></canvas></div></div>
            <div class="painel"><h3>De onde vem a receita com a reforma</h3><p class="sub">Composição da projeção, por componente, em R$ de 2025.</p>
                <div class="canvas-box"><canvas id="gComp" role="img" aria-label="Gráfico de barras empilhadas com a composição da receita projetada de 2029 a 2033: tributos atuais residuais, IBS pelo critério histórico, IBS por destino e Seguro-Receita."></canvas></div></div>
        </div>
        <div class="painel">
            <h3>Ano a ano, 2029–2033</h3><p class="sub">Receita estimada com e sem a reforma, e a diferença entre as duas.</p>
            <div class="tabela-wrap"><table class="dados">
                <thead><tr><th>Ano</th><th>Sem a reforma</th><th>Com a reforma</th><th>Diferença</th><th>Variação</th>${temSeguro ? '<th>Seguro-Receita</th>' : ''}</tr></thead>
                <tbody>${linhas}</tbody></table></div>
        </div>
        <div class="posicao">
            ${m.neutro_aproximado || m.neutro_suspeito ? '<span>Posição nos rankings indisponível para municípios com ressalva de dados.</span>' : `
            <span>Variação em 2033: <b>${fmtInt(posBR)}º</b> entre os ${fmtInt(ok.length)} municípios do país com dados confiáveis, do maior ganho à maior perda.</span>
            <span>Em ${base.uf}: <b>${fmtInt(posUF)}º</b> entre ${fmtInt(naUF.length)}.</span>`}
        </div>
        <div class="cta-ficha">
            <div><h3>Quer o diagnóstico completo de ${esc(base.nome)}?</h3>
            <p>A ficha mostra a ordem de grandeza. A Vertex monta o relatório individual, com o plano de ação para o orçamento e a capacitação da equipe.</p></div>
            <div class="botoes" id="ctaFichaBotoes"></div>
        </div>`;

    $('btnCopiar').addEventListener('click', e => {
        const url = location.origin + location.pathname + '?m=' + cod;
        (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(() => { e.target.textContent = 'Link copiado'; }, () => { prompt('Copie o link:', url); });
        track('copiar_link', {municipio: base.nome});
    });
    $('btnImprimir').addEventListener('click', () => { track('imprimir_ficha', {municipio: base.nome}); window.print(); });
    contatoBotoes($('ctaFichaBotoes'), base);
    desenharGraficos(m, base);
    $('fichaTitulo').focus({preventScroll: true});
}

function desenharGraficos(m, base) {
    if (typeof Chart === 'undefined') { document.querySelectorAll('.canvas-box').forEach(b => { b.innerHTML = '<p class="nota">O gráfico não pôde ser carregado. Os valores estão na tabela abaixo.</p>'; }); return; }
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
        ? 'Olá! Vi a estimativa de ' + base.nome + '/' + base.uf + ' no portal Municípios na Reforma e gostaria de conversar sobre o diagnóstico da reforma tributária para a prefeitura.'
        : 'Olá! Vim pelo portal Municípios na Reforma e gostaria de conversar sobre o diagnóstico da reforma tributária para a minha prefeitura.';
    const html = [];
    if (CONFIG.whatsapp) html.push(`<a class="btn btn-gold" data-contato="whatsapp" href="https://wa.me/${CONFIG.whatsapp}?text=${encodeURIComponent(texto)}" rel="noopener" target="_blank">Falar pelo WhatsApp</a>`);
    if (CONFIG.email) html.push(`<a class="btn ${CONFIG.whatsapp ? 'btn-ghost-light' : 'btn-gold'}" data-contato="email" href="mailto:${CONFIG.email}?subject=${encodeURIComponent(assunto)}&body=${encodeURIComponent(texto)}">Enviar e-mail</a>`);
    alvo.innerHTML = html.join('') || '<span class="nota" style="color:#cfd4ea;margin:0">Canal de contato em configuração.</span>';
    alvo.querySelectorAll('[data-contato]').forEach(a => a.addEventListener('click', () => track('clique_contato', {canal: a.dataset.contato, municipio: base ? base.nome : 'geral'})));
}
contatoBotoes($('botoesContato'), null);
document.querySelectorAll('a[data-contato="cabecalho"]').forEach(a => a.addEventListener('click', () => track('clique_contato', {canal: 'cabecalho'})));
})();
