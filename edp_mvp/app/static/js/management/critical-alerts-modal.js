/**
 * Critical Alerts Modal System
 * 
 * Automatic modal display for critical alerts following Command Center design philosophy
 * - Shows automatically on first session visit
 * - Manual trigger via button
 * - No emojis, technical aesthetic
 * - Dark mode optimized
 */

class CriticalAlertsModal {
    constructor() {
        this.modalId = 'criticalAlertsModal';
        this.sessionKey = 'criticalAlertsShown';
        this.isInitialized = false;
        this.init();
    }

    /**
     * Initialize the modal system
     */
    init() {
        if (this.isInitialized) return;
        
        this.createModal();
        this.bindEvents();
        this.checkAutoShow();
        this.isInitialized = true;
        
        console.log('Critical Alerts Modal System initialized');
    }

    /**
     * Create the modal HTML structure
     */
    createModal() {
        const modalHTML = `
            <div id="${this.modalId}" class="critical-alerts-modal" style="display: none;">
                <div class="critical-alerts-backdrop"></div>
                <div class="critical-alerts-container">
                    <div class="critical-alerts-header">
                        <div class="critical-alerts-title">
                            <div class="critical-alerts-icon">ALERTA CRÍTICA</div>
                            <h2>Estado Crítico Detectado</h2>
                            <div class="critical-alerts-subtitle">Revisión de EDPs Requiriendo Atención Inmediata</div>
                        </div>
                        <button class="critical-alerts-close" onclick="criticalAlertsModal.close()">
                            <span class="close-icon">×</span>
                        </button>
                    </div>
                    
                    <div class="critical-alerts-content">
                        <div class="critical-alerts-summary">
                            <div class="summary-stats">
                                <div class="stat-item critical">
                                    <div class="stat-value" id="criticalCount">0</div>
                                    <div class="stat-label">EDPs Críticos</div>
                                </div>
                                <div class="stat-item amount">
                                    <div class="stat-value" id="criticalAmount">$0M</div>
                                    <div class="stat-label">Monto en Riesgo</div>
                                </div>
                                <div class="stat-item days">
                                    <div class="stat-value" id="criticalDays">0</div>
                                    <div class="stat-label">Días Promedio</div>
                                </div>
                            </div>
                        </div>
                        
                                         
                        <div class="critical-alerts-details">
                            <div class="details-header">
                                <h4>EDPs Críticos Detallados</h4>
                                <div class="details-summary">
                                    <span class="summary-item">
                                        <strong id="topCriticalCount">0</strong> EDPs prioritarios
                                    </span>
                                    <span class="summary-item">
                                        <strong id="topCriticalAmount">$0M</strong> en riesgo
                                    </span>
                                    <span class="summary-item">
                                        <strong id="topCriticalProjects">0</strong> proyectos afectados
                                    </span>
                                </div>
                            </div>
                            <div class="critical-edps-table-container" id="criticalEDPsList">
                                <!-- La tabla de EDPs críticos se cargará dinámicamente aquí -->
                            </div>
                        </div>
                        
                        <div class="critical-alerts-actions">
                            <div class="action-section">
                                <h3>Plan de Acción Inmediata</h3>
                                <div class="action-steps">
                                    <div class="action-step">
                                        <div class="step-badge">1</div>
                                        <div class="step-content">
                                            <strong>Contactar al cliente</strong>
                                            <span>Dentro de las próximas 4 horas</span>
                                        </div>
                                    </div>
                                    <div class="action-step">
                                        <div class="step-badge">2</div>
                                        <div class="step-content">
                                            <strong>Revisar documentación</strong>
                                            <span>Validar toda la documentación pendiente</span>
                                        </div>
                                    </div>
                                    <div class="action-step">
                                        <div class="step-badge">3</div>
                                        <div class="step-content">
                                            <strong>Actualizar estado</strong>
                                            <span>Actualizar el estado del documento en el sistema</span>
                                        </div>
                                    </div>
                                    <div class="action-step">
                                        <div class="step-badge">4</div>
                                        <div class="step-content">
                                            <strong>Escalar si es necesario</strong>
                                            <span>Supervisión si no hay respuesta del cliente</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="critical-alerts-footer">
                            <button class="btn-secondary" onclick="criticalAlertsModal.close()">
                                Entendido
                            </button>
                            <button class="btn-primary" onclick="criticalAlertsModal.viewDetails()">
                                Ver Detalles Completos
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Close modal on backdrop click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('critical-alerts-backdrop')) {
                this.close();
            }
        });

        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible()) {
                this.close();
            }
        });
    }

    /**
     * Check if modal should be shown automatically
     */
    checkAutoShow() {
        const hasShown = sessionStorage.getItem(this.sessionKey);
        
        if (!hasShown && this.shouldShowAutoModal()) {
            // Delay to ensure page is fully loaded
            setTimeout(() => {
                this.show();
            }, 1500);
        }
    }

    /**
     * Determine if auto-modal should be shown
     */
    shouldShowAutoModal() {
        // Check if there are critical alerts to show
        const kpisData = window.kpisData;
        if (!kpisData) return false;
        
        const criticalCount = kpisData.total_critical_edps || kpisData.critical_projects_count || 0;
        const criticalAmount = kpisData.critical_amount || 0;
        
        return criticalCount > 0 || criticalAmount > 0;
    }

    /**
     * Show the modal
     */
    show() {
        this.updateModalContent();
        const modal = document.getElementById(this.modalId);
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            
            // Mark as shown in session
            sessionStorage.setItem(this.sessionKey, 'true');
            
            console.log('Critical Alerts Modal displayed');
        }
    }

    /**
     * Close the modal
     */
    close() {
        const modal = document.getElementById(this.modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
            console.log('Critical Alerts Modal closed');
        }
    }

    /**
     * Check if modal is visible
     */
    isVisible() {
        const modal = document.getElementById(this.modalId);
        return modal && modal.style.display === 'flex';
    }

    /**
     * Update modal content with current data
     */
    updateModalContent() {
        const kpisData = window.kpisData;
        if (!kpisData) return;

        const criticalCount = kpisData.total_critical_edps || kpisData.critical_projects_count || 0;
        const criticalAmount = kpisData.critical_amount || 0;
        const criticalDays = kpisData.critical_days_average || 0;

        // Update stats
        const countElement = document.getElementById('criticalCount');
        const amountElement = document.getElementById('criticalAmount');
        const daysElement = document.getElementById('criticalDays');

        if (countElement) countElement.textContent = criticalCount;
        if (amountElement) amountElement.textContent = this.formatAmount(criticalAmount);
        if (daysElement) daysElement.textContent = Math.round(criticalDays);
        
        // Load detailed critical EDPs
        this.loadCriticalEDPsDetails();
    }

    /**
     * Format amount to millions
     */
    formatAmount(amount) {
        if (!amount || amount === 0) return '$0M';
        const amountInMillions = amount / 1000000;
        return `$${amountInMillions.toFixed(1)}M`;
    }

    /**
     * Load detailed critical EDPs from backend
     */
    async loadCriticalEDPsDetails() {
        try {
            const response = await fetch('/management/api/critical_edps');
            if (!response.ok) {
                console.log('Error loading critical EDPs details');
                return;
            }
            
            const data = await response.json();
            console.log('Critical EDPs API response:', data);
            
            if (data.success && data.critical_edps) {
                this.displayCriticalEDPsDetails(data.critical_edps);
            } else {
                console.log('No critical EDPs data available');
            }
        } catch (error) {
            console.log('Error loading critical EDPs details:', error);
        }
    }

    /**
     * Display critical EDPs details in the modal
     */
    displayCriticalEDPsDetails(criticalData) {
        console.log('Displaying critical EDPs details:', criticalData);
        
        const listContainer = document.getElementById('criticalEDPsList');
        const topCountElement = document.getElementById('topCriticalCount');
        const topAmountElement = document.getElementById('topCriticalAmount');
        
        if (!listContainer) {
            console.log('Critical EDPs list container not found');
            return;
        }
        
        // Check if we have the new format (projects with EDPs) or old format (direct EDPs)
        const isNewFormat = criticalData.length > 0 && criticalData[0].edps;
        console.log('Data format detected:', isNewFormat ? 'new (projects)' : 'old (direct EDPs)');
        
        if (isNewFormat) {
            // New format: projects with EDPs
            this.displayProjectsFormat(criticalData, listContainer, topCountElement, topAmountElement);
        } else {
            // Old format: direct EDPs list
            this.displayEDPsFormat(criticalData, listContainer, topCountElement, topAmountElement);
        }
    }

    /**
     * Display data in projects format (new format)
     */
    displayProjectsFormat(criticalData, listContainer, topCountElement, topAmountElement) {
        // Update summary
        if (topCountElement) {
            topCountElement.textContent = criticalData.length || 0;
        }
        
        if (topAmountElement) {
            const totalAmount = criticalData.reduce((sum, project) => sum + (project.total_monto || 0), 0);
            topAmountElement.textContent = this.formatAmount(totalAmount);
        }
        
        // Generate EDPs list
        let html = '';
        
        if (criticalData && criticalData.length > 0) {
            // Sort by max days without movement (most critical first)
            const sortedProjects = criticalData.sort((a, b) => 
                (b.max_dias_sin_movimiento || 0) - (a.max_dias_sin_movimiento || 0)
            );
            
            // Show top 5 most critical projects
            const topProjects = sortedProjects.slice(0, 5);
            
            topProjects.forEach((project, index) => {
                const projectAmount = this.formatAmount(project.total_monto || 0);
                const maxDays = project.max_dias_sin_movimiento || 0;
                const edpCount = project.edps ? project.edps.length : 0;
                
                html += `
                    <div class="critical-edp-item">
                        <div class="edp-header">
                            <div class="edp-project-info">
                                <div class="project-name">${project.proyecto || 'Proyecto N/A'}</div>
                                <div class="project-client">${project.cliente || 'Cliente N/A'}</div>
                            </div>
                            <div class="edp-metrics">
                                <div class="metric critical-days">
                                    <span class="metric-value">${maxDays}</span>
                                    <span class="metric-label">días</span>
                                </div>
                                <div class="metric amount">
                                    <span class="metric-value">${projectAmount}</span>
                                    <span class="metric-label">monto</span>
                                </div>
                                <div class="metric edp-count">
                                    <span class="metric-value">${edpCount}</span>
                                    <span class="metric-label">EDPs</span>
                                </div>
                            </div>
                        </div>
                        <div class="edp-details">
                            <div class="project-manager">
                                <strong>Jefe de Proyecto:</strong> ${project.jefe_proyecto || 'Sin asignar'}
                            </div>
                            <div class="edp-list">
                                ${this.generateEDPsList(project.edps || [])}
                            </div>
                        </div>
                    </div>
                `;
            });
        } else {
            html = `
                <div class="no-critical-edps">
                    <div class="no-data-message">No se encontraron EDPs críticos en este momento</div>
                </div>
            `;
        }
        
        listContainer.innerHTML = html;
    }

    /**
     * Display data in EDPs format (current API format)
     */
    displayEDPsFormat(criticalEDPs, listContainer, topCountElement, topAmountElement) {
        console.log('Displaying EDPs format with data:', criticalEDPs);
        
        // Update summary
        if (topCountElement) {
            topCountElement.textContent = criticalEDPs.length || 0;
        }
        
        if (topAmountElement) {
            const totalAmount = criticalEDPs.reduce((sum, edp) => sum + (edp.monto || 0), 0);
            topAmountElement.textContent = this.formatAmount(totalAmount);
        }
        
        // Update projects count
        const topProjectsElement = document.getElementById('topCriticalProjects');
        if (topProjectsElement) {
            const uniqueProjects = new Set();
            criticalEDPs.forEach(edp => {
                const projectKey = `${edp.proyecto}_${edp.cliente}`;
                uniqueProjects.add(projectKey);
            });
            topProjectsElement.textContent = uniqueProjects.size;
        }
        
        // Generate EDPs table
        let html = '';
        
        if (criticalEDPs && criticalEDPs.length > 0) {
            // Sort by days first, then by amount (most critical first)
            const sortedEDPs = criticalEDPs.sort((a, b) => {
                const daysA = b.dias || 0;
                const daysB = a.dias || 0;
                if (daysA !== daysB) return daysA - daysB;
                return (b.monto || 0) - (a.monto || 0);
            });
            
            // Show top 15 most critical EDPs
            const topEDPs = sortedEDPs.slice(0, 15);
            
            html = `
                <div class="critical-edps-table-wrapper">
                    <div class="table-header-actions">
                        <div class="table-summary">
                            <span class="summary-highlight">
                                <strong>${topEDPs.filter(edp => (edp.dias || 0) > 90).length}</strong> CRÍTICOS
                            </span>
                            <span class="summary-highlight">
                                <strong>${topEDPs.filter(edp => (edp.dias || 0) > 60 && (edp.dias || 0) <= 90).length}</strong> ALTOS
                            </span>
                            <span class="summary-highlight">
                                <strong>${this.formatAmount(topEDPs.reduce((sum, edp) => sum + (edp.monto || 0), 0))}</strong> TOTAL
                            </span>
                        </div>

                    </div>
                    <table class="critical-edps-table">
                        <thead>
                            <tr>
                                <th class="th-priority">#</th>
                                <th class="th-urgency">Urgencia</th>
                                <th class="th-edp">EDP</th>
                                <th class="th-project">Proyecto</th>
                                <th class="th-client">Cliente</th>
                                <th class="th-manager">Jefe Proyecto</th>
                                <th class="th-days">Días</th>
                                <th class="th-amount">Monto</th>
                                <th class="th-status">Estado</th>
                                <th class="th-actions">Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${topEDPs.map((edp, index) => {
                                const edpId = edp.n_edp || edp.id || 'N/A';
                                const edpAmount = this.formatAmount(edp.monto || 0);
                                const edpDays = edp.dias || edp.dias_sin_movimiento || 0;
                                const edpStatus = edp.estado || 'pendiente';
                                
                                // Determine urgency level
                                const urgencyClass = edpDays > 90 ? 'critical-urgency' : edpDays > 60 ? 'high-urgency' : 'medium-urgency';
                                const urgencyText = edpDays > 90 ? 'CRÍTICO' : edpDays > 60 ? 'ALTO' : 'MEDIO';
                                const priorityClass = index < 3 ? 'top-priority' : index < 8 ? 'high-priority' : 'normal-priority';
                                
                                return `
                                    <tr class="edp-row ${urgencyClass} ${priorityClass}" data-edp-id="${edpId}">
                                        <td class="td-priority">
                                            <span class="priority-number">${index + 1}</span>
                                        </td>
                                        <td class="td-urgency">
                                            <span class="urgency-badge ${urgencyClass}">${urgencyText}</span>
                                            ${edpDays > 90 ? '<span class="blink-warning">!</span>' : ''}
                                        </td>
                                        <td class="td-edp">
                                            <span class="edp-id">${edpId}</span>
                                        </td>
                                        <td class="td-project">
                                            <span class="project-name">${edp.proyecto || 'N/A'}</span>
                                        </td>
                                        <td class="td-client">
                                            <span class="client-name">${edp.cliente || 'N/A'}</span>
                                        </td>
                                        <td class="td-manager">
                                            <span class="manager-name">${edp.jefe_proyecto || 'Sin asignar'}</span>
                                        </td>
                                        <td class="td-days">
                                            <span class="days-value ${edpDays > 90 ? 'critical-days' : edpDays > 60 ? 'high-days' : ''}">${edpDays}</span>
                                        </td>
                                        <td class="td-amount">
                                            <span class="amount-value">${edpAmount}</span>
                                        </td>
                                        <td class="td-status">
                                            <span class="status-badge">${edpStatus}</span>
                                        </td>
                                        <td class="td-actions">
                                            <div class="action-buttons">
                                                <button class="action-btn-small email-btn" onclick="criticalAlertsModal.sendIndividualEmail('${edpId}')" title="Enviar Email">
                                                    EMAIL
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            html = `
                <div class="no-critical-edps">
                    <div class="no-data-message">No se encontraron EDPs críticos en este momento</div>
                </div>
            `;
        }
        
        listContainer.innerHTML = html;
    }

    /**
     * Generate HTML for individual EDPs list
     */
    generateEDPsList(edps) {
        if (!edps || edps.length === 0) {
            return '<div class="no-edps">Sin EDPs específicos</div>';
        }
        
        // Sort EDPs by days (most critical first)
        // Sort by days first, then by amount (most critical first)
        const sortedEDPs = edps.sort((a, b) => {
            const daysA = b.dias || b.dias_sin_movimiento || 0;
            const daysB = a.dias || a.dias_sin_movimiento || 0;
            if (daysA !== daysB) return daysA - daysB;
            return (b.monto || 0) - (a.monto || 0);
        });
        
        // Show top 6 EDPs per project for better overview
        const topEDPs = sortedEDPs.slice(0, 6);
        
        return topEDPs.map(edp => {
            const edpId = edp.n_edp || edp.id || 'N/A';
            const edpAmount = this.formatAmount(edp.monto || 0);
            const edpDays = edp.dias || edp.dias_sin_movimiento || 0;
            const edpStatus = edp.estado || 'pendiente';
            
            console.log('EDP item:', { id: edpId, amount: edpAmount, days: edpDays, status: edpStatus });
            
            return `
                <div class="edp-item">
                    <div class="edp-id">${edpId}</div>
                    <div class="edp-info">
                        <div class="edp-amount">${edpAmount}</div>
                        <div class="edp-days">${edpDays} días</div>
                        <div class="edp-status">${edpStatus}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    /**
     * View detailed critical alerts
     */
    viewDetails() {
        this.close();
        
        // Trigger the existing critical EDPs modal
        if (typeof showCriticalEDPsModal === 'function') {
            showCriticalEDPsModal();
        } else {
            console.log('showCriticalEDPsModal function not available');
        }
    }

    /**
     * Manual trigger for showing the modal
     */
    showManual() {
        this.show();
    }

    /**
     * Reset session state (for testing)
     */
    resetSession() {
        sessionStorage.removeItem(this.sessionKey);
        console.log('Critical Alerts Modal session reset');
    }



    /**
     * Send individual email for specific EDP
     */
    async sendIndividualEmail(edpId) {
        console.log(`Sending individual email for EDP: ${edpId}`);
        this.showNotification(`Enviando email a EDP ${edpId}...`, 'info');
        
        try {
            const response = await fetch('/management/api/send_edp_email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    edp_id: edpId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Email enviado exitosamente a EDP ${edpId}`, 'success');
            } else {
                this.showNotification(`Error al enviar email: ${data.message || 'Error desconocido'}`, 'error');
            }
        } catch (error) {
            console.error('Error sending individual email:', error);
            this.showNotification('Error de conexión al enviar email', 'error');
        }
    }



    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 3000);
    }
}

// Initialize the modal system
let criticalAlertsModal;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    criticalAlertsModal = new CriticalAlertsModal();
});

// Also initialize if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        criticalAlertsModal = new CriticalAlertsModal();
    });
} else {
    criticalAlertsModal = new CriticalAlertsModal();
}

// Global functions for external access
window.showCriticalAlertsModal = () => {
    if (criticalAlertsModal) {
        criticalAlertsModal.showManual();
    }
};

window.resetCriticalAlertsSession = () => {
    if (criticalAlertsModal) {
        criticalAlertsModal.resetSession();
    }
}; 