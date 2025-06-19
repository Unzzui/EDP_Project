// === CONTROLLER KANBAN METRICS & STATISTICS ===

// Variables globales que serán configuradas desde el HTML
window.dsoGlobal = window.dsoGlobal || 0;
window.userAccessLevel = window.userAccessLevel || 'none';
window.managerName = window.managerName || '';
window.currentUserRole = window.currentUserRole || '';
window.isRestrictedUser = window.isRestrictedUser || false;

// === INICIALIZACIÓN DE MÉTRICAS ===
document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 Inicializando métricas del kanban...');
    
    // Configurar atributos de datos para el JavaScript externo
    setupDataAttributes();
    
    // Inicializar métricas
    initializeMetrics();
    
    console.log('✅ Métricas del kanban inicializadas correctamente');
});

// === CONFIGURACIÓN DE ATRIBUTOS DE DATOS ===
function setupDataAttributes() {
    // Los atributos se configuran desde el HTML template
    // Esta función puede expandirse si necesitamos configuración adicional
    
    console.log('🔧 Atributos de datos configurados:', {
        initialFilter: document.body.getAttribute('data-initial-filter'),
        filterMes: document.body.getAttribute('data-filter-mes'),
        filterJefe: document.body.getAttribute('data-filter-jefe'),
        filterCliente: document.body.getAttribute('data-filter-cliente'),
        filterEstado: document.body.getAttribute('data-filter-estado')
    });
}

// === INICIALIZACIÓN DE MÉTRICAS ===
function initializeMetrics() {
    // Obtener datos desde variables globales que se configuran en el HTML
    const estadisticas = window.estadisticasData || {};
    const registros = window.registrosData || [];
    
    console.log('🔍 Datos del kanban:', {
        estadisticas: estadisticas,
        registros: registros.length
    });
    
    if (Object.keys(estadisticas).length > 0) {
        updateBasicStatistics(estadisticas);
    }
    
    if (registros && Array.isArray(registros) && registros.length > 0) {
        calculateAndUpdateMetrics(registros);
    } else {
        console.warn('⚠️ No hay registros disponibles para calcular métricas');
    }
    
    updateTimestamps();
}

// === ACTUALIZAR ESTADÍSTICAS BÁSICAS ===
function updateBasicStatistics(estadisticas) {
    console.log('📈 Actualizando estadísticas básicas...');
    
    // Actualizar estadísticas básicas (panel inferior)
    const metaMensual = document.getElementById('meta-mensual');
    if (metaMensual) {
        metaMensual.textContent = '$' + (estadisticas.meta_mensual || 0).toLocaleString();
    }
    
    // Actualizar KPIs del banner principal
    updateBannerKPIs(estadisticas);
}

// === ACTUALIZAR KPIs DEL BANNER ===
function updateBannerKPIs(estadisticas) {
    const kpiElements = {
        totalEdpsBanner: document.getElementById('total-edps-banner'),
        criticosBanner: document.getElementById('criticos-banner'),
        pendientesBanner: document.getElementById('pendientes-banner'),
        validadosBanner: document.getElementById('validados-banner'),
        dsoBanner: document.getElementById('dso-banner')
    };
    
    if (kpiElements.totalEdpsBanner) {
        kpiElements.totalEdpsBanner.textContent = (estadisticas.total_edps || 0).toLocaleString();
    }
    if (kpiElements.criticosBanner) {
        kpiElements.criticosBanner.textContent = (estadisticas.total_criticos || 0).toLocaleString();
    }
    if (kpiElements.pendientesBanner) {
        kpiElements.pendientesBanner.textContent = (estadisticas.total_pendientes || 0).toLocaleString();
    }
    if (kpiElements.validadosBanner) {
        kpiElements.validadosBanner.textContent = (estadisticas.total_validados || 0).toLocaleString();
    }
    
    // DSO se actualiza en calculateAndUpdateMetrics()
}

// === CALCULAR Y ACTUALIZAR MÉTRICAS ===
function calculateAndUpdateMetrics(registros) {
    console.log('🧮 Calculando métricas adicionales...');
    
    const totalRegistros = registros.length;
    const totalMonto = registros.reduce((sum, r) => sum + (parseFloat(r.monto_aprobado) || 0), 0);
    const criticos = registros.filter(r => r.dias_espera > 60).length;
    const pendientes = registros.filter(r => r.estado && ['enviado', 'revisión', 'pendiente'].includes(r.estado.toLowerCase())).length;
    const validados = registros.filter(r => r.estado && ['validado', 'pagado'].includes(r.estado.toLowerCase())).length;
    
    // Usar DSO global calculado en el servidor
    const dso = window.dsoGlobal || 0;
    
    // Actualizar métricas en el panel principal
    updateMainPanelMetrics({
        totalRegistros,
        pendientes,
        validados,
        totalMonto,
        dso
    });
    
    // Actualizar también los KPIs del banner con datos calculados
    updateBannerCalculatedKPIs({
        totalRegistros,
        criticos,
        pendientes,
        validados,
        dso
    });
    
    // Actualizar barra de progreso
    updateProgressBar(validados, totalRegistros);
    
    console.log('📊 Métricas calculadas y actualizadas:', {
        total: totalRegistros,
        pendientes: pendientes,
        validados: validados,
        monto: totalMonto,
        criticos: criticos,
        dso: dso
    });
}

