/**
 * Dashboard Management - Main JavaScript
 * Funcionalidad principal del dashboard de management
 */

/**
 * Format amount to millions with proper formatting
 */
function formatAmount(amount) {
    if (!amount || amount === 0) return 'Sin monto';
    const amountInMillions = amount / 1000000;
    return `$${amountInMillions.toFixed(1)}M`;
}

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
    // Remove existing notification
    const existingNotification = document.getElementById('notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Clear any existing timeouts
    if (window.notificationTimeout) {
        clearTimeout(window.notificationTimeout);
        window.notificationTimeout = null;
    }
    
    // Determine icon and color based on type
    let icon = '';
    let bgColor = '';
    switch (type) {
        case 'success':
            icon = '✓';
            bgColor = '#10b981';
            break;
        case 'error':
            icon = '✗';
            bgColor = '#ef4444';
            break;
        case 'warning':
            icon = '⚠';
            bgColor = '#f59e0b';
            break;
        default:
            icon = 'ℹ';
            bgColor = '#3b82f6';
    }
    
    const notification = document.createElement('div');
    notification.id = 'notification';
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${icon}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
        <div class="notification-progress"></div>
    `;
    notification.style.cssText = `
        position: fixed; top: 30px; right: 30px; z-index: 999999;
        background: ${bgColor}; color: white; border-radius: 8px;
        padding: 16px 20px; min-width: 300px; max-width: 500px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        animation: slideIn 0.3s ease; font-family: 'JetBrains Mono', monospace;
        font-size: 14px; line-height: 1.4;
    `;
    
    // Add styles for notification content
    const style = document.createElement('style');
    style.textContent = `
        .notification-content {
            display: flex; align-items: center; gap: 12px;
        }
        .notification-icon {
            font-size: 16px; font-weight: bold; flex-shrink: 0;
        }
        .notification-message {
            flex: 1; word-wrap: break-word;
        }
        .notification-close {
            background: none; border: none; color: white;
            font-size: 18px; cursor: pointer; padding: 0;
            opacity: 0.7; transition: opacity 0.2s;
        }
        .notification-close:hover {
            opacity: 1;
        }
        .notification-progress {
            position: absolute; bottom: 0; left: 0; height: 3px;
            background: rgba(255, 255, 255, 0.3); width: 100%;
            animation: progress 5s linear;
        }
        @keyframes progress {
            from { width: 100%; }
            to { width: 0%; }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Auto-hide after appropriate time based on type
    const autoHideTime = type === 'info' ? 4000 : type === 'success' ? 6000 : type === 'error' ? 8000 : 5000;
    window.notificationTimeout = setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, autoHideTime);
}

