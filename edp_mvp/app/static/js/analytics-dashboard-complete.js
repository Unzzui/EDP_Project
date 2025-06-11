/**
 * Analytics Dashboard JavaScript
 * Handles all chart rendering and interactive features for the Analytics Dashboard
 */

// Global Chart.js configuration
Chart.defaults.font.family = "'Segoe UI', 'Roboto', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#5a5c69';

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
     * Create DSO Evolution Chart
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

        try {
            this.charts.dsoEvolution = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'DSO Actual',
                            data: actualData,
                            borderColor: '#dc3545',
                            backgroundColor: 'rgba(220, 53, 69, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#dc3545',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                            pointRadius: 5
                        },
                        {
                            label: 'DSO Objetivo',
                            data: targetData,
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            fill: false,
                            pointRadius: 0
                        },
                        {
                            label: 'Predicción',
                            data: predictedData,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            borderWidth: 2,
                            borderDash: [3, 3],
                            fill: false,
                            pointBackgroundColor: '#667eea',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                            pointRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#667eea',
                            borderWidth: 1,
                            cornerRadius: 6,
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.parsed.y} días`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            min: 60,
                            max: 160,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return value + ' días';
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
            
            console.log('✅ DSO Evolution Chart created successfully');
        } catch (error) {
            console.error('❌ Error creating DSO Evolution Chart:', error);
        }
    }

    /**
     * Create Correlation Matrix Chart
     */
    createCorrelationMatrix() {
        console.log('📊 Creating Correlation Matrix...');
        const ctx = document.getElementById('correlationMatrix');
        
        if (!ctx) {
            console.warn('❌ Correlation Matrix canvas not found');
            return;
        }

        const correlations = this.analyticsData.correlations?.key_correlations || [
            {metric1: "DSO", metric2: "Rentabilidad", correlation: -0.72},
            {metric1: "Volumen", metric2: "Eficiencia", correlation: 0.65},
            {metric1: "Proceso", metric2: "Satisfacción", correlation: -0.58}
        ];

        try {
            this.charts.correlationMatrix = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: correlations.map(c => `${c.metric1} vs ${c.metric2}`),
                    datasets: [{
                        label: 'Correlación',
                        data: correlations.map(c => c.correlation),
                        backgroundColor: correlations.map(c => {
                            const abs = Math.abs(c.correlation);
                            if (abs > 0.7) return c.correlation > 0 ? '#28a745' : '#dc3545';
                            if (abs > 0.5) return c.correlation > 0 ? '#17a2b8' : '#fd7e14';
                            return '#6c757d';
                        }),
                        borderColor: correlations.map(c => {
                            const abs = Math.abs(c.correlation);
                            if (abs > 0.7) return c.correlation > 0 ? '#1e7e34' : '#bd2130';
                            if (abs > 0.5) return c.correlation > 0 ? '#117a8b' : '#e55d0a';
                            return '#495057';
                        }),
                        borderWidth: 2,
                        borderRadius: 4
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
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y;
                                    const strength = Math.abs(value) > 0.7 ? 'Fuerte' : 
                                                   Math.abs(value) > 0.5 ? 'Moderada' : 'Débil';
                                    const direction = value > 0 ? 'Positiva' : 'Negativa';
                                    return `Correlación: ${value.toFixed(2)} (${strength} ${direction})`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            min: -1,
                            max: 1,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
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
                                maxRotation: 45,
                                minRotation: 45
                            }
                        }
                    }
                }
            });
            
            console.log('✅ Correlation Matrix created successfully');
        } catch (error) {
            console.error('❌ Error creating Correlation Matrix:', error);
        }
    }

    /**
     * Create Cash Flow Prediction Chart
     */
    createCashFlowPrediction() {
        console.log('📊 Creating Cash Flow Prediction...');
        const ctx = document.getElementById('cashFlowPrediction');
        
        if (!ctx) {
            console.warn('❌ Cash Flow Prediction canvas not found');
            return;
        }

        const baseCashFlow = this.analyticsData.predictions?.cash_flow_30d || 38500000;
        
        // Generate 12 weeks of prediction data
        const labels = [];
        const predictedData = [];
        const upperBound = [];
        const lowerBound = [];
        
        for (let i = 0; i < 12; i++) {
            const date = new Date();
            date.setDate(date.getDate() + (i * 7));
            labels.push(date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' }));
            
            // Simulate cash flow with some variability
            const variation = (Math.random() - 0.5) * 0.2;
            const predicted = baseCashFlow * (1 + variation + (i * 0.02));
            const confidence = 0.15; // 15% confidence interval
            
            predictedData.push(predicted / 1000000); // Convert to millions
            upperBound.push(predicted * (1 + confidence) / 1000000);
            lowerBound.push(predicted * (1 - confidence) / 1000000);
        }

        try {
            this.charts.cashFlowPrediction = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Predicción',
                            data: predictedData,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            borderWidth: 3,
                            fill: false,
                            tension: 0.4,
                            pointBackgroundColor: '#667eea',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                            pointRadius: 5
                        },
                        {
                            label: 'Límite Superior',
                            data: upperBound,
                            borderColor: 'rgba(102, 126, 234, 0.3)',
                            backgroundColor: 'rgba(102, 126, 234, 0.05)',
                            borderWidth: 1,
                            fill: '+1',
                            tension: 0.4,
                            pointRadius: 0
                        },
                        {
                            label: 'Límite Inferior',
                            data: lowerBound,
                            borderColor: 'rgba(102, 126, 234, 0.3)',
                            backgroundColor: 'rgba(102, 126, 234, 0.05)',
                            borderWidth: 1,
                            fill: false,
                            tension: 0.4,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                filter: function(legendItem, chartData) {
                                    return legendItem.datasetIndex === 0; // Only show main prediction line
                                }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            callbacks: {
                                label: function(context) {
                                    if (context.datasetIndex === 0) {
                                        return `Predicción: $${context.parsed.y.toFixed(1)}M`;
                                    }
                                    return null;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toFixed(1) + 'M';
                                }
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
            
            console.log('✅ Cash Flow Prediction created successfully');
        } catch (error) {
            console.error('❌ Error creating Cash Flow Prediction:', error);
        }
    }

    /**
     * Create Risk Analysis Chart
     */
    createRiskAnalysis() {
        console.log('📊 Creating Risk Analysis...');
        const ctx = document.getElementById('riskAnalysis');
        
        if (!ctx) {
            console.warn('❌ Risk Analysis canvas not found');
            return;
        }

        const riskData = [
            { level: 'Bajo', count: 25, color: '#28a745' },
            { level: 'Medio', count: 18, color: '#ffc107' },
            { level: 'Alto', count: 8, color: '#fd7e14' },
            { level: 'Crítico', count: 4, color: '#dc3545' }
        ];

        try {
            this.charts.riskAnalysis = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: riskData.map(r => r.level),
                    datasets: [{
                        data: riskData.map(r => r.count),
                        backgroundColor: riskData.map(r => r.color),
                        borderColor: '#fff',
                        borderWidth: 2,
                        hoverBorderWidth: 3
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
                                padding: 15,
                                usePointStyle: true
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
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
            
            console.log('✅ Risk Analysis created successfully');
        } catch (error) {
            console.error('❌ Error creating Risk Analysis:', error);
        }
    }

    /**
     * Create Client Segmentation Chart
     */
    createClientSegmentation() {
        console.log('📊 Creating Client Segmentation...');
        const ctx = document.getElementById('clientSegmentation');
        
        if (!ctx) {
            console.warn('❌ Client Segmentation canvas not found');
            return;
        }

        const segments = this.analyticsData.segmentation?.client_segments || [
            {name: "Premium", count: 12, dso: 68, revenue: 45, risk: "low"},
            {name: "Estándar", count: 28, dso: 95, revenue: 35, risk: "medium"},
            {name: "Básico", count: 15, dso: 145, revenue: 20, risk: "high"}
        ];

        try {
            this.charts.clientSegmentation = new Chart(ctx, {
                type: 'bubble',
                data: {
                    datasets: [{
                        label: 'Segmentos de Cliente',
                        data: segments.map(s => ({
                            x: s.dso,
                            y: s.revenue,
                            r: s.count,
                            segment: s.name,
                            risk: s.risk
                        })),
                        backgroundColor: segments.map(s => {
                            switch(s.risk) {
                                case 'low': return 'rgba(40, 167, 69, 0.6)';
                                case 'medium': return 'rgba(255, 193, 7, 0.6)';
                                case 'high': return 'rgba(220, 53, 69, 0.6)';
                                default: return 'rgba(108, 117, 125, 0.6)';
                            }
                        }),
                        borderColor: segments.map(s => {
                            switch(s.risk) {
                                case 'low': return '#28a745';
                                case 'medium': return '#ffc107';
                                case 'high': return '#dc3545';
                                default: return '#6c757d';
                            }
                        }),
                        borderWidth: 2
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
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            callbacks: {
                                title: function(context) {
                                    return context[0].raw.segment;
                                },
                                label: function(context) {
                                    const data = context.raw;
                                    return [
                                        `DSO: ${data.x} días`,
                                        `Revenue: ${data.y}%`,
                                        `Clientes: ${data.r}`,
                                        `Riesgo: ${data.risk}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'DSO (días)'
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Revenue (%)'
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        }
                    }
                }
            });
            
            console.log('✅ Client Segmentation created successfully');
        } catch (error) {
            console.error('❌ Error creating Client Segmentation:', error);
        }
    }

    /**
     * Create Size Segmentation Chart
     */
    createSizeSegmentation() {
        console.log('📊 Creating Size Segmentation...');
        const ctx = document.getElementById('sizeSegmentation');
        
        if (!ctx) {
            console.warn('❌ Size Segmentation canvas not found');
            return;
        }

        const segments = this.analyticsData.segmentation?.size_segments || [
            {name: "Grande", count: 8, revenue: 60, margin: 18},
            {name: "Mediano", count: 25, revenue: 30, margin: 22},
            {name: "Pequeño", count: 22, revenue: 10, margin: 15}
        ];

        try {
            this.charts.sizeSegmentation = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: segments.map(s => s.name),
                    datasets: [
                        {
                            label: 'Revenue (%)',
                            data: segments.map(s => s.revenue),
                            backgroundColor: 'rgba(102, 126, 234, 0.8)',
                            borderColor: '#667eea',
                            borderWidth: 2,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Margen (%)',
                            data: segments.map(s => s.margin),
                            backgroundColor: 'rgba(40, 167, 69, 0.8)',
                            borderColor: '#28a745',
                            borderWidth: 2,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.parsed.y}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Revenue (%)'
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Margen (%)'
                            },
                            grid: {
                                drawOnChartArea: false
                            }
                        }
                    }
                }
            });
            
            console.log('✅ Size Segmentation created successfully');
        } catch (error) {
            console.error('❌ Error creating Size Segmentation:', error);
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        console.log('🔧 Setting up event listeners...');
        
        // Filter change handlers
        const periodFilter = document.getElementById('periodFilter');
        const segmentFilter = document.getElementById('segmentFilter');
        const metricFilter = document.getElementById('metricFilter');
        
        if (periodFilter) {
            periodFilter.addEventListener('change', () => {
                console.log('Period filter changed:', periodFilter.value);
                this.updateChartsForPeriod(periodFilter.value);
            });
        }
        
        if (segmentFilter) {
            segmentFilter.addEventListener('change', () => {
                console.log('Segment filter changed:', segmentFilter.value);
                this.updateChartsForSegment(segmentFilter.value);
            });
        }
        
        if (metricFilter) {
            metricFilter.addEventListener('change', () => {
                console.log('Metric filter changed:', metricFilter.value);
                this.updateChartsForMetric(metricFilter.value);
            });
        }
        
        console.log('✅ Event listeners setup complete');
    }

    /**
     * Update charts for period filter
     */
    updateChartsForPeriod(period) {
        console.log(`🔄 Updating charts for period: ${period}`);
        // Implementation would go here for real data updates
        // For now, just add visual feedback
        this.addLoadingStates();
        setTimeout(() => {
            this.removeLoadingStates();
        }, 500);
    }

    /**
     * Update charts for segment filter
     */
    updateChartsForSegment(segment) {
        console.log(`🔄 Updating charts for segment: ${segment}`);
        // Implementation would go here for real data updates
        this.addLoadingStates();
        setTimeout(() => {
            this.removeLoadingStates();
        }, 500);
    }

    /**
     * Update charts for metric filter
     */
    updateChartsForMetric(metric) {
        console.log(`🔄 Updating charts for metric: ${metric}`);
        // Implementation would go here for real data updates
        this.addLoadingStates();
        setTimeout(() => {
            this.removeLoadingStates();
        }, 500);
    }

    /**
     * Get default data structure
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
                    {metric1: "DSO", metric2: "Rentabilidad", correlation: -0.72},
                    {metric1: "Volumen", metric2: "Eficiencia", correlation: 0.65},
                    {metric1: "Proceso", metric2: "Satisfacción", correlation: -0.58}
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
                    {name: "Premium", count: 12, dso: 68, revenue: 45, risk: "low"},
                    {name: "Estándar", count: 28, dso: 95, revenue: 35, risk: "medium"},
                    {name: "Básico", count: 15, dso: 145, revenue: 20, risk: "high"}
                ],
                size_segments: [
                    {name: "Grande", count: 8, revenue: 60, margin: 18},
                    {name: "Mediano", count: 25, revenue: 30, margin: 22},
                    {name: "Pequeño", count: 22, revenue: 10, margin: 15}
                ]
            }
        };
    }

    /**
     * Destroy all charts (for cleanup)
     */
    destroy() {
        console.log('🧹 Destroying charts...');
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
        console.log('✅ Charts destroyed');
    }
}

// Global function for updating analytics (called from template)
function updateAnalytics() {
    console.log('🔄 Global updateAnalytics called');
    // Could implement live data refresh here
    location.reload();
}

// Export for use in other modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsDashboard;
}
