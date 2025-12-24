/**
 * Eduardo Araujo - Personal Website
 * Main JavaScript
 *
 * Features:
 * - Loading screen management
 * - Mobile menu toggle
 * - Smooth scrolling
 * - Scroll animations (Intersection Observer)
 * - Header scroll effects
 * - Lazy loading for images
 * - Accessibility improvements
 */

(function() {
    'use strict';

    // ==========================================================================
    // Configuration
    // ==========================================================================

    const CONFIG = {
        loadingDelay: 500,
        scrollThreshold: 100,
        animationThreshold: 0.1,
        lazyLoadMargin: '50px'
    };

    // ==========================================================================
    // DOM Elements
    // ==========================================================================

    const elements = {
        loading: document.getElementById('loading'),
        menuToggle: document.getElementById('menuToggle'),
        navLinks: document.getElementById('navLinks'),
        header: document.querySelector('header'),
        sections: document.querySelectorAll('section'),
        images: document.querySelectorAll('img[data-src]'),
        yearElement: document.querySelector('footer p')
    };

    // ==========================================================================
    // Loading Screen
    // ==========================================================================

    function hideLoadingScreen() {
        if (elements.loading) {
            setTimeout(() => {
                elements.loading.classList.add('hidden');
                // Remove from DOM after animation
                setTimeout(() => {
                    elements.loading.style.display = 'none';
                }, 500);
            }, CONFIG.loadingDelay);
        }
    }

    // ==========================================================================
    // Mobile Menu
    // ==========================================================================

    function initMobileMenu() {
        if (!elements.menuToggle || !elements.navLinks) return;

        elements.menuToggle.addEventListener('click', toggleMenu);

        // Close menu when clicking a link
        elements.navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeMenu);
        });

        // Close menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && elements.navLinks.classList.contains('active')) {
                closeMenu();
            }
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!elements.navLinks.contains(e.target) &&
                !elements.menuToggle.contains(e.target) &&
                elements.navLinks.classList.contains('active')) {
                closeMenu();
            }
        });
    }

    function toggleMenu() {
        const isActive = elements.navLinks.classList.toggle('active');
        elements.menuToggle.classList.toggle('active');

        // Update ARIA attributes
        elements.menuToggle.setAttribute('aria-expanded', isActive);

        // Prevent body scroll when menu is open
        document.body.style.overflow = isActive ? 'hidden' : '';
    }

    function closeMenu() {
        elements.menuToggle.classList.remove('active');
        elements.navLinks.classList.remove('active');
        elements.menuToggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    }

    // ==========================================================================
    // Smooth Scrolling
    // ==========================================================================

    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', handleSmoothScroll);
        });
    }

    function handleSmoothScroll(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        const target = document.querySelector(targetId);

        if (target) {
            const headerOffset = 80;
            const elementPosition = target.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });

            // Update URL without jumping
            history.pushState(null, null, targetId);
        }
    }

    // ==========================================================================
    // Scroll Animations
    // ==========================================================================

    function initScrollAnimations() {
        const observer = new IntersectionObserver(handleIntersection, {
            threshold: CONFIG.animationThreshold,
            rootMargin: '0px 0px -50px 0px'
        });

        elements.sections.forEach(section => {
            observer.observe(section);
        });
    }

    function handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }

    // ==========================================================================
    // Header Scroll Effect
    // ==========================================================================

    function initHeaderScrollEffect() {
        let lastScroll = 0;
        let ticking = false;

        window.addEventListener('scroll', () => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    handleHeaderScroll();
                    ticking = false;
                });
                ticking = true;
            }
        });
    }

    function handleHeaderScroll() {
        const currentScroll = window.pageYOffset;

        if (currentScroll > CONFIG.scrollThreshold) {
            elements.header.classList.add('scrolled');
        } else {
            elements.header.classList.remove('scrolled');
        }
    }

    // ==========================================================================
    // Lazy Loading
    // ==========================================================================

    function initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver(handleImageIntersection, {
                threshold: 0.1,
                rootMargin: CONFIG.lazyLoadMargin
            });

            elements.images.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback for older browsers
            elements.images.forEach(img => {
                img.src = img.dataset.src;
            });
        }
    }

    function handleImageIntersection(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src || img.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    }

    // ==========================================================================
    // Footer Year Update
    // ==========================================================================

    function updateFooterYear() {
        if (elements.yearElement) {
            const currentYear = new Date().getFullYear();
            elements.yearElement.textContent = `© ${currentYear} Eduardo Araujo. Todos os direitos reservados.`;
        }
    }

    // ==========================================================================
    // Accessibility Improvements
    // ==========================================================================

    function initAccessibility() {
        // Add ARIA labels to menu toggle
        if (elements.menuToggle) {
            elements.menuToggle.setAttribute('aria-label', 'Toggle navigation menu');
            elements.menuToggle.setAttribute('aria-expanded', 'false');
            elements.menuToggle.setAttribute('aria-controls', 'navLinks');
        }

        // Handle focus management
        document.addEventListener('keydown', handleKeyboardNavigation);
    }

    function handleKeyboardNavigation(e) {
        // Tab trap for mobile menu
        if (elements.navLinks && elements.navLinks.classList.contains('active')) {
            const focusableElements = elements.navLinks.querySelectorAll('a, button');
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            if (e.key === 'Tab') {
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                } else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        }
    }

    // ==========================================================================
    // Error Handling for External Resources
    // ==========================================================================

    function initImageErrorHandling() {
        document.querySelectorAll('img').forEach(img => {
            img.addEventListener('error', function() {
                // Replace with placeholder or initials
                this.style.display = 'flex';
                this.style.alignItems = 'center';
                this.style.justifyContent = 'center';
                this.style.background = 'var(--bg-section)';
                this.style.color = 'var(--accent)';
                this.style.fontSize = '2rem';
                this.alt = 'EA'; // Initials fallback
            });
        });
    }

    // ==========================================================================
    // Initialize
    // ==========================================================================

    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initAll);
        } else {
            initAll();
        }
    }

    function initAll() {
        hideLoadingScreen();
        initMobileMenu();
        initSmoothScroll();
        initScrollAnimations();
        initHeaderScrollEffect();
        initLazyLoading();
        updateFooterYear();
        initAccessibility();
        initImageErrorHandling();
    }

    // Start the application
    window.addEventListener('load', init);

})();
