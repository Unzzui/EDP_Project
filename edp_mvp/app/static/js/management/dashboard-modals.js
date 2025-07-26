/**
 * Dashboard Management - Modals JavaScript
 * Funcionalidad de modales del dashboard de management
 */

/**
 * Muestra detalles de un jefe de proyecto
 */
function showManagerDetail(nombre, dso, monto, proyectos) {
    // Parse the DSO value to get just the number
    const dsoValue = parseInt(dso.replace('d', ''));
    const montoValue = parseFloat(monto.replace('M CLP', ''));
    const proyectosCount = parseInt(proyectos.replace(' proyectos', ''));
    
    // Calculate critical EDPs (simulate based on DSO)
    const criticalEDPs = Math.max(0, Math.floor((dsoValue - 60) / 15));
    
    // Determine trend based on DSO
    let trend = '→';
    let trendText = 'Estable';
    let trendClass = 'stable';
    
    if (dsoValue > 150) {
        trend = '↗️';
        trendText = 'Empeorando';
        trendClass = 'worsening';
    } else if (dsoValue < 120) {
        trend = '↘️';
        trendText = 'Mejorando';
        trendClass = 'improving';
    }

    const modalContent = `
        <div class="manager-detail-modal">
            <div class="manager-header-section">
                <div class="manager-avatar">
                    <div class="manager-initials">${nombre.split(' ').map(n => n[0]).join('')}</div>
                </div>
                <div class="manager-info">
                    <h3 class="manager-name">${nombre}</h3>
                    <div class="manager-contact">
                        <div class="contact-item">
                            <span class="contact-label">Email:</span>
                            <span class="contact-value">${nombre.toLowerCase().replace(' ', '.')}@company.com</span>
                        </div>
                        <div class="contact-item">
                            <span class="contact-label">Teléfono:</span>
                            <span class="contact-value">+56 9 xxxx xxxx</span>
                        </div>
                        <div class="contact-item">
                            <span class="contact-label">Última actualización:</span>
                            <span class="contact-value">${new Date().toLocaleDateString('es-CL')}</span>
                        </div>
                    </div>
                </div>
                <div class="manager-performance">
                    <div class="performance-metric critical">
                        <div class="metric-value">${dsoValue}d</div>
                        <div class="metric-label">DSO Actual</div>
                    </div>
                    <div class="performance-trend ${trendClass}">
                        <div class="trend-icon">${trend}</div>
                        <div class="trend-text">${trendText}</div>
                    </div>
                </div>
            </div>

            <div class="manager-kpis-grid">
                <div class="manager-kpi">
                    <div class="kpi-value warning">${montoValue.toFixed(1)}M</div>
                    <div class="kpi-label">CLP Gestionado</div>
                </div>
                <div class="manager-kpi">
                    <div class="kpi-value info">${proyectosCount}</div>
                    <div class="kpi-label">Proyectos Activos</div>
                </div>
                <div class="manager-kpi">
                    <div class="kpi-value ${criticalEDPs > 0 ? 'critical' : 'positive'}">${criticalEDPs}</div>
                    <div class="kpi-label">EDPs Críticos</div>
                </div>
                <div class="manager-kpi">
                    <div class="kpi-value neutral">${Math.max(0, dsoValue - 35)}</div>
                    <div class="kpi-label">Días sobre Target</div>
                </div>
            </div>

            <div class="manager-projects-section">
                <div class="kpi-section-title">Proyectos Bajo Responsabilidad</div>
                <div class="kpi-table-container">
                    <table class="kpi-detail-table">
                        <thead>
                            <tr>
                                <th>Proyecto</th>
                                <th>Cliente</th>
                                <th>Monto</th>
                                <th>DSO</th>
                                <th>Estado</th>
                                <th>Último Contacto</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${generateManagerProjects(nombre, proyectosCount, montoValue)}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="manager-comparison-section">
                <div class="kpi-section-title">Comparación con Equipo</div>
                <div class="comparison-chart">
                    <div class="comparison-bar">
                        <span class="comparison-label">Promedio Equipo</span>
                        <div class="comparison-bar-fill" style="width: 70%">
                            <span class="comparison-value">142d</span>
                        </div>
                    </div>
                    <div class="comparison-bar current">
                        <span class="comparison-label">${nombre}</span>
                        <div class="comparison-bar-fill" style="width: ${Math.min(100, (dsoValue / 200) * 100)}%">
                            <span class="comparison-value">${dsoValue}d</span>
                        </div>
                    </div>
                    <div class="comparison-bar target">
                        <span class="comparison-label">Target</span>
                        <div class="comparison-bar-fill" style="width: 25%">
                            <span class="comparison-value">35d</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="manager-actions-section">
                <div class="kpi-section-title">Acciones Sugeridas</div>
                <div class="action-suggestions">
                    <div class="suggestion-item priority-high">
                        <div class="suggestion-priority">ALTA</div>
                        <div class="suggestion-text">Revisar ${criticalEDPs > 0 ? criticalEDPs : 'todos los'} EDPs críticos con más de 90 días</div>
                    </div>
                    <div class="suggestion-item priority-medium">
                        <div class="suggestion-priority">MEDIA</div>
                        <div class="suggestion-text">Implementar seguimiento semanal con clientes principales</div>
                    </div>
                    <div class="suggestion-item priority-low">
                        <div class="suggestion-priority">BAJA</div>
                        <div class="suggestion-text">Optimizar proceso de facturación para reducir tiempo de cobro</div>
                    </div>
                </div>
            </div>

            <div class="kpi-actions-section">
                <div class="kpi-actions-grid">
                    <button class="kpi-action-btn info" onclick="contactManagerAdvanced('${nombre}', 'call')">
                        Llamar
                    </button>
                    <button class="kpi-action-btn warning" onclick="contactManagerAdvanced('${nombre}', 'email')">
                        Email
                    </button>
                    <button class="kpi-action-btn positive" onclick="scheduleManagerMeeting('${nombre}')">
                        Programar Reunión
                    </button>
                    <button class="kpi-action-btn neutral" onclick="assignManagerSupport('${nombre}')">
                        Asignar Apoyo
                    </button>
                </div>
            </div>
        </div>
    `;

    showModal(`Detalle Jefe de Proyecto - ${nombre}`, modalContent, 'large');
}

/**
 * Muestra detalles del forecast de un día específico
 */
