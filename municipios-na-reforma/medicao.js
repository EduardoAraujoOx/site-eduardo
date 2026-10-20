/* GA4 opcional: só na produção, com ID válido e autorização do visitante.
   Desative a medição otimizada no fluxo Web do GA4: os eventos são definidos aqui.
   Veja ../docs/municipios-seo-medicao.md para configurar e validar a propriedade. */
(function () {
'use strict';

const CHAVE = 'mnr-medicao-v1';
const VALIDADE = 180 * 24 * 60 * 60 * 1000;
const HOSTS = ['municipiosnareforma.com.br', 'www.municipiosnareforma.com.br'];
const EVENTOS = new Set([
    'aba', 'mapa_uf', 'trilho_uf', 'trilho_municipio', 'ranking_ordem', 'ranking_uf',
    'ranking_municipio', 'busca_municipio', 'local_sugerido', 'clique_mapa_uf',
    'clique_mapa', 'abrir_memoria', 'copiar_link', 'imprimir_ficha', 'compartilhar',
    'sens_ano_base', 'cadastro', 'clique_contato', 'livro_cadastro', 'contato_enviado',
    'servico_abrir'
]);
const OPCOES = {
    uf: 'AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO BR'.split(' '),
    aba: ['visao-geral', 'municipio', 'rankings', 'agenda', 'memoria', 'metodologia'],
    canal: ['whatsapp', 'email', 'formulario'],
    origem: ['gps', 'conexao', 'memoria'],
    local: ['aba', 'ficha', 'memoria', 'flutuante'],
    ordem: ['pct', 'rs']
};
let id = '', autorizada = false, carregada = false, banner = null, focoAnterior = null;

function lerEscolha() {
    try {
        const registro = JSON.parse(localStorage.getItem(CHAVE));
        if (registro && ['granted', 'denied'].includes(registro.escolha) &&
            Number.isFinite(registro.em) && registro.em <= Date.now() && Date.now() - registro.em < VALIDADE) {
            return registro.escolha;
        }
    } catch (_) { /* armazenamento indisponível: perguntar a cada visita */ }
    return null;
}

function guardarEscolha(escolha) {
    try { localStorage.setItem(CHAVE, JSON.stringify({escolha, em: Date.now()})); }
    catch (_) { /* a escolha continua valendo nesta página */ }
}

function paginaPublica() {
    // Não enviar parâmetros arbitrários da URL, fragmentos ou texto de formulários.
    const url = new URL('https://municipiosnareforma.com.br/');
    const municipio = new URLSearchParams(location.search).get('m');
    if (/^\d{7}$/.test(municipio || '')) url.searchParams.set('m', municipio);
    return url.href;
}

function referenciaPublica() {
    try {
        const url = new URL(document.referrer);
        return /^https?:$/.test(url.protocol) ? url.origin + '/' : '';
    } catch (_) { return ''; }
}

function gtag() { window.dataLayer.push(arguments); }

function carregar() {
    if (carregada) return;
    carregada = true;
    window['ga-disable-' + id] = false;
    window.dataLayer = window.dataLayer || [];
    gtag('consent', 'default', {
        analytics_storage: 'denied', ad_storage: 'denied',
        ad_user_data: 'denied', ad_personalization: 'denied'
    });
    gtag('consent', 'update', {analytics_storage: 'granted'});
    gtag('js', new Date());
    gtag('config', id, {
        send_page_view: false,
        allow_google_signals: false,
        allow_ad_personalization_signals: false,
        page_location: paginaPublica(),
        page_referrer: referenciaPublica()
    });
    gtag('event', 'page_view', {page_location: paginaPublica(), page_referrer: referenciaPublica()});
    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id);
    document.head.appendChild(script);
}

function limparCookies() {
    const dominios = new Set([location.hostname, '.' + location.hostname, 'municipiosnareforma.com.br', '.municipiosnareforma.com.br']);
    document.cookie.split(';').forEach(parte => {
        const nome = parte.trim().split('=')[0];
        if (!/^_ga(?:_[a-z0-9_]+)?$/i.test(nome)) return;
        const expirar = nome + '=; Max-Age=0; Path=/; SameSite=Lax';
        document.cookie = expirar;
        dominios.forEach(dominio => { document.cookie = expirar + '; Domain=' + dominio; });
    });
}

function fecharBanner() {
    if (banner) banner.remove();
    banner = null;
    document.body.classList.remove('medicao-pendente');
    if (focoAnterior && focoAnterior.isConnected) focoAnterior.focus({preventScroll: true});
    focoAnterior = null;
}

function escolher(aceitar) {
    const estavaCarregada = carregada;
    autorizada = aceitar;
    guardarEscolha(aceitar ? 'granted' : 'denied');
    fecharBanner();
    if (aceitar) carregar();
    else {
        window['ga-disable-' + id] = true;
        limparCookies();
        // Recarregar retira a biblioteca da página, sem iniciar pings sem cookies.
        if (estavaCarregada) location.reload();
    }
}

function abrirBanner(porPreferencias) {
    if (banner) return;
    focoAnterior = porPreferencias ? document.activeElement : null;
    banner = document.createElement('section');
    banner.className = 'medicao-aviso';
    banner.setAttribute('aria-labelledby', 'medicaoTitulo');
    banner.innerHTML = '<h2 id="medicaoTitulo" tabindex="-1">Podemos medir o uso do painel?</h2>' +
        '<p>Com sua autorização, usamos o Google Analytics para contar visitas e cliques. Você pode consultar todo o painel sem aceitar e mudar sua escolha na <a href="#view-privacidade" data-medicao-privacidade>política de privacidade</a>.</p>' +
        '<div class="medicao-acoes"><button type="button" class="btn btn-gold" data-medicao-aceitar>Aceitar medição</button>' +
        '<button type="button" class="btn btn-ghost" data-medicao-recusar>Continuar sem medição</button></div>';
    banner.querySelector('[data-medicao-aceitar]').addEventListener('click', () => escolher(true));
    banner.querySelector('[data-medicao-recusar]').addEventListener('click', () => escolher(false));
    banner.querySelector('[data-medicao-privacidade]').addEventListener('click', e => {
        e.preventDefault();
        const link = document.querySelector('.site-foot a[data-ir="privacidade"]');
        if (link) link.click();
    });
    document.body.appendChild(banner);
    document.body.classList.add('medicao-pendente');
    if (porPreferencias) banner.querySelector('h2').focus({preventScroll: true});
}

function iniciar(identificador) {
    if (id || !/^G-[A-Z0-9]{6,20}$/.test(identificador || '') || !HOSTS.includes(location.hostname)) return;
    id = identificador;
    const aviso = document.getElementById('privAnalytics');
    if (aviso) aviso.textContent = 'Com sua autorização, usamos o Google Analytics 4 (Google) para medir visitas e ações no painel, por meio de cookies de audiência. A medição é opcional e os recursos de publicidade ficam desativados. Os eventos definidos pelo portal não incluem nome, e-mail, telefone nem texto de formulários. A escolha fica guardada neste navegador por até 180 dias e pode ser alterada no botão abaixo. Os dados de uso são processados pelo Google, inclusive fora do Brasil; consulte também policies.google.com/privacy.';
    const preferencias = document.getElementById('medicaoPreferencias');
    if (preferencias) {
        preferencias.hidden = false;
        preferencias.addEventListener('click', () => abrirBanner(true));
    }
    const escolha = lerEscolha();
    if (escolha === 'granted') { autorizada = true; carregar(); }
    else if (escolha === 'denied') limparCookies();
    else abrirBanner(false);
}

function registrar(evento, params) {
    if (!autorizada || !carregada || !EVENTOS.has(evento)) return;
    const dados = {};
    const entrada = params || {};
    Object.keys(OPCOES).forEach(chave => {
        if (OPCOES[chave].includes(entrada[chave])) dados[chave] = entrada[chave];
    });
    if (/^\d{7}$/.test(String(entrada.municipio_codigo || ''))) dados.municipio_codigo = String(entrada.municipio_codigo);
    if (/^20(?:1[9]|2[0-9]|3[0-3])$/.test(String(entrada.ano || ''))) dados.ano = String(entrada.ano);
    if (typeof entrada.contato === 'boolean') dados.contato = entrada.contato;
    dados.page_location = paginaPublica();
    gtag('event', evento, dados);
}

window.MnrMedicao = {iniciar, registrar};
})();
