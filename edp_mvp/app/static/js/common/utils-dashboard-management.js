/**
 * Management Dashboard Utilities
 * Common utility functions for management dashboards
 */

/**
 * Format currency values
 */
function formatCurrency(value) {
    if (typeof value !== 'number') {
        value = parseFloat(value) || 0;
    }
    
    return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

/**
 * Format percentage values
 */
function formatPercentage(value, decimals = 1) {
    if (typeof value !== 'number') {
        value = parseFloat(value) || 0;
    }
    
    return new Intl.NumberFormat('es-CL', {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value / 100);
}

/**
 * Format date values
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-CL', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

/**
 * Calculate days between dates
 */
function daysBetween(date1, date2) {
    const oneDay = 24 * 60 * 60 * 1000;
    const firstDate = new Date(date1);
    const secondDate = new Date(date2);
    
    return Math.round(Math.abs((firstDate - secondDate) / oneDay));
}

/**
 * Get status color based on value
 */
function getStatusColor(status) {
    const colors = {
        'pendiente': '#f59e0b',
        'en_proceso': '#3b82f6',
        'completado': '#10b981',
        'revision': '#8b5cf6',
        'aprobado': '#059669',
        'rechazado': '#ef4444',
        'critico': '#dc2626',
        'normal': '#6b7280',
        'urgente': '#f97316'
    };
    
    return colors[status] || colors['normal'];
}

/**
 * Debounce function for performance
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

/**
 * Throttle function for performance
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Show loading spinner
 */
function showLoading(container) {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = `
        <div class="spinner"></div>
        <p>Cargando...</p>
    `;
    container.appendChild(spinner);
    return spinner;
}

/**
 * Hide loading spinner
 */
function hideLoading(spinner) {
    if (spinner && spinner.parentNode) {
        spinner.parentNode.removeChild(spinner);
    }
}

/**
 * Show error message
 */
function showError(container, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <div class="error-icon">⚠️</div>
        <p>${message}</p>
    `;
    container.appendChild(errorDiv);
    return errorDiv;
}

/**
 * Create chart configuration
 */
function createChartConfig(type, data, options = {}) {
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                mode: 'index',
                intersect: false,
            }
        }
    };
    
    return {
        type: type,
        data: data,
        options: { ...defaultOptions, ...options }
    };
}

/**
 * API call helper
 */
async function apiCall(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

/**
 * Update URL parameters without reload
 */
function updateUrlParams(params) {
    const url = new URL(window.location);
    Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== '') {
            url.searchParams.set(key, params[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    window.history.replaceState({}, '', url);
}

/**
 * Get URL parameter
 */
function getUrlParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// Export utilities
window.managementUtils = {
    formatCurrency,
    formatPercentage,
    formatDate,
    daysBetween,
    getStatusColor,
    debounce,
    throttle,
    showLoading,
    hideLoading,
    showError,
    createChartConfig,
    apiCall,
    updateUrlParams,
    getUrlParam
};
