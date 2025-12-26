/**
 * Publications Manager
 * Handles loading, rendering, and managing publications from JSON
 */

const PublicationsManager = {
    publications: [],
    currentLang: 'pt',
    translations: null,

    // Initialize the manager
    async init() {
        try {
            await this.loadPublications();
            await this.loadTranslations();
            this.render();
        } catch (error) {
            console.error('Error initializing publications:', error);
        }
    },

    // Load publications from JSON
    async loadPublications() {
        try {
            const response = await fetch('data/publications.json');
            const data = await response.json();
            this.publications = data.publications;
        } catch (error) {
            console.error('Error loading publications:', error);
            this.publications = [];
        }
    },

    // Load translations
    async loadTranslations() {
        try {
            const response = await fetch('data/translations.json');
            this.translations = await response.json();
        } catch (error) {
            console.error('Error loading translations:', error);
            this.translations = null;
        }
    },

    // Get sorted publications (pinned first, then by date)
    getSortedPublications() {
        return [...this.publications].sort((a, b) => {
            // Pinned items first
            if (a.pinned && !b.pinned) return -1;
            if (!a.pinned && b.pinned) return 1;
            // Then sort by date (newest first)
            return new Date(b.date) - new Date(a.date);
        });
    },

    // Group publications by year
    getPublicationsByYear() {
        const sorted = this.getSortedPublications();
        const grouped = {};

        sorted.forEach(pub => {
            if (!grouped[pub.year]) {
                grouped[pub.year] = [];
            }
            grouped[pub.year].push(pub);
        });

        return grouped;
    },

    // Format date for display
    formatDate(dateStr) {
        const [year, month] = dateStr.split('-');
        const monthNames = this.translations?.[this.currentLang]?.months || {
            '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março', '04': 'Abril',
            '05': 'Maio', '06': 'Junho', '07': 'Julho', '08': 'Agosto',
            '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
        };
        return `${monthNames[month]} ${year}`;
    },

    // Get text based on current language
    getText(pub, field) {
        if (this.currentLang === 'en' && pub[`${field}_en`]) {
            return pub[`${field}_en`];
        }
        return pub[field];
    },

    // Render publications to the page
    render() {
        const container = document.querySelector('.publications-container');
        if (!container) return;

        const publicationsByYear = this.getPublicationsByYear();
        const years = Object.keys(publicationsByYear).sort((a, b) => b - a);
        const t = this.translations?.[this.currentLang]?.publications || {};

        let html = '';

        years.forEach(year => {
            html += `
                <div class="publication-year">
                    <h3 class="year-header">${year}</h3>
                    <div class="publications-grid">
            `;

            publicationsByYear[year].forEach(pub => {
                const pinnedBadge = pub.pinned ?
                    `<span class="pinned-badge">${t.pinned || 'Destaque'}</span>` : '';

                html += `
                    <article class="publication-card ${pub.pinned ? 'pinned' : ''}" data-id="${pub.id}">
                        <div class="publication-header">
                            <div class="publication-info">
                                <h3>${this.getText(pub, 'title')}</h3>
                                <p class="source">${pub.source}</p>
                            </div>
                            <span class="publication-date">${this.formatDate(pub.date)}</span>
                        </div>
                        ${pinnedBadge}
                        <p>${this.getText(pub, 'description')}</p>
                        <a href="${pub.url}" target="_blank" rel="noopener noreferrer" class="read-more">
                            ${t.readMore || 'Ler artigo completo'} <span aria-hidden="true">&#8594;</span>
                        </a>
                    </article>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    },

    // Change language and re-render
    setLanguage(lang) {
        this.currentLang = lang;
        this.render();
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    PublicationsManager.init();
});

// Export for use in admin
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PublicationsManager;
}
