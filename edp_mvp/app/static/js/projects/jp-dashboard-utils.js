/**
 * JP Dashboard Utilities
 * Common functions and helpers for the JP dashboard
 */

class JPDashboardUtils {
  /**
   * Format currency values consistently
   */
  static formatCurrency(amount) {
    if (amount >= 1000000) {
      return '$' + (amount / 1000000).toFixed(1) + 'M';
    } else if (amount >= 1000) {
      return '$' + (amount / 1000).toFixed(0) + 'K';
    } else {
      return '$' + amount.toLocaleString();
    }
  }

  /**
   * Format percentage values
   */
  static formatPercentage(value, decimals = 1) {
    return parseFloat(value).toFixed(decimals) + '%';
  }

  /**
   * Get status color class based on value and thresholds
   */
  static getStatusColor(value, type = 'default') {
    switch (type) {
      case 'dso':
        if (value <= 30) return 'success';
        if (value <= 45) return 'warning';
        return 'danger';
      
      case 'margin':
        if (value >= 20) return 'success';
        if (value >= 10) return 'warning';
        if (value >= 0) return 'info';
        return 'danger';
      
      case 'efficiency':
        if (value >= 80) return 'success';
        if (value >= 60) return 'warning';
        return 'danger';
      
      default:
        return 'info';
    }
  }

  /**
   * Debounce function for performance optimization
   */
  static debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * Throttle function for scroll events
   */
  static throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  /**
   * Show notification toast
   */
  static showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
      </div>
    `;
    
    // Add styles if not already present
    if (!document.getElementById('notification-styles')) {
      const styles = document.createElement('style');
      styles.id = 'notification-styles';
      styles.textContent = `
        .notification {
          position: fixed;
          top: 20px;
          right: 20px;
          padding: 12px 16px;
          border-radius: 8px;
          color: white;
          font-weight: 500;
          z-index: 1000;
          animation: slideInRight 0.3s ease;
          max-width: 400px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .notification-success { background: #10b981; }
        .notification-warning { background: #f59e0b; }
        .notification-danger { background: #ef4444; }
        .notification-info { background: #3b82f6; }
        
        .notification-content {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .notification-close {
          background: none;
          border: none;
          color: white;
          font-size: 18px;
          cursor: pointer;
          margin-left: 12px;
        }
        
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `;
      document.head.appendChild(styles);
    }
    
    document.body.appendChild(notification);
    
    // Auto remove after duration
    setTimeout(() => {
      if (notification.parentElement) {
        notification.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
      }
    }, duration);
  }

  /**
   * Animate number counting effect
   */
  static animateNumber(element, start, end, duration = 1000) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
      current += increment;
      if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
        current = end;
        clearInterval(timer);
      }
      element.textContent = Math.round(current);
    }, 16);
  }

  /**
   * Create loading spinner
   */
  static createLoadingSpinner(size = 'medium') {
    const spinner = document.createElement('div');
    spinner.className = `loading-spinner loading-spinner-${size}`;
    
    // Add spinner styles if not present
    if (!document.getElementById('spinner-styles')) {
      const styles = document.createElement('style');
      styles.id = 'spinner-styles';
      styles.textContent = `
        .loading-spinner {
          border: 2px solid #f3f4f6;
          border-top: 2px solid #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        
        .loading-spinner-small { width: 16px; height: 16px; }
        .loading-spinner-medium { width: 24px; height: 24px; }
        .loading-spinner-large { width: 32px; height: 32px; }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `;
      document.head.appendChild(styles);
    }
    
    return spinner;
  }

  /**
   * Validate form data
   */
  static validateForm(formData, rules) {
    const errors = {};
    
    for (const [field, rule] of Object.entries(rules)) {
      const value = formData[field];
      
      if (rule.required && (!value || value.trim() === '')) {
        errors[field] = `${rule.label || field} es requerido`;
        continue;
      }
      
      if (value && rule.type === 'email' && !this.isValidEmail(value)) {
        errors[field] = `${rule.label || field} debe ser un email válido`;
      }
      
      if (value && rule.type === 'number' && isNaN(value)) {
        errors[field] = `${rule.label || field} debe ser un número`;
      }
      
      if (value && rule.min && value.length < rule.min) {
        errors[field] = `${rule.label || field} debe tener al menos ${rule.min} caracteres`;
      }
      
      if (value && rule.max && value.length > rule.max) {
        errors[field] = `${rule.label || field} no puede tener más de ${rule.max} caracteres`;
      }
    }
    
    return {
      isValid: Object.keys(errors).length === 0,
      errors
    };
  }

  /**
   * Check if email is valid
   */
  static isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Get relative time string
   */
  static getRelativeTime(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - new Date(date)) / 1000);
    
    if (diffInSeconds < 60) return 'hace unos segundos';
    if (diffInSeconds < 3600) return `hace ${Math.floor(diffInSeconds / 60)} minutos`;
    if (diffInSeconds < 86400) return `hace ${Math.floor(diffInSeconds / 3600)} horas`;
    if (diffInSeconds < 2592000) return `hace ${Math.floor(diffInSeconds / 86400)} días`;
    if (diffInSeconds < 31536000) return `hace ${Math.floor(diffInSeconds / 2592000)} meses`;
    return `hace ${Math.floor(diffInSeconds / 31536000)} años`;
  }

  /**
   * Copy text to clipboard
   */
  static async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      this.showNotification('Texto copiado al portapapeles', 'success');
      return true;
    } catch (err) {
      console.error('Error copying to clipboard:', err);
      this.showNotification('Error al copiar texto', 'danger');
      return false;
    }
  }

  /**
   * Download data as CSV
   */
  static downloadCSV(data, filename = 'data.csv') {
    const csvContent = this.arrayToCSV(data);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }

  /**
   * Convert array of objects to CSV string
   */
  static arrayToCSV(data) {
    if (!data.length) return '';
    
    const headers = Object.keys(data[0]);
    const csvHeaders = headers.join(',');
    
    const csvRows = data.map(row => 
      headers.map(header => {
        const value = row[header];
        return typeof value === 'string' && value.includes(',') 
          ? `"${value}"` 
          : value;
      }).join(',')
    );
    
    return [csvHeaders, ...csvRows].join('\n');
  }

  /**
   * Generate random ID
   */
  static generateId(prefix = 'id') {
    return `${prefix}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Check if element is in viewport
   */
  static isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
  }

  /**
   * Smooth scroll to element
   */
  static scrollToElement(element, offset = 0) {
    const elementPosition = element.offsetTop - offset;
    window.scrollTo({
      top: elementPosition,
      behavior: 'smooth'
    });
  }
}

// Make utilities available globally
window.JPDashboardUtils = JPDashboardUtils; 