/* Notícias: radar de links sobre a reforma tributária.
   Os dados vêm de /api/noticias (coleta de fontes selecionadas, com cache de uma hora na rede da Vercel).
   O portal mostra só título, fonte e data; o texto da matéria fica no veículo de origem. */
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
const track = (evento, params) => { if (window.MnrMedicao) window.MnrMedicao.registrar(evento, params); };

const GRUPOS = {oficiais: ['cgibs', 'governo', 'congresso'], entes: ['entes'], imprensa: ['imprensa']};
const ROTULO = {cgibs: 'Comitê Gestor', governo: 'Governo', congresso: 'Congresso', entes: 'Entidade', imprensa: 'Imprensa'};
const OFICIAIS = [
    ['Agência Senado', 'https://www12.senado.leg.br/noticias'],
    ['Agência Câmara', 'https://www.camara.leg.br/noticias'],
    ['Receita Federal', 'https://www.gov.br/receitafederal/pt-br/assuntos/noticias'],
    ['Comitê Gestor do IBS', 'https://www.cgibs.gov.br/noticias-menu']
];

let dados = null, carregando = null, grupo = '', soMunicipal = false;

const dia = iso => { const d = new Date(iso); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); };
const rotuloDia = iso => {
    const d = dia(iso), hoje = dia(new Date().toISOString()), dif = Math.round((hoje - d) / 864e5);
    if (dif === 0) return 'Hoje';
    if (dif === 1) return 'Ontem';
    return d.toLocaleDateString('pt-BR', {day: 'numeric', month: 'long', ...(d.getFullYear() !== hoje.getFullYear() ? {year: 'numeric'} : {})});
};
const hora = iso => new Date(iso).toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});

function carrega() {
    if (dados) return Promise.resolve(dados);
    if (!carregando) carregando = fetch('/api/noticias').then(r => {
        if (!r.ok) throw new Error('/api/noticias ' + r.status);
        return r.json();
    }).then(d => { dados = d; return d; }).finally(() => { carregando = null; });
    return carregando;
}

function render() {
    const raiz = document.getElementById('noticiasLista');
    raiz.replaceChildren();
    const aceitos = grupo ? GRUPOS[grupo] : null;
    const itens = dados.itens.filter(i => (!aceitos || aceitos.includes(i.tipo)) && (!soMunicipal || i.municipal));
    let atual = '';
    itens.forEach(i => {
        const rotulo = rotuloDia(i.publicado_em);
        if (rotulo !== atual) { atual = rotulo; raiz.append(el('h3', {class: 'noticias-dia', text: rotulo})); }
        const oficial = GRUPOS.oficiais.includes(i.tipo);
        const meta = el('span', {class: 'noticia-meta'},
            el('span', {class: 'noticia-tag ' + (oficial ? 'oficial' : i.tipo === 'entes' ? 'entes' : ''), text: ROTULO[i.tipo] || 'Fonte'}),
            i.municipal ? el('span', {class: 'noticia-tag municipio', text: 'Municípios'}) : null,
            el('span', {text: i.fonte}),
            el('span', {class: 'noticia-fim', text: hora(i.publicado_em)}));
        const a = el('a', {class: 'noticia', href: i.url, target: '_blank', rel: 'noopener noreferrer'}, el('span', {class: 'noticia-titulo', text: i.titulo}), meta);
        a.addEventListener('click', () => track('noticia_clique', {tipo: i.tipo}));
        raiz.append(a);
    });
    if (!itens.length) raiz.append(el('div', {class: 'vazio'}, el('p', {text: 'Nenhuma notícia encontrada com esse filtro nos últimos ' + dados.janela_dias + ' dias.'})));
    rodape();
}

function rodape() {
    const r = document.getElementById('noticiasRodape');
    r.replaceChildren();
    const quando = new Date(dados.atualizado_em);
    r.append('Lista atualizada em ' + quando.toLocaleDateString('pt-BR') + ' às ' + hora(dados.atualizado_em) +
        '. A seleção é automática e não significa endosso: os títulos e as matérias pertencem aos veículos. Aparecem as notícias dos últimos ' + dados.janela_dias + ' dias que citam a reforma tributária ou seus tributos. Alguns links passam pelo Google Notícias antes de abrir o veículo.');
    if (dados.fontes && dados.fontes.length) r.append(el('details', {class: 'noticias-fontes'}, el('summary', {text: 'Fontes monitoradas'}), el('p', {text: dados.fontes.join(' · ')})));
}

function falha() {
    const raiz = document.getElementById('noticiasLista');
    raiz.replaceChildren(el('div', {class: 'vazio'}, el('p', {text: 'Não foi possível carregar o radar agora. Tente de novo em instantes ou vá direto às fontes oficiais:'}),
        el('p', {class: 'noticias-links'}, OFICIAIS.map(([nome, url]) => el('a', {href: url, target: '_blank', rel: 'noopener noreferrer', text: nome})))));
    document.getElementById('noticiasRodape').replaceChildren();
}

function abre() {
    if (dados) return;
    carrega().then(render).catch(e => { console.error(e); falha(); });
}

document.querySelectorAll('.tab-btn[data-view="noticias"]').forEach(b => b.addEventListener('click', abre));
document.querySelectorAll('#noticiasFiltro button').forEach(b => b.addEventListener('click', () => {
    grupo = b.dataset.grupo;
    document.querySelectorAll('#noticiasFiltro button').forEach(x => x.classList.toggle('active', x === b));
    if (dados) render();
}));
document.getElementById('noticiasMunicipal').addEventListener('change', e => { soMunicipal = e.target.checked; if (dados) render(); });

})();
