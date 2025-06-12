/**
 * Operational Dashboard Charts
 * Comprehensive chart system for granular operational analysis
 */

// Chart instances storage
const operationalCharts = {};

// Color schemes for consistency
const chartColors = {
    primary: '#3B82F6',
    secondary: '#10B981', 
    warning: '#F59E0B',
    danger: '#EF4444',
    success: '#059669',
    info: '#0EA5E9',
    purple: '#8B5CF6',
    pink: '#EC4899',
    orange: '#F97316',
    gray: '#6B7280'
};

// Utility functions
function formatCurrency(value) {
    const formatted = new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 1
    }).format(value * 1000000);
    
    // Reemplazar comas con puntos para separador de miles
    return formatted.replace(/,/g, '.');
}

function formatNumber(value) {
    return new Intl.NumberFormat('es-CL').format(value);
}

// Get chart data from global variables or defaults
function getChartData() {
    if (window.dashboardData) {
        console.log('📊 Using real dashboard data:', window.dashboardData);
        return window.dashboardData;
    } else {
        console.warn('⚠️ No dashboard data found, using fallback data');
        return {
            operational_chart_data: {},
            kpis: {},
            aging: { buckets: {} },
            cash_forecast: {},
            profitability: { gestores: [], clientes: [], proyectos: [] }
        };
    }
}

// 1. Financial Trend Chart - USANDO DATOS REALES
function initFinancialTrendChart() {
    const ctx = document.getElementById('financialTrendChart');
    if (!ctx) return;

    const data = getChartData();
    const financialData = data.operational_chart_data?.tendencia_financiera || {};
    
    console.log('📈 Initializing Financial Trend Chart with real data:', financialData);

    operationalCharts.financialTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: financialData.labels || ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
            datasets: financialData.datasets || [
                {
                    label: 'Ingresos Cobrados (M$)',
                    data: [28.5, 31.2, 27.8, 35.1, 39.3, 42.7],
                    borderColor: chartColors.success,
                    backgroundColor: chartColors.success + '20',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3
                },
                {
                    label: 'Meta Mensual (M$)',
                    data: [40.0, 40.0, 40.0, 40.0, 40.0, 40.0],
                    borderColor: chartColors.danger,
                    backgroundColor: chartColors.danger + '20',
                    fill: false,
                    tension: 0,
                    borderWidth: 2,
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toFixed(1) + 'M';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value + 'M';
                        }
                    }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            }
        }
    });
}

// 2. Cash-In Forecast Chart - USANDO DATOS REALES
function initCashInForecastChart() {
    const ctx = document.getElementById('cashInForecastChart');
    if (!ctx) return;

    const data = getChartData();
    const cashData = data.operational_chart_data?.cash_in_forecast || {};
    
    console.log('💰 Initializing Cash-In Forecast Chart with real data:', cashData);

    operationalCharts.cashForecast = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: cashData.labels || ['30 días', '60 días', '90 días'],
            datasets: cashData.datasets || [
                {
                    label: 'Flujo Conservador (M$)',
                    data: [38.4, 20.1, 9.2],
                    backgroundColor: chartColors.primary + '80',
                    borderColor: chartColors.primary,
                    borderWidth: 2,
                    borderRadius: 6,
                },
                {
                    label: 'Flujo Optimista (M$)',
                    data: [43.0, 24.4, 12.8],
                    backgroundColor: chartColors.success + '80',
                    borderColor: chartColors.success,
                    borderWidth: 2,
                    borderRadius: 6,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 10
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const probabilidad = context.datasetIndex === 0 ? [85, 70, 50] : [95, 85, 70];
                            return [
                                context.dataset.label + ': $' + context.parsed.y.toFixed(1) + 'M',
                                'Probabilidad: ' + probabilidad[context.dataIndex] + '%'
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value + 'M';
                        }
                    }
                }
            }
        }
    });
}

