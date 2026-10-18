/* Agenda: prazos que exigem providência do município e publicações do CGIBS.
   Os dados vêm de /data/cronograma-municipal.json, /data/cgibs-publicacoes.json
   e /data/cgibs-editorial.json (este último com a explicação de cada ato). */
(function () {
'use strict';

const el = (tag, attrs, ...filhos) => {
    const n = document.createElement(tag);
    for (const k in (attrs || {})) {
        if (k === 'class') n.className = attrs[k];
        else if (k === 'text') n.textContent = attrs[k];
        else n.setAttribute(k, attrs[k]);
    }
    filhos.flat().forEach(f => { if (f != null) n.append(f.nodeType ? f : document.createTextNode(f)); });
    return n;
};
const getJSON = url => fetch(url).then(r => { if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); });
const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
const dataBR = iso => { const [a, m, d] = iso.split('-').map(Number); return d + ' de ' + MESES[m - 1] + ' de ' + a; };
const dataCurta = iso => iso.split('-').reverse().join('/');
const hojeISO = () => new Date().toISOString().slice(0, 10);

let cron = null, pubs = null, edit = null, carregando = null;
const carrega = () => carregando || (carregando = Promise.all([
    getJSON('/data/cronograma-municipal.json'),
    getJSON('/data/cgibs-publicacoes.json').catch(() => null),
    getJSON('/data/cgibs-editorial.json').catch(() => ({ fichas: {} }))
]).then(([c, p, e]) => { cron = c; pubs = p; edit = e.fichas || {}; }));

/* ── situação de cada marco, em relação ao dia de hoje ── */
function situacao(m, hoje) {
    const fim = m.data_fim || m.data;
    if (fim < hoje) return m.tipo === 'inicio' ? { chave: 'curso', rotulo: 'Já em vigor' } : { chave: 'encerrado', rotulo: m.data_fim ? 'Encerrado' : 'Prazo encerrado' };
    if (m.data <= hoje) return { chave: 'curso', rotulo: 'Em curso' };
    return { chave: 'futuro', rotulo: 'Previsto' };
}
const proximoMarco = hoje => cron.marcos.filter(m => m.acao_municipio && (m.data_fim || m.data) >= hoje)
    .sort((a, b) => a.data.localeCompare(b.data))[0];

/* ── prazos ── */
function renderPrazos() {
    const raiz = document.getElementById('agendaPrazos');
    const hoje = hojeISO();
    const so = document.getElementById('soProvidencia').checked;
    const prox = proximoMarco(hoje);
    raiz.replaceChildren();
    let anoAtual = null;
    const lista = el('ol', { class: 'linha-tempo' });
    cron.marcos.slice().sort((a, b) => a.data.localeCompare(b.data)).forEach(m => {
        if (so && !m.acao_municipio) return;
        const ano = m.data.slice(0, 4);
        if (ano !== anoAtual) { anoAtual = ano; lista.append(el('li', { class: 'lt-ano', text: ano })); }
        const s = situacao(m, hoje);
        const ehProx = prox && prox.id === m.id;
        const item = el('li', { class: 'lt-item lt-' + s.chave + (ehProx ? ' lt-prox' : ''), id: 'marco-' + m.id });
        const mostraSit = s.chave === 'curso' || m.tipo !== 'inicio' && s.chave === 'encerrado';
        const topo = el('div', { class: 'lt-topo' },
            el('span', { class: 'lt-data', text: m.rotulo_data }),
            ehProx ? el('span', { class: 'chip chip-prox', text: 'Próxima providência' }) : (mostraSit ? el('span', { class: 'chip chip-' + s.chave, text: s.rotulo }) : null),
            m.quem === 'Município' && !ehProx ? el('span', { class: 'chip chip-quem', text: 'Providência do município' }) : null,
            m.a_confirmar ? el('span', { class: 'chip chip-conf', text: 'Data a confirmar' }) : null);
        item.append(topo, el('h3', { text: m.titulo }), el('p', { text: m.resumo }));
        if (m.acao_municipio) item.append(el('div', { class: 'lt-acao' }, el('strong', { text: 'O que fazer: ' }), m.acao_municipio));
        item.append(el('details', { class: 'lt-base' }, el('summary', { text: 'Base legal' }), el('p', { text: m.base_legal.join('; ') })));
        const vinc = (m.pub_ids || []).map(id => pubs && pubs.itens.find(i => i.id === id)).filter(Boolean);
        if (vinc.length) item.append(el('p', { class: 'lt-pubs' }, 'Ato oficial: ', vinc.map((p, i) =>
            [i ? ' · ' : '', el('a', { href: p.pdf_url, target: '_blank', rel: 'noopener', text: p.titulo })]).flat()));
        lista.append(item);
    });
    raiz.append(lista);
    raiz.append(el('p', { class: 'agenda-aviso', text: cron.aviso }));
}

/* ── publicações ── */
function renderPubs() {
    const raiz = document.getElementById('agendaPubs');
    raiz.replaceChildren();
    if (!pubs) { raiz.append(el('p', { class: 'vazio', text: 'A lista de publicações não pôde ser carregada agora.' })); return; }
    const q = document.getElementById('pubBusca').value.trim().toLowerCase();
    const tipo = document.getElementById('pubTipo').value;
    const todas = document.getElementById('pubTodas').checked;
    const itens = pubs.itens.filter(i => {
        const f = edit[i.id] || {};
        if (!todas && f.relevancia === 'baixa') return false;
        if (tipo && i.tipo !== tipo) return false;
        if (q && !(i.titulo + ' ' + (f.o_que_e || '') + ' ' + (f.tema || '')).toLowerCase().includes(q)) return false;
        return true;
    });
    raiz.append(el('p', { class: 'pub-conta', 'aria-live': 'polite', text: itens.length + (itens.length === 1 ? ' ato' : ' atos') + (todas ? '' : ' de maior relevância para os municípios (de ' + pubs.total + ' publicados)') }));
    itens.forEach(i => {
        const f = edit[i.id] || {};
        const card = el('article', { class: 'pub' + (i.revogado ? ' pub-revogado' : '') });
        card.append(el('div', { class: 'pub-topo' },
            el('span', { class: 'chip chip-tipo', text: i.tipo }),
            f.tema ? el('span', { class: 'chip chip-tema', text: f.tema }) : null,
            i.revogado ? el('span', { class: 'chip chip-conf', text: 'Revogado' }) : null,
            el('time', { class: 'pub-data', datetime: i.publicado_em, text: 'Publicado em ' + dataCurta(i.publicado_em) })));
        card.append(el('h3', { text: i.titulo }));
        if (f.o_que_e) card.append(el('p', { class: 'pub-que', text: f.o_que_e }));
        if (f.por_que_importa || f.acao_municipio) {
            const d = el('details', { class: 'pub-porque' }, el('summary', { text: 'Por que importa para o município' }));
            if (f.por_que_importa) d.append(el('p', { text: f.por_que_importa }));
            if (f.acao_municipio) d.append(el('div', { class: 'lt-acao' }, el('strong', { text: 'O que fazer: ' }), f.acao_municipio));
            d.append(el('p', { class: 'pub-sel' },
                f.revisado_pelo_autor ? 'Leitura do portal; não substitui o ato oficial.' : 'Texto em revisão. Leitura do portal; não substitui o ato oficial.'));
            card.append(d);
        }
        card.append(el('a', { class: 'btn btn-sm btn-pdf', href: i.pdf_url, target: '_blank', rel: 'noopener', text: 'Abrir o PDF oficial' }));
        raiz.append(card);
    });
    if (!itens.length) raiz.append(el('p', { class: 'vazio', text: 'Nenhum ato encontrado com esse filtro.' }));
    raiz.append(el('p', { class: 'agenda-aviso', text: 'Fonte: seções de legislação do site do CGIBS (' + pubs.fonte.replace('https://', '') + '), lidas em ' + dataCurta(pubs.coletado_em) + '. Uma rotina do portal repete essa leitura periodicamente; se um ato novo ainda não aparece aqui, consulte o site do Comitê.' }));
}

/* ── montagem ── */
function montaAgenda() {
    const tipos = [...new Set(pubs ? pubs.itens.map(i => i.tipo) : [])].sort();
    const sel = document.getElementById('pubTipo');
    if (sel.options.length <= 1) tipos.forEach(t => sel.append(el('option', { value: t, text: t })));
    renderPrazos(); renderPubs();
}
function mostraSecao(qual) {
    document.querySelectorAll('#agendaAbas button').forEach(b => b.classList.toggle('active', b.dataset.secao === qual));
    document.getElementById('agendaSecPrazos').hidden = qual !== 'prazos';
    document.getElementById('agendaSecPubs').hidden = qual !== 'pubs';
}
function abreAgenda() {
    carrega().then(montaAgenda).catch(e => {
        console.error(e);
        document.getElementById('agendaPrazos').textContent = 'Não foi possível carregar a agenda agora. Atualize a página em instantes.';
    });
}

document.querySelectorAll('.tab-btn[data-view="agenda"]').forEach(b => b.addEventListener('click', abreAgenda));
document.querySelectorAll('#agendaAbas button').forEach(b => b.addEventListener('click', () => mostraSecao(b.dataset.secao)));
document.getElementById('soProvidencia').addEventListener('change', () => cron && renderPrazos());
['pubBusca', 'pubTipo', 'pubTodas'].forEach(id => document.getElementById(id).addEventListener(id === 'pubBusca' ? 'input' : 'change', () => pubs && renderPubs()));

})();