function showForecastDetail(day, amount, probability) {
    // Parse values
    const amountValue = parseFloat(amount.replace('M', ''));
    const probValue = parseInt(probability.replace('% prob', ''));
    
    // Generate EDPs for this day
    const edpsForDay = generateForecastEDPs(day, amountValue, probValue);
    
    const modalContent = `
        <div class="forecast-detail-modal">
            <div class="forecast-day-header">
                <div class="day-info">
                    <div class="day-title">${day}</div>
                    <div class="day-date">${getForecastDate(day)}</div>
                </div>
                <div class="day-metrics">
                    <div class="day-metric">
                        <div class="metric-value positive">${amount}</div>
                        <div class="metric-label">Monto Proyectado</div>
                    </div>
                    <div class="day-metric">
                        <div class="metric-value ${probValue > 70 ? 'positive' : probValue > 50 ? 'warning' : 'critical'}">${probValue}%</div>
                        <div class="metric-label">Confianza Promedio</div>
                    </div>
                </div>
            </div>

            <div class="forecast-summary">
                <div class="summary-stats">
                    <div class="stat-item info">
                        <div class="stat-value">${edpsForDay.length}</div>
                        <div class="stat-label">EDPs Programados</div>
                    </div>
                    <div class="stat-item ${edpsForDay.filter(e => e.risk === 'Alto').length > 0 ? 'warning' : 'positive'}">
                        <div class="stat-value">${edpsForDay.filter(e => e.risk === 'Alto').length}</div>
                        <div class="stat-label">EDPs en Riesgo</div>
                    </div>
                    <div class="stat-item positive">
                        <div class="stat-value">${edpsForDay.filter(e => e.confidence > 80).length}</div>
                        <div class="stat-label">Alta Confianza</div>
                    </div>
                </div>
            </div>

            <div class="forecast-edps-section">
                <div class="kpi-section-title">EDPs Programados para ${day}</div>
                <div class="kpi-table-container">
                    <table class="kpi-detail-table">
                        <thead>
                            <tr>
                                <th>Cliente</th>
                                <th>Proyecto</th>
                                <th>Monto</th>
                                <th>Confianza</th>
                                <th>Riesgo</th>
                                <th>Responsable</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${edpsForDay.map(edp => `
                                <tr class="${edp.risk === 'Alto' ? 'warning-row' : edp.confidence > 80 ? 'positive-row' : ''}" onclick="showEDPDetail('${edp.proyecto}')">
                                    <td>${edp.cliente}</td>
                                    <td class="project-id">${edp.proyecto}</td>
                                    <td class="amount">${edp.monto}M CLP</td>
                                    <td><span class="probability ${edp.confidence > 80 ? 'positive' : edp.confidence > 60 ? 'warning' : 'critical'}">${edp.confidence}%</span></td>
                                    <td><span class="status-badge ${edp.risk === 'Alto' ? 'warning' : edp.risk === 'Medio' ? 'info' : 'positive'}">${edp.risk}</span></td>
                                    <td class="contact">${edp.responsable}</td>
                                    <td><button class="action-btn ${edp.risk === 'Alto' ? 'warning' : 'info'}" onclick="executeForecastAction('${edp.accion}', '${edp.proyecto}')">${edp.accion}</button></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="forecast-actions-section">
                <div class="kpi-section-title">Acciones para Asegurar Cobro</div>
                <div class="action-suggestions">
                    <div class="suggestion-item priority-high">
                        <div class="suggestion-priority">URGENTE</div>
                        <div class="suggestion-text">Confirmar fechas de pago con ${edpsForDay.filter(e => e.risk === 'Alto').length} EDPs en riesgo</div>
                    </div>
                    <div class="suggestion-item priority-medium">
                        <div class="suggestion-priority">MEDIA</div>
                        <div class="suggestion-text">Validar documentación pendiente para acelerar procesos</div>
                    </div>
                    <div class="suggestion-item priority-low">
                        <div class="suggestion-priority">BAJA</div>
                        <div class="suggestion-text">Enviar recordatorios preventivos a clientes programados</div>
                    </div>
                </div>
            </div>

            <div class="kpi-actions-section">
                <div class="kpi-actions-grid">
                    <button class="kpi-action-btn warning" onclick="confirmAllPayments('${day}')">
                        Confirmar Pagos
                    </button>
                    <button class="kpi-action-btn info" onclick="sendDayReminders('${day}')">
                        Enviar Recordatorios
                    </button>
                    <button class="kpi-action-btn positive" onclick="accelerateDayCollection('${day}')">
                        Acelerar Cobros
                    </button>
                    <button class="kpi-action-btn neutral" onclick="exportDayForecast('${day}')">
                        Exportar Detalle
                    </button>
                </div>
            </div>
        </div>
    `;

    showModal(`Forecast ${day} - ${getForecastDate(day)}`, modalContent, 'large');
}

/**
 * Ejecuta una alerta específica
 */
function executeAlert(title, impact, description) {
    createModal({
        title: `Ejecutar Alerta: ${title}`,
        content: `
            <div class="alert-execution">
                <div class="alert-info">
                    <div class="detail-row">
                        <span class="detail-label">Impacto:</span>
                        <span class="detail-value">${impact}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Descripción:</span>
                        <span class="detail-value">${description}</span>
                    </div>
                </div>
                <div class="action-options">
                    <h4>Acciones Disponibles:</h4>
                    <div class="action-grid">
                        <button onclick="escalateAlert('${title}')" class="action-btn warning">Escalar</button>
                        <button onclick="assignAlert('${title}')" class="action-btn primary">Asignar</button>
                        <button onclick="snoozeAlert('${title}')" class="action-btn secondary">Posponer</button>
                        <button onclick="resolveAlert('${title}')" class="action-btn success">Resolver</button>
                    </div>
                </div>
            </div>
        `,
        actions: [
            { text: 'Cerrar', action: 'close', class: 'secondary' }
        ]
    });
}

/**
 * Función genérica para crear modales
 */
function createModal({ title, content, actions = [], size = 'medium' }) {
    // Remover modal existente si existe
    const existingModal = document.getElementById('dynamicModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Crear estructura del modal
    const modal = document.createElement('div');
    modal.id = 'dynamicModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content ${size}">
            <div class="modal-header">
                <h3 class="modal-title">${title}</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
            <div class="modal-footer">
                ${actions.map(action => `
                    <button class="modal-btn ${action.class || 'primary'}" 
                            onclick="${action.action === 'close' ? 'closeModal()' : action.action}">
                        ${action.text}
                    </button>
                `).join('')}
            </div>
        </div>
    `;

    // Agregar estilos CSS inline para el modal
    const modalStyles = document.createElement('style');
    modalStyles.textContent = `
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            backdrop-filter: blur(4px);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .modal-content {
            background: var(--bg-primary);
            border: 1px solid var(--border-primary);
            border-radius: 8px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            color: var(--text-primary);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            transform: translateY(-20px);
            transition: transform 0.3s ease;
        }
        .modal-content.large {
            max-width: 600px;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-primary);
        }
        .modal-title {
            margin: 0;
            color: var(--text-primary);
            font-size: 18px;
            font-weight: 600;
        }
        .modal-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
            transition: all 0.2s ease;
        }
        .modal-close:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }
        .modal-body {
            margin-bottom: 20px;
        }
        .modal-footer {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }
        .modal-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .modal-btn.primary {
            background: var(--accent-blue);
            color: white;
        }
        .modal-btn.primary:hover {
            background: var(--accent-blue-dark);
        }
        .modal-btn.secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-primary);
        }
        .modal-btn.secondary:hover {
            background: var(--bg-tertiary);
        }
        .modal-btn.success {
            background: var(--accent-green);
            color: white;
        }
        .modal-btn.warning {
            background: var(--accent-orange);
            color: white;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding: 4px 0;
        }
        .detail-label {
            color: var(--text-secondary);
            font-weight: 500;
        }
        .detail-value {
            color: var(--text-primary);
            font-weight: 600;
        }
        .detail-actions, .action-options {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid var(--border-primary);
        }
        .action-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 12px;
        }
        .action-btn {
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .action-btn.primary {
            background: var(--accent-blue);
            color: white;
        }
        .action-btn.secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-primary);
        }
        .action-btn.success {
            background: var(--accent-green);
            color: white;
        }
        .action-btn.warning {
            background: var(--accent-orange);
            color: white;
        }
        .forecast-breakdown ul {
            margin: 8px 0;
            padding-left: 20px;
        }
        .forecast-breakdown li {
            margin-bottom: 4px;
            color: var(--text-secondary);
        }
    `;

    // Agregar modal y estilos al DOM
    if (!document.getElementById('modalStyles')) {
        modalStyles.id = 'modalStyles';
        document.head.appendChild(modalStyles);
    }

    document.body.appendChild(modal);

    // Show with animation
    requestAnimationFrame(() => {
        modal.style.opacity = '1';
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.transform = 'translateY(0)';
        }
    });

    // Cerrar modal al hacer clic en el overlay
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Cerrar modal con Escape
    document.addEventListener('keydown', handleEscapeKey);
}

/**
 * Maneja la tecla Escape para cerrar modales
 */
function handleEscapeKey(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
}

// Funciones de acciones específicas para modales

function contactManager(manager) {
    console.log(`📞 Contactando a ${manager}`);
    closeModal();
    // Aquí iría la lógica para contactar al manager
}

function viewManagerProjects(manager) {
    console.log(`📋 Viendo proyectos de ${manager}`);
    closeModal();
    // Aquí iría la lógica para mostrar proyectos del manager
}

function viewForecastBreakdown(day) {
    console.log(`📊 Viendo desglose de forecast para ${day}`);
    closeModal();
    // Aquí iría la lógica para mostrar desglose detallado
}

function escalateAlert(title) {
    console.log(`🚨 Escalando alerta: ${title}`);
    closeModal();
    // Aquí iría la lógica para escalar la alerta
}

function assignAlert(title) {
    console.log(`👤 Asignando alerta: ${title}`);
    closeModal();
    // Aquí iría la lógica para asignar la alerta
}

function snoozeAlert(title) {
    console.log(`⏰ Posponiendo alerta: ${title}`);
    closeModal();
    // Aquí iría la lógica para posponer la alerta
}

function resolveAlert(title) {
    console.log(`✅ Resolviendo alerta: ${title}`);
    closeModal();
    // Aquí iría la lógica para resolver la alerta
}

// Funciones adicionales del dashboard