// === ACTUALIZAR MÉTRICAS DEL PANEL PRINCIPAL ===
function updateMainPanelMetrics(metrics) {
    const elements = {
        totalEdps: document.getElementById('total-edps'),
        totalPendientes: document.getElementById('total-pendientes'),
        totalValidados: document.getElementById('total-validados'),
        montoTotal: document.getElementById('monto-total'),
        dsoPrincipal: document.getElementById('dso-principal')
    };
    
    if (elements.totalEdps) {
        elements.totalEdps.textContent = metrics.totalRegistros.toLocaleString();
    }
    if (elements.totalPendientes) {
        elements.totalPendientes.textContent = metrics.pendientes.toLocaleString();
    }
    if (elements.totalValidados) {
        elements.totalValidados.textContent = metrics.validados.toLocaleString();
    }
    if (elements.montoTotal) {
        elements.montoTotal.textContent = '$' + metrics.totalMonto.toLocaleString();
    }
    
    // Actualizar DSO con colores según el valor
    updateDSOElement(elements.dsoPrincipal, metrics.dso);
}

// === ACTUALIZAR KPIs CALCULADOS DEL BANNER ===
function updateBannerCalculatedKPIs(metrics) {
    const elements = {
        totalEdpsBanner: document.getElementById('total-edps-banner'),
        criticosBanner: document.getElementById('criticos-banner'),
        pendientesBanner: document.getElementById('pendientes-banner'),
        validadosBanner: document.getElementById('validados-banner'),
        dsoBanner: document.getElementById('dso-banner')
    };
    
    if (elements.totalEdpsBanner) {
        elements.totalEdpsBanner.textContent = metrics.totalRegistros.toLocaleString();
    }
    if (elements.criticosBanner) {
        elements.criticosBanner.textContent = metrics.criticos.toLocaleString();
    }
    if (elements.pendientesBanner) {
        elements.pendientesBanner.textContent = metrics.pendientes.toLocaleString();
    }
    if (elements.validadosBanner) {
        elements.validadosBanner.textContent = metrics.validados.toLocaleString();
    }
    
    // Actualizar DSO en el banner con colores
    updateDSOElement(elements.dsoBanner, metrics.dso);
}

// === ACTUALIZAR ELEMENTO DSO CON COLORES ===
function updateDSOElement(element, dsoValue) {
    if (!element) return;
    
    element.textContent = dsoValue;
    
    // Aplicar colores según el valor del DSO
    if (dsoValue <= 30) {
        element.className = 'text-2xl font-bold text-[color:var(--accent-green)]'; // Excelente
    } else if (dsoValue <= 45) {
        element.className = 'text-2xl font-bold text-[color:var(--text-primary)]'; // Bueno
    } else if (dsoValue <= 60) {
        element.className = 'text-2xl font-bold text-[color:var(--accent-amber)]'; // Regular
    } else {
        element.className = 'text-2xl font-bold text-[color:var(--accent-red)]'; // Crítico
    }
}

// === ACTUALIZAR BARRA DE PROGRESO ===
function updateProgressBar(validados, totalRegistros) {
    const progressBar = document.getElementById('progress-bar');
    const progressPercentage = document.getElementById('progress-percentage');
    
    if (progressBar && progressPercentage && totalRegistros > 0) {
        const progressValue = Math.round((validados / totalRegistros) * 100);
        progressBar.style.width = progressValue + '%';
        progressPercentage.textContent = progressValue + '%';
    }
}

// === ACTUALIZAR TIMESTAMPS ===
function updateTimestamps() {
    const lastUpdated = document.getElementById('last-updated-date');
    const lastUpdatedBanner = document.getElementById('last-updated-banner');
    const currentTime = new Date().toLocaleTimeString();
    
    if (lastUpdated) {
        lastUpdated.textContent = 'Actualizado: ' + currentTime;
    }
    if (lastUpdatedBanner) {
        lastUpdatedBanner.textContent = 'Actualizado: ' + currentTime;
    }
}

// === FUNCIONES PÚBLICAS PARA ACTUALIZACIÓN MANUAL ===
window.updateKanbanMetrics = function(estadisticas, registros) {
    if (estadisticas) {
        updateBasicStatistics(estadisticas);
    }
    
    if (registros && Array.isArray(registros)) {
        calculateAndUpdateMetrics(registros);
    }
    
    updateTimestamps();
    console.log('🔄 Métricas actualizadas manualmente');
};

window.refreshMetrics = function() {
    // Función para refrescar métricas desde datos globales actuales
    if (window.estadisticasData && window.registrosData) {
        window.updateKanbanMetrics(window.estadisticasData, window.registrosData);
    }
};

console.log('📊 Controller Kanban Metrics JS cargado correctamente'); 