function closeNotification() {
    const notification = document.getElementById('notification');
    if (notification) {
        notification.remove();
    }
    if (window.notificationTimeout) {
        clearTimeout(window.notificationTimeout);
        window.notificationTimeout = null;
    }
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

// ==========================================================================
// NEW DASHBOARD.TSX STYLE FUNCTIONS
// ==========================================================================

/**
 * Switch account view type in Active Accounts KPI
 */
function switchAccountView(viewType) {
    const countElement = document.getElementById('activeAccountsCount');
    const subtitleElement = document.getElementById('activeAccountsSubtitle');
    
    if (!countElement || !subtitleElement) return;
    
    switch(viewType) {
        case 'clientes':
            // Count unique clients from equipo data
            let clientCount = 0;
            if (window.equipoData && Array.isArray(window.equipoData)) {
                const uniqueClients = new Set();
                window.equipoData.forEach(manager => {
                    if (manager.clients && Array.isArray(manager.clients)) {
                        manager.clients.forEach(client => {
                            uniqueClients.add(client.nombre);
                        });
                    }
                });
                clientCount = uniqueClients.size;
            }
            countElement.textContent = clientCount;
            subtitleElement.textContent = `${clientCount} UNIQUE CLIENTS`;
            break;
            
        case 'jefes':
            const managerCount = window.equipoData ? window.equipoData.length : 0;
            countElement.textContent = managerCount;
            const totalEdps = window.kpisData && window.kpisData.total_edps_activos ? window.kpisData.total_edps_activos : 0;
            subtitleElement.textContent = `${totalEdps} OPEN INVOICES`;
            break;
            
        case 'proyectos':
            let projectCount = 0;
            if (window.equipoData && Array.isArray(window.equipoData)) {
                projectCount = window.equipoData.reduce((total, manager) => {
                    return total + (manager.proyectos_count || 0);
                }, 0);
            }
            countElement.textContent = projectCount;
            subtitleElement.textContent = `${projectCount} ACTIVE PROJECTS`;
            break;
    }
}

/**
 * Show modal for Total Receivables KPI
 */
function showTotalReceivablesModal() {
    const totalReceivables = window.kpisData && window.kpisData.total_monto_propuesto ? 
        (window.kpisData.total_monto_propuesto / 1000000).toFixed(1) : 0;
    
    showModal('Total Receivables Details', `
        <div class="modal-kpi-detail">
            <div class="kpi-detail-main">
                <div class="kpi-detail-value">$${totalReceivables}M CLP</div>
                <div class="kpi-detail-label">Total Outstanding Receivables</div>
            </div>
            <div class="kpi-detail-breakdown">
                <div class="breakdown-item">
                    <span class="breakdown-label">Current (0-30 days):</span>
                    <span class="breakdown-value">$${window.kpisData && window.kpisData.aging_0_30_amount ? (window.kpisData.aging_0_30_amount / 1000000).toFixed(1) : 0}M</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Past Due (31+ days):</span>
                    <span class="breakdown-value">$${window.kpisData && window.kpisData.aging_31_plus_amount ? (window.kpisData.aging_31_plus_amount / 1000000).toFixed(1) : 0}M</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Critical (+90 days):</span>
                    <span class="breakdown-value critical">$${window.kpisData && window.kpisData.aging_90_plus_amount ? (window.kpisData.aging_90_plus_amount / 1000000).toFixed(1) : 0}M</span>
                </div>
            </div>
        </div>
    `);
}

/**
 * Show modal for Critical Receivables
 */
function showCriticalReceivablesModal() {
    const criticalAmount = window.kpisData && window.kpisData.critical_amount ? 
        (window.kpisData.critical_amount / 1000000).toFixed(1) : 0;
    
    showModal('Critical Receivables (+90 Days)', `
        <div class="modal-kpi-detail">
            <div class="kpi-detail-main critical">
                <div class="kpi-detail-value">$${criticalAmount}M CLP</div>
                <div class="kpi-detail-label">Overdue 90+ Days</div>
            </div>
            <div class="kpi-detail-actions">
                <button class="modal-action-btn primary" onclick="generateCollectionPlan()">Generate Collection Plan</button>
                <button class="modal-action-btn secondary" onclick="scheduleClientCalls()">Schedule Follow-ups</button>
            </div>
        </div>
    `);
}

/**
 * Show modal for Active Accounts details
 */
function showActiveAccountsModal() {
    const selector = document.getElementById('accountTypeSelector');
    const viewType = selector ? selector.value : 'jefes';
    
    let content = '';
    
    switch(viewType) {
        case 'clientes':
            content = generateClientsModalContent();
            break;
        case 'jefes':
            content = generateManagersModalContent();
            break;
        case 'proyectos':
            content = generateProjectsModalContent();
            break;
    }
    
    showModal(`Active Accounts - ${viewType.charAt(0).toUpperCase() + viewType.slice(1)}`, content);
}

/**
 * Show modal for Collection Performance
 */
function showCollectionPerformanceModal() {
    const dso = window.kpisData && window.kpisData.dso_actual ? window.kpisData.dso_actual.toFixed(0) : '--';
    const target = 30;
    const variance = window.kpisData && window.kpisData.dso_actual ? (window.kpisData.dso_actual - target).toFixed(0) : 0;
    
    showModal('Collection Performance Analysis', `
        <div class="modal-kpi-detail">
            <div class="kpi-detail-main">
                <div class="kpi-detail-value">${dso} Days</div>
                <div class="kpi-detail-label">Average Collection Period</div>
            </div>
            <div class="performance-metrics">
                <div class="metric-row">
                    <span class="metric-label">Target DSO:</span>
                    <span class="metric-value">${target} days</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Variance:</span>
                    <span class="metric-value ${variance > 0 ? 'negative' : variance < 0 ? 'positive' : 'neutral'}">${variance > 0 ? '+' : ''}${variance} days</span>
                </div>
                <div class="metric-row">
                    <span class="metric-label">Collection Efficiency:</span>
                    <span class="metric-value">${window.kpisData && window.kpisData.collection_efficiency ? window.kpisData.collection_efficiency.toFixed(0) : '--'}%</span>
                </div>
            </div>
        </div>
    `);
}

/**
 * Show aging detail modal with EDP data and email functionality
 */
function showAgingDetail(range) {
    // Show loading modal first
    showModal(`Aging Analysis: ${range} Days`, `
        <div class="modal-aging-detail">
            <div class="aging-detail-header">
                <div class="aging-range-badge">${range}D</div>
                <div class="aging-risk-level">${getRiskLevel(range)}</div>
            </div>
            <div class="aging-detail-loading">
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <div class="loading-text">Cargando EDPs en aging ${range} días...</div>
                </div>
            </div>
        </div>
    `);
    
    // Fetch detailed aging data
    console.log(`Fetching aging data for range: ${range}`);
    fetch(`/management/api/aging_detail/${range}`)
        .then(response => {
            console.log(`📡 Response status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log(`Aging data received:`, data);
            if (!data.success) {
                showNotification(`${data.message}`, 'error');
                return;
            }
            
            const { aging_edps, summary } = data;
            
            // Debug: Log summary data
            console.log(`Summary data:`, summary);
            console.log(`Total amount: ${summary.total_amount}`);
            console.log(`Formatted amount: ${formatAmount(summary.total_amount)}`);
            console.log(`Raw total_amount: ${summary.total_amount}, Type: ${typeof summary.total_amount}`);
            
            // Generate EDPs table HTML
            const edpsTableHtml = generateAgingEDPsTable(aging_edps, range);
            
            // Generate action plan based on risk level
            const actionPlanHtml = generateAgingActionPlan(summary, range);
            
            // Update modal with detailed content
            const modalContent = `
                <div class="modal-aging-detail">
                    <div class="aging-detail-header">
                        <div class="aging-range-badge ${summary.risk_level}">${range}D</div>
                        <div class="aging-risk-level ${summary.risk_level}">${getRiskLevel(range).toUpperCase()}</div>
                    </div>
                    
                    <div class="aging-detail-summary">
                        <div class="aging-summary-metrics">
                            <div class="aging-summary-metric">
                                <div class="summary-metric-value">${formatAmount(summary.total_amount)}</div>
                                <div class="summary-metric-label">Monto Total</div>
                            </div>
                            <div class="aging-summary-metric">
                                <div class="summary-metric-value">${summary.total_edps}</div>
                                <div class="summary-metric-label">EDPs</div>
                            </div>
                            <div class="aging-summary-metric">
                                <div class="summary-metric-value">${summary.average_days.toFixed(0)}d</div>
                                <div class="summary-metric-label">Promedio</div>
                            </div>
                            <div class="aging-summary-metric">
                                <div class="summary-metric-value">${summary.max_days}d</div>
                                <div class="summary-metric-label">Máximo</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="aging-detail-content">
                        <div class="aging-edps-section">
                            <div class="section-header">
                                <h4 class="section-title">EDPs en Aging ${range} Días</h4>
                                <div class="section-actions">
                                    <button class="section-action-btn warning" onclick="sendAgingRangeEmails('${range}')">
                                        Enviar Emails
                                    </button>
                                    <button class="section-action-btn info" onclick="exportAgingRangeData('${range}')">
                                        Exportar
                                    </button>
                                </div>
                            </div>
                            <div class="aging-edps-table-container">
                                <table class="aging-edps-table">
                                    <thead>
                                        <tr>
                                            <th>EDP</th>
                                            <th>Cliente</th>
                                            <th>Proyecto</th>
                                            <th>Monto</th>
                                            <th>Días</th>
                                            <th>Jefe</th>
                                            <th>Estado</th>
                                            <th>Email</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${edpsTableHtml}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        
                        <div class="aging-action-plan">
                            <div class="section-header">
                                <h4 class="section-title">Plan de Acción - ${getRiskLevel(range)}</h4>
                            </div>
                            ${actionPlanHtml}
                        </div>
                    </div>
                    
                    <div class="aging-detail-actions">
                        <button class="modal-action-btn primary" onclick="exportAgingReport('${range}')">
                            Export Report
                        </button>
                        <button class="modal-action-btn secondary" onclick="generateActionPlan('${range}')">
                            Action Plan
                        </button>
                        <button class="modal-action-btn warning" onclick="scheduleAgingFollowup('${range}')">
                            Programar Seguimiento
                        </button>
                    </div>
                </div>
            `;
            
            // Update the modal content
            console.log(`Updating modal content for range: ${range}`);
            const modalElement = document.querySelector('.modal-body');
            console.log(`Modal element found:`, modalElement);
            
            if (modalElement) {
                modalElement.innerHTML = modalContent;
                console.log(`Modal content updated successfully`);
            } else {
                // Fallback: try to find modal by other selectors
                console.log(`Modal body not found, trying fallback selectors`);
                const modalFallback = document.querySelector('.modal-content') || 
                                    document.querySelector('.modal') ||
                                    document.querySelector('[class*="modal"]');
                console.log(`Fallback modal element:`, modalFallback);
                
                if (modalFallback) {
                    modalFallback.innerHTML = modalContent;
                    console.log(`Modal content updated via fallback`);
                } else {
                    console.error('No se pudo encontrar el elemento modal para actualizar');
                    showNotification('Error al actualizar el modal', 'error');
                }
            }
        })
        .catch(error => {
            console.error('Error loading aging detail:', error);
            showNotification('Error al cargar datos de aging', 'error');
        });
}

/**
 * Generate EDPs table HTML for aging modal
 */
function generateAgingEDPsTable(aging_edps, range) {
    if (!aging_edps || aging_edps.length === 0) {
        return `
            <tr>
                <td colspan="8" class="no-data-cell">
                    <div class="no-data-message">
                        <div class="no-data-text">No hay EDPs en aging ${range} días</div>
                        <div class="no-data-subtext">Excelente gestión preventiva de cobros</div>
                    </div>
                </td>
            </tr>
        `;
    }
    
    return aging_edps.map(edp => {
        const riskClass = edp.risk_level || 'warning';
        return `
            <tr class="aging-edp-row ${riskClass}-row" onclick="showEDPDetailModal('${edp.n_edp}')">
                <td class="edp-id-cell text-center" title="Número EDP">${edp.n_edp || 'N/A'}</td>
                <td class="cliente-cell" title="${edp.cliente}">${edp.cliente}</td>
                <td class="proyecto-cell font-medium" title="${edp.proyecto}">${edp.proyecto}</td>
                <td class="monto-cell text-right">${formatAmount(edp.monto_propuesto)}</td>
                <td class="dias-cell text-center">
                    <span class="dias-badge ${riskClass}">${edp.dias}d</span>
                </td>
                <td class="jefe-cell" title="${edp.jefe_proyecto}">${edp.jefe_proyecto}</td>
                <td class="estado-cell text-center">
                    <span class="status-badge ${getStatusBadgeClass(edp.estado)}">${edp.estado || 'N/A'}</span>
                </td>
                <td class="email-cell text-center">
                    <button 
                        class="email-btn ${riskClass}" 
                        onclick="event.stopPropagation(); sendIndividualEDPEmail('${edp.id || edp.n_edp}', '${edp.n_edp}', '${edp.cliente}')" 
                        title="Enviar email de aging (${edp.email_cliente})">
                        <svg width="14" height="14" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"></path>
                            <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"></path>
                        </svg>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Generate action plan HTML for aging modal
 */
function generateAgingActionPlan(summary, range) {
    const riskLevel = summary.risk_level;
    const totalEDPs = summary.total_edps;
    
    let actionPlan = '';
    
    switch (riskLevel) {
        case 'safe':
            actionPlan = `
                <div class="action-plan safe">
                    <div class="action-step">
                        <div class="step-icon">OK</div>
                        <div class="step-content">
                            <div class="step-title">Estado Saludable</div>
                            <div class="step-description">Los EDPs en este rango están dentro de parámetros normales</div>
                        </div>
                    </div>
                    <div class="action-step">
                        <div class="step-icon">MON</div>
                        <div class="step-content">
                            <div class="step-title">Monitoreo Rutinario</div>
                            <div class="step-description">Continuar con seguimiento semanal estándar</div>
                        </div>
                    </div>
                </div>
            `;
            break;
            
        case 'warning':
            actionPlan = `
                <div class="action-plan warning">
                    <div class="action-step">
                        <div class="step-icon">WARN</div>
                        <div class="step-content">
                            <div class="step-title">Contacto Preventivo</div>
                            <div class="step-description">Enviar emails de recordatorio a ${totalEDPs} clientes</div>
                        </div>
                    </div>
                    <div class="action-step">
                        <div class="step-icon">CALL</div>
                        <div class="step-content">
                            <div class="step-title">Llamadas de Seguimiento</div>
                            <div class="step-description">Programar llamadas para la próxima semana</div>
                        </div>
                    </div>
                    <div class="action-step">
                        <div class="step-icon">REV</div>
                        <div class="step-content">
                            <div class="step-title">Revisión en 7 Días</div>
                            <div class="step-description">Evaluar progreso y escalar si es necesario</div>
                        </div>
                    </div>
                </div>
            `;
            break;
            
        case 'alert':
        case 'danger':
            actionPlan = `
                <div class="action-plan critical">
                    <div class="action-step">
                        <div class="step-icon">URG</div>
                        <div class="step-content">
                            <div class="step-title">Acción Inmediata Requerida</div>
                            <div class="step-description">${totalEDPs} EDPs requieren atención urgente</div>
                        </div>
                    </div>
                    <div class="action-step">
                        <div class="step-icon">EMAIL</div>
                        <div class="step-content">
                            <div class="step-title">Emails Urgentes</div>
                            <div class="step-description">Enviar notificaciones críticas a todos los clientes</div>
                        </div>
                    </div>
                    <div class="action-step">
                        <div class="step-icon">CALL</div>
                        <div class="step-content">
                            <div class="step-title">Llamadas Inmediatas</div>
                            <div class="step-description">Contactar por teléfono en las próximas 24 horas</div>
                        </div>
                    </div>
                    <div class="action-step">
                        <div class="step-icon">ESC</div>
                        <div class="step-content">
                            <div class="step-title">Escalación a Gerencia</div>
                            <div class="step-description">Notificar a jefes de proyecto sobre situación crítica</div>
                        </div>
                    </div>
                </div>
            `;
            break;
            
        case 'critical':
            actionPlan = `
                <div class="action-plan critical">
                    <div class="action-step">
                        <div class="step-icon">CRIT</div>
                        <div class="step-content">
                            <div class="step-title">CRÍTICO - Acción Inmediata</div>
                            <div class="step-description">${totalEDPs} EDPs en estado crítico requieren intervención</div>
                        </div>
                    </div>
                    <div class="action-step">
                        <div class="step-icon">EMAIL</div>
                        <div class="step-content">
                            <div class="step-title">Emails Críticos</div>
                            <div class="step-description">Enviar notificaciones urgentes con plazo de 48 horas</div>
                        </div>
                    </div>
                    <div class="action-step">
                        <div class="step-icon">CALL</div>
                        <div class="step-content">
                            <div class="step-title">Llamadas Urgentes</div>
                            <div class="step-description">Contactar inmediatamente por teléfono</div>
                        </div>
                    </div>
                    <div class="action-step">
                        <div class="step-icon">MTG</div>
                        <div class="step-content">
                            <div class="step-title">Reunión de Emergencia</div>
                            <div class="step-description">Programar reunión con gerencia en las próximas 24 horas</div>
                        </div>
                    </div>
                    <div class="action-step">
                        <div class="step-icon">PLAN</div>
                        <div class="step-content">
                            <div class="step-title">Plan de Recuperación</div>
                            <div class="step-description">Desarrollar estrategia de cobro agresiva</div>
                        </div>
                    </div>
                </div>
            `;
            break;
            
        default:
            actionPlan = `
                <div class="action-plan neutral">
                    <div class="action-step">
                        <div class="step-icon">INFO</div>
                        <div class="step-content">
                            <div class="step-title">Información</div>
                            <div class="step-description">Revisar estado de ${totalEDPs} EDPs en este rango</div>
                        </div>
                    </div>
                </div>
            `;
    }
    
    return actionPlan;
}

/**
 * Send emails for specific aging range
 */
function sendAgingRangeEmails(range) {
    // Optimistic UI - show success immediately
    showNotification(`Enviando emails para aging ${range} días...`, 'info');
    
    // Disable button to prevent double-click
    const button = event.target;
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Enviando...';
    button.style.opacity = '0.7';
    
    // Show progress indicator
    const progressNotification = document.createElement('div');
    progressNotification.id = 'progress-notification';
    progressNotification.style.cssText = `
        position: fixed; top: 80px; right: 30px; z-index: 999998;
        background: #3b82f6; color: white; border-radius: 8px;
        padding: 12px 16px; font-family: 'JetBrains Mono', monospace;
        font-size: 12px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    `;
    progressNotification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <div class="spinner" style="width: 12px; height: 12px; border: 2px solid transparent; border-top: 2px solid white; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            <span>Procesando emails...</span>
        </div>
    `;
    document.body.appendChild(progressNotification);
    
    fetch('/management/api/send_aging_range_emails', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            range: range
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Emails enviados exitosamente para aging ${range} días`, 'success');
        } else {
            showNotification(`Error al enviar emails de aging ${range}: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error sending aging range emails:', error);
        showNotification('Error de conexión al enviar emails de aging', 'error');
    })
    .finally(() => {
        // Remove progress notification
        const progressNotification = document.getElementById('progress-notification');
        if (progressNotification) {
            progressNotification.remove();
        }
        
        // Re-enable button
        button.disabled = false;
        button.textContent = originalText;
        button.style.opacity = '1';
    });
}

/**
 * Send individual EDP email with optimistic UI
 */
function sendIndividualEDPEmail(edpId, edpNumber, cliente) {
    // Find the button that was clicked
    const button = event.target.closest('.email-btn');
    if (!button) return;
    
    const originalText = button.innerHTML;
    const originalClass = button.className;
    
    // Optimistic UI - disable button and show loading state
    button.disabled = true;
    button.innerHTML = `
        <svg width="14" height="14" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"></path>
            <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"></path>
        </svg>
        <span style="margin-left: 4px;">Enviando...</span>
    `;
    button.className = originalClass + ' sending';
    button.style.opacity = '0.7';
    
    showNotification(`Enviando email para EDP ${edpNumber} (${cliente})...`, 'info');
    
    fetch('/management/api/send_edp_email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            edp_id: edpId,
            edp_number: edpNumber,
            cliente: cliente
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Email enviado exitosamente para EDP ${edpNumber}`, 'success');
            // Show success state briefly
            button.innerHTML = `
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                <span style="margin-left: 4px;">Enviado</span>
            `;
            button.style.backgroundColor = '#10b981';
            button.style.color = 'white';
        } else {
            showNotification(`Error al enviar email para EDP ${edpNumber}: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error sending individual EDP email:', error);
        showNotification('Error de conexión al enviar email individual', 'error');
    })
    .finally(() => {
        // Re-enable button after a delay
        setTimeout(() => {
            button.disabled = false;
            button.innerHTML = originalText;
            button.className = originalClass;
            button.style.opacity = '1';
            button.style.backgroundColor = '';
            button.style.color = '';
        }, 3000);
    });
}

/**
 * Export aging range data
 */
function exportAgingRangeData(range) {
    console.log(`📊 Exporting aging data for range: ${range}`);
    showNotification(`Exportando datos de aging ${range} días...`, 'info');
    
    // Implementation would generate and download CSV/Excel report
    setTimeout(() => {
        showNotification('Datos de aging exportados exitosamente', 'success');
    }, 2000);
}

/**
 * Schedule aging followup
 */
function scheduleAgingFollowup(range) {
    console.log(`📅 Scheduling followup for aging range: ${range}`);
    showNotification(`Programando seguimiento para aging ${range} días...`, 'info');
    
    // Implementation would schedule followup tasks
    setTimeout(() => {
        showNotification('Seguimiento programado exitosamente', 'success');
    }, 1500);
}

/**
 * Show EDP detail modal (placeholder - implemented in dashboard-modals.js)
 */
function showEDPDetailModal(edpId) {
    console.log(`🔍 Opening EDP detail modal for: ${edpId}`);
    // This function is implemented in dashboard-modals.js
    // The modal will be handled by the existing implementation
    showNotification(`Abriendo detalles del EDP ${edpId}...`, 'info');
}

/**
 * Export aging report
 */
function exportAgingReport(range = 'all') {
    console.log(`📊 Exporting aging report for: ${range}`);
    // Implementation would generate and download report
    showNotification('Aging report exported successfully', 'success');
}

/**
 * Refresh aging data
 */
function refreshAgingData() {
    console.log('🔄 Refreshing aging data...');
    // Implementation would refresh data from server
    showNotification('Aging data refreshed', 'info');
}

/**
 * Generate collection plan
 */
function generateCollectionPlan() {
    console.log('📋 Generating collection plan...');
    showNotification('Collection plan generated', 'success');
}

/**
 * Schedule client calls
 */
function scheduleClientCalls() {
    console.log('📞 Scheduling client calls...');
    showNotification('Client calls scheduled', 'success');
}

/**
 * Update credit limits
 */
function updateCreditLimits() {
    console.log('💳 Updating credit limits...');
    showNotification('Credit limits updated', 'success');
}

/**
 * Export risk data
 */
function exportRiskData() {
    console.log('📈 Exporting risk data...');
    showNotification('Risk data exported', 'success');
}

/**
 * Show high risk clients
 */
function showHighRiskClients() {
    showModal('High Risk Clients', generateRiskClientsList('high'));
}

/**
 * Show watch list clients
 */
function showWatchListClients() {
    showModal('Watch List Clients', generateRiskClientsList('watch'));
}

/**
 * Show safe clients
 */
function showSafeClients() {
    showModal('Safe Clients', generateRiskClientsList('safe'));
}

/**
 * Show risk trends
 */
function showRiskTrends() {
    showModal('Risk Trends Analysis', `
        <div class="risk-trends-analysis">
            <div class="trend-chart-placeholder">
                📊 Risk trend chart would be displayed here
            </div>
            <div class="trend-insights">
                <h4>Key Insights:</h4>
                <ul>
                    <li>Average risk score: ${window.kpisData && window.kpisData.average_risk_score ? window.kpisData.average_risk_score.toFixed(0) : '--'}</li>
                    <li>Trend: ${window.kpisData && window.kpisData.risk_score_trend ? (window.kpisData.risk_score_trend > 0 ? 'Increasing' : 'Decreasing') : 'Stable'}</li>
                    <li>High risk clients: ${window.kpisData && window.kpisData.high_risk_clients_count ? window.kpisData.high_risk_clients_count : 0}</li>
                </ul>
            </div>
        </div>
    `);
}

/**
 * Update risk analysis based on timeframe
 */
function updateRiskAnalysis(timeframe) {
    console.log(`🔄 Updating risk analysis for ${timeframe} days`);
    showNotification('Risk analysis updated', 'info');
}

/**
 * Filter risk category
 */
function filterRiskCategory(category) {
    console.log(`🔍 Filtering by category: ${category}`);
    showNotification(`Filtered by ${category}`, 'info');
}

/**
 * Generate risk report
 */
function generateRiskReport() {
    console.log('📊 Generating comprehensive risk report...');
    showNotification('Risk report generated', 'success');
}

/**
 * Schedule review
 */
function scheduleReview() {
    console.log('📅 Scheduling risk review meeting...');
    showNotification('Review meeting scheduled', 'success');
}

// Helper functions

function getRiskLevel(range) {
    const riskLevels = {
        '0-15': 'LOW RISK',
        '16-30': 'NORMAL',
        '31-45': 'WATCH',
        '46-60': 'ALERT',
        '61-90': 'DANGER',
        '90+': 'CRITICAL'
    };
    return riskLevels[range] || 'UNKNOWN';
}

function getStatusBadgeClass(estado) {
    if (!estado) return 'neutral';
    
    const estadoLower = estado.toLowerCase();
    
    // Estados positivos/activos
    if (estadoLower.includes('aprobado') || estadoLower.includes('approved')) return 'safe';
    if (estadoLower.includes('pagado') || estadoLower.includes('paid')) return 'safe';
    if (estadoLower.includes('completado') || estadoLower.includes('completed')) return 'safe';
    if (estadoLower.includes('activo') || estadoLower.includes('active')) return 'good';
    if (estadoLower.includes('en proceso') || estadoLower.includes('in progress')) return 'good';
    
    // Estados de revisión/pendiente
    if (estadoLower.includes('revisión') || estadoLower.includes('review')) return 'warning';
    if (estadoLower.includes('pendiente') || estadoLower.includes('pending')) return 'warning';
    if (estadoLower.includes('en espera') || estadoLower.includes('waiting')) return 'warning';
    
    // Estados críticos/urgentes
    if (estadoLower.includes('rechazado') || estadoLower.includes('rejected')) return 'danger';
    if (estadoLower.includes('cancelado') || estadoLower.includes('cancelled')) return 'danger';
    if (estadoLower.includes('bloqueado') || estadoLower.includes('blocked')) return 'critical';
    if (estadoLower.includes('urgente') || estadoLower.includes('urgent')) return 'critical';
    
    // Estados neutrales
    if (estadoLower.includes('borrador') || estadoLower.includes('draft')) return 'neutral';
    if (estadoLower.includes('nuevo') || estadoLower.includes('new')) return 'neutral';
    
    // Por defecto
    return 'neutral';
}

function generateClientsModalContent() {
    return `
        <div class="accounts-modal-content">
            <div class="accounts-summary">Total unique clients across all projects</div>
            <div class="accounts-list">
                ${window.equipoData && Array.isArray(window.equipoData) ? 
                    window.equipoData.map(manager => 
                        manager.clients && Array.isArray(manager.clients) ?
                            manager.clients.map(client => `
                                <div class="account-item">
                                    <div class="account-name">${client.nombre}</div>
                                    <div class="account-details">PM: ${manager.nombre}</div>
                                </div>
                            `).join('') : ''
                    ).join('') : '<div class="no-data">No client data available</div>'
                }
            </div>
        </div>
    `;
}

function generateManagersModalContent() {
    return `
        <div class="accounts-modal-content">
            <div class="accounts-summary">Project managers and their portfolios</div>
            <div class="accounts-list">
                ${window.equipoData && Array.isArray(window.equipoData) ? 
                    window.equipoData.map(manager => `
                        <div class="account-item">
                            <div class="account-name">${manager.nombre}</div>
                            <div class="account-details">${manager.proyectos_count || 0} projects • DSO: ${manager.dso_days || '--'}d</div>
                        </div>
                    `).join('') : '<div class="no-data">No manager data available</div>'
                }
            </div>
        </div>
    `;
}

function generateProjectsModalContent() {
    let projectCount = 0;
    if (window.equipoData && Array.isArray(window.equipoData)) {
        projectCount = window.equipoData.reduce((total, manager) => {
            return total + (manager.proyectos_count || 0);
        }, 0);
    }
    
    return `
        <div class="accounts-modal-content">
            <div class="accounts-summary">${projectCount} active projects</div>
            <div class="accounts-list">
                ${window.equipoData && Array.isArray(window.equipoData) ? 
                    window.equipoData.map(manager => `
                        <div class="account-item">
                            <div class="account-name">${manager.proyectos_count || 0} Projects</div>
                            <div class="account-details">Managed by ${manager.nombre}</div>
                        </div>
                    `).join('') : '<div class="no-data">No project data available</div>'
                }
            </div>
        </div>
    `;
}

function generateRiskClientsList(riskType) {
    const riskConfig = {
        high: { title: 'High Risk Clients', threshold: 80, color: 'critical' },
        watch: { title: 'Watch List Clients', threshold: 40, color: 'warning' },
        safe: { title: 'Safe Clients', threshold: 0, color: 'success' }
    };
    
    const config = riskConfig[riskType];
    
    return `
        <div class="risk-clients-modal">
            <div class="risk-clients-header">
                <div class="risk-badge ${config.color}">${config.title.toUpperCase()}</div>
            </div>
            <div class="risk-clients-list">
                <div class="no-data">Risk client data would be displayed here based on actual client risk scores</div>
            </div>
        </div>
    `;
}

function showNotification(message, type = 'info') {
    console.log(`📢 ${type.toUpperCase()}: ${message}`);
    // Implementation would show actual notification UI
}