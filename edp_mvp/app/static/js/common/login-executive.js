/**
 * Executive Login Page JavaScript
 * Following the Executive Dashboard Design System Philosophy
 * Dual theme support: Command Center (Dark) / Executive Suite (Light)
 * Enhanced Features: Password strength, validation, shortcuts, help system
 */

class ExecutiveLogin {
    constructor() {
        this.currentTheme = this.getStoredTheme() || 'dark';
        this.passwordVisible = false;
        this.loginAttempts = 0;
        this.maxAttempts = 5;
        this.init();
    }

    init() {
        this.bindEvents();
        this.applyTheme();
        this.initializeAnimations();
        this.startClock();
        this.setupShortcuts();
    }

    bindEvents() {
        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Form submission
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Input validation and feedback
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        
        if (emailInput) {
            emailInput.addEventListener('input', (e) => this.validateEmail(e.target));
            emailInput.addEventListener('blur', (e) => this.validateEmail(e.target));
            emailInput.addEventListener('focus', () => this.clearValidationError('email'));
        }

        if (passwordInput) {
            passwordInput.addEventListener('input', (e) => this.handlePasswordInput(e.target));
            passwordInput.addEventListener('blur', (e) => this.validatePassword(e.target));
            passwordInput.addEventListener('focus', () => this.clearValidationError('password'));
        }

        // Password toggle
        const passwordToggle = document.getElementById('passwordToggle');
        if (passwordToggle) {
            passwordToggle.addEventListener('click', () => this.togglePasswordVisibility());
        }

        // Button actions
        const helpButton = document.getElementById('helpButton');
        const forgotPassword = document.getElementById('forgotPassword');

        if (helpButton) {
            helpButton.addEventListener('click', () => this.showHelpModal());
        }

        if (forgotPassword) {
            forgotPassword.addEventListener('click', (e) => this.handleForgotPassword(e));
        }

        // Modal and panel controls
        this.bindModalEvents();
        this.bindShortcutPanelEvents();
    }

    bindModalEvents() {
        const helpModal = document.getElementById('helpModal');
        const closeHelp = document.getElementById('closeHelp');

        if (closeHelp) {
            closeHelp.addEventListener('click', () => this.hideHelpModal());
        }

        if (helpModal) {
            helpModal.addEventListener('click', (e) => {
                if (e.target === helpModal) {
                    this.hideHelpModal();
                }
            });
        }
    }

