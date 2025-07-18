/**
 * Dashboard Management - Charts JavaScript
 * Funcionalidad de gráficos del dashboard de management
 */

// Variable global para almacenar instancias de charts
let dashboardCharts = {};

/**
 * Inicializa todos los charts del dashboard
 */
function initializeDashboardCharts() {
    console.log('📊 Inicializando charts del dashboard...');
    initializeDSOChart();
    // Aquí se pueden agregar más charts en el futuro
}

/**
 * Inicializa el gráfico de tendencia DSO
 */
function initializeDSOChart() {
    const chartCanvas = document.getElementById('dsoTrendChart');
    // Intentar obtener el DSO real de diferentes fuentes
    const realDSO = window.kpisData?.dso_actual || window.kpisData?.dso || 
                   (window.kpisData && window.kpisData.dso_actual > 0 ? window.kpisData.dso_actual : null);
    
    if (chartCanvas && realDSO && realDSO > 0) {
        const ctx = chartCanvas.getContext('2d');
        
        console.log(`📈 Creando gráfico DSO con valor real: ${realDSO}`);
        
        // Solo mostrar punto de datos real, no crear datos históricos falsos
        dashboardCharts.dsoChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Actual'],
                datasets: [{
                    label: 'DSO Actual',
                    data: [realDSO],
                    borderColor: '#ff0066',
                    backgroundColor: 'rgba(255, 0, 102, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                }, {
                    label: 'Target DSO',
                    data: [35],
                    borderColor: '#00ff88',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        display: true,
                        labels: {
                            color: '#ffffff'
                        }
                    }
                },
                layout: {
                    padding: 20
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#888888', font: { family: 'JetBrains Mono', size: 10 } }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#888888', font: { family: 'JetBrains Mono', size: 10 } },
                        min: 0,
                        max: Math.max(realDSO * 1.2, 50)
                    }
                },
                elements: {
                    point: { radius: 6, hoverRadius: 8 }
                },
                // Configurar el background del canvas
                onResize: function(chart, size) {
                    chart.canvas.parentNode.style.backgroundColor = 'var(--bg-primary)';
                }
            }
        });
        
        // Aplicar background al contenedor del chart
        applyChartBackground(dashboardCharts.dsoChart);
        
        console.log('✅ Gráfico DSO inicializado correctamente');
    } else {
        console.log('⚠️ No se pudo inicializar el gráfico DSO - datos insuficientes');
    }
}

/**
 * Aplica background consistente a los contenedores de charts
 */
function applyChartBackground(chartInstance) {
    if (chartInstance && chartInstance.canvas && chartInstance.canvas.parentNode) {
        const container = chartInstance.canvas.parentNode;
        container.style.backgroundColor = 'var(--bg-primary)';
        container.style.borderRadius = '8px';
        container.style.padding = '10px';
        container.style.border = '1px solid var(--border-primary)';
    }
}

/**
 * Actualiza el gráfico DSO con nuevos datos
 */
function updateDSOChart(newDSOValue) {
    if (dashboardCharts.dsoChart && newDSOValue > 0) {
        dashboardCharts.dsoChart.data.datasets[0].data = [newDSOValue];
        dashboardCharts.dsoChart.options.scales.y.max = Math.max(newDSOValue * 1.2, 50);
        dashboardCharts.dsoChart.update('active');
        console.log(`📊 Gráfico DSO actualizado con valor: ${newDSOValue}`);
    }
}

/**
 * Destruye todos los charts para limpiar memoria
 */
function destroyDashboardCharts() {
    Object.values(dashboardCharts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    dashboardCharts = {};
    console.log('🗑️ Charts del dashboard destruidos');
}

/**
 * Redimensiona todos los charts
 */
function resizeDashboardCharts() {
    Object.values(dashboardCharts).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

/**
 * Configuración común para todos los charts
 */
const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                color: '#ffffff',
                usePointStyle: true,
                padding: 15
            }
        },
        tooltip: {
            backgroundColor: 'var(--bg-primary)',
            titleColor: '#ffffff',
            bodyColor: '#ffffff',
            borderColor: 'var(--border-primary)',
            borderWidth: 1
        }
    },
    scales: {
        x: {
            grid: { color: 'rgba(255, 255, 255, 0.1)' },
            ticks: { color: '#888888', font: { family: 'JetBrains Mono', size: 10 } }
        },
        y: {
            grid: { color: 'rgba(255, 255, 255, 0.1)' },
            ticks: { color: '#888888', font: { family: 'JetBrains Mono', size: 10 } }
        }
    }
};

/**
 * Inicializa un chart de barras genérico
 */
function createBarChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(`⚠️ Canvas ${canvasId} no encontrado`);
        return null;
    }

    const ctx = canvas.getContext('2d');
    const chartOptions = { ...commonChartOptions, ...options };

    const chart = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: chartOptions
    });

    applyChartBackground(chart);
    return chart;
}

/**
 * Inicializa un chart de líneas genérico
 */
function createLineChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(`⚠️ Canvas ${canvasId} no encontrado`);
        return null;
    }

    const ctx = canvas.getContext('2d');
    const chartOptions = { ...commonChartOptions, ...options };

    const chart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: chartOptions
    });

    applyChartBackground(chart);
    return chart;
}

/**
 * Inicializa un chart de dona genérico
 */
function createDoughnutChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(`⚠️ Canvas ${canvasId} no encontrado`);
        return null;
    }

    const ctx = canvas.getContext('2d');
    const chartOptions = { 
        ...commonChartOptions, 
        ...options,
        scales: undefined // Los charts de dona no usan scales
    };

    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: chartOptions
    });

    applyChartBackground(chart);
    return chart;
}

/**
 * Colores predefinidos para charts
 */
const chartColors = {
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    light: '#f8fafc',
    dark: '#1e293b',
    muted: '#64748b'
};

/**
 * Genera una paleta de colores para datasets
 */
function generateColorPalette(count) {
    const colors = Object.values(chartColors);
    const palette = [];
    
    for (let i = 0; i < count; i++) {
        palette.push(colors[i % colors.length]);
    }
    
    return palette;
}

/**
 * Formatea números para mostrar en charts
 */
function formatChartNumber(value, type = 'currency') {
    switch (type) {
        case 'currency':
            return new Intl.NumberFormat('es-CL', {
                style: 'currency',
                currency: 'CLP',
                minimumFractionDigits: 0,
                maximumFractionDigits: 1
            }).format(value * 1000000);
        case 'percentage':
            return `${value.toFixed(1)}%`;
        case 'number':
            return new Intl.NumberFormat('es-CL').format(value);
        default:
            return value.toString();
    }
}

// Event listeners para redimensionamiento
window.addEventListener('resize', () => {
    setTimeout(resizeDashboardCharts, 100);
});

// Cleanup al salir de la página
window.addEventListener('beforeunload', () => {
    destroyDashboardCharts();
}); 