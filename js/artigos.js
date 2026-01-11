/**
 * Artigos Loader - NYT Style Publications
 * Loads articles from JSON and renders them in the NYT-style layout
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        jsonPath: 'data/artigos.json',
        articlesPerPage: 4,
        placeholderImage: 'images/placeholder-article.jpg'
    };

    // State
    let allArticles = [];
    let displayedCount = 0;
    let featuredArticle = null;

    // DOM Elements
    const featuredContainer = document.getElementById('artigo-destaque');
    const articlesGrid = document.getElementById('artigos-lista');
    const loadMoreBtn = document.getElementById('btn-carregar-mais');
    const shareBtn = document.getElementById('btn-compartilhar');

    /**
     * Initialize the articles section
     */
    async function init() {
        try {
            const response = await fetch(CONFIG.jsonPath);
            if (!response.ok) throw new Error('Failed to load articles');

            const data = await response.json();
            allArticles = data.artigos || [];

            // Separate featured article
            featuredArticle = allArticles.find(a => a.destaque);
            const regularArticles = allArticles.filter(a => !a.destaque);
            allArticles = regularArticles;

            // Render
            if (featuredArticle) {
                renderFeaturedArticle(featuredArticle);
            }

            loadMoreArticles();

            // Setup load more button
            if (loadMoreBtn) {
                loadMoreBtn.addEventListener('click', loadMoreArticles);
                updateLoadMoreButton();
            }

            // Setup share button
            if (shareBtn) {
                shareBtn.addEventListener('click', handleShare);
            }

        } catch (error) {
            console.error('Error loading articles:', error);
            if (featuredContainer) {
                featuredContainer.innerHTML = '<p style="text-align:center;color:#666;">Não foi possível carregar os artigos.</p>';
            }
        }
    }

    /**
     * Render the featured article
     */
    function renderFeaturedArticle(article) {
        if (!featuredContainer) return;

        const imageUrl = article.imagem || CONFIG.placeholderImage;
        const articleUrl = article.linkExterno || `publicacoes/${article.slug}.html`;

        featuredContainer.innerHTML = `
            <a href="${articleUrl}" class="nyt-featured-link" target="${article.linkExterno ? '_blank' : '_self'}" rel="${article.linkExterno ? 'noopener noreferrer' : ''}">
                <div class="nyt-featured-image">
                    <img src="${imageUrl}" alt="${article.imagemAlt || article.titulo}" loading="lazy"
                         onerror="this.src='${CONFIG.placeholderImage}'">
                </div>
            </a>
            <div class="nyt-featured-content">
                <span class="nyt-category">${article.categoria}</span>
                <a href="${articleUrl}" class="nyt-featured-link" target="${article.linkExterno ? '_blank' : '_self'}" rel="${article.linkExterno ? 'noopener noreferrer' : ''}">
                    <h3 class="nyt-featured-title">${article.titulo}</h3>
                </a>
                <p class="nyt-featured-excerpt">${article.resumo}</p>
                <div class="nyt-meta">
                    <span>${article.dataFormatada}</span>
                    <span class="nyt-meta-dot"></span>
                    <span>${article.tempoLeitura} de leitura</span>
                </div>
            </div>
        `;
    }

    /**
     * Load more articles
     */
    function loadMoreArticles() {
        const articlesToShow = allArticles.slice(displayedCount, displayedCount + CONFIG.articlesPerPage);

        articlesToShow.forEach(article => {
            const articleElement = createArticleElement(article);
            if (articlesGrid) {
                articlesGrid.appendChild(articleElement);
            }
        });

        displayedCount += articlesToShow.length;
        updateLoadMoreButton();
    }

    /**
     * Create an article element
     */
    function createArticleElement(article) {
        const div = document.createElement('article');
        div.className = 'nyt-article';

        const imageUrl = article.imagem || CONFIG.placeholderImage;
        const articleUrl = article.linkExterno || `publicacoes/${article.slug}.html`;
        const target = article.linkExterno ? '_blank' : '_self';
        const rel = article.linkExterno ? 'noopener noreferrer' : '';

        div.innerHTML = `
            <div class="nyt-article-content">
                <span class="nyt-category">${article.categoria}</span>
                <a href="${articleUrl}" target="${target}" rel="${rel}" class="nyt-article-link">
                    <h4 class="nyt-article-title">${article.titulo}</h4>
                </a>
                <p class="nyt-article-excerpt">${article.resumo}</p>
                <div class="nyt-meta">
                    <span>${article.dataFormatada}</span>
                    <span class="nyt-meta-dot"></span>
                    <span>${article.tempoLeitura}</span>
                </div>
            </div>
            <a href="${articleUrl}" target="${target}" rel="${rel}" class="nyt-article-thumb">
                <img src="${imageUrl}" alt="${article.imagemAlt || article.titulo}" loading="lazy"
                     onerror="this.src='${CONFIG.placeholderImage}'">
            </a>
        `;

        return div;
    }

    /**
     * Handle share button click
     */
    async function handleShare() {
        const shareData = {
            title: 'Publicações de Eduardo Reis Araujo',
            text: 'Artigos sobre economia, finanças públicas e políticas governamentais',
            url: window.location.origin + '/#publicacoes'
        };

        try {
            if (navigator.share) {
                // Use native share on mobile
                await navigator.share(shareData);
            } else {
                // Fallback: copy to clipboard
                await navigator.clipboard.writeText(shareData.url);
                showShareFeedback('Link copiado!');
            }
        } catch (err) {
            if (err.name !== 'AbortError') {
                // User didn't cancel, try clipboard
                try {
                    await navigator.clipboard.writeText(shareData.url);
                    showShareFeedback('Link copiado!');
                } catch {
                    showShareFeedback('Erro ao compartilhar');
                }
            }
        }
    }

    /**
     * Show temporary feedback message
     */
    function showShareFeedback(message) {
        if (!shareBtn) return;
        const originalText = shareBtn.innerHTML;
        shareBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="20 6 9 17 4 12"/></svg> ${message}`;
        setTimeout(() => {
            shareBtn.innerHTML = originalText;
        }, 2000);
    }

    /**
     * Update load more button state
     */
    function updateLoadMoreButton() {
        if (!loadMoreBtn) return;

        if (displayedCount >= allArticles.length) {
            loadMoreBtn.disabled = true;
            loadMoreBtn.textContent = 'Todos os artigos carregados';
        } else {
            loadMoreBtn.disabled = false;
            const remaining = allArticles.length - displayedCount;
            loadMoreBtn.textContent = `Carregar mais (${remaining} restantes)`;
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