function coordinateManagers() {
    const modalContent = `
        <div class="coordination-modal">
            <div class="coordination-summary">
                <div class="summary-stats">
                    <div class="stat-item critical">
                        <div class="stat-value">4</div>
                        <div class="stat-label">Jefes con DSO >150d</div>
                    </div>
                    <div class="stat-item warning">
                        <div class="stat-value">2</div>
                        <div class="stat-label">Requieren apoyo inmediato</div>
                    </div>
                    <div class="stat-item info">
                        <div class="stat-value">148d</div>
                        <div class="stat-label">DSO promedio equipo</div>
                    </div>
                </div>
            </div>

            <div class="coordination-priorities">
                <div class="kpi-section-title">Prioridades de Coordinación</div>
                <div class="priority-list">
                    <div class="priority-item urgent">
                        <div class="priority-badge urgent">URGENTE</div>
                        <div class="priority-content">
                            <div class="priority-title">Pedro Rojas - 154d DSO</div>
                            <div class="priority-description">8 EDPs críticos • 804M CLP en riesgo • Requiere intervención inmediata</div>
                            <div class="priority-actions">
                                <button class="priority-btn critical" onclick="contactManagerAdvanced('Pedro Rojas', 'emergency')">Contactar Ahora</button>
                                <button class="priority-btn warning" onclick="escalateManager('Pedro Rojas')">Escalar</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="priority-item high">
                        <div class="priority-badge high">ALTA</div>
                        <div class="priority-content">
                            <div class="priority-title">Carolina López - 147d DSO</div>
                            <div class="priority-description">12 EDPs críticos • 1870M CLP gestionado • Necesita apoyo</div>
                            <div class="priority-actions">
                                <button class="priority-btn warning" onclick="assignManagerSupport('Carolina López')">Asignar Apoyo</button>
                                <button class="priority-btn info" onclick="scheduleManagerMeeting('Carolina López')">Reunión</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="priority-item medium">
                        <div class="priority-badge medium">MEDIA</div>
                        <div class="priority-content">
                            <div class="priority-title">Ana Pérez - 144d DSO</div>
                            <div class="priority-description">5 EDPs críticos • 1089M CLP • Seguimiento preventivo</div>
                            <div class="priority-actions">
                                <button class="priority-btn info" onclick="scheduleManagerMeeting('Ana Pérez')">Programar Seguimiento</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="coordination-actions">
                <div class="kpi-section-title">Acciones de Coordinación</div>
                <div class="coordination-options">
                    <div class="coordination-option">
                        <div class="option-title">Reunión Semanal de Equipo</div>
                        <div class="option-description">Revisar estado de todos los jefes de proyecto</div>
                        <button class="kpi-action-btn info" onclick="scheduleTeamMeeting()">Programar</button>
                    </div>
                    
                    <div class="coordination-option">
                        <div class="option-title">Redistribución de Carga</div>
                        <div class="option-description">Reasignar proyectos críticos a jefes con mejor DSO</div>
                        <button class="kpi-action-btn warning" onclick="redistributeProjects()">Analizar</button>
                    </div>
                    
                    <div class="coordination-option">
                        <div class="option-title">Capacitación en Cobranza</div>
                        <div class="option-description">Programa de mejora para jefes con DSO elevado</div>
                        <button class="kpi-action-btn positive" onclick="scheduleTraining()">Organizar</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    showModal('Coordinación de Equipo Operacional', modalContent, 'large');
}

function exportForecast() {
    console.log('📤 Exportando forecast...');
    // Aquí iría la lógica para exportar el forecast
}

function analyzeDSOTrend() {
    createModal({
        title: 'Análisis de Tendencia DSO',
        content: `
            <div class="dso-analysis">
                <p>Análisis de tendencia DSO disponible:</p>
                <div class="analysis-options">
                    <button onclick="generateDSOReport()" class="action-btn primary">Generar Reporte</button>
                    <button onclick="comparePeriods()" class="action-btn secondary">Comparar Períodos</button>
                    <button onclick="identifyBottlenecks()" class="action-btn warning">Identificar Cuellos de Botella</button>
                </div>
            </div>
        `,
        actions: [
            { text: 'Cerrar', action: 'close', class: 'secondary' }
        ]
    });
}

function executeAllAlerts() {
    createModal({
        title: 'Ejecutar Todas las Alertas',
        content: `
            <div class="bulk-actions">
                <p>¿Estás seguro de que quieres ejecutar acciones en todas las alertas activas?</p>
                <div class="warning-message">
                    <strong>Advertencia:</strong> Esta acción procesará todas las alertas críticas y de alto impacto.
                </div>
            </div>
        `,
        actions: [
            { text: 'Confirmar', action: () => processBulkAlerts(), class: 'warning' },
            { text: 'Cancelar', action: 'close', class: 'secondary' }
        ]
    });
}

// Funciones auxiliares para las acciones

function scheduleTeamMeeting() {
    console.log('📅 Agendando reunión de equipo');
    closeModal();
}

function sendDSOReport() {
    console.log('📧 Enviando reporte DSO');
    closeModal();
}

function redistributeWorkload() {
    console.log('⚖️ Redistribuyendo carga de trabajo');
    closeModal();
}

function escalateIssues() {
    console.log('🚨 Escalando problemas');
    closeModal();
}

function generateDSOReport() {
    console.log('📊 Generando reporte DSO');
    closeModal();
}

function comparePeriods() {
    console.log('📈 Comparando períodos');
    closeModal();
}

function identifyBottlenecks() {
    console.log('🔍 Identificando cuellos de botella');
    closeModal();
}

function processBulkAlerts() {
    console.log('⚡ Procesando todas las alertas');
    closeModal();
}

/**
 * Muestra modal de EDPs críticos
 */
function showCriticalEDPsModal() {
    const criticalCount = window.kpisData?.critical_projects_count || 0;
    const criticalAmount = window.kpisData?.critical_amount || 0;
    
    createModal({
        title: `EDPs Críticos (${criticalCount})`,
        content: `
            <div class="critical-edps-detail">
                <div class="alert-summary">
                    <div class="summary-metric">
                        <span class="metric-label">EDPs Vencidos:</span>
                        <span class="metric-value critical">${criticalCount}</span>
                    </div>
                    <div class="summary-metric">
                        <span class="metric-label">Monto en Riesgo:</span>
                        <span class="metric-value critical">$${(criticalAmount).toFixed(0)}M CLP</span>
                    </div>
                    <div class="summary-metric">
                        <span class="metric-label">Días Promedio:</span>
                        <span class="metric-value critical">>90 días</span>
                    </div>
                </div>
                <div class="action-plan">
                    <h4>Plan de Acción Inmediata:</h4>
                    <ul class="action-list">
                        <li>Contactar clientes con mayor monto pendiente</li>
                        <li>Revisar estado de documentación</li>
                        <li>Coordinar con jefes de proyecto responsables</li>
                        <li>Evaluar opciones de cobranza</li>
                    </ul>
                </div>
                <div class="next-steps">
                    <h4>Próximos Pasos:</h4>
                    <div class="step-grid">
                        <button onclick="contactCriticalClients()" class="step-btn critical">Contactar Clientes</button>
                        <button onclick="reviewDocumentation()" class="step-btn warning">Revisar Docs</button>
                        <button onclick="coordinateManagers()" class="step-btn primary">Coordinar Jefes</button>
                        <button onclick="generateCriticalReport()" class="step-btn secondary">Generar Reporte</button>
                    </div>
                </div>
            </div>
        `,
        actions: [
            { text: 'Ver Lista Completa', action: () => viewCriticalEDPsList(), class: 'primary' },
            { text: 'Cerrar', action: 'close', class: 'secondary' }
        ],
        size: 'large'
    });
}

/**
 * Muestra modal de alerta DSO elevado
 */
function showDSOAlertModal() {
    const dsoActual = window.kpisData?.dso_actual || 0;
    const dsoTarget = 60;
    const diferencia = dsoActual - dsoTarget;
    
    createModal({
        title: `Alerta DSO Elevado`,
        content: `
            <div class="dso-alert-detail">
                <div class="dso-metrics">
                    <div class="metric-card critical">
                        <div class="metric-title">DSO Actual</div>
                        <div class="metric-value">${Math.round(dsoActual)} días</div>
                    </div>
                    <div class="metric-card neutral">
                        <div class="metric-title">Target</div>
                        <div class="metric-value">${dsoTarget} días</div>
                    </div>
                    <div class="metric-card warning">
                        <div class="metric-title">Diferencia</div>
                        <div class="metric-value">+${Math.round(diferencia)} días</div>
                    </div>
                </div>
                <div class="dso-impact">
                    <h4>Impacto en Flujo de Caja:</h4>
                    <div class="impact-calculation">
                        <div class="impact-row">
                            <span>Pérdida diaria estimada:</span>
                            <span class="impact-amount">$${(diferencia * 35000).toFixed(0)} CLP</span>
                        </div>
                        <div class="impact-row">
                            <span>Pérdida mensual proyectada:</span>
                            <span class="impact-amount critical">$${(diferencia * 35000 * 30).toFixed(0)} CLP</span>
                        </div>
                    </div>
                </div>
                <div class="dso-actions">
                    <h4>Acciones Recomendadas:</h4>
                    <div class="action-grid">
                        <button onclick="analyzeDSOTrend()" class="action-btn primary">Analizar Tendencia</button>
                        <button onclick="identifyBottlenecks()" class="action-btn warning">Identificar Cuellos de Botella</button>
                        <button onclick="coordinateManagers()" class="action-btn secondary">Coordinar Equipo</button>
                        <button onclick="generateDSOReport()" class="action-btn info">Generar Reporte</button>
                    </div>
                </div>
            </div>
        `,
        actions: [
            { text: 'Plan de Mejora', action: () => createDSOImprovementPlan(), class: 'primary' },
            { text: 'Cerrar', action: 'close', class: 'secondary' }
        ],
        size: 'large'
    });
}

/**
 * Muestra modal de flujo de caja bajo
 */
function showLowCashflowModal() {
    const forecast7d = window.kpisData?.forecast_7_dias || 0;
    const forecast30d = window.kpisData?.forecast_30_dias || 0;
    
    createModal({
        title: `Alerta: Flujo Proyectado Bajo`,
        content: `
            <div class="cashflow-alert-detail">
                <div class="forecast-metrics">
                    <div class="metric-card warning">
                        <div class="metric-title">Próximos 7 días</div>
                        <div class="metric-value">${forecast7d.toFixed(1)}M CLP</div>
                    </div>
                    <div class="metric-card info">
                        <div class="metric-title">Próximos 30 días</div>
                        <div class="metric-value">${forecast30d.toFixed(1)}% del backlog</div>
                    </div>
                </div>
                <div class="cashflow-analysis">
                    <h4>Análisis de Situación:</h4>
                    <div class="analysis-points">
                        <div class="analysis-point ${forecast7d < 0.5 ? 'critical' : 'warning'}">
                            <span class="point-indicator"></span>
                            <span>Flujo 7 días: ${forecast7d < 0.5 ? 'Crítico' : 'Bajo'}</span>
                        </div>
                        <div class="analysis-point ${forecast30d < 10 ? 'critical' : 'warning'}">
                            <span class="point-indicator"></span>
                            <span>Pipeline 30 días: ${forecast30d < 10 ? 'Insuficiente' : 'Limitado'}</span>
                        </div>
                    </div>
                </div>
                <div class="cashflow-recommendations">
                    <h4>Recomendaciones:</h4>
                    <ul class="recommendation-list">
                        <li>Acelerar procesos de cobranza en curso</li>
                        <li>Revisar EDPs próximos a vencer</li>
                        <li>Contactar clientes con pagos programados</li>
                        <li>Evaluar opciones de financiamiento puente</li>
                    </ul>
                </div>
                <div class="cashflow-actions">
                    <div class="action-grid">
                        <button onclick="accelerateCollection()" class="action-btn critical">Acelerar Cobranza</button>
                        <button onclick="reviewUpcomingEDPs()" class="action-btn warning">Revisar EDPs</button>
                        <button onclick="contactScheduledClients()" class="action-btn primary">Contactar Clientes</button>
                        <button onclick="generateCashflowReport()" class="action-btn secondary">Generar Reporte</button>
                    </div>
                </div>
            </div>
        `,
        actions: [
            { text: 'Plan de Acción', action: () => createCashflowPlan(), class: 'primary' },
            { text: 'Cerrar', action: 'close', class: 'secondary' }
        ],
        size: 'large'
    });
}

// Funciones de soporte para las acciones de los modales
function contactCriticalClients() {
    alert('Funcionalidad: Contactar clientes críticos - En desarrollo');
    closeModal();
}

function reviewDocumentation() {
    alert('Funcionalidad: Revisar documentación - En desarrollo');
    closeModal();
}

function generateCriticalReport() {
    alert('Funcionalidad: Generar reporte de EDPs críticos - En desarrollo');
    closeModal();
}

function viewCriticalEDPsList() {
    alert('Funcionalidad: Ver lista completa de EDPs críticos - En desarrollo');
    closeModal();
}

function createDSOImprovementPlan() {
    alert('Funcionalidad: Crear plan de mejora DSO - En desarrollo');
    closeModal();
}

function accelerateCollection() {
    alert('Funcionalidad: Acelerar cobranza - En desarrollo');
    closeModal();
}

function reviewUpcomingEDPs() {
    alert('Funcionalidad: Revisar EDPs próximos - En desarrollo');
    closeModal();
}

function contactScheduledClients() {
    alert('Funcionalidad: Contactar clientes programados - En desarrollo');
    closeModal();
}

function generateCashflowReport() {
    alert('Funcionalidad: Generar reporte de flujo de caja - En desarrollo');
    closeModal();
}

function createCashflowPlan() {
    alert('Funcionalidad: Crear plan de flujo de caja - En desarrollo');
    closeModal();
}

// ===== MODAL BASE FUNCTIONS =====

function showModal(title, content, size = 'medium') {
    // Remove existing modal if any
    const existingModal = document.getElementById('dynamicModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal HTML
    const modalHTML = `
        <div id="dynamicModal" class="modal-overlay" onclick="closeModal(event)">
            <div class="modal-container ${size}" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2 class="modal-title">${title}</h2>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
            </div>
        </div>
    `;
    
    // Add to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show with animation
    const modal = document.getElementById('dynamicModal');
    requestAnimationFrame(() => {
        modal.style.opacity = '1';
        const modalContainer = modal.querySelector('.modal-container');
        if (modalContainer) {
            modalContainer.style.transform = 'translateY(0)';
        }
    });
    
    // Add escape key listener
    document.addEventListener('keydown', handleModalEscape);
}

function closeModal(event) {
    if (event && event.target !== event.currentTarget && !event.target.classList.contains('modal-close')) {
        return;
    }
    
    const modal = document.getElementById('dynamicModal');
    if (modal) {
        modal.style.opacity = '0';
        
        // Handle both modal types: .modal-container and .modal-content
        const modalContainer = modal.querySelector('.modal-container');
        const modalContent = modal.querySelector('.modal-content');
        
        if (modalContainer) {
            modalContainer.style.transform = 'translateY(-20px)';
        } else if (modalContent) {
            modalContent.style.transform = 'translateY(-20px)';
        }
        
        setTimeout(() => {
            modal.remove();
            document.removeEventListener('keydown', handleModalEscape);
        }, 300);
    }
}

function handleModalEscape(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
}

function showNotification(message, type = 'info') {
    // Remove existing notification
    const existingNotification = document.getElementById('notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    const notificationHTML = `
        <div id="notification" class="notification ${type}">
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="closeNotification()">&times;</button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', notificationHTML);
    
    const notification = document.getElementById('notification');
    requestAnimationFrame(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    });
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        closeNotification();
    }, 5000);
}

