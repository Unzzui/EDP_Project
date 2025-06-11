/**
 * Analytics Dashboard JavaScript - Professional Version
 * Enhanced with thicker lines, vibrant colors, and improved chart styling
 */

// Global Chart.js configuration for professional appearance
Chart.defaults.font.family = "'Segoe UI', 'Roboto', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#ffffff';
Chart.defaults.backgroundColor = '#252a3a';

// Professional color palette
const CHART_COLORS = {
    primary: '#3b82f6',
    success: '#10b981', 
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    purple: '#8b5cf6',
    pink: '#ec4899',
    yellow: '#eab308',
    gradient: {
        blue: ['#3b82f6', '#1d4ed8'],
        green: ['#10b981', '#059669'],
        purple: ['#8b5cf6', '#7c3aed'],
        orange: ['#f59e0b', '#d97706']
    }
};

/**
 * Main Analytics Dashboard Class
 */
class AnalyticsDashboard {
    constructor(analyticsData) {
        this.analyticsData = analyticsData || this.getDefaultData();
        this.charts = {};
        this.init();
    }

    /**
     * Initialize the dashboard
     */
    init() {
        console.log('🎯 Initializing Analytics Dashboard with data:', this.analyticsData);
        
        // Add loading animations
        this.addLoadingStates();
        
        // Initialize charts with a small delay for better UX
        setTimeout(() => {
            this.initializeCharts();
            this.removeLoadingStates();
            this.setupEventListeners();
        }, 100);
        
        console.log('📊 Analytics Dashboard initialized successfully');
    }