    bindShortcutPanelEvents() {
        const closeShortcuts = document.getElementById('closeShortcuts');
        
        if (closeShortcuts) {
            closeShortcuts.addEventListener('click', () => this.hideShortcutsPanel());
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        this.storeTheme();
        this.showThemeChangeNotification();
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        
        const themeText = document.getElementById('themeText');
        if (themeText) {
            themeText.textContent = this.currentTheme === 'light' ? 'CMD_MODE' : 'EXEC_MODE';
        }

        // Update welcome message based on theme
        this.updateWelcomeMessage();

        // Smooth transition
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    updateWelcomeMessage() {
        // Welcome message removed - no longer needed
    }

    validateEmail(input) {
        const value = input.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const isEmail = emailRegex.test(value);
        const isUsername = value.length >= 3 && /^[a-zA-Z0-9_]+$/.test(value);
        
        let isValid = false;
        let message = '';

        if (!value) {
            message = 'El usuario es requerido';
        } else if (value.length < 3) {
            message = 'Debe tener al menos 3 caracteres';
        } else if (!isEmail && !isUsername) {
            message = 'Formato de usuario inválido';
        } else {
            isValid = true;
        }

        this.setFieldValidation('email', isValid, message);
        return isValid;
    }

    validatePassword(input) {
        const value = input.value;
        let isValid = false;
        let message = '';

        if (!value) {
            message = 'La contraseña es requerida';
        } else if (value.length < 6) {
            message = 'Debe tener al menos 6 caracteres';
        } else {
            isValid = true;
        }

        this.setFieldValidation('password', isValid, message);
        return isValid;
    }

    handlePasswordInput(input) {
        this.updatePasswordStrength(input.value);
        this.validatePassword(input);
    }

    updatePasswordStrength(password) {
        const strengthIndicator = document.getElementById('passwordStrength');
        const strengthFill = document.getElementById('strengthFill');
        const strengthText = document.getElementById('strengthText');

        if (!password) {
            strengthIndicator.classList.remove('show');
            return;
        }

        strengthIndicator.classList.add('show');

        const strength = this.calculatePasswordStrength(password);
        
        // Remove existing classes
        strengthFill.className = 'strength-fill';
        
        switch (strength.level) {
            case 1:
                strengthFill.classList.add('weak');
                strengthText.textContent = 'Débil';
                break;
            case 2:
                strengthFill.classList.add('fair');
                strengthText.textContent = 'Regular';
                break;
            case 3:
                strengthFill.classList.add('good');
                strengthText.textContent = 'Buena';
                break;
            case 4:
                strengthFill.classList.add('strong');
                strengthText.textContent = 'Fuerte';
                break;
            default:
                strengthText.textContent = 'Muy débil';
        }
    }

    calculatePasswordStrength(password) {
        let score = 0;
        const checks = {
            length: password.length >= 8,
            lowercase: /[a-z]/.test(password),
            uppercase: /[A-Z]/.test(password),
            numbers: /\d/.test(password),
            symbols: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };

        score = Object.values(checks).filter(Boolean).length;
        
        return {
            level: Math.min(score, 4),
            checks
        };
    }

    setFieldValidation(fieldName, isValid, message) {
        const input = document.getElementById(fieldName);
        const errorElement = document.getElementById(`${fieldName}Error`);
        
        if (input) {
            input.classList.remove('valid', 'invalid');
            input.classList.add(isValid ? 'valid' : 'invalid');
        }

        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.toggle('show', !isValid && message);
        }
    }

    clearValidationError(fieldName) {
        const input = document.getElementById(fieldName);
        const errorElement = document.getElementById(`${fieldName}Error`);
        
        if (input) {
            input.classList.remove('invalid');
        }
        
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }

    togglePasswordVisibility() {
        const passwordInput = document.getElementById('password');
        const showIcon = document.querySelector('.show-icon');
        const hideIcon = document.querySelector('.hide-icon');

        this.passwordVisible = !this.passwordVisible;
        
        if (passwordInput) {
            passwordInput.type = this.passwordVisible ? 'text' : 'password';
        }

        if (showIcon && hideIcon) {
            showIcon.style.display = this.passwordVisible ? 'none' : 'block';
            hideIcon.style.display = this.passwordVisible ? 'block' : 'none';
        }
    }

    handleFormSubmit(e) {
        e.preventDefault();
        
        // Check if too many attempts
        if (this.loginAttempts >= this.maxAttempts) {
            this.showError('Demasiados intentos. Intenta de nuevo más tarde.');
            return;
        }

        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');

        const emailValid = emailInput ? this.validateEmail(emailInput) : false;
        const passwordValid = passwordInput ? this.validatePassword(passwordInput) : false;

        if (!emailValid || !passwordValid) {
            this.showError('Por favor, corrige los errores antes de continuar');
            return;
        }

        this.startLoading();
        this.loginAttempts++;

        // Submit the form normally (remove demo mode)
        e.target.submit();
    }

    startLoading() {
        const loginButton = document.getElementById('loginButton');
        if (loginButton) {
            loginButton.classList.add('loading');
            loginButton.disabled = true;
        }
    }

    stopLoading() {
        const loginButton = document.getElementById('loginButton');
        if (loginButton) {
            loginButton.classList.remove('loading');
            loginButton.disabled = false;
        }
    }

    showHelpModal() {
        const helpModal = document.getElementById('helpModal');
        if (helpModal) {
            helpModal.classList.add('show');
        }
    }

    hideHelpModal() {
        const helpModal = document.getElementById('helpModal');
        if (helpModal) {
            helpModal.classList.remove('show');
        }
    }

    showShortcutsPanel() {
        const shortcutsPanel = document.getElementById('shortcutsPanel');
        if (shortcutsPanel) {
            shortcutsPanel.classList.add('show');
        }
    }

    hideShortcutsPanel() {
        const shortcutsPanel = document.getElementById('shortcutsPanel');
        if (shortcutsPanel) {
            shortcutsPanel.classList.remove('show');
        }
    }

    handleForgotPassword(e) {
        e.preventDefault();
        this.showInfo('Contacta con el administrador del sistema para restablecer tu contraseña.');
    }

    setupShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt + T: Toggle theme
            if (e.altKey && e.key === 't') {
                e.preventDefault();
                this.toggleTheme();
            }

            // Alt + H: Show help
            if (e.altKey && e.key === 'h') {
                e.preventDefault();
                this.showHelpModal();
            }

            // Ctrl + Enter: Submit form
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                const loginForm = document.getElementById('loginForm');
                if (loginForm) {
                    loginForm.dispatchEvent(new Event('submit', { cancelable: true }));
                }
            }

