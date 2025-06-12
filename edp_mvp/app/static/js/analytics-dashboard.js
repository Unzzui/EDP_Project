/*
 * Analytics Dashboard JavaScript - Professional Version
 * Enhanced with thicker lines, vibrant colors, and improved chart styling
 */

// Global error handler for Chart.js animation issues
window.addEventListener('error', function(event) {
    if (event.message && event.message.includes('_fn is not a function')) {
        console.warn('🛡️ Chart.js animation error intercepted and handled');
        event.preventDefault();
        return false;
    }
});

// Unhandled promise rejection handler for async chart errors
window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && event.reason.toString().includes('Chart')) {
        console.warn('🛡️ Chart.js promise rejection handled:', event.reason);
        event.preventDefault();
    }
});

// Function to get CSS variable value
function getCSSVar(varName) {
    return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
}

// Function to get current theme colors
function getThemeColors() {
    return {
        primary: getCSSVar('--accent-blue'),
        success: getCSSVar('--accent-green'), 
        warning: getCSSVar('--accent-amber'),
        danger: getCSSVar('--accent-red'),
        info: getCSSVar('--info'),
        purple: getCSSVar('--accent-purple'),
        orange: getCSSVar('--accent-orange'),
        textPrimary: getCSSVar('--text-primary'),
        textSecondary: getCSSVar('--text-secondary'),
        background: getCSSVar('--background'),
        bgCard: getCSSVar('--bg-card'),
        borderColor: getCSSVar('--border-color'),
        successBg: getCSSVar('--success-bg'),
        warningBg: getCSSVar('--warning-bg'),
        dangerBg: getCSSVar('--danger-bg'),
        infoBg: getCSSVar('--info-bg')
    };
}

// Global Chart.js configuration for professional appearance with enhanced animations
Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = getCSSVar('--text-primary');
Chart.defaults.backgroundColor = getCSSVar('--bg-card');

// Enhanced global animations - using safe easing function and proper callbacks
Chart.defaults.animation = {
    duration: 1000,
    easing: 'easeInOutCubic',
    onComplete: function() {
        // Ensure proper cleanup of animation state
        if (this.chart && this.chart.canvas) {
            this.chart.canvas.style.opacity = '1';
        }
    },
    onProgress: function(context) {
        // Prevent callback errors by ensuring context exists
        if (!context || !context.chart || !context.chart.canvas) return;
        // Safe progress handling
        try {
            const progress = context.currentStep / context.numSteps;
            if (progress >= 0 && progress <= 1) {
                // Animation progressing normally
            }
        } catch (error) {
            // Silently handle animation callback errors
            console.warn('Animation callback error handled:', error);
        }
    }
};

Chart.defaults.elements.point.hoverRadius = 8;
Chart.defaults.elements.point.radius = 5;
Chart.defaults.elements.line.tension = 0.4;
Chart.defaults.elements.line.borderWidth = 3;
Chart.defaults.elements.bar.borderRadius = 6;

// Professional color palette using CSS variables
const CHART_COLORS = getThemeColors();

/*
 * Main Analytics Dashboard Class
 */
class AnalyticsDashboard {
    constructor(analyticsData) {
        this.analyticsData = analyticsData || this.getDefaultData();
        this.charts = {};
        
        // Prevent multiple instances
        if (window.analyticsInstanceActive) {
            console.warn('⚠️ Analytics Dashboard instance already active. Destroying previous instance.');
            if (window.analyticsDashboard && window.analyticsDashboard.destroyCharts) {
                window.analyticsDashboard.destroyCharts();
            }
        }
        
        window.analyticsInstanceActive = true;
        window.analyticsDashboard = this;
        
        this.init();
    }

    /*
     * Initialize the dashboard
     */
    init() {
        console.log('🎯 Initializing Analytics Dashboard with data:', this.analyticsData);
        
        try {
            // Add loading animations
            this.addLoadingStates();
            
            // Add floating action button
     
            
            // Initialize charts with a small delay for better UX and animation safety
            setTimeout(() => {
                try {
                    this.initializeCharts();
                    this.removeLoadingStates();
                    this.addEntranceAnimations();
                    this.setupThemeWatcher();
                    this.setupInteractiveEffects();
                } catch (error) {
                    console.error('❌ Error during chart initialization:', error);
                    this.removeLoadingStates();
                    this.showNotification('Error al cargar gráficos', 'error');
                }
            }, 500);
        } catch (error) {
            console.error('❌ Error during dashboard initialization:', error);
            this.showNotification('Error al inicializar dashboard', 'error');
        }
    }

