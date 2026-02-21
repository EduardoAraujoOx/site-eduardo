/**
 * Search — sistema de busca unificado
 * Cobre: Publicações (artigos.json), Ensino e Indicadores (search-index.json)
 *
 * Uso: incluir <script src="/js/search.js"></script> em qualquer página.
 * Qualquer elemento com id="searchBtn" ou data-search-trigger terá o clique vinculado.
 * Atalho de teclado: Ctrl+K / Cmd+K
 */

(function () {
    'use strict';

    /* =====================================================
       Estado
       ===================================================== */
    var indexData = null;   // search-index.json (Ensino + Indicadores)
    var artigos = null;     // artigos.json convertido para formato comum
    var isLoading = false;
    var isOpen = false;
    var overlay = null;
    var inputEl = null;
    var resultsEl = null;
    var debounceTimer = null;

    var SECTION_ORDER = ['Publicações', 'Ensino', 'Indicadores'];

    /* =====================================================
       Injeção do modal no DOM
       ===================================================== */
    function injectModal() {
        var container = document.createElement('div');
        container.innerHTML = [
            '<div class="srch-overlay" id="srchOverlay" role="dialog" aria-modal="true" aria-label="Buscar no site">',
            '  <div class="srch-container">',
            '    <div class="srch-input-row">',
            '      <svg class="srch-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">',
            '        <circle cx="11" cy="11" r="8"></circle>',
            '        <path d="m21 21-4.35-4.35"></path>',
            '      </svg>',
            '      <input',
            '        class="srch-input"',
            '        id="srchInput"',
            '        type="search"',
            '        placeholder="Buscar publicações, notas de aula, indicadores\u2026"',
            '        autocomplete="off"',
            '        autocorrect="off"',
            '        autocapitalize="off"',
            '        spellcheck="false"',
            '      />',
            '      <button class="srch-close" id="srchClose" aria-label="Fechar busca">',
            '        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">',
            '          <path d="M18 6L6 18M6 6l12 12"/>',
            '        </svg>',
            '      </button>',
            '    </div>',
            '    <div class="srch-results" id="srchResults" role="listbox" aria-label="Resultados da busca"></div>',
            '    <div class="srch-footer">',
            '      <span class="srch-hint"><kbd class="srch-kbd">Esc</kbd> fechar</span>',
            '      <span class="srch-hint"><kbd class="srch-kbd">\u2191\u2193</kbd> navegar</span>',
            '      <span class="srch-hint"><kbd class="srch-kbd">\u21b5</kbd> abrir</span>',
            '    </div>',
            '  </div>',
            '</div>'
        ].join('\n');

        document.body.appendChild(container.firstElementChild);

        overlay = document.getElementById('srchOverlay');
        inputEl = document.getElementById('srchInput');
        resultsEl = document.getElementById('srchResults');

        // Fechar ao clicar no fundo
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeSearch();
        });

        document.getElementById('srchClose').addEventListener('click', closeSearch);
        inputEl.addEventListener('input', handleInput);
        inputEl.addEventListener('keydown', handleKeydown);
    }

    /* =====================================================
       Abrir / fechar
       ===================================================== */
    function openSearch() {
        if (!overlay) injectModal();
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        isOpen = true;
        inputEl.value = '';
        showInitialState();
        // Foco com delay mínimo para garantir transição CSS
        requestAnimationFrame(function () { inputEl.focus(); });
        // Carregar dados na primeira abertura
        if (!indexData || !artigos) loadData();
    }

    function closeSearch() {
        if (!overlay) return;
        overlay.classList.remove('active');
        document.body.style.overflow = '';
        isOpen = false;
    }

    /* =====================================================
       Carregamento de dados
       ===================================================== */
    function loadData() {
        if (isLoading) return;
        isLoading = true;

        var promises = [
            fetch('/data/search-index.json').then(function (r) { return r.json(); }),
            fetch('/data/artigos.json').then(function (r) { return r.json(); })
        ];

        Promise.all(promises).then(function (results) {
            indexData = results[0];

            var raw = (results[1].artigos || []);
            artigos = raw.map(function (a) {
                return {
                    id: 'artigo-' + a.id,
                    tipo: 'Publicações',
                    secaoLabel: a.categoria,
                    titulo: a.titulo,
                    resumo: a.subtitulo || a.resumo || '',
                    tags: a.tags || [],
                    url: '/publicacoes/' + a.slug + '.html',
                    dataFormatada: a.dataFormatada || ''
                };
            });

            isLoading = false;

            // Se o usuário já digitou algo enquanto carregava
            if (isOpen && inputEl && inputEl.value.trim()) {
                handleInput();
            }
        }).catch(function (err) {
            console.error('[Search] Erro ao carregar índice:', err);
            isLoading = false;
        });
    }

    /* =====================================================
       Motor de busca
       ===================================================== */
    function normalize(str) {
        return (str || '')
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-z0-9\s]/g, ' ');
    }

    function scoreItem(item, q) {
        var titleN  = normalize(item.titulo);
        var resumoN = normalize(item.resumo);
        var tagsN   = normalize((item.tags || []).join(' '));
        var secaoN  = normalize(item.secaoLabel || '');

        // Título exato: pontuação máxima
        if (titleN.indexOf(q) !== -1) return 3;
        // Tags: pontuação alta
        if (tagsN.indexOf(q) !== -1) return 2;
        // Resumo / seção: pontuação baixa
        if (resumoN.indexOf(q) !== -1 || secaoN.indexOf(q) !== -1) return 1;
        return 0;
    }

    function doSearch(rawQuery) {
        var q = normalize(rawQuery.trim());
        if (!q || q.length < 2) return [];

        var all = (artigos || []).concat(indexData || []);

        var scored = [];
        for (var i = 0; i < all.length; i++) {
            var score = scoreItem(all[i], q);
            if (score > 0) scored.push({ item: all[i], score: score });
        }

        scored.sort(function (a, b) { return b.score - a.score; });

        return scored.map(function (s) { return s.item; });
    }

    /* =====================================================
       Destaque de termos
       ===================================================== */
    function escHtml(s) {
        return (s || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function highlight(text, rawQuery) {
        var safe = escHtml(text);
        if (!rawQuery) return safe;
        var q = rawQuery.trim();
        if (!q || q.length < 2) return safe;

        // Escapa caracteres especiais de regex
        var escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        try {
            var re = new RegExp('(' + escaped + ')', 'gi');
            return safe.replace(re, '<mark>$1</mark>');
        } catch (e) {
            return safe;
        }
    }

    /* =====================================================
       Renderização
       ===================================================== */
    function showInitialState() {
        resultsEl.innerHTML =
            '<div class="srch-empty">' +
            '  <p>Busque em publicações, notas de aula e indicadores</p>' +
            '</div>';
    }

    function showNoResults(query) {
        resultsEl.innerHTML =
            '<div class="srch-empty">' +
            '  <p>Nenhum resultado para <strong>"' + escHtml(query) + '"</strong></p>' +
            '</div>';
    }

    function showLoading() {
        resultsEl.innerHTML =
            '<div class="srch-empty">' +
            '  <p>Carregando\u2026</p>' +
            '</div>';
    }

    function renderResults(items, query) {
        if (!items.length) {
            showNoResults(query);
            return;
        }

        // Agrupar por tipo
        var groups = {};
        for (var i = 0; i < items.length; i++) {
            var tipo = items[i].tipo;
            if (!groups[tipo]) groups[tipo] = [];
            groups[tipo].push(items[i]);
        }

        var html = '';
        SECTION_ORDER.forEach(function (tipo) {
            if (!groups[tipo]) return;
            html += '<div class="srch-group-header">' + escHtml(tipo) + '</div>';
            groups[tipo].forEach(function (item) {
                html += renderItem(item, query);
            });
        });

        resultsEl.innerHTML = html;
    }

    function renderItem(item, query) {
        var rawExcerpt = (item.resumo || '').slice(0, 160);
        if ((item.resumo || '').length > 160) rawExcerpt += '\u2026';

        var badge = item.secaoLabel
            ? '<span class="srch-badge">' + escHtml(item.secaoLabel) + '</span>'
            : '';
        var dateMeta = item.dataFormatada
            ? '<span class="srch-date">' + escHtml(item.dataFormatada) + '</span>'
            : '';
        var excerpt = rawExcerpt
            ? '<div class="srch-result-excerpt">' + highlight(rawExcerpt, query) + '</div>'
            : '';

        return [
            '<a href="' + escHtml(item.url) + '" class="srch-result" role="option">',
            '  <div class="srch-result-title">' + highlight(item.titulo, query) + '</div>',
            '  <div class="srch-result-meta">' + badge + dateMeta + '</div>',
            excerpt,
            '</a>'
        ].join('');
    }

    /* =====================================================
       Handlers de input
       ===================================================== */
    function handleInput() {
        var q = inputEl.value.trim();
        clearTimeout(debounceTimer);

        if (!q) {
            showInitialState();
            return;
        }

        if (isLoading) {
            showLoading();
            return;
        }

        debounceTimer = setTimeout(function () {
            var results = doSearch(q);
            renderResults(results, q);
        }, 120);
    }

    function handleKeydown(e) {
        if (e.key === 'Escape') {
            closeSearch();
            return;
        }

        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            var items = Array.prototype.slice.call(resultsEl.querySelectorAll('.srch-result'));
            if (!items.length) return;

            var focused = resultsEl.querySelector('.srch-result.focused');
            var idx = items.indexOf(focused);

            if (e.key === 'ArrowDown') {
                idx = Math.min(idx + 1, items.length - 1);
            } else {
                idx = Math.max(idx - 1, 0);
            }

            items.forEach(function (el) { el.classList.remove('focused'); });
            items[idx].classList.add('focused');
            items[idx].scrollIntoView({ block: 'nearest' });
            return;
        }

        if (e.key === 'Enter') {
            var focused = resultsEl.querySelector('.srch-result.focused');
            if (focused) focused.click();
        }
    }

    /* =====================================================
       Atalho global de teclado
       ===================================================== */
    document.addEventListener('keydown', function (e) {
        // Cmd+K ou Ctrl+K — abre ou fecha
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            if (isOpen) closeSearch();
            else openSearch();
            return;
        }
        // Esc — fecha se aberto
        if (e.key === 'Escape' && isOpen) {
            closeSearch();
        }
    });

    /* =====================================================
       Vinculação aos botões da página
       ===================================================== */
    function attachToButtons() {
        var btns = document.querySelectorAll('#searchBtn, [data-search-trigger]');
        for (var i = 0; i < btns.length; i++) {
            btns[i].addEventListener('click', openSearch);
        }
    }

    /* =====================================================
       Inicialização
       ===================================================== */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', attachToButtons);
    } else {
        attachToButtons();
    }

    // API pública (opcional)
    window.siteSearch = { open: openSearch, close: closeSearch };

})();