// 3. Department Profitability Chart
// 3. Department Profit Chart - USANDO DATOS REALES
function initDepartmentProfitChart() {
    const ctx = document.getElementById('departmentProfitChart');
    if (!ctx) return;

    const data = getChartData();
    const profitData = data.operational_chart_data?.rendimiento_gestores || {};
    
    console.log('📊 Initializing Department Profit Chart with real data:', profitData);

    // Use real profitability data if available
    const gestores = data.profitability?.gestores || [];
    
    let labels = [];
    let valores = [];
    let colores = [];

    if (gestores.length > 0) {
        // Use real data
        gestores.slice(0, 8).forEach(gestor => {
            labels.push(gestor.gestor || 'Gestor');
            valores.push(gestor.margin_percentage || 0);
            
            // Color based on performance
            if (gestor.margin_percentage >= 25) {
                colores.push(chartColors.success);
            } else if (gestor.margin_percentage >= 15) {
                colores.push(chartColors.primary);
            } else if (gestor.margin_percentage >= 5) {
                colores.push(chartColors.warning);
            } else {
                colores.push(chartColors.danger);
            }
        });
    } else {
        // Fallback data
        labels = profitData.labels || ['Gestor A', 'Gestor B', 'Gestor C', 'Gestor D', 'Gestor E'];
        valores = profitData.datasets?.[0]?.data || [28.5, 22.3, 18.7, 15.2, 12.8];
        colores = valores.map(val => {
            if (val >= 25) return chartColors.success;
            if (val >= 15) return chartColors.primary;
            if (val >= 5) return chartColors.warning;
            return chartColors.danger;
        });
    }

    operationalCharts.departmentProfit = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Rentabilidad (%)',
                data: valores,
                backgroundColor: colores.map(c => c + '80'),
                borderColor: colores,
                borderWidth: 2,
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Rentabilidad: ' + context.parsed.x.toFixed(1) + '%';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 35,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// 4. Pareto Client Chart - USANDO DATOS REALES
function initParetoClientChart() {
    const ctx = document.getElementById('paretoClientChart');
    if (!ctx) return;

    const data = getChartData();
    const clientData = data.operational_chart_data?.concentracion_clientes || {};
    
    console.log('📊 Initializing Pareto Client Chart with real data:', clientData);

    operationalCharts.paretoClient = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: clientData.labels || ['Cliente A', 'Cliente B', 'Cliente C', 'Cliente D', 'Cliente E'],
            datasets: [
                {
                    type: 'bar',
                    label: 'Ingresos (M$)',
                    data: clientData.datasets?.[0]?.data || [45.2, 28.7, 18.3, 12.1, 8.9],
                    backgroundColor: chartColors.primary + '80',
                    borderColor: chartColors.primary,
                    borderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    type: 'line',
                    label: '% Acumulado',
                    data: clientData.datasets?.[1]?.data || [35, 58, 72, 82, 90],
                    borderColor: chartColors.warning,
                    backgroundColor: chartColors.warning + '20',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.2,
                    yAxisID: 'y1',
                    pointBackgroundColor: chartColors.warning,
                    pointBorderColor: chartColors.warning,
                    pointRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value + 'M';
                        }
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        }
    });
}

