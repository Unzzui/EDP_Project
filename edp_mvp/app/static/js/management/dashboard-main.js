/**
 * Dashboard Management - Main JavaScript
 * Funcionalidad principal del dashboard de management
 */

// Inicialización del dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

/**
 * Inicializa todos los componentes del dashboard
 */
function initializeDashboard() {
    // Debug: verificar datos disponibles
    console.log('🔍 Dashboard data available:', {
        kpisData: window.kpisData ? 'Available' : 'Not available',
        chartsData: window.chartsData ? 'Available' : 'Not available',
        equipoData: window.equipoData ? 'Available' : 'Not available',
        alertasData: window.alertasData ? 'Available' : 'Not available'
    });
    
    if (window.kpisData) {
        console.log('📊 KPIs Data sample:', {
            dso_actual: window.kpisData.dso_actual,
            dso: window.kpisData.dso,
            ingresos_totales: window.kpisData.ingresos_totales
        });
    }
    
    updateTime();
    initializeDashboardCharts(); // Usar función del archivo charts
    startTimeUpdate();
    
    // Initialize tooltips
    initializeTooltips();
}

/**
 * Actualiza el tiempo actual en el header
 */
  function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleString("es-ES", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    const lastUpdateString = now.toLocaleString("es-ES", {
      hour: "2-digit",
      minute: "2-digit",
    });
    
    const timeElement = document.getElementById("current-time");
    const lastUpdateElement = document.getElementById("last-update");
    
    if (timeElement) {
      timeElement.textContent = timeString;
    }
    if (lastUpdateElement) {
      lastUpdateElement.textContent = lastUpdateString;
    }
  }

/**
 * Actualiza el timestamp de última actualización
 */
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('es-ES', { 
        hour: '2-digit', 
        minute: '2-digit'
    });
    const lastUpdateElement = document.getElementById('last-update');
    if (lastUpdateElement) {
        lastUpdateElement.textContent = timeString;
    }
}

/**
 * Inicia la actualización automática del tiempo
 */
function startTimeUpdate() {
    // Actualizar immediately
    updateTime();
    updateLastUpdateTime();
    
    // Actualizar cada segundo para el tiempo actual
    setInterval(updateTime, 1000);
    
    // Actualizar cada 5 minutos para last-update (tiempo real de datos)
    setInterval(updateLastUpdateTime, 300000); // 5 minutes
}

// Función de charts movida a dashboard-charts.js

// Funciones de modales movidas a dashboard-modals.js