function closeNotification() {
    const notification = document.getElementById('notification');
    if (notification) {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
}

// ===== KPI CARDS MODALS =====

// Modal para EDPs Críticos
function showCriticalKPIModal() {
    const kpis = window.kpisData || {};
    
    const modalContent = `
        <div class="modal-header-kpi">
            <div class="modal-title-kpi">EDPs Críticos - Análisis Detallado</div>
            <div class="modal-subtitle-kpi">Proyectos con más de 60 días pendientes</div>
        </div>
        
        <div class="modal-content-kpi">
            <div class="kpi-summary-grid">
                <div class="kpi-summary-item critical">
                    <div class="kpi-summary-label">Total EDPs</div>
                    <div class="kpi-summary-value">${kpis.critical_projects_count || 0}</div>
                </div>
                <div class="kpi-summary-item critical">
                    <div class="kpi-summary-label">Monto en Riesgo</div>
                    <div class="kpi-summary-value">${kpis.critical_amount ? `${kpis.critical_amount.toFixed(1)}M CLP` : 'Sin datos'}</div>
                </div>
                <div class="kpi-summary-item critical">
                    <div class="kpi-summary-label">Promedio Días</div>
                    <div class="kpi-summary-value" id="critical-avg-days">--</div>
                </div>
                <div class="kpi-summary-item critical">
                    <div class="kpi-summary-label">Tendencia</div>
                    <div class="kpi-summary-value" id="critical-trend">--</div>
                </div>
            </div>
            
            <div class="kpi-detail-section">
                <div class="kpi-section-title">Distribución por Jefe de Proyecto</div>
                <div class="kpi-managers-preview">
                    ${generateManagersPreview('critical')}
                </div>
            </div>
            
            <div class="kpi-detail-section">
                <div class="kpi-section-title">Top 5 EDPs Críticos</div>
                <div class="kpi-table-container">
                    <table class="kpi-detail-table">
                        <thead>
                            <tr>
                                <th>Cliente</th>
                                <th>Proyecto</th>
                                <th>Monto</th>
                                <th>Días</th>
                                <th>Jefe</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${generateCriticalEDPsTable()}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="kpi-actions-section">
                <div class="kpi-section-title">Acciones Recomendadas</div>
                <div class="kpi-actions-grid">
                    <button class="kpi-action-btn critical" onclick="contactAllCriticalClients()">
                        Contactar Todos los Clientes
                    </button>
                    <button class="kpi-action-btn warning" onclick="generateCriticalReport()">
                        Generar Reporte Detallado
                    </button>
                    <button class="kpi-action-btn info" onclick="scheduleCriticalFollowup()">
                        Programar Seguimiento
                    </button>
                </div>
            </div>
        </div>
    `;
    
    showModal('EDPs Críticos', modalContent, 'large');
}

// Modal para Aging 31-60
function showAgingKPIModal() {
    const kpis = window.kpisData || {};
    
    const modalContent = `
        <div class="modal-header-kpi">
            <div class="modal-title-kpi">EDPs Aging 31-60 Días</div>
            <div class="modal-subtitle-kpi">Zona de advertencia - Prevención crítica</div>
        </div>
        
        <div class="modal-content-kpi">
            <div class="kpi-summary-grid">
                <div class="kpi-summary-item warning">
                    <div class="kpi-summary-label">Total EDPs</div>
                    <div class="kpi-summary-value">${kpis.aging_31_60_count || 0}</div>
                </div>
                <div class="kpi-summary-item warning">
                    <div class="kpi-summary-label">Monto Total</div>
                    <div class="kpi-summary-value">${kpis.aging_31_60_amount ? `${kpis.aging_31_60_amount.toFixed(1)}M CLP` : 'Sin datos'}</div>
                </div>
                <div class="kpi-summary-item warning">
                    <div class="kpi-summary-label">Días Promedio</div>
                    <div class="kpi-summary-value" id="aging-avg-days">--</div>
                </div>
                <div class="kpi-summary-item warning">
                    <div class="kpi-summary-label">Tendencia</div>
                    <div class="kpi-summary-value" id="aging-trend">--</div>
                </div>
            </div>
            
            <div class="kpi-detail-section">
                <div class="kpi-section-title">EDPs en Zona Warning</div>
                <div class="kpi-table-container">
                    <table class="kpi-detail-table">
                        <thead>
                            <tr>
                                <th>Cliente</th>
                                <th>Proyecto</th>
                                <th>Monto</th>
                                <th>Días</th>
                                <th>Contacto</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${generateAgingEDPsTable()}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="kpi-detail-section">
                <div class="kpi-section-title">Plan Preventivo</div>
                <div class="prevention-timeline">
                    <div class="prevention-step">
                        <div class="prevention-day">Hoy</div>
                        <div class="prevention-action">Contacto inicial por email</div>
                    </div>
                    <div class="prevention-step">
                        <div class="prevention-day">+3 días</div>
                        <div class="prevention-action">Llamada de seguimiento</div>
                    </div>
                    <div class="prevention-step">
                        <div class="prevention-day">+7 días</div>
                        <div class="prevention-action">Reunión presencial/virtual</div>
                    </div>
                </div>
            </div>
            
            <div class="kpi-actions-section">
                <div class="kpi-actions-grid">
                    <button class="kpi-action-btn warning" onclick="sendAgingEmails()">
                        Enviar Emails Preventivos
                    </button>
                    <button class="kpi-action-btn info" onclick="scheduleAgingCalls()">
                        Programar Llamadas
                    </button>
                    <button class="kpi-action-btn neutral" onclick="exportAgingData()">
                        Exportar Lista
                    </button>
                </div>
            </div>
        </div>
    `;
    
    showModal('Aging 31-60 Días', modalContent, 'large');
}

// Modal para Cobro Rápido
function showFastCollectionModal() {
    const kpis = window.kpisData || {};
    
    const modalContent = `
        <div class="modal-header-kpi">
            <div class="modal-title-kpi">Cobro Rápido - EDPs <30 Días</div>
            <div class="modal-subtitle-kpi">Proyectos con flujo saludable</div>
        </div>
        
        <div class="modal-content-kpi">
            <div class="kpi-summary-grid">
                <div class="kpi-summary-item positive">
                    <div class="kpi-summary-label">Total EDPs</div>
                    <div class="kpi-summary-value">${kpis.fast_collection_count || 0}</div>
                </div>
                <div class="kpi-summary-item positive">
                    <div class="kpi-summary-label">Monto Saludable</div>
                    <div class="kpi-summary-value">${kpis.fast_collection_amount ? `${kpis.fast_collection_amount.toFixed(1)}M CLP` : 'Sin datos'}</div>
                </div>
                <div class="kpi-summary-item positive">
                    <div class="kpi-summary-label">Velocidad Promedio</div>
                    <div class="kpi-summary-value" id="fast-avg-days">--</div>
                </div>
                <div class="kpi-summary-item positive">
                    <div class="kpi-summary-label">Tendencia</div>
                    <div class="kpi-summary-value" id="fast-trend">--</div>
                </div>
            </div>
            
            <div class="kpi-detail-section">
                <div class="kpi-section-title">EDPs Próximos a Cobrar</div>
                <div class="kpi-table-container">
                    <table class="kpi-detail-table">
                        <thead>
                            <tr>
                                <th>Cliente</th>
                                <th>Proyecto</th>
                                <th>Monto</th>
                                <th>Días</th>
                                <th>Fecha Est. Cobro</th>
                                <th>Probabilidad</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${generateFastCollectionTable()}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="kpi-detail-section">
                <div class="kpi-section-title">Proyección Flujo de Caja</div>
                <div class="cashflow-projection">
                    <div class="projection-item">
                        <div class="projection-period">Próximos 7 días</div>
                        <div class="projection-amount positive">${kpis.fast_projection_7d || '--'} CLP</div>
                    </div>
                    <div class="projection-item">
                        <div class="projection-period">Próximos 15 días</div>
                        <div class="projection-amount positive">${kpis.fast_projection_15d || '--'} CLP</div>
                    </div>
                    <div class="projection-item">
                        <div class="projection-period">Próximos 30 días</div>
                        <div class="projection-amount positive">${kpis.fast_projection_30d || '--'} CLP</div>
                    </div>
                </div>
            </div>
            
            <div class="kpi-actions-section">
                <div class="kpi-actions-grid">
                    <button class="kpi-action-btn positive" onclick="accelerateCollection()">
                        Acelerar Cobros
                    </button>
                    <button class="kpi-action-btn info" onclick="confirmCollectionDates()">
                        Confirmar Fechas
                    </button>
                    <button class="kpi-action-btn neutral" onclick="exportFastCollection()">
                        Exportar Proyección
                    </button>
                </div>
            </div>
        </div>
    `;
    
    showModal('Cobro Rápido', modalContent, 'large');
}

// Modal para Meta Gap
function showMetaGapModal() {
    const kpis = window.kpisData || {};
    
    const modalContent = `
        <div class="modal-header-kpi">
            <div class="modal-title-kpi">Meta Gap - Análisis de Brecha</div>
            <div class="modal-subtitle-kpi">Diferencia entre meta y realidad</div>
        </div>
        
        <div class="modal-content-kpi">
            <div class="kpi-summary-grid">
                <div class="kpi-summary-item ${kpis.meta_gap && kpis.meta_gap > 3 ? 'warning' : 'positive'}">
                    <div class="kpi-summary-label">Brecha Actual</div>
                    <div class="kpi-summary-value">${kpis.meta_gap ? `${kpis.meta_gap.toFixed(1)}M CLP` : '--'}</div>
                </div>
                <div class="kpi-summary-item info">
                    <div class="kpi-summary-label">% Cumplimiento</div>
                    <div class="kpi-summary-value">${kpis.progreso_objetivo ? `${kpis.progreso_objetivo.toFixed(0)}%` : '--'}</div>
                </div>
                <div class="kpi-summary-item neutral">
                    <div class="kpi-summary-label">Días Restantes</div>
                    <div class="kpi-summary-value">${kpis.days_remaining || '--'} días</div>
                </div>
                <div class="kpi-summary-item critical">
                    <div class="kpi-summary-label">Requerido Diario</div>
                    <div class="kpi-summary-value">${kpis.meta_gap && kpis.days_remaining ? `${(kpis.meta_gap / kpis.days_remaining).toFixed(1)}M` : '--'}</div>
                </div>
            </div>
            
            <div class="kpi-detail-section">
                <div class="kpi-section-title">Progreso vs Meta</div>
                <div class="meta-progress-chart">
                    <div class="progress-bar-container">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${kpis.progreso_objetivo || 0}%"></div>
                        </div>
                        <div class="progress-labels">
                            <span class="progress-current">${kpis.progreso_objetivo ? `${kpis.progreso_objetivo.toFixed(0)}%` : '0%'}</span>
                            <span class="progress-target">100%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="kpi-detail-section">
                <div class="kpi-section-title">Plan de Acción para Cerrar Brecha</div>
                <div class="action-plan">
                    <div class="plan-step priority-high">
                        <div class="plan-icon">1</div>
                        <div class="plan-content">
                            <div class="plan-title">Acelerar EDPs Críticos</div>
                            <div class="plan-desc">Contactar inmediatamente los ${kpis.critical_projects_count || 0} EDPs críticos</div>
                        </div>
                    </div>
                    <div class="plan-step priority-medium">
                        <div class="plan-icon">2</div>
                        <div class="plan-content">
                            <div class="plan-title">Optimizar Pipeline</div>
                            <div class="plan-desc">Revisar EDPs en aging 31-60 días para prevenir escalamiento</div>
                        </div>
                    </div>
                    <div class="plan-step priority-low">
                        <div class="plan-icon">3</div>
                        <div class="plan-content">
                            <div class="plan-title">Confirmar Proyecciones</div>
                            <div class="plan-desc">Validar fechas de cobro de EDPs rápidos</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="kpi-actions-section">
                <div class="kpi-actions-grid">
                    <button class="kpi-action-btn critical" onclick="executeGapPlan()">
                        Ejecutar Plan Urgente
                    </button>
                    <button class="kpi-action-btn warning" onclick="reviewMetaStrategy()">
                        Revisar Estrategia
                    </button>
                    <button class="kpi-action-btn info" onclick="generateMetaReport()">
                        Generar Reporte
                    </button>
                </div>
            </div>
        </div>
    `;
    
    showModal('Meta Gap', modalContent, 'large');
}

// ===== HELPER FUNCTIONS =====

function generateManagersPreview(type) {
    const equipo = window.equipoData || [];
    if (equipo.length === 0) {
        return '<div class="no-managers-data">Sin datos de equipo disponibles</div>';
    }
    
    return equipo.slice(0, 4).map(jefe => `
        <div class="manager-preview-item">
            <div class="manager-name">${jefe.nombre}</div>
            <div class="manager-count">${jefe.proyectos_count || 0} EDPs</div>
            <div class="manager-amount">${jefe.monto_gestionado ? `${(jefe.monto_gestionado / 1000000).toFixed(1)}M` : '--'}</div>
        </div>
    `).join('');
}

function generateCriticalEDPsTable() {
    // Return a loading placeholder initially, then load real data
    const tableId = 'critical-edps-table-' + Date.now();
    
    // Start loading data immediately
    setTimeout(() => loadCriticalEDPsData(tableId), 100);
    
    return `
        <tr id="${tableId}">
            <td colspan="6" class="no-data-cell">
                <div class="loading-table">
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <div class="loading-text">Cargando EDPs críticos...</div>
                    </div>
                </div>
            </td>
        </tr>
    `;
}

function loadCriticalEDPsData(tableId) {
    fetch('/management/api/critical_edps')
        .then(response => response.json())
        .then(data => {
            const loadingRow = document.getElementById(tableId);
            if (!loadingRow) return;
            
            // Find the tbody parent to insert new rows
            const tbody = loadingRow.parentElement;
            if (!tbody) return;
            
            // Remove the loading row
            loadingRow.remove();
            
            if (!data.success || !data.critical_edps || data.critical_edps.length === 0) {
                const noDataRow = document.createElement('tr');
                noDataRow.innerHTML = `
                    <td colspan="6" class="no-data-cell">
                        <div class="no-data-message">
                            <div class="no-data-text">No hay EDPs críticos</div>
                            <div class="no-data-subtext">Todos los proyectos están dentro de plazos normales</div>
                        </div>
                    </td>
                `;
                tbody.appendChild(noDataRow);
                return;
            }
            
            // Generate real table rows and insert them
            data.critical_edps.forEach(edp => {
                const urgencyClass = edp.urgencia === 'critical' ? 'critical-row' : 'high-risk-row';
                const urgencyBadge = edp.urgencia === 'critical' ? 'CRÍTICO' : 'ALTO RIESGO';
                
                const row = document.createElement('tr');
                row.className = urgencyClass;
                row.style.cursor = 'pointer';
                row.onclick = () => showEDPDetailModal(edp.n_edp);
                
                row.innerHTML = `
                    <td class="cliente-cell" title="${edp.cliente}">${edp.cliente}</td>
                    <td class="proyecto-cell font-medium" title="${edp.proyecto}">${edp.proyecto}</td>
                    <td class="monto-cell text-right">${edp.monto_formatted}</td>
                    <td class="dias-cell text-center">
                        <span class="dias-badge ${edp.urgencia}">${edp.dias}d</span>
                    </td>
                    <td class="jefe-cell" title="${edp.jefe_proyecto}">${edp.jefe_proyecto}</td>
                    <td class="estado-cell text-center">
                        <span class="status-badge ${edp.urgencia}">${urgencyBadge}</span>
                    </td>
                `;
                
                tbody.appendChild(row);
            });
            
            // Add summary row at the end
            const summaryRow = document.createElement('tr');
            summaryRow.innerHTML = `
                <td colspan="6" class="summary-cell">
                    <div class="table-summary">
                        <div class="summary-stats">
                            <span class="stat-item">
                                <strong>${data.summary.total_count}</strong> EDPs críticos
                            </span>
                            <span class="stat-item">
                                <strong>${formatCurrency(data.summary.total_amount)}</strong> en riesgo
                            </span>
                            <span class="stat-item">
                                <strong>${data.summary.avg_days}</strong> días promedio
                            </span>
                        </div>
                    </div>
                </td>
            `;
            tbody.appendChild(summaryRow);
            
            // Update summary metrics with real data
            if (data.summary) {
                const avgDaysEl = document.getElementById('critical-avg-days');
                const trendEl = document.getElementById('critical-trend');
                
                if (avgDaysEl) {
                    avgDaysEl.textContent = `${data.summary.avg_days} días`;
                }
                
                if (trendEl) {
                    const trend = data.summary.trend_change || 0;
                    const trendSymbol = trend > 0 ? '+' : '';
                    const trendClass = trend > 0 ? 'critical' : trend < 0 ? 'positive' : 'neutral';
                    trendEl.innerHTML = `<span class="${trendClass}">${trendSymbol}${trend}%</span>`;
                }
            }
        })
        .catch(error => {
            const loadingRow = document.getElementById(tableId);
            if (loadingRow) {
                loadingRow.innerHTML = `
                    <td colspan="6" class="no-data-cell">
                        <div class="error-message">
                            <div class="error-text">Error cargando EDPs críticos</div>
                            <div class="error-subtext">${error.message}</div>
                        </div>
                    </td>
                `;
            }
        });
}

function generateAgingEDPsTable() {
    // Return a loading placeholder initially, then load real data
    const tableId = 'aging-edps-table-' + Date.now();
    
    // Start loading data immediately
    setTimeout(() => loadAgingEDPsData(tableId), 100);
    
    return `
        <tr id="${tableId}">
            <td colspan="6" class="no-data-cell">
                <div class="loading-table">
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <div class="loading-text">Cargando EDPs en aging...</div>
                    </div>
                </div>
            </td>
        </tr>
    `;
}

function loadAgingEDPsData(tableId) {
    fetch('/management/api/aging_edps')
        .then(response => response.json())
        .then(data => {
            const loadingRow = document.getElementById(tableId);
            if (!loadingRow) return;
            
            // Find the tbody parent to insert new rows
            const tbody = loadingRow.parentElement;
            if (!tbody) return;
            
            // Remove the loading row
            loadingRow.remove();
            
            if (!data.success || !data.aging_edps || data.aging_edps.length === 0) {
                const noDataRow = document.createElement('tr');
                noDataRow.innerHTML = `
                    <td colspan="6" class="no-data-cell">
                        <div class="no-data-message">
                            <div class="no-data-text">No hay EDPs en aging 31-60 días</div>
                            <div class="no-data-subtext">Excelente gestión preventiva de cobros</div>
                        </div>
                    </td>
                `;
                tbody.appendChild(noDataRow);
                return;
            }
            
            // Generate real table rows and insert them
            data.aging_edps.forEach(edp => {
                const row = document.createElement('tr');
                row.className = 'warning-row';
                row.style.cursor = 'pointer';
                row.onclick = () => showEDPDetailModal(edp.n_edp);
                
                row.innerHTML = `
                    <td class="cliente-cell" title="${edp.cliente}">${edp.cliente}</td>
                    <td class="proyecto-cell font-medium" title="${edp.proyecto}">${edp.proyecto}</td>
                    <td class="monto-cell text-right">${edp.monto_formatted}</td>
                    <td class="dias-cell text-center">
                        <span class="dias-badge warning">${edp.dias}d</span>
                    </td>
                    <td class="jefe-cell" title="${edp.jefe_proyecto}">${edp.jefe_proyecto}</td>
                    <td class="estado-cell text-center">
                        <span class="status-badge warning">AGING</span>
                    </td>
                `;
                
                tbody.appendChild(row);
            });
            
            // Add summary row
            const summaryRow = document.createElement('tr');
            summaryRow.innerHTML = `
                <td colspan="6" class="summary-cell">
                    <div class="table-summary">
                        <div class="summary-stats">
                            <span class="stat-item">
                                <strong>${data.summary.total_count}</strong> EDPs en aging
                            </span>
                            <span class="stat-item">
                                <strong>${formatCurrency(data.summary.total_amount)}</strong> en gestión
                            </span>
                            <span class="stat-item">
                                <strong>${data.summary.avg_days}</strong> días promedio
                            </span>
                        </div>
                    </div>
                </td>
            `;
            tbody.appendChild(summaryRow);
            
            // Update summary metrics with real data
            if (data.summary) {
                const avgDaysEl = document.getElementById('aging-avg-days');
                const trendEl = document.getElementById('aging-trend');
                
                if (avgDaysEl) {
                    avgDaysEl.textContent = `${data.summary.avg_days} días`;
                }
                
                if (trendEl) {
                    const trend = data.summary.trend_change || 0;
                    const trendSymbol = trend > 0 ? '+' : '';
                    const trendClass = trend > 0 ? 'warning' : trend < 0 ? 'positive' : 'neutral';
                    trendEl.innerHTML = `<span class="${trendClass}">${trendSymbol}${trend}%</span>`;
                }
            }
        })
        .catch(error => {
            const loadingRow = document.getElementById(tableId);
            if (loadingRow) {
                loadingRow.innerHTML = `
                    <td colspan="6" class="no-data-cell">
                        <div class="error-message">
                            <div class="error-text">Error cargando EDPs en aging</div>
                            <div class="error-subtext">${error.message}</div>
                        </div>
                    </td>
                `;
            }
        });
}

function generateFastCollectionTable() {
    // Return a loading placeholder initially, then load real data
    const tableId = 'fast-collection-table-' + Date.now();
    
    // Start loading data immediately
    setTimeout(() => loadFastCollectionData(tableId), 100);
    
    return `
        <tr id="${tableId}">
            <td colspan="6" class="no-data-cell">
                <div class="loading-table">
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <div class="loading-text">Cargando EDPs de cobro rápido...</div>
                    </div>
                </div>
            </td>
        </tr>
    `;
}

function loadFastCollectionData(tableId) {
    fetch('/management/api/fast_collection_edps')
        .then(response => response.json())
        .then(data => {
            const loadingRow = document.getElementById(tableId);
            if (!loadingRow) return;
            
            // Find the tbody parent to insert new rows
            const tbody = loadingRow.parentElement;
            if (!tbody) return;
            
            // Remove the loading row
            loadingRow.remove();
            
            if (!data.success || !data.fast_collection_edps || data.fast_collection_edps.length === 0) {
                const noDataRow = document.createElement('tr');
                noDataRow.innerHTML = `
                    <td colspan="6" class="no-data-cell">
                        <div class="no-data-message">
                            <div class="no-data-text">No hay EDPs de cobro rápido</div>
                            <div class="no-data-subtext">Oportunidad de acelerar procesos de cobro</div>
                        </div>
                    </td>
                `;
                tbody.appendChild(noDataRow);
                return;
            }
            
            // Generate real table rows and insert them
            data.fast_collection_edps.forEach(edp => {
                const row = document.createElement('tr');
                row.className = 'success-row';
                row.style.cursor = 'pointer';
                row.onclick = () => showEDPDetailModal(edp.n_edp);
                
                row.innerHTML = `
                    <td class="cliente-cell" title="${edp.cliente}">${edp.cliente}</td>
                    <td class="proyecto-cell font-medium" title="${edp.proyecto}">${edp.proyecto}</td>
                    <td class="monto-cell text-right">${edp.monto_formatted}</td>
                    <td class="dias-cell text-center">
                        <span class="dias-badge success">${edp.dias}d</span>
                    </td>
                    <td class="jefe-cell" title="${edp.jefe_proyecto}">${edp.jefe_proyecto}</td>
                    <td class="estado-cell text-center">
                        <span class="status-badge success">RÁPIDO</span>
                    </td>
                `;
                
                tbody.appendChild(row);
            });
            
            // Add summary row
            const summaryRow = document.createElement('tr');
            summaryRow.innerHTML = `
                <td colspan="6" class="summary-cell">
                    <div class="table-summary">
                        <div class="summary-stats">
                            <span class="stat-item">
                                <strong>${data.summary.total_count}</strong> EDPs de cobro rápido
                            </span>
                            <span class="stat-item">
                                <strong>${formatCurrency(data.summary.total_amount)}</strong> saludable
                            </span>
                            <span class="stat-item">
                                <strong>${data.summary.avg_days}</strong> días promedio
                            </span>
                        </div>
                    </div>
                </td>
            `;
            tbody.appendChild(summaryRow);
            
            // Update summary metrics with real data
            if (data.summary) {
                const avgDaysEl = document.getElementById('fast-avg-days');
                const trendEl = document.getElementById('fast-trend');
                
                if (avgDaysEl) {
                    avgDaysEl.textContent = `${data.summary.avg_days} días`;
                }
                
                if (trendEl) {
                    const trend = data.summary.trend_change || 0;
                    const trendSymbol = trend > 0 ? '+' : '';
                    const trendClass = trend > 0 ? 'warning' : trend < 0 ? 'positive' : 'neutral';
                    trendEl.innerHTML = `<span class="${trendClass}">${trendSymbol}${trend}%</span>`;
                }
            }
        })
        .catch(error => {
            const loadingRow = document.getElementById(tableId);
            if (loadingRow) {
                loadingRow.innerHTML = `
                    <td colspan="6" class="no-data-cell">
                        <div class="error-message">
                            <div class="error-text">Error cargando EDPs de cobro rápido</div>
                            <div class="error-subtext">${error.message}</div>
                        </div>
                    </td>
                `;
            }
        });
}

// ===== ACTION FUNCTIONS =====

function contactAllCriticalClients() {
    showNotification('Iniciando contacto con clientes críticos...', 'info');
    // Implementar lógica de contacto masivo
}

function generateCriticalReport() {
    showNotification('Generando reporte de EDPs críticos...', 'info');
    // Implementar generación de reporte
}

function scheduleCriticalFollowup() {
    showNotification('Programando seguimiento automático...', 'info');
    // Implementar programación de seguimiento
}

function sendAgingEmails() {
    showNotification('Enviando emails preventivos...', 'info');
    // Implementar envío de emails
}

function scheduleAgingCalls() {
    showNotification('Programando llamadas de seguimiento...', 'info');
    // Implementar programación de llamadas
}

function exportAgingData() {
    showNotification('Exportando datos de aging...', 'info');
    // Implementar exportación
}

function accelerateCollection() {
    showNotification('Acelerando procesos de cobro...', 'info');
    // Implementar aceleración de cobros
}

function confirmCollectionDates() {
    showNotification('Confirmando fechas de cobro...', 'info');
    // Implementar confirmación de fechas
}

function exportFastCollection() {
    showNotification('Exportando proyección de cobros...', 'info');
    // Implementar exportación
}

function executeGapPlan() {
    showNotification('Ejecutando plan de cierre de brecha...', 'warning');
    // Implementar ejecución del plan
}

function reviewMetaStrategy() {
    showNotification('Iniciando revisión de estrategia...', 'info');
    // Implementar revisión de estrategia
}

function generateMetaReport() {
    showNotification('Generando reporte de meta...', 'info');
    // Implementar generación de reporte
}

// ===== MANAGER DETAIL FUNCTIONS =====

// Generate manager projects data (real data only)
function generateManagerProjects(managerName, proyectosCount, montoValue) {
    // Return a loading placeholder initially, then load real data
    const tableId = 'manager-projects-table-' + Date.now();
    
    // Start loading data immediately
    setTimeout(() => loadManagerProjectsData(tableId, managerName), 100);
    
    return `
        <tr id="${tableId}">
            <td colspan="6" class="no-data-cell">
                <div class="loading-table">
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <div class="loading-text">Cargando proyectos de ${managerName}...</div>
                    </div>
                </div>
            </td>
        </tr>
    `;
}

function loadManagerProjectsData(tableId, managerName) {
    console.log(`🔍 Cargando proyectos para manager: ${managerName}`);
    
    // Encode manager name for URL
    const encodedManagerName = encodeURIComponent(managerName);
    
    fetch(`/management/api/manager_projects/${encodedManagerName}`)
        .then(response => {
            console.log(`📡 Response status: ${response.status}`);
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📊 Manager projects data received:', data);
            
            const tableRow = document.getElementById(tableId);
            if (!tableRow) {
                console.warn('⚠️ Table row not found');
                return;
            }
            
            const tbody = tableRow.closest('tbody');
            if (!tbody) {
                console.warn('⚠️ Tbody not found');
                return;
            }
            
            // Remove loading row
            tableRow.remove();
            
            if (!data.success || !data.manager_projects || data.manager_projects.length === 0) {
                const noDataRow = document.createElement('tr');
                noDataRow.innerHTML = `
                    <td colspan="6" class="no-data-cell">
                        <div class="text-center py-4">
                            <div class="text-xl mb-2">📋</div>
                            <div class="font-medium mb-1">No hay proyectos asignados</div>
                            <div class="text-sm opacity-70">${managerName} no tiene proyectos activos en este momento</div>
                        </div>
                    </td>
                `;
                tbody.appendChild(noDataRow);
                return;
            }
            
            // Create rows for each project
            data.manager_projects.forEach((project, index) => {
                const row = document.createElement('tr');
                row.className = `manager-project-row ${project.priority} ${index % 2 === 0 ? 'even' : 'odd'}`;
                
                // Determine priority colors
                let priorityClass = '';
                let dsoClass = 'neutral';
                if (project.dso > 60) {
                    priorityClass = 'critical-row';
                    dsoClass = 'critical';
                } else if (project.dso > 30) {
                    priorityClass = 'warning-row';
                    dsoClass = 'warning';
                } else if (project.dso < 15) {
                    priorityClass = 'positive-row';
                    dsoClass = 'positive';
                }
                
                row.innerHTML = `
                    <td class="proyecto-cell">
                        <div class="font-medium">${project.proyecto}</div>
                        <div class="text-xs opacity-70">EDP: ${project.n_edp}</div>
                    </td>
                    <td class="cliente-cell">
                        <div class="font-medium">${project.cliente}</div>
                    </td>
                    <td class="monto-cell text-right">
                        <span class="font-mono">${project.monto_formatted}</span>
                    </td>
                    <td class="text-center">
                        <span class="dso-badge ${dsoClass}">${project.dso}d</span>
                    </td>
                    <td class="text-center">
                        <span class="status-badge ${project.priority}">${project.estado}</span>
                    </td>
                    <td class="text-center text-sm">
                        ${project.last_contact}
                    </td>
                `;
                
                // Add click event to show EDP detail
                row.addEventListener('click', () => {
                    if (project.id && project.id !== 'N/A') {
                        showEDPDetailModal(project.id);
                    }
                });
                
                tbody.appendChild(row);
            });
            
            // Add summary row
            if (data.summary) {
                const summaryRow = document.createElement('tr');
                summaryRow.className = 'summary-row';
                summaryRow.innerHTML = `
                    <td colspan="6" class="summary-cell">
                        <div class="table-summary">
                            <div class="summary-grid">
                                <div class="summary-item">
                                    <span class="summary-label">Total Proyectos:</span>
                                    <span class="summary-value">${data.summary.total_projects}</span>
                                </div>
                                                                 <div class="summary-item">
                                     <span class="summary-label">Monto Total:</span>
                                     <span class="summary-value">${formatCurrency(data.summary.total_amount || 0)}</span>
                                 </div>
                                <div class="summary-item">
                                    <span class="summary-label">DSO Promedio:</span>
                                    <span class="summary-value ${data.summary.avg_dso > 60 ? 'critical' : data.summary.avg_dso > 30 ? 'warning' : 'positive'}">${data.summary.avg_dso}d</span>
                                </div>
                                <div class="summary-item">
                                    <span class="summary-label">Proyectos Críticos:</span>
                                    <span class="summary-value ${data.summary.critical_projects > 0 ? 'critical' : 'positive'}">${data.summary.critical_projects}</span>
                                </div>
                            </div>
                        </div>
                    </td>
                `;
                tbody.appendChild(summaryRow);
            }
            
            console.log(`✅ Manager projects table populated with ${data.manager_projects.length} projects`);
            
        })
        .catch(error => {
            console.error('❌ Error loading manager projects:', error);
            
            const tableRow = document.getElementById(tableId);
            if (tableRow) {
                tableRow.innerHTML = `
                    <td colspan="6" class="error-cell">
                        <div class="text-center py-4">
                            <div class="text-xl mb-2">⚠️</div>
                            <div class="font-medium mb-1">Error al cargar proyectos</div>
                            <div class="text-sm opacity-70">${error.message}</div>
                            <button onclick="loadManagerProjectsData('${tableId}', '${managerName}')" class="retry-btn mt-2">
                                Reintentar
                            </button>
                        </div>
                    </td>
                `;
            }
        });
}

// Manager contact functions
function contactManagerAdvanced(managerName, method) {
    let title = '';
    let message = '';
    let type = 'info';
    
    switch(method) {
        case 'call':
            title = 'Llamar a ' + managerName;
            message = `Iniciando llamada telefónica con ${managerName}. El número será marcado automáticamente.`;
            break;
        case 'email':
            title = 'Email a ' + managerName;
            message = `Abriendo cliente de email para enviar mensaje a ${managerName.toLowerCase().replace(' ', '.')}@company.com`;
            break;
        case 'emergency':
            title = 'Contacto de Emergencia';
            message = `Iniciando protocolo de contacto urgente con ${managerName}. Se enviará notificación inmediata.`;
            type = 'warning';
            break;
    }
    
    showNotificationModal(title, message, type);
}

function scheduleManagerMeeting(managerName) {
    showNotificationModal(
        'Programar Reunión',
        `Programando reunión con ${managerName} para revisar estado de proyectos y estrategias de mejora de DSO.`,
        'info'
    );
}

function assignManagerSupport(managerName) {
    showNotificationModal(
        'Asignar Apoyo',
        `Asignando recursos de apoyo adicionales para ${managerName}. Se coordinará con el equipo de soporte.`,
        'positive'
    );
}

// Team coordination functions
function redistributeProjects() {
    showNotificationModal(
        'Redistribución de Proyectos',
        'Analizando cargas de trabajo para redistribuir proyectos críticos y optimizar el DSO del equipo.',
        'warning'
    );
}

function scheduleTraining() {
    showNotificationModal(
        'Capacitación Programada',
        'Organizando programa de capacitación en técnicas de cobranza y gestión de clientes para el equipo.',
        'positive'
    );
}

function escalateManager(managerName) {
    showNotificationModal(
        'Escalamiento',
        `Escalando situación de ${managerName} a nivel directivo. Se iniciará protocolo de intervención.`,
        'critical'
    );
}

function showProjectDetail(projectId) {
    showNotificationModal(
        'Detalle de Proyecto',
        `Mostrando información detallada del proyecto ${projectId}. Funcionalidad en desarrollo.`,
        'info'
    );
}

// Notification modal function
function showNotificationModal(title, message, type) {
    const typeClass = type === 'critical' ? 'critical' : 
                     type === 'warning' ? 'warning' : 
                     type === 'positive' ? 'positive' : 'info';
    
    const modalContent = `
        <div class="notification-modal ${typeClass}">
            <div class="notification-icon">
                ${type === 'critical' ? '⚠️' : 
                  type === 'warning' ? '⚡' : 
                  type === 'positive' ? '✅' : 'ℹ️'}
            </div>
            <div class="notification-content">
                <div class="notification-message">${message}</div>
            </div>
        </div>
    `;
    
    showModal(title, modalContent, 'medium');
}

// ===== FORECAST FUNCTIONS =====

// Generate forecast EDPs for a specific day (real data only)
function generateForecastEDPs(day, totalAmount, avgConfidence) {
    // Return empty array - only show real EDPs when available from backend
    return [];
}

// Get forecast date for a day
function getForecastDate(day) {
    const today = new Date();
    const dayMap = {
        'Lun': 1, 'Mar': 2, 'Mié': 3, 'Jue': 4, 'Vie': 5, 'Sáb': 6, 'Dom': 0
    };
    
    const targetDay = dayMap[day];
    const currentDay = today.getDay();
    let daysToAdd = targetDay - currentDay;
    
    if (daysToAdd <= 0) daysToAdd += 7;
    
    const targetDate = new Date(today);
    targetDate.setDate(today.getDate() + daysToAdd);
    
    return targetDate.toLocaleDateString('es-CL', { 
        day: '2-digit', 
        month: '2-digit' 
    });
}

// Show consolidated forecast modal (when clicking on title)
function showWeeklyForecastModal() {
    const kpis = window.kpisData || {};
    const weeklyTotal = (kpis.forecast_7_dias || 0);
    const weeklyTarget = 5.0; // Weekly target in M CLP
    
    // Generate weekly summary (real data only)
    const weeklyData = [
        { day: 'Lun', amount: kpis.forecast_day_1 || 0, confidence: 0 },
        { day: 'Mar', amount: kpis.forecast_day_2 || 0, confidence: 0 },
        { day: 'Mié', amount: kpis.forecast_day_3 || 0, confidence: 0 },
        { day: 'Jue', amount: kpis.forecast_day_4 || 0, confidence: 0 },
        { day: 'Vie', amount: kpis.forecast_day_5 || 0, confidence: 0 },
        { day: 'Sáb', amount: kpis.forecast_day_6 || 0, confidence: 0 },
        { day: 'Dom', amount: kpis.forecast_day_7 || 0, confidence: 0 }
    ];
    
    const criticalDays = weeklyData.filter(d => d.confidence < 60);
    const highConfidenceDays = weeklyData.filter(d => d.confidence > 80);
    
    const modalContent = `
        <div class="weekly-forecast-modal">
            <div class="weekly-summary">
                <div class="summary-header">
                    <div class="summary-metric">
                        <div class="metric-value ${weeklyTotal >= weeklyTarget ? 'positive' : 'warning'}">${weeklyTotal.toFixed(1)}M</div>
                        <div class="metric-label">Total Semanal</div>
                    </div>
                    <div class="summary-metric">
                        <div class="metric-value neutral">${weeklyTarget.toFixed(1)}M</div>
                        <div class="metric-label">Meta Semanal</div>
                    </div>
                    <div class="summary-metric">
                        <div class="metric-value ${weeklyTotal >= weeklyTarget ? 'positive' : 'critical'}">${((weeklyTotal / weeklyTarget) * 100).toFixed(0)}%</div>
                        <div class="metric-label">Cumplimiento</div>
                    </div>
                </div>
            </div>

            <div class="weekly-breakdown">
                <div class="kpi-section-title">Desglose por Día</div>
                <div class="weekly-chart">
                    ${weeklyData.map(item => `
                        <div class="weekly-day-item" onclick="showForecastDetail('${item.day}', '${item.amount.toFixed(1)}M', '${item.confidence}% prob')">
                            <div class="day-header">
                                <div class="day-name">${item.day}</div>
                                <div class="day-date">${getForecastDate(item.day)}</div>
                            </div>
                            <div class="day-amount ${item.amount > 1.0 ? 'high' : item.amount > 0.5 ? 'medium' : 'low'}">${item.amount.toFixed(1)}M</div>
                            <div class="day-confidence ${item.confidence > 70 ? 'positive' : item.confidence > 50 ? 'warning' : 'critical'}">${item.confidence}%</div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="weekly-analysis">
                <div class="kpi-section-title">Análisis Semanal</div>
                <div class="analysis-grid">
                    <div class="analysis-item">
                        <div class="analysis-title">Días Críticos</div>
                        <div class="analysis-value critical">${criticalDays.length}</div>
                        <div class="analysis-desc">Días con confianza <60%</div>
                    </div>
                    <div class="analysis-item">
                        <div class="analysis-title">Alta Confianza</div>
                        <div class="analysis-value positive">${highConfidenceDays.length}</div>
                        <div class="analysis-desc">Días con confianza >80%</div>
                    </div>
                    <div class="analysis-item">
                        <div class="analysis-title">Riesgo Semanal</div>
                        <div class="analysis-value ${criticalDays.length > 2 ? 'critical' : criticalDays.length > 0 ? 'warning' : 'positive'}">
                            ${criticalDays.length > 2 ? 'Alto' : criticalDays.length > 0 ? 'Medio' : 'Bajo'}
                        </div>
                        <div class="analysis-desc">Evaluación general</div>
                    </div>
                </div>
            </div>

            <div class="weekly-actions">
                <div class="kpi-section-title">Plan de Seguimiento Semanal</div>
                <div class="weekly-plan">
                    <div class="plan-step priority-high">
                        <div class="plan-icon">1</div>
                        <div class="plan-content">
                            <div class="plan-title">Focalizar Días Críticos</div>
                            <div class="plan-desc">Intervenir ${criticalDays.map(d => d.day).join(', ')} para mejorar confianza</div>
                        </div>
                    </div>
                    <div class="plan-step priority-medium">
                        <div class="plan-icon">2</div>
                        <div class="plan-content">
                            <div class="plan-title">Consolidar Alta Confianza</div>
                            <div class="plan-desc">Asegurar cobros en ${highConfidenceDays.map(d => d.day).join(', ')}</div>
                        </div>
                    </div>
                    <div class="plan-step priority-low">
                        <div class="plan-icon">3</div>
                        <div class="plan-content">
                            <div class="plan-title">Monitoreo Continuo</div>
                            <div class="plan-desc">Actualizar proyecciones diariamente</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="kpi-actions-section">
                <div class="kpi-actions-grid">
                    <button class="kpi-action-btn critical" onclick="focusCriticalDays()">
                        Intervenir Días Críticos
                    </button>
                    <button class="kpi-action-btn warning" onclick="updateWeeklyProjections()">
                        Actualizar Proyecciones
                    </button>
                    <button class="kpi-action-btn positive" onclick="generateWeeklyReport()">
                        Generar Reporte
                    </button>
                    <button class="kpi-action-btn info" onclick="scheduleWeeklyReview()">
                        Programar Revisión
                    </button>
                </div>
            </div>
        </div>
    `;

    showModal('Forecast Semanal - Próximos 7 Días', modalContent, 'large');
}

// Forecast action functions
function executeForecastAction(action, projectId) {
    showNotificationModal(
        `${action} - ${projectId}`,
        `Ejecutando acción "${action}" para el proyecto ${projectId}. Se contactará al responsable.`,
        'info'
    );
}

function confirmAllPayments(day) {
    showNotificationModal(
        'Confirmar Pagos',
        `Iniciando confirmación de todos los pagos programados para ${day}. Se enviará comunicación a todos los clientes.`,
        'warning'
    );
}

function sendDayReminders(day) {
    showNotificationModal(
        'Enviar Recordatorios',
        `Enviando recordatorios automáticos a todos los clientes con EDPs programados para ${day}.`,
        'info'
    );
}

function accelerateDayCollection(day) {
    showNotificationModal(
        'Acelerar Cobros',
        `Activando protocolo de aceleración de cobros para todos los EDPs del ${day}. Se priorizarán las gestiones.`,
        'positive'
    );
}

function exportDayForecast(day) {
    showNotificationModal(
        'Exportar Forecast',
        `Generando reporte detallado del forecast para ${day} en formato Excel.`,
        'info'
    );
}

function focusCriticalDays() {
    showNotificationModal(
        'Intervenir Días Críticos',
        'Iniciando protocolo de intervención para días con baja confianza. Se asignarán recursos adicionales.',
        'critical'
    );
}

function updateWeeklyProjections() {
    showNotificationModal(
        'Actualizar Proyecciones',
        'Recalculando proyecciones semanales con datos más recientes. Se notificarán los cambios.',
        'warning'
    );
}

function generateWeeklyReport() {
    showNotificationModal(
        'Generar Reporte Semanal',
        'Creando reporte ejecutivo del forecast semanal con análisis y recomendaciones.',
        'positive'
    );
}

function scheduleWeeklyReview() {
    showNotificationModal(
        'Programar Revisión',
        'Agendando reunión semanal de revisión de forecast con el equipo operacional.',
        'info'
    );
}

function exportForecast() {
    showNotificationModal(
        'Exportar Forecast',
        'Generando archivo Excel con el forecast completo de los próximos 7 días, incluyendo detalles por EDP y análisis de confianza.',
        'info'
    );
}

// Helper function to show EDP detail modal
function showEDPDetailModal(edpId) {
    // Try to open EDP modal if function exists (from other modal system)
    if (typeof openEdpModal === 'function') {
        openEdpModal(edpId);
        return;
    }
    
    // Alternative: navigate to EDP detail page
    if (edpId && edpId !== 'N/A') {
        window.open(`/dashboard/edp/${edpId}`, '_blank');
    }
}

// Add CSS styles for loading spinners and table styling
if (!document.getElementById('modal-table-styles')) {
    const modalStyles = document.createElement('style');
    modalStyles.id = 'modal-table-styles';
    modalStyles.innerHTML = `
        /* Loading spinner styles */
        .loading-table {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 200px;
        }
        
        .loading-spinner {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border-color, #e5e7eb);
            border-top: 3px solid var(--accent-blue, #3b82f6);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-text {
            color: var(--text-secondary, #6b7280);
            font-size: 14px;
        }
        
        /* Table row styling */
        .kpi-detail-table tbody tr {
            transition: background-color 0.2s ease;
            cursor: pointer;
        }
        
        .kpi-detail-table tbody tr:hover {
            background-color: var(--bg-highlight, #f8fafc);
        }
        
        .critical-row {
            background-color: rgba(239, 68, 68, 0.1);
        }
        
        .critical-row:hover {
            background-color: rgba(239, 68, 68, 0.15);
        }
        
        .high-risk-row {
            background-color: rgba(245, 158, 11, 0.1);
        }
        
        .high-risk-row:hover {
            background-color: rgba(245, 158, 11, 0.15);
        }
        
        .warning-row {
            background-color: rgba(251, 191, 36, 0.1);
        }
        
        .warning-row:hover {
            background-color: rgba(251, 191, 36, 0.15);
        }
        
        .success-row {
            background-color: rgba(34, 197, 94, 0.1);
        }
        
        .success-row:hover {
            background-color: rgba(34, 197, 94, 0.15);
        }
        
        /* Badge styling */
        .dias-badge, .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .dias-badge.critical, .status-badge.critical {
            background-color: #fee2e2;
            color: #dc2626;
        }
        
        .dias-badge.high, .status-badge.high {
            background-color: #fef3c7;
            color: #d97706;
        }
        
        .dias-badge.warning, .status-badge.warning {
            background-color: #fef3c7;
            color: #d97706;
        }
        
        .dias-badge.success, .status-badge.success {
            background-color: #dcfce7;
            color: #16a34a;
        }
        
        /* Table summary styling */
        .table-summary {
            margin-top: 16px;
            padding: 12px;
            background-color: var(--bg-subtle, #f8fafc);
            border-radius: 8px;
            border: 1px solid var(--border-color, #e5e7eb);
        }
        
        .summary-stats {
            display: flex;
            gap: 24px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .stat-item {
            color: var(--text-secondary, #6b7280);
            font-size: 14px;
        }
        
        .stat-item strong {
            color: var(--text-primary, #111827);
        }
        
        /* Cell styling */
        .cliente-cell, .proyecto-cell, .jefe-cell {
            max-width: 150px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .monto-cell {
            font-family: 'Courier New', monospace;
            font-weight: 600;
        }
        
        /* Summary cell styling */
        .summary-cell {
            background-color: var(--bg-subtle, #f8fafc);
            border-top: 2px solid var(--border-color, #e5e7eb);
            padding: 12px;
        }
        
        .summary-cell .table-summary {
            margin: 0;
            background: transparent;
            border: none;
            border-radius: 0;
            padding: 0;
        }
        
        /* Error message styling */
        .error-message {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            padding: 32px;
            color: var(--accent-red, #dc2626);
        }
        
        .error-text {
            font-weight: 600;
            font-size: 16px;
        }
        
        .error-subtext {
            font-size: 14px;
            color: var(--text-secondary, #6b7280);
        }
        
        /* Error message styling */
        .error-cell {
            background-color: var(--bg-subtle, #fef2f2);
            border: 1px solid var(--accent-red, #ef4444);
            padding: 16px;
            text-align: center;
        }
        
        .retry-btn {
            background: var(--accent-blue, #3b82f6);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: background-color 0.2s;
        }
        
        .retry-btn:hover {
            background: var(--accent-blue-dark, #2563eb);
        }
        
        /* DSO badge styling */
        .dso-badge {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .dso-badge.critical {
            background-color: rgba(239, 68, 68, 0.1);
            color: var(--accent-red, #ef4444);
            border: 1px solid var(--accent-red, #ef4444);
        }
        
        .dso-badge.warning {
            background-color: rgba(245, 158, 11, 0.1);
            color: var(--accent-yellow, #f59e0b);
            border: 1px solid var(--accent-yellow, #f59e0b);
        }
        
        .dso-badge.positive {
            background-color: rgba(34, 197, 94, 0.1);
            color: var(--accent-green, #22c55e);
            border: 1px solid var(--accent-green, #22c55e);
        }
        
        .dso-badge.neutral {
            background-color: rgba(107, 114, 128, 0.1);
            color: var(--text-secondary, #6b7280);
            border: 1px solid var(--text-secondary, #6b7280);
        }
        
        /* Status badge styling */
        .status-badge {
            padding: 2px 6px;
            border-radius: 8px;
            font-size: 10px;
            font-weight: 500;
            text-transform: uppercase;
        }
        
        .status-badge.critical {
            background-color: rgba(239, 68, 68, 0.1);
            color: var(--accent-red, #ef4444);
        }
        
        .status-badge.warning {
            background-color: rgba(245, 158, 11, 0.1);
            color: var(--accent-yellow, #f59e0b);
        }
        
        .status-badge.positive {
            background-color: rgba(34, 197, 94, 0.1);
            color: var(--accent-green, #22c55e);
        }
        
        .status-badge.normal {
            background-color: rgba(59, 130, 246, 0.1);
            color: var(--accent-blue, #3b82f6);
        }
        
        /* Manager project row styling */
        .manager-project-row {
            transition: background-color 0.2s;
            cursor: pointer;
        }
        
        .manager-project-row:hover {
            background-color: var(--bg-hover, rgba(59, 130, 246, 0.05));
        }
        
        .manager-project-row.critical-row {
            border-left: 3px solid var(--accent-red, #ef4444);
        }
        
        .manager-project-row.warning-row {
            border-left: 3px solid var(--accent-yellow, #f59e0b);
        }
        
        .manager-project-row.positive-row {
            border-left: 3px solid var(--accent-green, #22c55e);
        }
        
        /* Summary row styling */
        .summary-row {
            border-top: 2px solid var(--border-color, #e5e7eb);
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            padding: 8px 0;
        }
        
        .summary-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .summary-label {
            font-weight: 500;
            color: var(--text-secondary, #6b7280);
        }
        
        .summary-value {
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .summary-value.critical {
            color: var(--accent-red, #ef4444);
        }
        
        .summary-value.warning {
            color: var(--accent-yellow, #f59e0b);
        }
        
        .summary-value.positive {
            color: var(--accent-green, #22c55e);
        }
    `;
    document.head.appendChild(modalStyles);
}

// Helper function to format numbers with dots as thousand separators
function formatNumberWithDots(number) {
    if (!number) return '0';
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

// Helper function to format currency with dots
function formatCurrency(amount) {
    if (!amount) return '$0';
    return `$${formatNumberWithDots(Math.round(amount))}`;
}