// 5. Aging Buckets Chart  
// 5. Aging Buckets Chart - USANDO DATOS REALES
function initAgingBucketsChart() {
    const ctx = document.getElementById('agingBucketsChart');
    if (!ctx) return;

    const data = getChartData();
    const agingData = data.operational_chart_data?.aging_buckets || data.aging || {};
    
    console.log('📊 Initializing Aging Buckets Chart with real data:', agingData);

    // Use real aging bucket data or chart data
    let bucketData;
    if (agingData.datasets && agingData.datasets[0] && agingData.datasets[0].data) {
        bucketData = agingData.datasets[0].data;
    } else if (data.aging?.buckets) {
        // Extract from aging.buckets structure
        const buckets = data.aging.buckets;
        bucketData = [
            buckets.bucket_0_30 || 45.2,
            buckets.bucket_31_60 || 28.7, 
            buckets.bucket_61_90 || 18.3,
            buckets.bucket_91_120 || 12.1,
            buckets.bucket_120_plus || 8.9
        ];
    } else {
        // Fallback data
        bucketData = [45.2, 28.7, 18.3, 12.1, 8.9];
    }

    operationalCharts.agingBuckets = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['0-30 días', '31-60 días', '61-90 días', '91-120 días', '+120 días'],
            datasets: [{
                data: bucketData,
                backgroundColor: [
                    chartColors.success + '80',
                    chartColors.primary + '80',
                    chartColors.warning + '80', 
                    chartColors.danger + '80',
                    '#7F1D1D80'
                ],
                borderColor: [
                    chartColors.success,
                    chartColors.primary,
                    chartColors.warning,
                    chartColors.danger,
                    '#7F1D1D'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': $' + context.parsed.toFixed(1) + 'M (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

// 6. DSO Trend Mini Chart
function initDSOTrendMini() {
    const ctx = document.getElementById('dsoTrendMini');
    if (!ctx) return;

    operationalCharts.dsoTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['', '', '', '', '', ''],
            datasets: [{
                data: [118, 122, 120, 125, 127, 124],
                borderColor: chartColors.danger,
                backgroundColor: chartColors.danger + '20',
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
}

// 7. Project Status Chart - USANDO DATOS REALES
function initProjectStatusChart() {
    const ctx = document.getElementById('projectStatusChart');
    if (!ctx) return;

    const data = getChartData();
    const statusData = data.operational_chart_data?.estado_proyectos || {};
    
    console.log('📊 Initializing Project Status Chart with real data:', statusData);

    operationalCharts.projectStatus = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: statusData.labels || ['A tiempo', 'En riesgo', 'Retrasados', 'Completados'],
            datasets: [{
                data: statusData.datasets?.[0]?.data || [45, 30, 25, 72],
                backgroundColor: [
                    chartColors.success + '80',
                    chartColors.warning + '80',
                    chartColors.danger + '80',
                    chartColors.primary + '80'
                ],
                borderColor: [
                    chartColors.success,
                    chartColors.warning,
                    chartColors.danger,
                    chartColors.primary
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + '%';
                        }
                    }
                }
            }
        }
    });
}

// 8. Project Bubble Chart (Risk Map)
function initProjectBubbleChart() {
    const ctx = document.getElementById('projectBubbleChart');
    if (!ctx) return;

    // Sample bubble data - in real implementation this would come from critical projects data
    const bubbleData = [
        { x: 15, y: 2.5, r: 8, label: 'Proyecto A', risk: 'Alto' },
        { x: 25, y: 1.8, r: 6, label: 'Proyecto B', risk: 'Medio' },
        { x: 45, y: 3.2, r: 10, label: 'Proyecto C', risk: 'Crítico' },
        { x: 35, y: 1.2, r: 4, label: 'Proyecto D', risk: 'Bajo' },
        { x: 55, y: 2.8, r: 7, label: 'Proyecto E', risk: 'Alto' }
    ];

    operationalCharts.projectBubble = new Chart(ctx, {
        type: 'bubble',
        data: {
            datasets: [{
                label: 'Proyectos',
                data: bubbleData,
                backgroundColor: function(context) {
                    const risk = context.raw.risk;
                    switch(risk) {
                        case 'Crítico': return chartColors.danger + '60';
                        case 'Alto': return chartColors.warning + '60';
                        case 'Medio': return chartColors.primary + '60';
                        case 'Bajo': return chartColors.success + '60';
                        default: return chartColors.gray + '60';
                    }
                },
                borderColor: function(context) {
                    const risk = context.raw.risk;
                    switch(risk) {
                        case 'Crítico': return chartColors.danger;
                        case 'Alto': return chartColors.warning;
                        case 'Medio': return chartColors.primary;
                        case 'Bajo': return chartColors.success;
                        default: return chartColors.gray;
                    }
                },
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const point = context.raw;
                            return [
                                point.label,
                                'Días: ' + point.x,
                                'Monto: $' + point.y + 'M',
                                'Riesgo: ' + point.risk
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Días de retraso'
                    },
                    beginAtZero: true
                },
                y: {
                    title: {
                        display: true,
                        text: 'Monto (M$)'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

// Chart view toggles and interactions
function initChartInteractions() {
    // Financial trend chart view toggle
    const financialButtons = document.querySelectorAll('[data-chart-view]');
    financialButtons.forEach(button => {
        button.addEventListener('click', function() {
            const view = this.dataset.chartView;
            
            // Update button states
            financialButtons.forEach(btn => {
                btn.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
                btn.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border', 'border-[color:var(--border-color)]');
            });
            
            this.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border', 'border-[color:var(--border-color)]');
            this.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
            
            // Update chart based on view
            // Implementation would update the chart data
            console.log('Switched to view:', view);
        });
    });

    // Project view toggle (chart vs bubble)
    const projectButtons = document.querySelectorAll('[data-view]');
    projectButtons.forEach(button => {
        button.addEventListener('click', function() {
            const view = this.dataset.view;
            
            // Update button states
            projectButtons.forEach(btn => {
                btn.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
                btn.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border', 'border-[color:var(--border-color)]');
            });
            
            this.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border', 'border-[color:var(--border-color)]');
            this.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
            
            // Toggle views
            const chartView = document.getElementById('project-chart-view');
            const bubbleView = document.getElementById('project-bubble-view');
            
            if (view === 'chart') {
                chartView.classList.remove('hidden');
                bubbleView.classList.add('hidden');
            } else {
                chartView.classList.add('hidden');
                bubbleView.classList.remove('hidden');
            }
        });
    });

    // Pareto client toggle
    const paretoButtons = document.querySelectorAll('[id^="pareto-toggle"]');
    paretoButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update button states
            paretoButtons.forEach(btn => {
                btn.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
                btn.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border', 'border-[color:var(--border-color)]');
            });
            
            this.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border', 'border-[color:var(--border-color)]');
            this.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
            
            // Update chart data based on selection
            const isIngresos = this.id === 'pareto-toggle-ingresos';
            console.log('Pareto view:', isIngresos ? 'ingresos' : 'pendiente');
        });
    });
}

// Initialize all charts
function initOperationalCharts() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(initOperationalCharts, 100);
        });
        return;
    }

    try {
        // Initialize ONLY ultra-operational components (removed all analysis/reporting)
        // Removed: initFinancialTrendChart (analysis chart, not operational)
        // Removed: initCashInForecastChart (chart removed, only alerts kept)
        // Removed: initDepartmentProfitChart (analysis, not operational)
        // Removed: initParetoClientChart (analysis, not operational)  
        // Removed: initAgingBucketsChart (chart removed, only alerts kept)
        // Removed: initDSOTrendMini (analysis, not operational)
        // Removed: initProjectStatusChart (performance metrics, not operational)
        // Removed: initProjectBubbleChart (performance metrics, not operational)
        initChartInteractions();
        
        console.log('✅ Ultra-operational dashboard initialized (no charts, only action buttons)');
    } catch (error) {
        console.error('❌ Error initializing operational dashboard:', error);
    }
}

// Cleanup function
function destroyOperationalCharts() {
    Object.values(operationalCharts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
}

// Operational Filters Management
class OperationalFilters {
    constructor() {
        this.form = document.getElementById('operationalFilters');
        if (!this.form) return;
        
        this.periodSelect = document.getElementById('filter_periodo');
        this.dateContainers = {
            inicio: document.getElementById('fecha_inicio_container'),
            fin: document.getElementById('fecha_fin_container')
        };
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateDateVisibility();
        this.markFieldsWithValues();
    }

    bindEvents() {
        // Period change handler
        if (this.periodSelect) {
            this.periodSelect.addEventListener('change', () => {
                this.updateDateVisibility();
            });
        }

        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.applyFilters();
        });

        // Reset filters
        const resetBtn = document.getElementById('resetFilters');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetFilters();
            });
        }

        // Refresh data
        const refreshBtn = document.getElementById('refreshData');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshData();
            });
        }

        // Save filters
        const saveBtn = document.getElementById('saveFilters');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveFilters();
            });
        }

        // Export data
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportData();
            });
        }

        // Mark fields with values on change
        this.form.addEventListener('change', () => {
            this.markFieldsWithValues();
        });
    }

    updateDateVisibility() {
        if (!this.periodSelect || !this.dateContainers.inicio || !this.dateContainers.fin) return;
        
        const isCustom = this.periodSelect.value === 'custom';
        
        this.dateContainers.inicio.style.display = isCustom ? 'block' : 'none';
        this.dateContainers.fin.style.display = isCustom ? 'block' : 'none';
    }

    markFieldsWithValues() {
        const inputs = this.form.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            const container = input.closest('.space-y-2');
            if (!container) return;

            const hasValue = input.type === 'date' ? 
                input.value !== '' : 
                (input.value !== '' && input.value !== 'todos');

            if (hasValue) {
                container.classList.add('filter-field', 'has-value');
            } else {
                container.classList.remove('has-value');
                container.classList.add('filter-field');
            }
        });
    }

    async applyFilters() {
        const formData = new FormData(this.form);
        const filters = Object.fromEntries(formData);
        
        // Show loading state
        this.setLoadingState(true);
        
        try {
            // Build query string
            const queryParams = new URLSearchParams();
            
            Object.entries(filters).forEach(([key, value]) => {
                if (value && value !== 'todos' && value !== '') {
                    queryParams.append(key, value);
                }
            });

            // Navigate to filtered URL
            const newUrl = `${window.location.pathname}?${queryParams.toString()}`;
            window.location.href = newUrl;
            
        } catch (error) {
            console.error('Error applying filters:', error);
            this.showMessage('Error al aplicar filtros', 'error');
            this.setLoadingState(false);
        }
    }

    resetFilters() {
        // Reset form to defaults
        this.form.reset();
        
        // Set default values
        const defaultValues = {
            'filter_periodo': '30',
            'filter_vista': 'general',
            'filter_departamento': 'todos',
            'filter_cliente': 'todos',
            'filter_estado': 'todos',
            'filter_gestor': 'todos'
        };
        
        Object.entries(defaultValues).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.value = value;
        });
        
        // Update UI
        this.updateDateVisibility();
        this.markFieldsWithValues();
        
        // Apply reset filters
        this.applyFilters();
    }

    async refreshData() {
        this.setLoadingState(true);
        
        try {
            // Add refresh parameter to current URL
            const url = new URL(window.location);
            url.searchParams.set('refresh', 'true');
            window.location.href = url.toString();
            
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showMessage('Error al actualizar datos', 'error');
            this.setLoadingState(false);
        }
    }

    saveFilters() {
        const formData = new FormData(this.form);
        const filters = Object.fromEntries(formData);
        
        // Remove empty/default values
        const cleanFilters = {};
        Object.entries(filters).forEach(([key, value]) => {
            if (value && value !== 'todos' && value !== '') {
                cleanFilters[key] = value;
            }
        });
        
        // Save to localStorage
        localStorage.setItem('operationalFilters', JSON.stringify(cleanFilters));
        
        this.showMessage('Vista guardada exitosamente', 'success');
    }

    async exportData() {
        this.setLoadingState(true);
        
        try {
            this.showMessage('Función de exportación en desarrollo', 'info');
        } catch (error) {
            console.error('Error exporting data:', error);
            this.showMessage('Error al exportar datos', 'error');
        } finally {
            this.setLoadingState(false);
        }
    }

    setLoadingState(loading) {
        const buttons = this.form.querySelectorAll('button');
        
        if (loading) {
            this.form.style.opacity = '0.6';
            buttons.forEach(btn => btn.disabled = true);
        } else {
            this.form.style.opacity = '1';
            buttons.forEach(btn => btn.disabled = false);
        }
    }

    showMessage(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg transition-all duration-300 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }
}

