/**
 * Manager Dashboard Optimized JavaScript
 * Handles async loading, cache management, and real-time updates
 */

class ManagerDashboardOptimized {
    constructor() {
        this.taskId = null;
        this.refreshInterval = null;
        this.cacheStatus = {
            isImmediate: false,
            isCached: true,
            isStale: false,
            taskId: null
        };
        this.init();
    }

    init() {
        console.log('🚀 Initializing optimized manager dashboard...');
        
        // Get cache status from page data
        const cacheStatusElement = document.getElementById('cache-status');
        if (cacheStatusElement) {
            try {
                this.cacheStatus = JSON.parse(cacheStatusElement.textContent);
                this.taskId = this.cacheStatus.taskId;
                console.log('📊 Cache status:', this.cacheStatus);
            } catch (e) {
                console.warn('Failed to parse cache status:', e);
            }
        }

        // Setup event listeners
        this.setupEventListeners();
        
        // Show loading indicators if needed
        this.handleCacheStatus();
        
        // Start monitoring if there's an active task
        if (this.taskId) {
            this.startTaskMonitoring();
        }

        // Setup event-based refresh (no more auto-refresh timers)
        this.setupEventBasedRefresh();
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('force-refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.forceRefresh());
        }

        // Clear cache button
        const clearCacheBtn = document.getElementById('clear-cache-btn');
        if (clearCacheBtn) {
            clearCacheBtn.addEventListener('click', () => this.clearCache());
        }

        // Filter change handlers
        const filterElements = document.querySelectorAll('.dashboard-filter');
        filterElements.forEach(element => {
            element.addEventListener('change', () => this.onFilterChange());
        });
    }

    handleCacheStatus() {
        const statusContainer = document.getElementById('dashboard-status');
        
        if (this.cacheStatus.isStale) {
            this.showStatusMessage('⚠️ Mostrando datos en cache. Actualizando...', 'warning');
        } else if (this.cacheStatus.isImmediate) {
            this.showStatusMessage('⚡ Datos básicos cargados. Calculando métricas completas...', 'info');
        } else if (!this.cacheStatus.isCached) {
            this.showStatusMessage('🔄 Calculando dashboard...', 'info');
        }
    }

    showStatusMessage(message, type = 'info') {
        const statusContainer = document.getElementById('dashboard-status');
        if (!statusContainer) return;

        const alertClass = type === 'warning' ? 'alert-warning' : 
                          type === 'error' ? 'alert-danger' : 'alert-info';

        statusContainer.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <span class="status-icon">${this.getStatusIcon(type)}</span>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    }

    getStatusIcon(type) {
        switch (type) {
            case 'warning': return '⚠️';
            case 'error': return '❌';
            case 'success': return '✅';
            default: return 'ℹ️';
        }
    }

    async forceRefresh() {
        console.log('🔄 Force refreshing dashboard...');
        
        const refreshBtn = document.getElementById('force-refresh-btn');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Actualizando...';
        }

