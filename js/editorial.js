/**
 * Editorial Homepage JavaScript
 * Loads and displays articles from JSON in editorial layout
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
    let sidebarArticles = [];

    // DOM Elements
    const featuredContainer = document.getElementById('featuredArticle');
    const articlesListContainer = document.getElementById('articlesList');
    const sidebarContainer = document.getElementById('sidebarArticles');
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mainNav = document.getElementById('mainNav');
    const searchBtn = document.getElementById('searchBtn');
    const langToggle = document.getElementById('langToggle');

    /**
     * Initialize the editorial homepage
     */
    async function init() {
        try {
            // Load articles
            await loadArticles();

            // Setup event listeners
            setupEventListeners();

            // Render articles
            renderFeaturedArticle();
            renderArticlesList();
            renderSidebar();

        } catch (error) {
            console.error('Error initializing editorial homepage:', error);
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

        // Separate featured article
        featuredArticle = articles.find(a => a.destaque) || articles[0];
        allArticles = articles.filter(a => a.id !== featuredArticle.id);

        // Sidebar articles (first 5 non-featured)
        sidebarArticles = allArticles.slice(0, 5);
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
        if (mobileMenuBtn && mainNav) {
            mobileMenuBtn.addEventListener('click', () => {
                mobileMenuBtn.classList.toggle('active');
                mainNav.classList.toggle('active');
            });
        }

        // Search button (placeholder functionality)
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                alert('Funcionalidade de busca em desenvolvimento');
            });
        }

        // Language toggle
        if (langToggle) {
            const langButtons = langToggle.querySelectorAll('button[data-lang]');
            langButtons.forEach(btn => {
                btn.addEventListener('click', () => {
                    langButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    // Language switch functionality would go here
                });
            });
        }

        // Close mobile menu when clicking nav links
        const navLinks = mainNav?.querySelectorAll('a');
        navLinks?.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenuBtn?.classList.remove('active');
                mainNav?.classList.remove('active');
            });
        });
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
            <a href="${articleUrl}" class="featured-image">
                <img src="${imageUrl}" alt="${article.imagemAlt || article.titulo}" loading="eager"
                     onerror="this.src='${CONFIG.placeholderImage}'">
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
            <div class="article-content-wrapper">
                <div class="article-category">${article.categoria}</div>
                <h3 class="article-title">
                    <a href="${articleUrl}">${article.titulo}</a>
                </h3>
                <p class="article-excerpt">${article.subtitulo || article.resumo}</p>
                <div class="article-meta">
                    <span>${article.dataFormatada}</span>
                    <span class="meta-dot"></span>
                    <span>${article.tempoLeitura}</span>
                    ${article.novo ? '<span class="tag-new">Novo</span>' : ''}
                </div>
            </div>
            <a href="${articleUrl}" class="article-thumbnail">
                <img src="${imageUrl}" alt="${article.imagemAlt || article.titulo}" loading="lazy"
                     onerror="this.src='${CONFIG.placeholderImage}'">
            </a>
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
     * Update load more button state
     */
    function updateLoadMoreButton() {
        if (!loadMoreBtn) return;

        if (displayedCount >= allArticles.length) {
            loadMoreBtn.disabled = true;
            loadMoreBtn.textContent = 'Todos os artigos carregados';
            loadMoreBtn.style.display = 'none';
        } else {
            loadMoreBtn.disabled = false;
            const remaining = allArticles.length - displayedCount;
            loadMoreBtn.textContent = `Carregar mais (${remaining} artigos)`;
        }
    }

    /**
     * Render sidebar articles
     */
    function renderSidebar() {
        if (!sidebarContainer || !sidebarArticles.length) return;

        sidebarArticles.forEach(article => {
            const articleDiv = document.createElement('a');
            articleDiv.href = `publicacoes/${article.slug}.html`;
            articleDiv.className = 'sidebar-article';

            articleDiv.innerHTML = `
                <div class="sidebar-article-category">${article.categoria}</div>
                <h4 class="sidebar-article-title">${article.titulo}</h4>
                <div class="sidebar-article-date">${article.dataFormatada}</div>
            `;

            sidebarContainer.appendChild(articleDiv);
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

    /**
     * Format date to Portuguese
     */
    function formatDate(dateString) {
        const date = new Date(dateString);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        // Check if today
        if (date.toDateString() === today.toDateString()) {
            return 'Hoje';
        }

        // Check if yesterday
        if (date.toDateString() === yesterday.toDateString()) {
            return 'Ontem';
        }

        // Format as "DD de mês de YYYY"
        const months = [
            'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
            'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
        ];

        const day = date.getDate();
        const month = months[date.getMonth()];
        const year = date.getFullYear();

        return `${day} de ${month} de ${year}`;
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
