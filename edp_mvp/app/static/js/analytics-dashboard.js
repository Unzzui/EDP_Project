/*
 * Analytics Dashboard JavaScript - ApexCharts Version
 * Switching to ApexCharts for better stability and compatibility
 */

// Theme-aware color palette
const CHART_COLORS = {
    primary: '#3b82f6',
    success: '#10b981', 
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    purple: '#8b5cf6',
    orange: '#f97316'
};

// Get theme-aware colors from CSS variables
function getThemeColors() {
    const root = document.documentElement;
    const computedStyle = getComputedStyle(root);
    
    return {
        primary: computedStyle.getPropertyValue('--accent-blue').trim() || CHART_COLORS.primary,
        success: computedStyle.getPropertyValue('--accent-green').trim() || CHART_COLORS.success,
        warning: computedStyle.getPropertyValue('--accent-amber').trim() || CHART_COLORS.warning,
        danger: computedStyle.getPropertyValue('--accent-red').trim() || CHART_COLORS.danger,
        info: computedStyle.getPropertyValue('--info').trim() || CHART_COLORS.info,
        purple: computedStyle.getPropertyValue('--accent-purple').trim() || CHART_COLORS.purple,
        orange: computedStyle.getPropertyValue('--accent-orange').trim() || CHART_COLORS.orange,
        textPrimary: computedStyle.getPropertyValue('--text-primary').trim() || '#1e293b',
        textSecondary: computedStyle.getPropertyValue('--text-secondary').trim() || '#475569',
        borderColor: computedStyle.getPropertyValue('--border-color').trim() || '#d0d7de',
        bgCard: computedStyle.getPropertyValue('--bg-card').trim() || '#ffffff'
    };
}