            // Alt + S: Show shortcuts
            if (e.altKey && e.key === 's') {
                e.preventDefault();
                this.showShortcutsPanel();
            }

            // Escape: Clear errors and hide modals
            if (e.key === 'Escape') {
                this.hideHelpModal();
                this.hideShortcutsPanel();
                this.clearAllValidationErrors();
            }
        });
    }

    clearAllValidationErrors() {
        ['email', 'password'].forEach(field => {
            this.clearValidationError(field);
        });
    }

    startClock() {
        const updateTime = () => {
            const timeElement = document.getElementById('currentTime');
            if (timeElement) {
                const now = new Date();
                const timeString = now.toLocaleTimeString('es-ES', { 
                    hour12: false,
                    timeZone: 'America/Mexico_City'
                });
                timeElement.textContent = timeString;
            }
        };

        updateTime();
        setInterval(updateTime, 1000);
    }

    showThemeChangeNotification() {
        const notification = document.createElement('div');
        notification.className = 'theme-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            color: var(--text-secondary);
            z-index: 3000;
            animation: slideDown 0.3s ease-out;
        `;

        const themeName = this.currentTheme === 'light' ? 'Executive Suite' : 'Command Center';
        notification.textContent = `Cambiado a ${themeName}`;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideUp 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    showNotification(message, type) {
        // Remove existing notifications
        const existing = document.querySelectorAll('.notification');
        existing.forEach(n => n.remove());

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--bg-secondary);
            border: 1px solid var(--status-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'});
            border-radius: 8px;
            padding: 16px;
            max-width: 300px;
            color: var(--status-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'});
            box-shadow: var(--shadow-elevated);
            z-index: 3000;
            animation: slideInRight 0.3s ease-out;
        `;

        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    ${type === 'error' ? '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>' :
                      type === 'success' ? '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22,4 12,14.01 9,11.01"/>' :
                      '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'}
                </svg>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    initializeAnimations() {
        // Simple entrance animation for the main card only
        const loginCard = document.querySelector('.login-card');
        if (loginCard) {
            loginCard.classList.add('animate-slide-up');
        }
    }

    getStoredTheme() {
        return localStorage.getItem('managerTheme');
    }

    storeTheme() {
        localStorage.setItem('managerTheme', this.currentTheme);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const executiveLogin = new ExecutiveLogin();
    
    // Show welcome message after initialization
    setTimeout(() => {
        if (executiveLogin.currentTheme === 'light') {
            executiveLogin.showInfo('Bienvenido al sistema ejecutivo de Pagora');
        } else {
            console.log('[SYSTEM] Command Center initialized');
        }
    }, 1500);
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('[SYSTEM] Session suspended');
    } else {
        console.log('[SYSTEM] Session resumed');
    }
});

// Performance monitoring
window.addEventListener('load', () => {
    const loadTime = performance.now();
    console.log(`[PERF] Executive Login loaded in ${loadTime.toFixed(2)}ms`);
    
    // Report critical performance metrics
    if ('performance' in window && 'getEntriesByType' in performance) {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            console.log(`[PERF] DOM loaded: ${navigation.domContentLoadedEventEnd.toFixed(2)}ms`);
            console.log(`[PERF] Page loaded: ${navigation.loadEventEnd.toFixed(2)}ms`);
        }
    }
});
