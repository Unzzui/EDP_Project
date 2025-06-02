// Gráficos de Análisis de Costos
let distribucionTipoChart = null;
let estadoPagosChart = null;
let topProveedoresChart = null;
let tendenciaCostosChart = null;

function initAnalisisCostosCharts() {
    // Distribución OPEX vs CAPEX
    const distribucionTipoCtx = document.getElementById('distribucion-tipo-chart').getContext('2d');
    distribucionTipoChart = new Chart(distribucionTipoCtx, {
        type: 'pie',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: ['rgba(59, 130, 246, 0.7)', 'rgba(16, 185, 129, 0.7)'],
                borderColor: ['rgb(59, 130, 246)', 'rgb(16, 185, 129)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            return `$${value.toFixed(2)}M`;
                        }
                    }
                }
            }
        }
    });

    // Estado de Pagos
    const estadoPagosCtx = document.getElementById('estado-pagos-chart').getContext('2d');
    estadoPagosChart = new Chart(estadoPagosCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: ['rgba(34, 197, 94, 0.7)', 'rgba(234, 179, 8, 0.7)'],
                borderColor: ['rgb(34, 197, 94)', 'rgb(234, 179, 8)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            return `$${value.toFixed(2)}M`;
                        }
                    }
                }
            }
        }
    });

    // Top 5 Proveedores
    const topProveedoresCtx = document.getElementById('top-proveedores-chart').getContext('2d');
    topProveedoresChart = new Chart(topProveedoresCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(16, 185, 129, 0.7)',
                    'rgba(234, 179, 8, 0.7)',
                    'rgba(239, 68, 68, 0.7)',
                    'rgba(168, 85, 247, 0.7)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.x;
                            return `$${value.toFixed(2)}M`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Millones de pesos (M$)'
                    }
                }
            }
        }
    });

    // Tendencia de Costos
    const tendenciaCostosCtx = document.getElementById('tendencia-costos-chart').getContext('2d');
    tendenciaCostosChart = new Chart(tendenciaCostosCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Costos Diarios',
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            return `$${value.toFixed(2)}M`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Millones de pesos (M$)'
                    }
                }
            }
        }
    });
}

function updateAnalisisCostosCharts(data) {
    if (!data || data.error) {
        console.error('Error en datos de análisis de costos:', data?.error);
        return;
    }

    // Actualizar KPIs
    document.getElementById('total-costos').textContent = data.kpis.total_costos.toFixed(2);
    document.getElementById('promedio-factura').textContent = data.kpis.promedio_factura.toFixed(2);
    document.getElementById('porcentaje-pagado').textContent = data.kpis.porcentaje_pagado.toFixed(1);
    document.getElementById('ratio-opex-capex').textContent = data.kpis.ratio_opex_capex.toFixed(1);

    // Actualizar Distribución OPEX vs CAPEX
    distribucionTipoChart.data.labels = data.distribucion_tipo.labels;
    distribucionTipoChart.data.datasets[0].data = data.distribucion_tipo.datasets[0].data;
    distribucionTipoChart.update();

    // Actualizar Estado de Pagos
    estadoPagosChart.data.labels = data.estado_pagos.labels;
    estadoPagosChart.data.datasets[0].data = data.estado_pagos.datasets[0].data;
    estadoPagosChart.update();

    // Actualizar Top 5 Proveedores
    topProveedoresChart.data.labels = data.top_proveedores.labels;
    topProveedoresChart.data.datasets[0].data = data.top_proveedores.datasets[0].data;
    topProveedoresChart.update();

    // Actualizar Tendencia de Costos
    tendenciaCostosChart.data.labels = data.tendencia_costos.labels;
    tendenciaCostosChart.data.datasets[0].data = data.tendencia_costos.datasets[0].data;
    tendenciaCostosChart.update();
}

// Agregar a la función de inicialización existente
document.addEventListener('DOMContentLoaded', function() {
    // ... existing initialization code ...
    
    initAnalisisCostosCharts();
});

// Agregar a la función de actualización existente
function updateDashboardCharts(data) {
    // ... existing update code ...
    
    if (data.analisis_costos) {
        updateAnalisisCostosCharts(data.analisis_costos);
    }
} 