// Auto-initialize when script loads
initOperationalCharts();

// Initialize filters when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('operationalFilters')) {
        window.operationalFilters = new OperationalFilters();
    }
});

// Export for global access
window.operationalCharts = operationalCharts;
window.initOperationalCharts = initOperationalCharts;
window.destroyOperationalCharts = destroyOperationalCharts;

/* ========== OPERATIONAL DASHBOARD ENHANCED INTERACTIVITY ========== */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Operational Dashboard Enhanced - Loading...');
    
    // Initialize all enhanced features
    initializeCardAnimations();
    initializeCounterAnimations();
    initializeProgressAnimations();
    initializeHoverEffects();
    initializeDataRefresh();
    
    console.log('✅ All enhanced features loaded successfully');
});

/* ========== CARD ANIMATIONS ========== */
function initializeCardAnimations() {
    const cards = document.querySelectorAll('.group');
    
    // Add intersection observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 100);
            }
        });
    }, observerOptions);
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}

/* ========== COUNTER ANIMATIONS ========== */
function initializeCounterAnimations() {
    const counters = document.querySelectorAll('.text-4xl, .text-3xl, .text-2xl');
    
    counters.forEach(counter => {
        const text = counter.textContent;
        const number = parseFloat(text.replace(/[^\d.]/g, ''));
        
        if (!isNaN(number) && number > 0) {
            animateCounter(counter, 0, number, 2000, text);
        }
    });
}

