/**
 * Editorial Homepage JavaScript v2
 * Loads and displays articles from JSON
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        jsonPath: 'data/artigos.json',
        articlesPerPage: 4,
        placeholderImage: 'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=800&h=450&fit=crop'
    };

    // State
    let allArticles = [];
    let displayedCount = 0;
    let featuredArticle = null;

    // DOM Elements
    const featuredContainer = document.getElementById('featuredArticle');
    const articlesListContainer = document.getElementById('articleList');
    const sidebarContainer = document.getElementById('sidebarList');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileMenuClose = document.getElementById('mobileMenuClose');
    const searchBtn = document.getElementById('searchBtn');
    const langSwitch = document.getElementById('langSwitch');

    /**
     * Initialize
     */
    async function init() {
        try {
            // Load articles
            await loadArticles();

            // Setup event listeners
            setupEventListeners();

            // Render content
            renderFeaturedArticle();
            renderArticlesList();
            renderSidebar();

        } catch (error) {
            console.error('Error initializing:', error);
            showError();
        }
    }

    /**
     * Load articles from JSON
     */
    async function loadArticles() {
        const response = await fetch(CONFIG.jsonPath);
        if (!response.ok) {
            throw new Error('Failed to load articles');
        }

        const data = await response.json();
        const articles = data.artigos || [];

        // Sort by date (newest first)
        articles.sort((a, b) => new Date(b.data) - new Date(a.data));

        // Find featured article
        featuredArticle = articles.find(a => a.destaque) || articles[0];
        allArticles = articles.filter(a => a.id !== featuredArticle.id);
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Load more button
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', loadMoreArticles);
        }

        // Mobile menu toggle
        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', toggleMobileMenu);
        }

        if (mobileMenuClose) {
            mobileMenuClose.addEventListener('click', toggleMobileMenu);
        }

        // Close mobile menu when clicking links
        const mobileNavLinks = document.querySelectorAll('.mobile-menu-nav a');
        mobileNavLinks.forEach(link => {
            link.addEventListener('click', () => {
                toggleMobileMenu();
            });
        });

        // Language switch
        if (langSwitch) {
            const langLinks = langSwitch.querySelectorAll('a[data-lang]');
            langLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    langLinks.forEach(l => l.classList.remove('active'));
                    link.classList.add('active');
                    // Language switch functionality would go here
                });
            });
        }
    }

    /**
     * Toggle mobile menu
     */
    function toggleMobileMenu() {
        if (mobileMenu) {
            mobileMenu.classList.toggle('active');
            document.body.style.overflow = mobileMenu.classList.contains('active') ? 'hidden' : '';
        }
    }

    /**
     * Render featured article
     */
    function renderFeaturedArticle() {
        if (!featuredContainer || !featuredArticle) return;

        const article = featuredArticle;
        const articleUrl = `publicacoes/${article.slug}.html`;
        const imageUrl = article.imagem || CONFIG.placeholderImage;

        featuredContainer.innerHTML = `
            <a href="${articleUrl}" class="featured-image-link">
                <img
                    src="${imageUrl}"
                    alt="${article.imagemAlt || article.titulo}"
                    class="featured-image"
                    loading="eager"
                    onerror="this.src='${CONFIG.placeholderImage}'"
                >
            </a>
            <div class="featured-category">${article.categoria}</div>
            <h2 class="featured-title">
                <a href="${articleUrl}">${article.titulo}</a>
            </h2>
            <p class="featured-subtitle">${article.subtitulo}</p>
            <div class="featured-meta">
                <span>${article.dataFormatada}</span>
                <span class="meta-dot"></span>
                <span>${article.tempoLeitura} de leitura</span>
                ${article.novo ? '<span class="tag-new">Novo</span>' : ''}
            </div>
        `;
    }

    /**
     * Render articles list
     */
    function renderArticlesList() {
        if (!articlesListContainer) return;

        const articlesToShow = allArticles.slice(displayedCount, displayedCount + CONFIG.articlesPerPage);

        articlesToShow.forEach(article => {
            const articleElement = createArticleElement(article);
            articlesListContainer.appendChild(articleElement);
        });

        displayedCount += articlesToShow.length;
        updateLoadMoreButton();
    }

    /**
     * Create article element
     */
    function createArticleElement(article) {
        const articleDiv = document.createElement('article');
        articleDiv.className = 'article-item';

        const articleUrl = `publicacoes/${article.slug}.html`;
        const imageUrl = article.imagem || CONFIG.placeholderImage;

        articleDiv.innerHTML = `
            <a href="${articleUrl}" class="article-thumb-link">
                <img
                    src="${imageUrl}"
                    alt="${article.imagemAlt || article.titulo}"
                    class="article-thumb"
                    loading="lazy"
                    onerror="this.src='${CONFIG.placeholderImage}'"
                >
            </a>
            <div class="article-info">
                <h3 class="article-title">
                    <a href="${articleUrl}">${article.titulo}</a>
                </h3>
                <div class="article-meta">
                    <span class="article-category">${article.categoria}</span>
                    <span class="meta-dot"></span>
                    <span>${article.dataFormatada}</span>
                    ${article.novo ? '<span class="meta-dot"></span><span class="tag-new">Novo</span>' : ''}
                </div>
            </div>
        `;

        return articleDiv;
    }

    /**
     * Load more articles
     */
    function loadMoreArticles() {
        renderArticlesList();
    }

    /**
     * Update load more button
     */
    function updateLoadMoreButton() {
        if (!loadMoreBtn) return;

        if (displayedCount >= allArticles.length) {
            loadMoreBtn.textContent = 'Não há mais artigos';
            loadMoreBtn.disabled = true;
        } else {
            const remaining = allArticles.length - displayedCount;
            loadMoreBtn.textContent = `Carregar mais artigos (${remaining})`;
            loadMoreBtn.disabled = false;
        }
    }

    /**
     * Render sidebar
     */
    function renderSidebar() {
        if (!sidebarContainer) return;

        const sidebarArticles = allArticles.slice(0, 5);

        sidebarArticles.forEach(article => {
            const li = document.createElement('li');
            li.className = 'sidebar-item';

            const articleUrl = `publicacoes/${article.slug}.html`;

            li.innerHTML = `
                <a href="${articleUrl}">
                    <h4 class="sidebar-item-title">${article.titulo}</h4>
                </a>
                <div class="sidebar-item-meta">
                    <span class="sidebar-item-category">${article.categoria}</span>
                    <span class="meta-dot"></span>
                    <span>${article.dataFormatada}</span>
                </div>
            `;

            sidebarContainer.appendChild(li);
        });
    }

    /**
     * Show error message
     */
    function showError() {
        if (featuredContainer) {
            featuredContainer.innerHTML = `
                <p style="text-align:center;color:#888;padding:2rem;">
                    Não foi possível carregar os artigos. Por favor, tente novamente mais tarde.
                </p>
            `;
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
