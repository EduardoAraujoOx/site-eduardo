/**
 * Internationalization (i18n) Manager
 * Handles language switching for the entire site
 */

const I18nManager = {
    currentLang: 'pt',
    translations: null,
    supportedLangs: ['pt', 'en'],

    // Initialize
    async init() {
        // Check for saved language preference
        const savedLang = localStorage.getItem('preferredLanguage');
        if (savedLang && this.supportedLangs.includes(savedLang)) {
            this.currentLang = savedLang;
        }

        await this.loadTranslations();
        this.updateLanguageToggle();
        this.applyTranslations();
        this.setupEventListeners();
    },

    // Load translations from JSON
    async loadTranslations() {
        try {
            const response = await fetch('data/translations.json');
            this.translations = await response.json();
        } catch (error) {
            console.error('Error loading translations:', error);
        }
    },

    // Get translation by key path (e.g., 'nav.about')
    t(keyPath) {
        if (!this.translations) return keyPath;

        const keys = keyPath.split('.');
        let value = this.translations[this.currentLang];

        for (const key of keys) {
            if (value && value[key] !== undefined) {
                value = value[key];
            } else {
                return keyPath;
            }
        }

        return value;
    },

    // Switch language
    setLanguage(lang) {
        if (!this.supportedLangs.includes(lang)) return;

        this.currentLang = lang;
        localStorage.setItem('preferredLanguage', lang);

        // Update HTML lang attribute
        document.documentElement.lang = lang === 'pt' ? 'pt-BR' : 'en';

        this.updateLanguageToggle();
        this.applyTranslations();

        // Notify publications manager if it exists
        if (typeof PublicationsManager !== 'undefined') {
            PublicationsManager.setLanguage(lang);
        }

        // Dispatch custom event for other modules
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
    },

    // Update language toggle button
    updateLanguageToggle() {
        const toggle = document.getElementById('langToggle');
        if (toggle) {
            toggle.setAttribute('data-lang', this.currentLang);
            const ptBtn = toggle.querySelector('[data-value="pt"]');
            const enBtn = toggle.querySelector('[data-value="en"]');

            if (ptBtn) ptBtn.classList.toggle('active', this.currentLang === 'pt');
            if (enBtn) enBtn.classList.toggle('active', this.currentLang === 'en');
        }
    },

    // Apply translations to all elements with data-i18n attribute
    applyTranslations() {
        // Elements with data-i18n attribute for text content
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translation = this.t(key);
            if (translation !== key) {
                el.textContent = translation;
            }
        });

        // Elements with data-i18n-placeholder for input placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            const translation = this.t(key);
            if (translation !== key) {
                el.placeholder = translation;
            }
        });

        // Elements with data-i18n-aria for aria-label
        document.querySelectorAll('[data-i18n-aria]').forEach(el => {
            const key = el.getAttribute('data-i18n-aria');
            const translation = this.t(key);
            if (translation !== key) {
                el.setAttribute('aria-label', translation);
            }
        });

        // Update select options with data-i18n-option
        document.querySelectorAll('select[data-i18n-options]').forEach(select => {
            const optionsKey = select.getAttribute('data-i18n-options');
            const options = this.t(optionsKey);
            if (typeof options === 'object') {
                select.querySelectorAll('option').forEach(option => {
                    const valueKey = option.value || 'select';
                    if (options[valueKey]) {
                        option.textContent = options[valueKey];
                    }
                });
            }
        });
    },

    // Setup event listeners
    setupEventListeners() {
        // Language toggle buttons
        document.querySelectorAll('[data-lang-switch]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const lang = btn.getAttribute('data-lang-switch');
                this.setLanguage(lang);
            });
        });
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    I18nManager.init();
});
