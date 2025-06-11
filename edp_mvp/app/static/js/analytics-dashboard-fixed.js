/** * Analytics Dashboard JavaScript - Professional Version * Enhanced with thicker lines, vibrant colors, and improved chart styling */// Global Chart.js configuration for professional appearanceChart.defaults.font.family = "'Segoe UI', 'Roboto', sans-serif";Chart.defaults.font.size = 12;Chart.defaults.color = '#ffffff';Chart.defaults.backgroundColor = '#252a3a';// Professional color paletteconst CHART_COLORS = {    primary: '#3b82f6',    success: '#10b981',     warning: '#f59e0b',    danger: '#ef4444',    info: '#06b6d4',    purple: '#8b5cf6',    pink: '#ec4899',    yellow: '#eab308',    gradient: {        blue: ['#3b82f6', '#1d4ed8'],        green: ['#10b981', '#059669'],        purple: ['#8b5cf6', '#7c3aed'],        orange: ['#f59e0b', '#d97706']    }};/** * Main Analytics Dashboard Class */class AnalyticsDashboard {    constructor(analyticsData) {        this.analyticsData = analyticsData || this.getDefaultData();        this.charts = {};        this.init();    }    /**     * Initialize the dashboard     */    init() {        console.log('🎯 Initializing Analytics Dashboard with data:', this.analyticsData);                // Add loading animations        this.addLoadingStates();                // Initialize charts with a small delay for better UX        setTimeout(() => {            this.initializeCharts();            this.removeLoadingStates();        }, 500);    }    /**     * Get default analytics data     */    getDefaultData() {        return {            dso: {                current_dso: 124,                target_dso: 90,                trend: -2.3,                variance: 34,                predicted_dso: 118,                insights: "DSO actual está por encima del objetivo"            },            correlations: {                key_correlations: [                    {"metric1": "DSO", "metric2": "Rentabilidad", "correlation": -0.72},                    {"metric1": "Volumen", "metric2": "Eficiencia", "correlation": 0.65},                    {"metric1": "Días de Proceso", "metric2": "Satisfacción Cliente", "correlation": -0.58}                ]            },            predictions: {                cash_flow_30d: 38500000,                confidence: 85.2,                risk_score: 4.8,                projects_at_risk: 6            },            segmentation: {                client_segments: [                    {"name": "Premium", "count": 12, "dso": 68, "revenue": 45, "risk": "low"},                    {"name": "Estándar", "count": 28, "dso": 95, "revenue": 35, "risk": "medium"},                    {"name": "Básico", "count": 15, "dso": 145, "revenue": 20, "risk": "high"}                ],                size_segments: [                    {"name": "Grande", "count": 8, "revenue": 60, "margin": 18},                    {"name": "Mediano", "count": 25, "revenue": 30, "margin": 22},                    {"name": "Pequeño", "count": 22, "revenue": 10, "margin": 15}                ]            }        };    }    /**     * Add loading states to charts     */    addLoadingStates() {        const chartContainers = document.querySelectorAll('.chart-canvas');        chartContainers.forEach(container => {            const loadingOverlay = document.createElement('div');            loadingOverlay.className = 'loading-overlay';            loadingOverlay.innerHTML = `                <div class="loading-spinner"></div>                <div class="loading-text">Cargando análisis...</div>            `;            container.appendChild(loadingOverlay);        });    }    /**     * Remove loading states     */    removeLoadingStates() {        const loadingOverlays = document.querySelectorAll('.loading-overlay');        loadingOverlays.forEach(overlay => {            overlay.remove();        });    }    /**     * Initialize all charts     */    initializeCharts() {        try {            this.createDSOEvolutionChart();            this.createCorrelationMatrix();            this.createCashFlowPrediction();            this.createRiskAnalysis();            this.createClientSegmentation();            this.createSizeSegmentation();            console.log('✅ All charts initialized successfully');        } catch (error) {            console.error('❌ Error initializing charts:', error);        }    }    /**     * Create DSO Evolution Chart with Professional Styling     */    createDSOEvolutionChart() {        const ctx = document.getElementById('dsoEvolutionChart');        if (!ctx) {            console.warn('DSO Evolution chart canvas not found');            return;        }        // Generate sample time series data        const last30Days = Array.from({length: 30}, (_, i) => {            const date = new Date();            date.setDate(date.getDate() - (29 - i));            return date;        });        const dsoData = last30Days.map((date, i) => {            const baseValue = this.analyticsData.dso.current_dso;            const variation = Math.sin(i * 0.3) * 8 + Math.random() * 6 - 3;            return Math.max(60, baseValue + variation);        });        const targetData = last30Days.map(() => this.analyticsData.dso.target_dso);        const predictedData = last30Days.slice(-7).map((date, i) => {            const trend = -0.8; // Improving trend            return dsoData[dsoData.length - 7 + i] + (trend * i);        });        this.charts.dsoEvolution = new Chart(ctx, {            type: 'line',            data: {                labels: last30Days.map(date => date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' })),                datasets: [                    {                        label: 'DSO Real',                        data: dsoData,                        borderColor: CHART_COLORS.primary,                        backgroundColor: `${CHART_COLORS.primary}20`,                        borderWidth: 4, // Thick line                        fill: true,                        tension: 0.4,                        pointRadius: 6,                        pointHoverRadius: 8,                        pointBackgroundColor: CHART_COLORS.primary,                        pointBorderColor: '#ffffff',                        pointBorderWidth: 2                    },                    {                        label: 'Objetivo',                        data: targetData,                        borderColor: CHART_COLORS.success,                        backgroundColor: `${CHART_COLORS.success}10`,                        borderWidth: 3,                        borderDash: [8, 4],                        fill: false,                        pointRadius: 0                    },                    {                        label: 'Predicción (7d)',                        data: [...Array(23).fill(null), ...predictedData],                        borderColor: CHART_COLORS.purple,                        backgroundColor: `${CHART_COLORS.purple}20`,                        borderWidth: 3,                        borderDash: [4, 4],                        fill: false,                        pointRadius: 5,                        pointBackgroundColor: CHART_COLORS.purple                    }                ]            },            options: {                responsive: true,                maintainAspectRatio: false,                plugins: {                    legend: {                        position: 'top',                        labels: {                            color: '#ffffff',                            font: { size: 14, weight: 'bold' },                            usePointStyle: true,                            padding: 20                        }                    },                    title: {                        display: false                    },                    tooltip: {                        mode: 'index',                        intersect: false,                        backgroundColor: 'rgba(0, 0, 0, 0.8)',                        titleColor: '#ffffff',                        bodyColor: '#ffffff',                        borderColor: CHART_COLORS.primary,                        borderWidth: 1                    }                },                interaction: {                    mode: 'nearest',                    axis: 'x',                    intersect: false                },                scales: {                    x: {                        display: true,                        grid: {                            color: 'rgba(255, 255, 255, 0.1)',                            lineWidth: 1                        },                        ticks: {                            color: '#ffffff',                            font: { weight: 'bold' }                        }                    },                    y: {                        display: true,                        grid: {                            color: 'rgba(255, 255, 255, 0.1)',                            lineWidth: 1                        },                        ticks: {                            color: '#ffffff',                            font: { weight: 'bold' },                            callback: function(value) {                                return value + 'd';                            }                        }                    }                }            }        });        console.log('✅ DSO Evolution Chart created successfully');    }    /**     * Create Correlation Matrix     */    createCorrelationMatrix() {        const ctx = document.getElementById('correlationChart');        if (!ctx) {            console.warn('Correlation chart canvas not found');            return;        }        const correlations = this.analyticsData.correlations.key_correlations;        const labels = correlations.map(c => `${c.metric1} vs ${c.metric2}`);        const values = correlations.map(c => Math.abs(c.correlation));        const colors = correlations.map(c => {            if (Math.abs(c.correlation) > 0.7) return CHART_COLORS.danger;            if (Math.abs(c.correlation) > 0.5) return CHART_COLORS.warning;            return CHART_COLORS.success;        });        this.charts.correlation = new Chart(ctx, {            type: 'bar',            data: {                labels: labels,                datasets: [{                    label: 'Fuerza de Correlación',                    data: values,                    backgroundColor: colors.map(color => `${color}80`),                    borderColor: colors,                    borderWidth: 3,                    borderRadius: 8,                    borderSkipped: false                }]            },            options: {                responsive: true,                maintainAspectRatio: false,                plugins: {                    legend: {                        display: false                    },                    tooltip: {                        backgroundColor: 'rgba(0, 0, 0, 0.8)',                        titleColor: '#ffffff',                        bodyColor: '#ffffff',                        callbacks: {                            label: function(context) {                                const correlation = correlations[context.dataIndex];                                return `Correlación: ${correlation.correlation.toFixed(2)}`;                            }                        }                    }                },                scales: {                    x: {                        display: true,                        grid: {                            display: false                        },                        ticks: {                            color: '#ffffff',                            font: { weight: 'bold' },                            maxRotation: 45                        }                    },                    y: {                        display: true,                        grid: {                            color: 'rgba(255, 255, 255, 0.1)'                        },                        ticks: {                            color: '#ffffff',                            font: { weight: 'bold' },                            callback: function(value) {                                return (value * 100).toFixed(0) + '%';                            }                        },                        max: 1                    }                }            }        });        console.log('✅ Correlation Matrix created successfully');    }    /**     * Create Cash Flow Prediction Chart     */    createCashFlowPrediction() {        const ctx = document.getElementById('cashFlowChart');        if (!ctx) {            console.warn('Cash Flow chart canvas not found');            return;        }        // Generate next 12 months data        const months = Array.from({length: 12}, (_, i) => {            const date = new Date();            date.setMonth(date.getMonth() + i);            return date.toLocaleDateString('es-ES', { month: 'short', year: '2-digit' });        });        const baseFlow = this.analyticsData.predictions.cash_flow_30d;        const cashFlowData = months.map((_, i) => {            const seasonality = Math.sin(i * Math.PI / 6) * 0.2;            const growth = i * 0.05;            const variance = (Math.random() - 0.5) * 0.1;            return baseFlow * (1 + seasonality + growth + variance);        });        this.charts.cashFlow = new Chart(ctx, {            type: 'line',            data: {                labels: months,                datasets: [{                    label: 'Flujo de Caja Predicho',                    data: cashFlowData,                    borderColor: CHART_COLORS.info,                    backgroundColor: `${CHART_COLORS.info}30`,                    borderWidth: 4,                    fill: true,                    tension: 0.4,                    pointRadius: 6,                    pointHoverRadius: 8,                    pointBackgroundColor: CHART_COLORS.info,                    pointBorderColor: '#ffffff',                    pointBorderWidth: 2                }]            },            options: {                responsive: true,                maintainAspectRatio: false,                plugins: {                    legend: {                        labels: {                            color: '#ffffff',                            font: { size: 14, weight: 'bold' }                        }                    },                    tooltip: {                        backgroundColor: 'rgba(0, 0, 0, 0.8)',                        titleColor: '#ffffff',                        bodyColor: '#ffffff',                        callbacks: {                            label: function(context) {                                return `€${(context.parsed.y / 1000000).toFixed(1)}M`;                            }                        }                    }                },                scales: {                    x: {                        grid: {                            color: 'rgba(255, 255, 255, 0.1)'                        },                        ticks: {                            color: '#ffffff',                            font: { weight: 'bold' }                        }                    },                    y: {                        grid: {                            color: 'rgba(255, 255, 255, 0.1)'                        },                        ticks: {                            color: '#ffffff',                            font: { weight: 'bold' },                            callback: function(value) {                                return '€' + (value / 1000000).toFixed(1) + 'M';                            }                        }                    }                }
            }
        });

        console.log('✅ Cash Flow Prediction Chart created successfully');
    }

    /**
     * Create Risk Analysis Chart
     */
    createRiskAnalysis() {
        const ctx = document.getElementById('riskChart');
        if (!ctx) {
            console.warn('Risk chart canvas not found');
            return;
        }

        const riskData = [
            { label: 'Bajo Riesgo', value: 65, color: CHART_COLORS.success },
            { label: 'Riesgo Medio', value: 25, color: CHART_COLORS.warning },
            { label: 'Alto Riesgo', value: 10, color: CHART_COLORS.danger }
        ];

        this.charts.risk = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: riskData.map(d => d.label),
                datasets: [{
                    data: riskData.map(d => d.value),
                    backgroundColor: riskData.map(d => `${d.color}80`),
                    borderColor: riskData.map(d => d.color),
                    borderWidth: 3,
                    hoverBorderWidth: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#ffffff',
                            font: { size: 13, weight: 'bold' },
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.parsed}%`;
                            }
                        }
                    }
                }
            }
        });

        console.log('✅ Risk Analysis Chart created successfully');
    }

    /**
     * Create Client Segmentation Chart
     */
    createClientSegmentation() {
        const ctx = document.getElementById('clientSegmentChart');
        if (!ctx) {
            console.warn('Client Segment chart canvas not found');
            return;
        }

        const segments = this.analyticsData.segmentation.client_segments;
        
        this.charts.clientSegment = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: segments.map(s => s.name),
                datasets: [
                    {
                        label: 'DSO (días)',
                        data: segments.map(s => s.dso),
                        backgroundColor: `${CHART_COLORS.primary}80`,
                        borderColor: CHART_COLORS.primary,
                        borderWidth: 2,
                        borderRadius: 6
                    },
                    {
                        label: 'Revenue (%)',
                        data: segments.map(s => s.revenue),
                        backgroundColor: `${CHART_COLORS.success}80`,
                        borderColor: CHART_COLORS.success,
                        borderWidth: 2,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff',
                            font: { size: 13, weight: 'bold' }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff'
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#ffffff',
                            font: { weight: 'bold' }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#ffffff',
                            font: { weight: 'bold' }
                        }
                    }
                }
            }
        });

        console.log('✅ Client Segmentation Chart created successfully');
    }

    /**
     * Create Size Segmentation Chart
     */
    createSizeSegmentation() {
        const ctx = document.getElementById('sizeSegmentChart');
        if (!ctx) {
            console.warn('Size Segment chart canvas not found');
            return;
        }

        const segments = this.analyticsData.segmentation.size_segments;
        
        this.charts.sizeSegment = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: segments.map(s => s.name),
                datasets: [{
                    data: segments.map(s => s.revenue),
                    backgroundColor: [
                        `${CHART_COLORS.purple}80`,
                        `${CHART_COLORS.info}80`,
                        `${CHART_COLORS.warning}80`
                    ],
                    borderColor: [
                        CHART_COLORS.purple,
                        CHART_COLORS.info,
                        CHART_COLORS.warning
                    ],
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '50%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#ffffff',
                            font: { size: 13, weight: 'bold' },
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.parsed}%`;
                            }
                        }
                    }
                }
            }
        });

        console.log('✅ Size Segmentation Chart created successfully');
    }

    /**
     * Update analytics data and refresh charts
     */
    updateAnalytics() {
        console.log('🔄 Updating analytics...');
        
        // Add loading states
        this.addLoadingStates();
        
        // Simulate API call delay
        setTimeout(() => {
            // Here you would typically fetch new data from the server
            // For now, we'll just refresh with current data
            this.destroyCharts();
            this.initializeCharts();
            this.removeLoadingStates();
            
            console.log('✅ Analytics updated successfully');
        }, 1000);
    }

    /**
     * Destroy all charts
     */
    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    /**
     * Add event listeners
     */
    addEventListeners() {
        // Update button
        const updateBtn = document.querySelector('[onclick="updateAnalytics()"]');
        if (updateBtn) {
            updateBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.updateAnalytics();
            });
        }

        // Filter changes
        const filters = document.querySelectorAll('#periodFilter, #segmentFilter, #metricFilter');
        filters.forEach(filter => {
            filter.addEventListener('change', () => {
                this.updateAnalytics();
            });
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌟 DOM loaded, initializing Analytics Dashboard...');
    
    try {
        // Get analytics data from script tag
        const analyticsDataElement = document.getElementById('analytics-data');
        let analyticsData = null;
        
        if (analyticsDataElement) {
            try {
                analyticsData = JSON.parse(analyticsDataElement.textContent);
                console.log('📊 Analytics data loaded from template:', analyticsData);
            } catch (e) {
                console.warn('⚠️ Failed to parse analytics data from template:', e);
            }
        }
        
        // Initialize dashboard
        window.analyticsInstance = new AnalyticsDashboard(analyticsData);
        window.analyticsInstance.addEventListeners();
        
        console.log('🎉 Analytics Dashboard initialized successfully!');
        
    } catch (error) {
        console.error('❌ Failed to initialize Analytics Dashboard:', error);
        
        // Show error message to user
        const errorDiv = document.createElement('div');
        errorDiv.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <h4 class="alert-heading">Error de Inicialización</h4>
                <p>No se pudo cargar el dashboard de análisis. Por favor, recarga la página o contacta al soporte técnico.</p>
                <hr>
                <p class="mb-0"><small>Error: ${error.message}</small></p>
            </div>
        `;
        
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertBefore(errorDiv, container.firstChild);
        }
    }
});

// Global function for update button (backward compatibility)
function updateAnalytics() {
    if (window.analyticsInstance) {
        window.analyticsInstance.updateAnalytics();
    } else {
        console.error('❌ Analytics instance not found');
    }
}

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsDashboard;
}