    /*
     * Setup theme change watcher
     */
    setupThemeWatcher() {
        // Watch for theme changes on the document element
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
                    console.log('🎨 Theme changed, updating chart colors...');
                    this.updateChartsForTheme();
                }
            });
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme', 'class']
        });

        // Also watch for class changes (in case theme is handled via classes)
        const classObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const classList = document.documentElement.classList;
                    if (classList.contains('light') || classList.contains('dark')) {
                        console.log('🎨 Theme class changed, updating chart colors...');
                        this.updateChartsForTheme();
                    }
                }
            });
        });

        classObserver.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class']
        });

        this.themeObserver = observer;
        this.classObserver = classObserver;
    }

    /*
     * Update all charts when theme changes
     */
    updateChartsForTheme() {
        // Update color palette
        this.updateChartColors();
        
        // Update each chart's options
        Object.keys(this.charts).forEach(key => {
            const chart = this.charts[key];
            if (chart && chart.options) {
                this.updateChartOptionsForTheme(chart);
                chart.update('none'); // Update without animation for better performance
            }
        });
    }

    /*
     * Update individual chart options for theme
     */
    updateChartOptionsForTheme(chart) {
        // Update text colors
        if (chart.options.plugins && chart.options.plugins.legend) {
            chart.options.plugins.legend.labels.color = CHART_COLORS.textPrimary;
        }
        
        if (chart.options.plugins && chart.options.plugins.tooltip) {
            chart.options.plugins.tooltip.backgroundColor = CHART_COLORS.bgCard;
            chart.options.plugins.tooltip.titleColor = CHART_COLORS.textPrimary;
            chart.options.plugins.tooltip.bodyColor = CHART_COLORS.textPrimary;
            chart.options.plugins.tooltip.borderColor = CHART_COLORS.borderColor;
        }

        // Update scale colors
        if (chart.options.scales) {
            Object.keys(chart.options.scales).forEach(scaleKey => {
                const scale = chart.options.scales[scaleKey];
                if (scale.grid) {
                    scale.grid.color = `${CHART_COLORS.borderColor}40`;
                }
                if (scale.ticks) {
                    scale.ticks.color = CHART_COLORS.textSecondary;
                }
            });
        }
    }

    /*
     * Get default analytics data
     */
    getDefaultData() {
        return {
            dso: {
                current_dso: 124,
                target_dso: 90,
                trend: -2.3,
                variance: 34,
                predicted_dso: 118,
                insights: "DSO actual está por encima del objetivo"
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

    /*
     * Add loading states with animations
     */
    addLoadingStates() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach((container, index) => {
            container.classList.add('chart-loading');
            container.style.animationDelay = `${index * 0.1}s`;
        });
    }

    /*
     * Remove loading states
     */
    removeLoadingStates() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            container.classList.remove('chart-loading');
        });
    }

    /*
     * Add entrance animations to charts
     */
    addEntranceAnimations() {
        const chartCards = document.querySelectorAll('.chart-card');
        chartCards.forEach((card, index) => {
            card.classList.add('chart-animate-in');
            card.style.animationDelay = `${index * 0.1}s`;
        });

        const metricCards = document.querySelectorAll('.metric-card');
        metricCards.forEach((card, index) => {
            card.classList.add('metric-animate-in');
            card.style.animationDelay = `${index * 0.1}s`;
        });
    }

 
    /*
     * Setup interactive effects
     */
    setupInteractiveEffects() {
        // Add hover effects to data points
        this.setupChartHoverEffects();
        
        // Add metric card interactions
        this.setupMetricCardEffects();
        
        // Add progress bar animations
        this.animateProgressBars();
    }

    /*
     * Setup chart hover effects
     */
    setupChartHoverEffects() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.canvas) {
                chart.canvas.addEventListener('mousemove', (e) => {
                    chart.canvas.style.cursor = 'pointer';
                });
                
                chart.canvas.addEventListener('mouseleave', (e) => {
                    chart.canvas.style.cursor = 'default';
                });
            }
        });
    }

    /*
     * Setup metric card effects
     */
    setupMetricCardEffects() {
        const metricCards = document.querySelectorAll('.metric-card');
        metricCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px)';
                card.style.boxShadow = '0 20px 40px rgba(0,0,0,0.1)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '';
            });
        });
    }

    /*
     * Animate progress bars
     */
    animateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-fill');
        progressBars.forEach((bar, index) => {
            const width = bar.style.width || bar.getAttribute('data-width') || '0%';
            bar.style.width = '0%';
            
            setTimeout(() => {
                bar.style.width = width;
            }, 300 + (index * 100));
        });
    }

    /*
     * Refresh dashboard with animation
     */
    refreshDashboard() {
        // Add loading state
        this.addLoadingStates();
        
        // Simulate data refresh
        setTimeout(() => {
            // Update charts with new data
            this.updateChartsData();
            this.removeLoadingStates();
            
            // Show success notification
            this.showNotification('Dashboard actualizado', 'success');
        }, 1500);
    }

    /*
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-full`;
        
        const bgClass = type === 'success' ? 'bg-green-500' : 
                       type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        
        notification.classList.add(bgClass, 'text-white');
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Animate out and remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    /*
     * Initialize all charts
     */
    initializeCharts() {
        try {
            // Destroy existing charts first to prevent canvas reuse errors
            this.destroyCharts();
            
            // Update colors to current theme
            this.updateChartColors();
            
            // Add a small delay between chart creation to prevent animation conflicts
            this.createDSOEvolutionChart();
            setTimeout(() => this.createCorrelationMatrix(), 100);
            setTimeout(() => this.createCashFlowPrediction(), 200);
            setTimeout(() => this.createRiskAnalysis(), 300);
            setTimeout(() => this.createClientSegmentation(), 400);
            setTimeout(() => this.createSizeSegmentation(), 500);
            
            console.log('✅ All charts initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing charts:', error);
        }
    }

    /*
     * Update chart colors based on current theme
     */
    updateChartColors() {
        // Update Chart.js defaults
        Chart.defaults.color = getCSSVar('--text-primary');
        Chart.defaults.backgroundColor = getCSSVar('--bg-card');
        
        // Update CHART_COLORS object
        Object.assign(CHART_COLORS, getThemeColors());
    }

    /*
     * Create DSO Evolution Chart with Professional Styling
     */
    createDSOEvolutionChart() {
        const ctx = document.getElementById('dsoEvolutionChart');
        if (!ctx) {
            console.warn('DSO Evolution chart canvas not found');
            return;
        }

        try {
            // Destroy existing chart if it exists (check both our registry and Chart.js registry)
            if (this.charts.dsoEvolution) {
                this.charts.dsoEvolution.destroy();
                this.charts.dsoEvolution = null;
            }
            
            // Also check Chart.js global registry for any chart using this canvas
            const existingChart = Chart.getChart(ctx);
            if (existingChart) {
                existingChart.destroy();
            }

            // Clear any pending animations
            if (ctx.getContext) {
                const context = ctx.getContext('2d');
                context.clearRect(0, 0, ctx.width, ctx.height);
            }

        // Generate sample time series data
        const last30Days = Array.from({length: 30}, (_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - (29 - i));
            return date;
        });

        const dsoData = last30Days.map((date, i) => {
            const baseValue = this.analyticsData.dso.current_dso;
            const variation = Math.sin(i * 0.3) * 8 + Math.random() * 6 - 3;
            return Math.max(60, baseValue + variation);
        });

        const targetData = last30Days.map(() => this.analyticsData.dso.target_dso);
        const predictedData = last30Days.slice(-7).map((date, i) => {
            const trend = -0.8; // Improving trend
            return dsoData[dsoData.length - 7 + i] + (trend * i);
        });

        this.charts.dsoEvolution = new Chart(ctx, {
            type: 'line',
            data: {
                labels: last30Days.map(date => date.toLocaleDateString('es-ES', { month: 'short', day: 'numeric' })),
                datasets: [
                    {
                        label: 'DSO Real',
                        data: dsoData,
                        borderColor: CHART_COLORS.primary,
                        backgroundColor: `${CHART_COLORS.primary}15`,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: CHART_COLORS.primary,
                        pointBorderColor: CHART_COLORS.background,
                        pointBorderWidth: 2
                    },
                    {
                        label: 'Objetivo',
                        data: targetData,
                        borderColor: CHART_COLORS.success,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [8, 4],
                        fill: false,
                        pointRadius: 0
                    },
                    {
                        label: 'Predicción (7d)',
                        data: [...Array(23).fill(null), ...predictedData],
                        borderColor: CHART_COLORS.purple,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [4, 4],
                        fill: false,
                        pointRadius: 3,
                        pointBackgroundColor: CHART_COLORS.purple
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: CHART_COLORS.textPrimary,
                            font: { size: 14, weight: 'bold' },
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    title: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: CHART_COLORS.bgCard,
                        titleColor: CHART_COLORS.textPrimary,
                        bodyColor: CHART_COLORS.textPrimary,
                        borderColor: CHART_COLORS.primary,
                        borderWidth: 1
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: `${CHART_COLORS.borderColor}60`,
                            lineWidth: 1
                        },
                        ticks: {
                            color: CHART_COLORS.textSecondary,
                            font: { weight: 'bold' }
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: `${CHART_COLORS.borderColor}60`,
                            lineWidth: 1
                        },
                        ticks: {
                            color: CHART_COLORS.textSecondary,
                            font: { weight: 'bold' },
                            callback: function(value) {
                                return value + 'd';
                            }
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutCubic',
                    onComplete: function() {
                        // Animation completed safely
                    },
                    onProgress: function(animation) {
                        // Safe progress callback
                        if (animation && typeof animation.animationObject === 'object') {
                            // Animation is progressing normally
                        }
                    }
                }
            }
        });

        console.log('✅ DSO Evolution Chart created successfully');
        } catch (error) {
            console.error('❌ Error creating DSO Evolution Chart:', error);
            this.charts.dsoEvolution = null;
        }
    }

    /*
     * Create Correlation Matrix
     */
    createCorrelationMatrix() {
        const ctx = document.getElementById('correlationMatrix');
        if (!ctx) {
            console.warn('Correlation chart canvas not found');
            return;
        }

        try {
            // Destroy existing chart if it exists (check both our registry and Chart.js registry)
            if (this.charts.correlation) {
                this.charts.correlation.destroy();
                this.charts.correlation = null;
            }
            
            // Also check Chart.js global registry for any chart using this canvas
            const existingChart = Chart.getChart(ctx);
            if (existingChart) {
                existingChart.destroy();
            }

            // Clear any pending animations
            if (ctx.getContext) {
                const context = ctx.getContext('2d');
                context.clearRect(0, 0, ctx.width, ctx.height);
            }

        const correlations = this.analyticsData.correlations.key_correlations;
        const labels = correlations.map(c => `${c.metric1} vs ${c.metric2}`);
        const values = correlations.map(c => Math.abs(c.correlation));
        const colors = correlations.map(c => {
            if (Math.abs(c.correlation) > 0.7) return CHART_COLORS.danger;
            if (Math.abs(c.correlation) > 0.5) return CHART_COLORS.warning;
            return CHART_COLORS.success;
        });

        this.charts.correlation = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Fuerza de Correlación',
                    data: values,
                    backgroundColor: colors.map(color => `${color}60`),
                    borderColor: colors,
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false
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
                        backgroundColor: CHART_COLORS.bgCard,
                        titleColor: CHART_COLORS.textPrimary,
                        bodyColor: CHART_COLORS.textPrimary,
                        borderColor: CHART_COLORS.borderColor,
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const correlation = correlations[context.dataIndex];
                                return `Correlación: ${correlation.correlation.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: CHART_COLORS.textPrimary,
                            font: { weight: 'bold' },
                            maxRotation: 45
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: `${CHART_COLORS.borderColor}40`
                        },
                        ticks: {
                            color: CHART_COLORS.textPrimary,
                            font: { weight: 'bold' },
                            callback: function(value) {
                                return (value * 100).toFixed(0) + '%';
                            }
                        },
                        max: 1
                    }
                }
            }
        });

        console.log('✅ Correlation Matrix created successfully');
        } catch (error) {
            console.error('❌ Error creating Correlation Matrix:', error);
            this.charts.correlation = null;
        }
    }

    /*
     * Create Cash Flow Prediction Chart
     */
    createCashFlowPrediction() {
        const ctx = document.getElementById('cashFlowPrediction');
        if (!ctx) {
            console.warn('Cash Flow chart canvas not found');
            return;
        }

        // Destroy existing chart if it exists (check both our registry and Chart.js registry)
        if (this.charts.cashFlow) {
            this.charts.cashFlow.destroy();
        }
        
        // Also check Chart.js global registry for any chart using this canvas
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
        }

        // Generate next 12 months data
        const months = Array.from({length: 12}, (_, i) => {
            const date = new Date();
            date.setMonth(date.getMonth() + i);
            return date.toLocaleDateString('es-ES', { month: 'short', year: '2-digit' });
        });

        const baseFlow = this.analyticsData.predictions.cash_flow_30d;
        const cashFlowData = months.map((_, i) => {
            const seasonality = Math.sin(i * Math.PI / 6) * 0.2;
            const growth = i * 0.05;
            const variance = (Math.random() - 0.5) * 0.1;
            return baseFlow * (1 + seasonality + growth + variance);
        });

        this.charts.cashFlow = new Chart(ctx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Flujo de Caja Predicho',
                    data: cashFlowData,
                    borderColor: CHART_COLORS.info,
                    backgroundColor: `${CHART_COLORS.info}20`,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: CHART_COLORS.info,
                    pointBorderColor: CHART_COLORS.background,
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: CHART_COLORS.textPrimary,
                            font: { size: 14, weight: 'bold' }
                        }
                    },
                    tooltip: {
                        backgroundColor: CHART_COLORS.bgCard,
                        titleColor: CHART_COLORS.textPrimary,
                        bodyColor: CHART_COLORS.textPrimary,
                        borderColor: CHART_COLORS.borderColor,
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `€${(context.parsed.y / 1000000).toFixed(1)}M`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: `${CHART_COLORS.borderColor}40`
                        },
                        ticks: {
                            color: CHART_COLORS.textSecondary,
                            font: { weight: 'bold' }
                        }
                    },
                    y: {
                        grid: {
                            color: `${CHART_COLORS.borderColor}40`
                        },
                        ticks: {
                            color: CHART_COLORS.textSecondary,
                            font: { weight: 'bold' },
                            callback: function(value) {
                                return '€' + (value / 1000000).toFixed(1) + 'M';
                            }
                        }
                    }
                }
            }
        });

        console.log('✅ Cash Flow Prediction Chart created successfully');
    }

    /*
     * Create Risk Analysis Chart
     */
    createRiskAnalysis() {
        const ctx = document.getElementById('riskAnalysis');
        if (!ctx) {
            console.warn('Risk chart canvas not found');
            return;
        }

        // Destroy existing chart if it exists (check both our registry and Chart.js registry)
        if (this.charts.risk) {
            this.charts.risk.destroy();
        }
        
        // Also check Chart.js global registry for any chart using this canvas
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
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
                            color: CHART_COLORS.textPrimary,
                            font: { size: 13, weight: 'bold' },
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: CHART_COLORS.bgCard,
                        titleColor: CHART_COLORS.textPrimary,
                        bodyColor: CHART_COLORS.textPrimary,
                        borderColor: CHART_COLORS.borderColor,
                        borderWidth: 1,
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

    /*
     * Create Client Segmentation Chart
     */
    createClientSegmentation() {
        const ctx = document.getElementById('clientSegmentation');
        if (!ctx) {
            console.warn('Client Segment chart canvas not found');
            return;
        }

        // Destroy existing chart if it exists (check both our registry and Chart.js registry)
        if (this.charts.clientSegment) {
            this.charts.clientSegment.destroy();
        }
        
        // Also check Chart.js global registry for any chart using this canvas
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
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
                        backgroundColor: `${CHART_COLORS.primary}60`,
                        borderColor: CHART_COLORS.primary,
                        borderWidth: 2,
                        borderRadius: 6
                    },
                    {
                        label: 'Revenue (%)',
                        data: segments.map(s => s.revenue),
                        backgroundColor: `${CHART_COLORS.success}60`,
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
                            color: CHART_COLORS.textPrimary,
                            font: { size: 13, weight: 'bold' }
                        }
                    },
                    tooltip: {
                        backgroundColor: CHART_COLORS.bgCard,
                        titleColor: CHART_COLORS.textPrimary,
                        bodyColor: CHART_COLORS.textPrimary,
                        borderColor: CHART_COLORS.borderColor,
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: CHART_COLORS.textPrimary,
                            font: { weight: 'bold' }
                        }
                    },
                    y: {
                        grid: {
                            color: `${CHART_COLORS.borderColor}40`
                        },
                        ticks: {
                            color: CHART_COLORS.textPrimary,
                            font: { weight: 'bold' }
                        }
                    }
                }
            }
        });

        console.log('✅ Client Segmentation Chart created successfully');
    }

    /*
     * Create Size Segmentation Chart
     */
    createSizeSegmentation() {
        console.log('📊 Creating Size Segmentation Chart...');
        const ctx = document.getElementById('sizeSegmentation');
        if (!ctx) {
            console.warn('Size Segment chart canvas not found');
            return;
        }

        try {
            // Destroy existing chart if it exists (check both our registry and Chart.js registry)
            if (this.charts.sizeSegment) {
                this.charts.sizeSegment.destroy();
                this.charts.sizeSegment = null;
            }
            
            // Also check Chart.js global registry for any chart using this canvas
            const existingChart = Chart.getChart(ctx);
            if (existingChart) {
                existingChart.destroy();
            }

            // Clear canvas to prevent rendering issues
            const canvasContext = ctx.getContext('2d');
            canvasContext.clearRect(0, 0, ctx.width, ctx.height);

            const segments = this.analyticsData.segmentation.size_segments;
            
            this.charts.sizeSegment = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: segments.map(s => s.name),
                    datasets: [{
                        data: segments.map(s => s.revenue),
                        backgroundColor: [
                            `${CHART_COLORS.purple}60`,
                            `${CHART_COLORS.info}60`,
                            `${CHART_COLORS.warning}60`
                        ],
                        borderColor: [
                            CHART_COLORS.purple,
                            CHART_COLORS.info,
                            CHART_COLORS.warning
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '50%',
                    animation: {
                        duration: 600,
                        easing: 'easeInOutCubic',
                        animateRotate: true,
                        animateScale: false,
                        onComplete: null, // Disable callback to prevent errors
                        onProgress: null  // Disable callback to prevent errors
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: CHART_COLORS.textPrimary,
                                font: { size: 13, weight: 'bold' },
                                padding: 20
                            }
                        },
                        tooltip: {
                            backgroundColor: CHART_COLORS.bgCard,
                            titleColor: CHART_COLORS.textPrimary,
                            bodyColor: CHART_COLORS.textPrimary,
                            borderColor: CHART_COLORS.borderColor,
                            borderWidth: 1,
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
        } catch (error) {
            console.error('❌ Error creating Size Segmentation Chart:', error);
            this.charts.sizeSegment = null;
        }
    }

    /*
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

    /*
     * Update charts data with new information
     */
    updateChartsData() {
        Object.keys(this.charts).forEach(key => {
            const chart = this.charts[key];
            if (chart && chart.data) {
                // Add sparkle animation to data update
                chart.update('active');
            }
        });
    }

    /*
     * Add sparkle effect to chart updates
     */
    addSparkleEffect(element) {
        element.style.position = 'relative';
        const sparkle = document.createElement('div');
        sparkle.className = 'absolute top-0 right-0 w-2 h-2 bg-yellow-400 rounded-full animate-ping';
        element.appendChild(sparkle);
        
        setTimeout(() => {
            sparkle.remove();
        }, 1500);
    }

    /*
     * Enhanced destroy method with animation
     */
    destroy() {
        // Destroy all charts
        this.destroyCharts();
        
        // Disconnect theme observers
        if (this.themeObserver) {
            this.themeObserver.disconnect();
            this.themeObserver = null;
        }
        
        if (this.classObserver) {
            this.classObserver.disconnect();
            this.classObserver = null;
        }
        
        // Clear global instance
        if (window.analyticsInstanceActive) {
            window.analyticsInstanceActive = false;
        }
        
        console.log('✅ Analytics Dashboard destroyed and cleaned up');
    }

    /*
     * Destroy all charts
     */
    destroyCharts() {
        console.log('🗑️ Destroying existing charts...');
        
        // First, destroy charts from our registry
        Object.keys(this.charts).forEach(key => {
            if (this.charts[key] && typeof this.charts[key].destroy === 'function') {
                try {
                    this.charts[key].destroy();
                    console.log(`✅ Destroyed chart: ${key}`);
                } catch (error) {
                    console.warn(`⚠️ Error destroying chart ${key}:`, error);
                }
            }
        });
        
        // Also destroy any charts from Chart.js global registry
        const canvasIds = ['dsoEvolutionChart', 'correlationMatrix', 'cashFlowPrediction', 'riskAnalysis', 'clientSegmentation', 'sizeSegmentation'];
        canvasIds.forEach(id => {
            const canvas = document.getElementById(id);
            if (canvas) {
                const existingChart = Chart.getChart(canvas);
                if (existingChart) {
                    try {
                        existingChart.destroy();
                        console.log(`✅ Destroyed global chart on canvas: ${id}`);
                    } catch (error) {
                        console.warn(`⚠️ Error destroying global chart on ${id}:`, error);
                    }
                }
            }
        });
        
        this.charts = {};
    }

    /*
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