function animateCounter(element, start, end, duration, originalText) {
    const increment = (end - start) / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            current = end;
            clearInterval(timer);
        }
        
        // Preserve original text format
        const newText = originalText.replace(/[\d.]+/, Math.floor(current).toString());
        element.textContent = newText;
    }, 16);
}

/* ========== PROGRESS ANIMATIONS ========== */
function initializeProgressAnimations() {
    // Animate progress rings
    const progressRings = document.querySelectorAll('[stroke-dasharray]');
    
    progressRings.forEach(ring => {
        const dashArray = ring.getAttribute('stroke-dasharray');
        const progress = parseFloat(dashArray.split(',')[0]);
        
        // Start from 0 and animate to target
        ring.setAttribute('stroke-dasharray', '0, 100');
        
        setTimeout(() => {
            ring.style.transition = 'stroke-dasharray 2s ease-in-out';
            ring.setAttribute('stroke-dasharray', dashArray);
        }, 500);
    });
    
    // Animate progress bars
    const progressBars = document.querySelectorAll('.w-1\\.5, .w-2');
    
    progressBars.forEach((bar, index) => {
        const originalHeight = bar.style.height || bar.classList.toString().match(/h-(\d+)/)?.[1];
        bar.style.height = '0';
        bar.style.transition = `height 0.8s ease-in-out ${index * 0.1}s`;
        
        setTimeout(() => {
            bar.style.height = originalHeight ? `${originalHeight * 0.25}rem` : bar.className.match(/h-(\d+)/)?.[0];
        }, 800);
    });
}

