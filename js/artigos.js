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
        const articleUrl = `publicacoes/${article.slug}.html`;

        featuredContainer.innerHTML = `
            <a href="${articleUrl}" class="nyt-featured-link">
                <div class="nyt-featured-image">
                    <img src="${imageUrl}" alt="${article.imagemAlt || article.titulo}" loading="lazy"
                         onerror="this.src='${CONFIG.placeholderImage}'">
                </div>
            </a>
            <div class="nyt-featured-content">
                <span class="nyt-category">${article.categoria}</span>
                <a href="${articleUrl}" class="nyt-featured-link">
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
        const articleUrl = `publicacoes/${article.slug}.html`;

        div.innerHTML = `
            <div class="nyt-article-content">
                <span class="nyt-category">${article.categoria}</span>
                <a href="${articleUrl}" class="nyt-article-link">
                    <h4 class="nyt-article-title">${article.titulo}</h4>
                </a>
                <p class="nyt-article-excerpt">${article.resumo}</p>
                <div class="nyt-meta">
                    <span>${article.dataFormatada}</span>
                    <span class="nyt-meta-dot"></span>
                    <span>${article.tempoLeitura}</span>
                </div>
            </div>
            <a href="${articleUrl}" class="nyt-article-thumb">
                <img src="${imageUrl}" alt="${article.imagemAlt || article.titulo}" loading="lazy"
                     onerror="this.src='${CONFIG.placeholderImage}'">
            </a>
        `;

        return div;
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