/**
 * Muestra una notificación temporal
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; z-index: 1000;
        padding: 12px 20px; border-radius: 8px; color: white;
        background: ${type === 'success' ? '#00ff88' : type === 'warning' ? '#ffab00' : '#0066ff'};
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

// Funciones de utilidad para botones del dashboard
function coordinateManagers() { 
    showNotification('Iniciando coordinación con jefes de proyecto', 'success'); 
}

function exportForecast() { 
    showNotification('Exportando datos de forecast', 'info'); 
}

function executeAllAlerts() { 
    showNotification('Ejecutando todas las alertas críticas', 'warning'); 
}

function showTargetDetails() { 
    showNotification('Generando reporte detallado de objetivos', 'info'); 
}

function analyzeDSOTrend() { 
    showNotification('Iniciando análisis profundo de DSO', 'info'); 
}

// Agregar estilos CSS dinámicamente
function addDashboardStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .modal-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.8); display: flex; justify-content: center; align-items: center;
            z-index: 1000; backdrop-filter: blur(10px);
        }
        .modal-content {
            background: var(--bg-primary); border: 1px solid var(--border-primary);
            border-radius: 8px; padding: 24px; max-width: 400px; width: 90%;
            color: var(--text-primary);
        }
        .modal-content h3 { color: var(--accent-primary); margin-bottom: 16px; }
        .modal-body { margin: 16px 0; line-height: 1.6; }
        .modal-actions { display: flex; gap: 12px; margin-top: 20px; }
        .btn-primary, .btn-secondary {
            padding: 8px 16px; border-radius: 4px; border: none; cursor: pointer;
            font-family: 'JetBrains Mono'; font-size: 12px; font-weight: 600;
        }
        .btn-primary { background: var(--accent-primary); color: var(--bg-primary); }
        .btn-secondary { background: var(--bg-tertiary); color: var(--text-secondary); }
        
        .no-data-message, .no-forecast-data, .no-alerts-message, .no-chart-data {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            padding: 40px 20px; color: var(--text-secondary); text-align: center;
        }
        .no-data-icon, .no-forecast-icon, .no-alerts-icon, .no-chart-icon {
            font-size: 48px; margin-bottom: 16px; opacity: 0.5;
        }
        .no-data-text, .no-forecast-text, .no-alerts-text, .no-chart-text {
            font-size: 16px; margin-bottom: 8px; color: var(--text-primary);
        }
        .no-data-subtext, .no-forecast-subtext, .no-alerts-subtext, .no-chart-subtext {
            font-size: 14px; opacity: 0.7;
        }
        
        .neutral { color: #888888 !important; }
        .header-metric-value.neutral { color: #888888 !important; }
        .kpi-impact.neutral { background: #333333; }
        .dso-cell.neutral { border-color: #555555; }
        
        .dso-projects {
            font-size: 10px;
            color: #888888;
            margin-top: 2px;
            font-family: 'JetBrains Mono';
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
}

// Inicializar estilos cuando se carga el documento
document.addEventListener('DOMContentLoaded', addDashboardStyles);

// ===== TOOLTIP POSITIONING SYSTEM =====
function initializeTooltips() {
    const metrics = document.querySelectorAll('.analytics-header-metric[data-tooltip]');
    
    metrics.forEach(metric => {
        const tooltipId = metric.getAttribute('data-tooltip');
        const tooltip = document.getElementById(tooltipId);
        
        if (!tooltip) return;
        
        // Mouse enter - show tooltip
        metric.addEventListener('mouseenter', (e) => {
            showTooltip(metric, tooltip);
        });
        
        // Mouse leave - hide tooltip
        metric.addEventListener('mouseleave', (e) => {
            hideTooltip(tooltip);
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            if (tooltip.style.opacity === '1') {
                positionTooltip(metric, tooltip);
            }
        });
    });
}

function showTooltip(trigger, tooltip) {
    // Position tooltip first
    positionTooltip(trigger, tooltip);
    
    // Show with animation
    requestAnimationFrame(() => {
        tooltip.style.opacity = '1';
        tooltip.style.visibility = 'visible';
        tooltip.style.transform = tooltip.getAttribute('data-final-transform') || 'translateY(4px)';
    });
}

function hideTooltip(tooltip) {
    tooltip.style.opacity = '0';
    tooltip.style.visibility = 'hidden';
    tooltip.style.transform = 'translateY(-4px)';
}

function positionTooltip(trigger, tooltip) {
    const triggerRect = trigger.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    let left = triggerRect.left + (triggerRect.width / 2) - (tooltip.offsetWidth / 2);
    let top = triggerRect.bottom + 12; // 12px gap below trigger
    
    // Horizontal boundary checks
    if (left < 10) {
        left = 10;
    } else if (left + tooltip.offsetWidth > viewportWidth - 10) {
        left = viewportWidth - tooltip.offsetWidth - 10;
    }
    
    // Vertical boundary checks
    if (top + tooltip.offsetHeight > viewportHeight - 10) {
        // Show above if no space below
        top = triggerRect.top - tooltip.offsetHeight - 12;
        tooltip.setAttribute('data-final-transform', 'translateY(-4px)');
        tooltip.setAttribute('data-position', 'above');
    } else {
        tooltip.setAttribute('data-final-transform', 'translateY(4px)');
        tooltip.setAttribute('data-position', 'below');
    }
    
    // Apply positioning
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
    
    // Position arrow
    const arrowLeft = triggerRect.left + (triggerRect.width / 2) - left;
    const arrow = tooltip.querySelector('::before');
    if (arrow) {
        tooltip.style.setProperty('--arrow-left', `${arrowLeft}px`);
    }
}