/* ========== ADVANCED HOVER EFFECTS ========== */
function initializeHoverEffects() {
    // Enhanced card hover effects with 3D transform
    const kpiCards = document.querySelectorAll('.h-\\[180px\\]');
    
    kpiCards.forEach(card => {
        card.addEventListener('mouseenter', function(e) {
            this.style.transform = 'translateY(-8px) scale(1.02) perspective(1000px) rotateX(5deg)';
            this.style.boxShadow = '0 25px 50px rgba(0, 0, 0, 0.2)';
            
            // Add glow effect
            const color = getComputedStyle(this).borderColor;
            this.style.boxShadow += `, 0 0 30px ${color}30`;
        });
        
        card.addEventListener('mouseleave', function(e) {
            this.style.transform = 'translateY(0) scale(1) perspective(1000px) rotateX(0deg)';
            this.style.boxShadow = '';
        });
        
        // Mouse move parallax effect
        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;
            
            const rotateX = (y - 0.5) * 10;
            const rotateY = (x - 0.5) * -10;
            
            this.style.transform = `translateY(-8px) scale(1.02) perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
    });
    
    // Button hover effects with ripple
    const buttons = document.querySelectorAll('button, a[class*="bg-"]');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                background-color: rgba(255, 255, 255, 0.6);
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

/* ========== DATA REFRESH SYSTEM ========== */
function initializeDataRefresh() {
    let refreshInterval;
    
    // Auto-refresh every 2 minutes
    refreshInterval = setInterval(() => {
        updateDashboardData();
    }, 120000);
    
    // Visual refresh indicator
    const refreshButton = document.querySelector('[onclick="location.reload()"]');
    if (refreshButton) {
        refreshButton.addEventListener('click', function(e) {
            e.preventDefault();
            showRefreshAnimation();
            setTimeout(() => {
                location.reload();
            }, 1000);
        });
    }
}

function updateDashboardData() {
    // Simulate data update with subtle animations
    const counters = document.querySelectorAll('.text-4xl, .text-3xl, .text-2xl');
    
    counters.forEach(counter => {
        counter.style.transform = 'scale(1.1)';
        counter.style.transition = 'transform 0.3s ease';
        
        setTimeout(() => {
            counter.style.transform = 'scale(1)';
        }, 300);
    });
    
    // Update timestamp
    const timestamp = document.querySelector('.font-bold.text-base');
    if (timestamp) {
        const now = new Date();
        const timeString = now.toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        timestamp.textContent = `Última actualización: Hoy ${timeString}`;
    }
}

function showRefreshAnimation() {
    const refreshIcon = document.querySelector('[onclick="location.reload()"] svg');
    if (refreshIcon) {
        refreshIcon.style.animation = 'spin 1s linear infinite';
    }
}

/* ========== REAL-TIME STATUS UPDATES ========== */
function initializeStatusIndicators() {
    const indicators = document.querySelectorAll('.animate-pulse, .animate-ping');
    
    indicators.forEach(indicator => {
        // Random pulse variations for more organic feel
        const randomDelay = Math.random() * 2;
        indicator.style.animationDelay = `${randomDelay}s`;
        
        // Occasionally change intensity
        setInterval(() => {
            const randomIntensity = 0.7 + Math.random() * 0.3;
            indicator.style.opacity = randomIntensity;
        }, 3000 + Math.random() * 2000);
    });
}

/* ========== CUSTOM CSS ANIMATIONS ========== */
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInScale {
        from {
            opacity: 0;
            transform: scale(0.8);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    .animate-slideInUp {
        animation: slideInUp 0.6s ease-out;
    }
    
    .animate-fadeInScale {
        animation: fadeInScale 0.5s ease-out;
    }
    
    /* Enhanced scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.1);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #5a67d8 0%, #6b46c1 100%);
    }
`;
document.head.appendChild(style);

/* ========== PERFORMANCE MONITORING ========== */
function initializePerformanceMonitoring() {
    // Monitor load times and provide feedback
    window.addEventListener('load', function() {
        const loadTime = performance.now();
        console.log(`📊 Dashboard loaded in ${Math.round(loadTime)}ms`);
        
        if (loadTime > 3000) {
            console.warn('⚠️ Dashboard loading slowly, consider optimizations');
        }
    });
    
    // Memory usage monitoring
    if ('memory' in performance) {
        setInterval(() => {
            const memory = performance.memory;
            if (memory.usedJSHeapSize > 50 * 1024 * 1024) { // 50MB
                console.warn('⚠️ High memory usage detected');
            }
        }, 60000);
    }
}

// Initialize performance monitoring
initializePerformanceMonitoring();

/* ========== EXPORT FUNCTIONS FOR GLOBAL ACCESS ========== */
window.OperationalDashboard = {
    refresh: updateDashboardData,
    showRefresh: showRefreshAnimation,
    initializeStatusIndicators: initializeStatusIndicators
};

console.log('🎨 Operational Dashboard Enhanced JS loaded successfully'); 