// Get common chart theme configuration
function getChartTheme() {
    const colors = getThemeColors();
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark' || 
                   (!document.documentElement.getAttribute('data-theme') && 
                    window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    return {
        colors: colors,
        theme: {
            mode: isDark ? 'dark' : 'light',
            palette: 'palette1'
        },
        chart: {
            background: 'transparent',
            foreColor: colors.textSecondary,
            fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            toolbar: {
                show: false
            },
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        grid: {
            borderColor: colors.borderColor,
            strokeDashArray: 3,
            opacity: isDark ? 0.3 : 0.2
        },
        tooltip: {
            theme: isDark ? 'dark' : 'light',
            style: {
                fontSize: '12px',
                fontFamily: 'Inter, sans-serif'
            }
        },
        legend: {
            labels: {
                colors: colors.textSecondary
            }
        }
    };
}

/*
 * Main Analytics Dashboard Class - ApexCharts Version
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
        console.log('🎯 Initializing Analytics Dashboard with ApexCharts:', this.analyticsData);
        
        // Check if ApexCharts is available
        if (typeof ApexCharts === 'undefined') {
            console.error('❌ ApexCharts not loaded! Please check the CDN link.');
            return;
        }
        
        console.log('✅ ApexCharts is available:', ApexCharts);
        
        // Initialize charts with a small delay for better UX
        setTimeout(() => {
            this.initializeCharts();
            console.log('✅ Analytics Dashboard initialized successfully with ApexCharts');
        }, 300);
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
     * Initialize all charts
     */
    initializeCharts() {
        try {
            // Destroy existing charts first
            this.destroyCharts();
            
            this.createDSOEvolutionChart();
            this.createCorrelationMatrix();
            this.createCashFlowPrediction();
            this.createRiskAnalysis();
            this.createClientSegmentation();
            this.createSizeSegmentation();
            console.log('✅ All ApexCharts initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing charts:', error);
        }
    }

    /*
     * Create DSO Evolution Chart with ApexCharts
     */
    createDSOEvolutionChart() {
        const container = document.getElementById('dsoEvolutionChart');
        console.log('🔍 Looking for dsoEvolutionChart container:', container);
        if (!container) {
            console.warn('❌ DSO Evolution chart container not found');
            return;
        }

        try {
            // Generate sample data
            const last30Days = Array.from({length: 30}, (_, i) => {
                const date = new Date();
                date.setDate(date.getDate() - (29 - i));
                return date.getTime();
            });

            const dsoData = last30Days.map((timestamp, i) => {
                const baseValue = this.analyticsData.dso.current_dso;
                const variation = Math.sin(i * 0.3) * 8 + Math.random() * 6 - 3;
                return [timestamp, Math.max(60, baseValue + variation)];
            });

            const targetData = last30Days.map(timestamp => [timestamp, this.analyticsData.dso.target_dso]);

            const themeConfig = getChartTheme();
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark' || 
                          (!document.documentElement.getAttribute('data-theme') && 
                           window.matchMedia('(prefers-color-scheme: dark)').matches);
            
            const dsoColor = isDark ? '#00d4ff' : '#3b82f6';
            const targetColor = themeConfig.colors.success;
            
            const options = {
                series: [
                    {
                        name: 'DSO Real',
                        data: dsoData
                    },
                    {
                        name: 'Objetivo',
                        data: targetData
                    }
                ],
                colors: [dsoColor, targetColor],
                chart: {
                    ...themeConfig.chart,
                    type: 'line',
                    height: 300
                },
                theme: themeConfig.theme,
                grid: themeConfig.grid,
                tooltip: themeConfig.tooltip,
                legend: {
                    ...themeConfig.legend,
                    position: 'top'
                },
                stroke: {
                    width: [4, 3], // Líneas más gruesas para mejor visibilidad
                    dashArray: [0, 5],
                    curve: 'smooth' // Líneas suaves
                },
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.7,
                        opacityTo: 0.9
                    }
                },
                xaxis: {
                    type: 'datetime',
                    labels: {
                        format: 'dd MMM'
                    }
                },
                yaxis: {
                    title: {
                        text: 'Días'
                    },
                    labels: {
                        formatter: function(value) {
                            return value.toFixed(0) + 'd';
                        }
                    }
                },
                tooltip: {
                    shared: true,
                    intersect: false,
                    x: {
                        format: 'dd MMM yyyy'
                    },
                    y: {
                        formatter: function(value) {
                            return value.toFixed(0) + ' días';
                        }
                    }
                }
            };

            this.charts.dsoEvolution = new ApexCharts(container, options);
            this.charts.dsoEvolution.render();
            
            console.log('✅ DSO Evolution Chart created successfully');
        } catch (error) {
            console.error('❌ Error creating DSO Evolution Chart:', error);
        }
    }

    /*
     * Create Correlation Matrix with ApexCharts
     */
    createCorrelationMatrix() {
        const container = document.getElementById('correlationMatrix');
        console.log('🔍 Looking for correlationMatrix container:', container);
        if (!container) {
            console.warn('❌ Correlation chart container not found');
            return;
        }

        try {
            const correlations = this.analyticsData.correlations.key_correlations;
            const categories = correlations.map(c => `${c.metric1} vs ${c.metric2}`);
            const values = correlations.map(c => Math.abs(c.correlation * 100));

            const themeConfig = getChartTheme();
            const options = {
                series: [{
                    name: 'Correlación',
                    data: values
                }],
                chart: {
                    ...themeConfig.chart,
                    type: 'bar',
                    height: 300
                },
                theme: themeConfig.theme,
                grid: themeConfig.grid,
                tooltip: themeConfig.tooltip,
                legend: {
                    ...themeConfig.legend,
                    show: false
                },
                plotOptions: {
                    bar: {
                        borderRadius: 4,
                        horizontal: false,
                        distributed: true
                    }
                },
                colors: [themeConfig.colors.info, themeConfig.colors.warning, themeConfig.colors.danger],
                xaxis: {
                    categories: categories,
                    labels: {
                        style: {
                            fontSize: '12px'
                        }
                    }
                },
                yaxis: {
                    title: {
                        text: 'Fuerza de Correlación (%)'
                    },
                    max: 100
                },
                tooltip: {
                    ...themeConfig.tooltip,
                    y: {
                        formatter: function(value, { dataPointIndex }) {
                            const correlation = correlations[dataPointIndex].correlation;
                            return `${value.toFixed(0)}% (${correlation.toFixed(2)})`;
                        }
                    }
                }
            };

            this.charts.correlation = new ApexCharts(container, options);
            this.charts.correlation.render();
            
            console.log('✅ Correlation Matrix created successfully');
        } catch (error) {
            console.error('❌ Error creating Correlation Matrix:', error);
        }
    }

    /*
     * Create Cash Flow Prediction Chart with ApexCharts
     */
    createCashFlowPrediction() {
        const container = document.getElementById('cashFlowPrediction');
        console.log('🔍 Looking for cashFlowPrediction container:', container);
        if (!container) {
            console.warn('❌ Cash Flow chart container not found');
            return;
        }

        try {
            // Generate sample data
            const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
            const cashFlowData = months.map((_, i) => {
                const base = this.analyticsData.predictions.cash_flow_30d;
                return (base * (1 + (Math.random() - 0.5) * 0.3)) / 1000000; // Convert to millions
            });

            const themeConfig = getChartTheme();
            const options = {
                series: [{
                    name: 'Flujo de Caja Predicho',
                    data: cashFlowData,
                    color: themeConfig.colors.purple
                }],
                chart: {
                    ...themeConfig.chart,
                    type: 'area',
                    height: 300
                },
                theme: themeConfig.theme,
                grid: themeConfig.grid,
                tooltip: themeConfig.tooltip,
                legend: {
                    ...themeConfig.legend,
                    position: 'top'
                },
                stroke: {
                    curve: 'smooth',
                    width: 3
                },
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.3,
                        opacityTo: 0.1
                    }
                },
                xaxis: {
                    categories: months
                },
                yaxis: {
                    title: {
                        text: 'Millones (€)'
                    },
                    labels: {
                        formatter: function(value) {
                            return '€' + value.toFixed(1) + 'M';
                        }
                    }
                },
                tooltip: {
                    ...themeConfig.tooltip,
                    y: {
                        formatter: function(value) {
                            return '€' + value.toFixed(1) + 'M';
                        }
                    }
                }
            };

            this.charts.cashFlow = new ApexCharts(container, options);
            this.charts.cashFlow.render();
            
            console.log('✅ Cash Flow Prediction Chart created successfully');
        } catch (error) {
            console.error('❌ Error creating Cash Flow Prediction Chart:', error);
        }
    }

    /*
     * Create Risk Analysis Chart with ApexCharts
     */
    createRiskAnalysis() {
        const container = document.getElementById('riskAnalysis');
        console.log('🔍 Looking for riskAnalysis container:', container);
        if (!container) {
            console.warn('❌ Risk chart container not found');
            return;
        }

        try {
            const themeConfig = getChartTheme();
            const options = {
                series: [65, 25, 10],
                labels: ['Bajo Riesgo', 'Riesgo Medio', 'Alto Riesgo'],
                colors: [themeConfig.colors.success, themeConfig.colors.warning, themeConfig.colors.danger],
                chart: {
                    ...themeConfig.chart,
                    type: 'donut',
                    height: 300
                },
                theme: themeConfig.theme,
                tooltip: themeConfig.tooltip,
                legend: {
                    ...themeConfig.legend,
                    position: 'bottom'
                },
                plotOptions: {
                    pie: {
                        donut: {
                            size: '65%'
                        }
                    }
                },
                tooltip: {
                    ...themeConfig.tooltip,
                    y: {
                        formatter: function(value) {
                            return value + '%';
                        }
                    }
                }
            };

            this.charts.risk = new ApexCharts(container, options);
            this.charts.risk.render();
            
            console.log('✅ Risk Analysis Chart created successfully');
        } catch (error) {
            console.error('❌ Error creating Risk Analysis Chart:', error);
        }
    }

    /*
     * Create Client Segmentation Chart with ApexCharts
     */
    createClientSegmentation() {
        const container = document.getElementById('clientSegmentation');
        console.log('🔍 Looking for clientSegmentation container:', container);
        if (!container) {
            console.warn('❌ Client Segment chart container not found');
            return;
        }

        try {
            const segments = this.analyticsData.segmentation.client_segments;
            
            const themeConfig = getChartTheme();
            const options = {
                series: [
                    {
                        name: 'DSO (días)',
                        data: segments.map(s => s.dso),
                        color: themeConfig.colors.primary
                    },
                    {
                        name: 'Revenue (%)',
                        data: segments.map(s => s.revenue),
                        color: themeConfig.colors.success
                    }
                ],
                chart: {
                    ...themeConfig.chart,
                    type: 'bar',
                    height: 300
                },
                theme: themeConfig.theme,
                grid: themeConfig.grid,
                tooltip: themeConfig.tooltip,
                legend: {
                    ...themeConfig.legend,
                    position: 'top'
                },
                plotOptions: {
                    bar: {
                        borderRadius: 4,
                        horizontal: false,
                        columnWidth: '70%'
                    }
                },
                xaxis: {
                    categories: segments.map(s => s.name)
                },
                yaxis: {
                    title: {
                        text: 'Valores'
                    }
                },
                tooltip: {
                    ...themeConfig.tooltip,
                    shared: true,
                    intersect: false
                }
            };

            this.charts.clientSegment = new ApexCharts(container, options);
            this.charts.clientSegment.render();
            
            console.log('✅ Client Segmentation Chart created successfully');
        } catch (error) {
            console.error('❌ Error creating Client Segmentation Chart:', error);
        }
    }

    /*
     * Create Size Segmentation Chart with ApexCharts
     */
    createSizeSegmentation() {
        const container = document.getElementById('sizeSegmentation');
        console.log('🔍 Looking for sizeSegmentation container:', container);
        if (!container) {
            console.warn('❌ Size Segment chart container not found');
            return;
        }

        try {
            const segments = this.analyticsData.segmentation.size_segments;
            
            const themeConfig = getChartTheme();
            const options = {
                series: segments.map(s => s.revenue),
                labels: segments.map(s => s.name),
                colors: [themeConfig.colors.purple, themeConfig.colors.info, themeConfig.colors.warning],
                chart: {
                    ...themeConfig.chart,
                    type: 'donut',
                    height: 300
                },
                theme: themeConfig.theme,
                tooltip: themeConfig.tooltip,
                legend: {
                    ...themeConfig.legend,
                    position: 'bottom'
                },
                plotOptions: {
                    pie: {
                        donut: {
                            size: '50%'
                        }
                    }
                },
                tooltip: {
                    ...themeConfig.tooltip,
                    y: {
                        formatter: function(value) {
                            return value + '%';
                        }
                    }
                }
            };

            this.charts.sizeSegment = new ApexCharts(container, options);
            this.charts.sizeSegment.render();
            
            console.log('✅ Size Segmentation Chart created successfully');
        } catch (error) {
            console.error('❌ Error creating Size Segmentation Chart:', error);
        }
    }

    /*
     * Update analytics data and refresh charts
     */
    updateAnalytics() {
        console.log('🔄 Updating analytics with ApexCharts...');
        
        setTimeout(() => {
            this.destroyCharts();
            this.initializeCharts();
            console.log('✅ Analytics updated successfully');
        }, 500);
    }

    /*
     * Destroy all charts
     */
    destroyCharts() {
        console.log('🗑️ Destroying existing ApexCharts...');
        
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
        
        this.charts = {};
    }

    /*
     * Enhanced destroy method
     */
    destroy() {
        this.destroyCharts();
        
        if (window.analyticsInstanceActive) {
            window.analyticsInstanceActive = false;
        }
        
        console.log('✅ Analytics Dashboard destroyed and cleaned up');
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

        // Theme change detection
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
                    console.log('🎨 Theme changed, updating charts...');
                    setTimeout(() => {
                        this.updateAnalytics();
                    }, 100);
                }
            });
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme']
        });

        // Also listen for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', () => {
                if (!document.documentElement.getAttribute('data-theme')) {
                    console.log('🎨 System theme changed, updating charts...');
                    setTimeout(() => {
                        this.updateAnalytics();
                    }, 100);
                }
            });
        }
    }
}

// Global function for update button
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