        try {
            const currentUrl = new URL(window.location);
            const refreshUrl = this.cacheStatus.refreshUrl || `/management/dashboard/refresh${currentUrl.search}`;
            
            const response = await fetch(refreshUrl);
            const result = await response.json();

            if (result.success) {
                this.updateDashboardData(result.data);
                this.showStatusMessage('✅ Dashboard actualizado correctamente', 'success');
                
                // Auto-hide success message
                setTimeout(() => {
                    const statusContainer = document.getElementById('dashboard-status');
                    if (statusContainer) statusContainer.innerHTML = '';
                }, 3000);
            } else {
                this.showStatusMessage(`❌ Error: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Error refreshing dashboard:', error);
            this.showStatusMessage('❌ Error de conexión al actualizar', 'error');
        } finally {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Actualizar';
            }
        }
    }

    async clearCache() {
        console.log('🗑️ Clearing cache...');
        
        try {
            const response = await fetch('/management/api/cache/clear?pattern=manager_dashboard:*');
            const result = await response.json();

            if (result.success) {
                this.showStatusMessage(`✅ Cache limpiado (${result.cleared_count} entradas)`, 'success');
                
                // Refresh after clearing cache
                setTimeout(() => this.forceRefresh(), 1000);
            } else {
                this.showStatusMessage(`❌ Error limpiando cache: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Error clearing cache:', error);
            this.showStatusMessage('❌ Error de conexión al limpiar cache', 'error');
        }
    }

    startTaskMonitoring() {
        if (!this.taskId) return;

        console.log(`📡 Monitoring task: ${this.taskId}`);
        
        this.refreshInterval = setInterval(async () => {
            try {
                const response = await fetch(`/management/dashboard/status/${this.taskId}`);
                const result = await response.json();

                console.log('Task status:', result);

                if (result.state === 'SUCCESS') {
                    console.log('✅ Task completed successfully');
                    this.updateDashboardData(result.result);
                    this.showStatusMessage('✅ Dashboard actualizado correctamente', 'success');
                    this.stopTaskMonitoring();
                    
                    // Auto-hide success message
                    setTimeout(() => {
                        const statusContainer = document.getElementById('dashboard-status');
                        if (statusContainer) statusContainer.innerHTML = '';
                    }, 3000);
                    
                } else if (result.state === 'FAILURE') {
                    console.error('❌ Task failed:', result.status);
                    this.showStatusMessage(`❌ Error en cálculo: ${result.status}`, 'error');
                    this.stopTaskMonitoring();
                    
                } else if (result.state === 'PROGRESS') {
                    const progress = Math.round((result.current / result.total) * 100);
                    this.showStatusMessage(`🔄 Progreso: ${progress}% - ${result.status}`, 'info');
                }
                
            } catch (error) {
                console.error('Error checking task status:', error);
                this.stopTaskMonitoring();
            }
        }, 2000); // Check every 2 seconds
    }

    stopTaskMonitoring() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            this.taskId = null;
        }
    }

    setupEventBasedRefresh() {
        // Instead of auto-refresh, setup event listeners for real data changes
        console.log('📡 Setting up event-based refresh system (no timers)');
        
        // Listen for Socket.IO events if available
        if (window.socket) {
            window.socket.on('edp_actualizado', (data) => {
                console.log('📢 EDP updated via Socket.IO:', data);
                this.handleDataChange('edp_updated', data);
            });
            
            window.socket.on('cache_invalidated', (data) => {
                console.log('📢 Cache invalidated via Socket.IO:', data);
                this.handleCacheInvalidation(data);
            });
        }
        
        // Listen for visibility change (user comes back to tab)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.handlePageVisibilityChange();
            }
        });
        
        // Optional: Check for updates when user interacts (but no auto-timers)
        ['click', 'keydown'].forEach(event => {
            document.addEventListener(event, () => {
                this.onUserActivity();
            }, { once: true, passive: true });
        });
        
        console.log('✅ Event-based refresh system active (no auto-refresh timers)');
    }

    handleDataChange(changeType, data) {
        console.log(`🔄 Handling data change: ${changeType}`, data);
        
        // Only refresh if the change affects current view
        if (this.shouldRefreshForChange(changeType, data)) {
            this.showStatusMessage('📡 Datos actualizados, refrescando...', 'info');
            
            // Small delay to avoid too frequent updates
            clearTimeout(this.dataChangeTimeout);
            this.dataChangeTimeout = setTimeout(() => {
                this.refreshKPIs();
            }, 1000);
        }
    }

    handleCacheInvalidation(data) {
        console.log('🗑️ Cache invalidated, data should be fresh on next request', data);
        // Just log it, don't auto-refresh - let user decide when to refresh
        this.showStatusMessage('💾 Cache actualizado por cambios en datos', 'success');
        
        // Auto-hide message
        setTimeout(() => {
            const statusContainer = document.getElementById('dashboard-status');
            if (statusContainer) statusContainer.innerHTML = '';
        }, 3000);
    }

    handlePageVisibilityChange() {
        console.log('👁️ User returned to page, checking for stale data');
        
        // Check cache age, but don't auto-refresh
        this.getCacheStatus().then(status => {
            if (status && status.cache_age > 300) { // 5 minutes
                this.showStatusMessage('⏰ Los datos pueden estar desactualizados. <button onclick="window.managerDashboard.forceRefresh()" class="btn btn-sm btn-outline-primary ms-2">Actualizar</button>', 'warning');
            }
        });
    }

    onUserActivity() {
        // Reset the user activity listener for next time
        setTimeout(() => {
            ['click', 'keydown'].forEach(event => {
                document.addEventListener(event, () => {
                    this.onUserActivity();
                }, { once: true, passive: true });
            });
        }, 60000); // Reset after 1 minute
    }

    shouldRefreshForChange(changeType, data) {
        // Define which changes should trigger refresh for current view
        const refreshTriggers = ['edp_updated', 'edp_state_changed', 'project_updated'];
        return refreshTriggers.includes(changeType);
    }

    async refreshKPIs() {
        // This method now only runs on-demand, not on timer
        try {
            console.log('🔄 Refreshing KPIs (triggered by event, not timer)');
            const currentUrl = new URL(window.location);
            const response = await fetch(`/management/api/kpis${currentUrl.search}`);
            const result = await response.json();

            if (result.success) {
                this.updateKPIElements(result.data);
                console.log('✅ KPIs refreshed from', result.source);
            }
        } catch (error) {
            console.error('Error refreshing KPIs:', error);
        }
    }

    updateKPIElements(kpis) {
        // Update KPI cards with new data
        Object.keys(kpis).forEach(key => {
            const element = document.querySelector(`[data-kpi="${key}"]`);
            if (element) {
                element.textContent = kpis[key];
                
                // Add pulse animation to indicate update
                element.classList.add('kpi-updated');
                setTimeout(() => element.classList.remove('kpi-updated'), 1000);
            }
        });
    }

    updateDashboardData(data) {
        console.log('🔄 Updating dashboard with new data...');
        
        try {
            // Update KPIs
            if (data.kpis) {
                this.updateKPIElements(data.kpis);
            }

            // Update charts
            if (data.charts && window.updateCharts) {
                window.updateCharts(data.charts);
            }

            // Update financial metrics
            if (data.financial_metrics) {
                this.updateFinancialMetrics(data.financial_metrics);
            }

            // Update alerts
            if (data.alerts) {
                this.updateAlerts(data.alerts);
            }

            // Update last updated timestamp
            const timestampElement = document.getElementById('last-updated');
            if (timestampElement) {
                timestampElement.textContent = new Date(data.last_updated || Date.now()).toLocaleString();
            }

        } catch (error) {
            console.error('Error updating dashboard data:', error);
        }
    }

    updateFinancialMetrics(metrics) {
        Object.keys(metrics).forEach(key => {
            const element = document.querySelector(`[data-metric="${key}"]`);
            if (element) {
                element.textContent = metrics[key];
            }
        });
    }

    updateAlerts(alerts) {
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) return;

        alertsContainer.innerHTML = alerts.map(alert => `
            <div class="alert alert-${alert.type || 'info'} alert-dismissible fade show">
                <strong>${alert.title || 'Alerta'}</strong>
                ${alert.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `).join('');
    }

    onFilterChange() {
        // Debounce filter changes
        clearTimeout(this.filterTimeout);
        this.filterTimeout = setTimeout(() => {
            console.log('🔍 Filters changed, refreshing dashboard...');
            this.showStatusMessage('🔄 Aplicando filtros...', 'info');
            
            // Submit the form or trigger refresh
            const form = document.querySelector('.filters-form');
            if (form) {
                form.submit();
            }
        }, 500);
    }

    // Performance monitoring
    async getPerformanceMetrics() {
        try {
            const response = await fetch('/management/api/performance/metrics');
            const result = await response.json();
            console.log('📊 Performance metrics:', result);
            return result;
        } catch (error) {
            console.error('Error getting performance metrics:', error);
            return null;
        }
    }

    // Cache status monitoring
    async getCacheStatus() {
        try {
            const response = await fetch('/management/api/cache/status');
            const result = await response.json();
            console.log('💾 Cache status:', result);
            return result;
        } catch (error) {
            console.error('Error getting cache status:', error);
            return null;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.managerDashboard = new ManagerDashboardOptimized();
});

// CSS for animations
const style = document.createElement('style');
style.textContent = `
    .kpi-updated {
        animation: pulse-update 1s ease-in-out;
    }

    @keyframes pulse-update {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); background-color: rgba(40, 167, 69, 0.1); }
        100% { transform: scale(1); }
    }

    .dashboard-loading {
        position: relative;
    }

    .dashboard-loading::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .status-icon {
        margin-right: 8px;
        font-size: 1.1em;
    }
`;
document.head.appendChild(style);