    /**
     * Add loading states to chart containers
     */
    addLoadingStates() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.classList.add('loading');
        });
    }

    /**
     * Remove loading states from chart containers
     */
    removeLoadingStates() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.classList.remove('loading');
            container.classList.add('fade-in');
        });
    }

    /**
     * Initialize all charts
     */
    initializeCharts() {
        console.log('📈 Starting chart initialization...');
        
        try {
            this.createDSOEvolutionChart();
            this.createCorrelationMatrix();
            this.createCashFlowPrediction();
            this.createRiskAnalysis();
            this.createClientSegmentation();
            this.createSizeSegmentation();
            
            console.log('📈 All charts initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing charts:', error);
        }
    }

    /**
     * Create DSO Evolution Chart with thick lines and vibrant colors
     */
    createDSOEvolutionChart() {
        console.log('📊 Creating DSO Evolution Chart...');
        const ctx = document.getElementById('dsoEvolutionChart');
        
        if (!ctx) {
            console.warn('❌ DSO Evolution Chart canvas not found');
            return;
        }

        const labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'];
        const currentDSO = this.analyticsData.dso?.current_dso || 124;
        const targetDSO = this.analyticsData.dso?.target_dso || 90;
        
        // Generate sample data with realistic trend
        const actualData = [145, 138, 142, 135, 128, currentDSO];
        const targetData = new Array(6).fill(targetDSO);
        const predictedData = [null, null, null, null, currentDSO, currentDSO - 6, currentDSO - 12];

        this.charts.dsoEvolution = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'DSO Actual',
                        data: actualData,
                        borderColor: CHART_COLORS.primary,
                        backgroundColor: `${CHART_COLORS.primary}20`,
                        borderWidth: 4, // Thick line
                        pointRadius: 6, // Visible data points
                        pointHoverRadius: 8,
                        pointBackgroundColor: CHART_COLORS.primary,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'DSO Objetivo',
                        data: targetData,
                        borderColor: CHART_COLORS.success,
                        backgroundColor: `${CHART_COLORS.success}15`,
                        borderWidth: 3,
                        borderDash: [5, 5],
                        pointRadius: 4,
                        pointBackgroundColor: CHART_COLORS.success,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        tension: 0
                    },
                    {
                        label: 'Predicción',
                        data: [...actualData.slice(0, 4), ...predictedData.slice(4)],
                        borderColor: CHART_COLORS.warning,
                        backgroundColor: `${CHART_COLORS.warning}20`,
                        borderWidth: 4,
                        borderDash: [10, 5],
                        pointRadius: 6,
                        pointBackgroundColor: CHART_COLORS.warning,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#ffffff',
                            font: { weight: 'bold', size: 12 },
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1a1d29',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#ffffff',
                            font: { weight: 'bold' },
                            callback: function(value) {
                                return value + ' días';
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#ffffff',
                            font: { weight: 'bold' }
                        }
                    }
                },
                elements: {
                    line: {
                        borderCapStyle: 'round',
                        borderJoinStyle: 'round'
                    }
                }
            }
        });

        console.log('✅ DSO Evolution Chart created successfully');
    }

    /**
     * Create enhanced Correlation Matrix with vibrant colors
     */
    createCorrelationMatrix() {
        console.log('📊 Creating Correlation Matrix...');
        const ctx = document.getElementById('correlationChart');
        
        if (!ctx) {
            console.warn('❌ Correlation Matrix canvas not found');
            return;
        }

        const correlationData = this.analyticsData.correlations?.key_correlations || [
            {"metric1": "DSO", "metric2": "Rentabilidad", "correlation": -0.72},
            {"metric1": "Volumen", "metric2": "Eficiencia", "correlation": 0.65},
            {"metric1": "Días de Proceso", "metric2": "Satisfacción Cliente", "correlation": -0.58}
        ];

        this.charts.correlation = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: correlationData.map(item => `${item.metric1} vs ${item.metric2}`),
                datasets: [{
                    label: 'Correlación',
                    data: correlationData.map(item => item.correlation),
                    backgroundColor: correlationData.map(item => 
                        item.correlation > 0 ? CHART_COLORS.success : CHART_COLORS.danger
                    ),
                    borderColor: correlationData.map(item => 
                        item.correlation > 0 ? CHART_COLORS.success : CHART_COLORS.danger
                    ),
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1a1d29',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                const strength = Math.abs(value) > 0.7 ? 'Fuerte' : 
                                                Math.abs(value) > 0.4 ? 'Moderada' : 'Débil';
                                const direction = value > 0 ? 'Positiva' : 'Negativa';
                                return `Correlación: ${value.toFixed(2)} (${strength} ${direction})`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        min: -1,
                        max: 1,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#ffffff',
                            font: { weight: 'bold' },
                            callback: function(value) {
                                return value.toFixed(1);
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#ffffff',
                            font: { weight: 'bold' },
                            maxRotation: 45
                        }
                    }
                }
            }
        });

        console.log('✅ Correlation Matrix created successfully');
    }

    /**
     * Create Cash Flow Prediction Chart with professional styling
     */
    createCashFlowPrediction() {
        console.log('📊 Creating Cash Flow Prediction Chart...');
        const ctx = document.getElementById('cashFlowChart');
        
        if (!ctx) {
            console.warn('❌ Cash Flow Prediction canvas not found');
            return;
        }

        const months = ['Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        const predicted = [32.5, 35.2, 38.5, 41.2, 44.8, 47.3];
        const lowerBound = [28.2, 30.8, 33.1, 35.9, 38.5, 41.0];
        const upperBound = [36.8, 39.6, 43.9, 46.5, 51.1, 53.6];

        this.charts.cashFlow = new Chart(ctx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Predicción',
                        data: predicted,
                        borderColor: CHART_COLORS.info,
                        backgroundColor: `${CHART_COLORS.info}30`,
                        borderWidth: 4,
                        pointRadius: 6,
                        pointBackgroundColor: CHART_COLORS.info,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Rango Inferior',
                        data: lowerBound,
                        borderColor: CHART_COLORS.warning,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [3, 3],
                        pointRadius: 3,
                        pointBackgroundColor: CHART_COLORS.warning,
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'Rango Superior',
                        data: upperBound,
                        borderColor: CHART_COLORS.success,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [3, 3],
                        pointRadius: 3,
                        pointBackgroundColor: CHART_COLORS.success,
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#ffffff',
                            font: { weight: 'bold', size: 11 },
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1a1d29',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#06b6d4',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: $${context.parsed.y.toFixed(1)}M`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#ffffff',
                            font: { weight: 'bold' },
                            callback: function(value) {
                                return '$' + value.toFixed(1) + 'M';
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#ffffff',
                            font: { weight: 'bold' }
                        }
                    }
                }
            }
        });

        console.log('✅ Cash Flow Prediction Chart created successfully');
    }

    /**
     * Create Risk Analysis Chart with enhanced styling
     */
    createRiskAnalysis() {
        console.log('📊 Creating Risk Analysis Chart...');
        const ctx = document.getElementById('riskChart');
        
        if (!ctx) {
            console.warn('❌ Risk Analysis canvas not found');
            return;
        }

        const riskCategories = ['Bajo Riesgo', 'Riesgo Medio', 'Alto Riesgo', 'Crítico'];
        const riskCounts = [22, 15, 8, 3];
        const riskColors = [CHART_COLORS.success, CHART_COLORS.warning, CHART_COLORS.danger, '#8b0000'];

        this.charts.risk = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: riskCategories,
                datasets: [{
                    data: riskCounts,
                    backgroundColor: riskColors,
                    borderColor: riskColors,
                    borderWidth: 3,
                    hoverBorderWidth: 4,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: '#ffffff',
                            font: { weight: 'bold', size: 11 },
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1a1d29',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} proyectos (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

        console.log('✅ Risk Analysis Chart created successfully');
    }

    /**
     * Create Client Segmentation Chart with vibrant colors
     */
    createClientSegmentation() {
        console.log('📊 Creating Client Segmentation Chart...');
        const ctx = document.getElementById('clientSegmentChart');
        
        if (!ctx) {
            console.warn('❌ Client Segmentation canvas not found');
            return;
        }

        const segments = this.analyticsData.segmentation?.client_segments || [
            {"name": "Premium", "count": 12, "dso": 68, "revenue": 45, "risk": "low"},
            {"name": "Estándar", "count": 28, "dso": 95, "revenue": 35, "risk": "medium"},
            {"name": "Básico", "count": 15, "dso": 145, "revenue": 20, "risk": "high"}
        ];

        this.charts.clientSegment = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: segments.map(s => s.name),
                datasets: [
                    {
                        label: 'Número de Clientes',
                        data: segments.map(s => s.count),
                        backgroundColor: CHART_COLORS.primary,
                        borderColor: CHART_COLORS.primary,
                        borderWidth: 2,
                        borderRadius: 6,
                        yAxisID: 'y'
                    },
                    {
                        label: 'DSO Promedio',
                        data: segments.map(s => s.dso),
                        backgroundColor: CHART_COLORS.warning,
                        borderColor: CHART_COLORS.warning,
                        borderWidth: 2,
                        borderRadius: 6,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#ffffff',
                            font: { weight: 'bold', size: 11 },
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1a1d29',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#ffffff',
                            font: { weight: 'bold' }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            color: '#ffffff',
                            font: { weight: 'bold' },
                            callback: function(value) {
                                return value + ' días';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
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
        console.log('📊 Creating Size Segmentation Chart...');
        const ctx = document.getElementById('sizeSegmentChart');
        
        if (!ctx) {
            console.warn('❌ Size Segmentation canvas not found');
            return;
        }

        const sizeSegments = this.analyticsData.segmentation?.size_segments || [
            {"name": "Grande", "count": 8, "revenue": 60, "margin": 18},
            {"name": "Mediano", "count": 25, "revenue": 30, "margin": 22},
            {"name": "Pequeño", "count": 22, "revenue": 10, "margin": 15}
        ];

        this.charts.sizeSegment = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: sizeSegments.map(s => s.name),
                datasets: [{
                    data: sizeSegments.map(s => s.revenue),
                    backgroundColor: [CHART_COLORS.primary, CHART_COLORS.purple, CHART_COLORS.success],
                    borderColor: [CHART_COLORS.primary, CHART_COLORS.purple, CHART_COLORS.success],
                    borderWidth: 3,
                    hoverBorderWidth: 4,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '50%',
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: '#ffffff',
                            font: { weight: 'bold', size: 11 },
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1a1d29',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${percentage}% (${context.parsed}% ingresos)`;
                            }
                        }
                    }
                }
            }
        });

        console.log('✅ Size Segmentation Chart created successfully');
    }

    /**
     * Setup event listeners for interactive features
     */
    setupEventListeners() {
        // Filter change handlers
        const periodFilter = document.getElementById('periodFilter');
        const segmentFilter = document.getElementById('segmentFilter');
        const metricFilter = document.getElementById('metricFilter');

        if (periodFilter) {
            periodFilter.addEventListener('change', () => this.updateChartsForPeriod());
        }

        if (segmentFilter) {
            segmentFilter.addEventListener('change', () => this.updateChartsForSegment());
        }

        if (metricFilter) {
            metricFilter.addEventListener('change', () => this.updateChartsForMetric());
        }

        console.log('✅ Event listeners setup completed');
    }

    /**
     * Update charts based on period filter
     */
    updateChartsForPeriod() {
        console.log('🔄 Updating charts for period change...');
        // Implementation for period-based updates
        this.addLoadingStates();
        setTimeout(() => {
            this.initializeCharts();
            this.removeLoadingStates();
        }, 500);
    }

    /**
     * Update charts based on segment filter
     */
    updateChartsForSegment() {
        console.log('🔄 Updating charts for segment change...');
        // Implementation for segment-based updates
        this.addLoadingStates();
        setTimeout(() => {
            this.initializeCharts();
            this.removeLoadingStates();
        }, 500);
    }

    /**
     * Update charts based on metric filter
     */
    updateChartsForMetric() {
        console.log('🔄 Updating charts for metric change...');
        // Implementation for metric-based updates
        this.addLoadingStates();
        setTimeout(() => {
            this.initializeCharts();
            this.removeLoadingStates();
        }, 500);
    }

    /**
     * Get default analytics data if none provided
     */
    getDefaultData() {
        return {
            dso: {
                current_dso: 124,
                target_dso: 90,
                trend: -2.3,
                variance: 34,
                predicted_dso: 118
            },
            correlations: {
                key_correlations: [
                    {"metric1": "DSO", "metric2": "Rentabilidad", "correlation": -0.72},
                    {"metric1": "Volumen", "metric2": "Eficiencia", "correlation": 0.65},
                    {"metric1": "Días de Proceso", "metric2": "Satisfacción Cliente", "correlation": -0.58}
                ]
            },
            predictions: {
                cash_flow_30d: 38500000,
                confidence: 85.2,
                risk_score: 4.8,
                projects_at_risk: 6
            },
            segmentation: {
                client_segments: [
                    {"name": "Premium", "count": 12, "dso": 68, "revenue": 45, "risk": "low"},
                    {"name": "Estándar", "count": 28, "dso": 95, "revenue": 35, "risk": "medium"},
                    {"name": "Básico", "count": 15, "dso": 145, "revenue": 20, "risk": "high"}
                ],
                size_segments: [
                    {"name": "Grande", "count": 8, "revenue": 60, "margin": 18},
                    {"name": "Mediano", "count": 25, "revenue": 30, "margin": 22},
                    {"name": "Pequeño", "count": 22, "revenue": 10, "margin": 15}
                ]
            }
        };
    }

    /**
     * Destroy all charts
     */
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
        console.log('🗑️ Analytics Dashboard destroyed');
    }
}

/**
 * Global function to update analytics (called by the Update button)
 */
function updateAnalytics() {
    console.log('🔄 Updating analytics dashboard...');
    if (window.analyticsDashboard) {
        window.analyticsDashboard.addLoadingStates();
        setTimeout(() => {
            window.analyticsDashboard.initializeCharts();
            window.analyticsDashboard.removeLoadingStates();
        }, 1000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM loaded, initializing Analytics Dashboard...');
    
    // Get analytics data from the script tag
    const analyticsDataScript = document.getElementById('analytics-data');
    let analyticsData = {};
    
    if (analyticsDataScript) {
        try {
            analyticsData = JSON.parse(analyticsDataScript.textContent);
            console.log('📊 Analytics data loaded successfully:', analyticsData);
        } catch (error) {
            console.warn('⚠️ Error parsing analytics data, using defaults:', error);
        }
    }
    
    // Initialize the dashboard
    window.analyticsDashboard = new AnalyticsDashboard(analyticsData);
});

// Export for module environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsDashboard;
}
