/*
 * Analytics Dashboard JavaScript - ApexCharts Version
 * Switching to ApexCharts for better stability and compatibility
 */

/*
 * MEJORAS DE ESTILO APLICADAS:
 * 
 * 1. FORMATEO DE NÚMEROS:
 *    - Máximo 1 decimal en todos los valores numéricos
 *    - Función formatNumber() para consistencia
 *    - Función formatCurrency() para valores monetarios
 *    - Soporte para formato K/M en números grandes
 * 
 * 2. ESTILO VISUAL:
 *    - Paleta de colores mejorada y tema-aware
 *    - Gradientes suaves y consistentes
 *    - Animaciones suaves y profesionales
 *    - Tipografía Inter en todos los elementos
 * 
 * 3. TOOLTIPS Y ETIQUETAS:
 *    - Formato consistente con máximo 1 decimal
 *    - Etiquetas descriptivas y claras
 *    - Colores tema-aware para mejor legibilidad
 * 
 * 4. INTERACTIVIDAD:
 *    - Animaciones suaves al cargar
 *    - Hover effects mejorados
 *    - Transiciones fluidas entre temas
 * 
 * 5. RESPONSIVIDAD:
 *    - Adaptación automática a tema claro/oscuro
 *    - Colores dinámicos basados en CSS variables
 *    - Tamaños de fuente escalables
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

// Standard number formatting function - max 1 decimal place
function formatNumber(value, decimals = 1, suffix = '') {
    if (value === null || value === undefined) return '0';
    
    const num = parseFloat(value);
    if (isNaN(num)) return '0';
    
    // For very large numbers, use K/M formatting only if no suffix is provided
    if (!suffix && Math.abs(num) >= 1000000) {
        return (num / 1000000).toFixed(decimals) + 'M';
    } else if (!suffix && Math.abs(num) >= 1000) {
        return (num / 1000).toFixed(decimals) + 'K';
    }
    
    // For regular numbers, use specified decimals
    return num.toFixed(decimals) + suffix;
}

// Special formatter for currency values in Chilean Pesos (CLP)
function formatCurrency(value, decimals = 0) {
    if (value === null || value === undefined) return '$0';
    
    const num = parseFloat(value);
    if (isNaN(num)) return '$0';
    
    if (Math.abs(num) >= 1000000000) {
        return '$' + (num / 1000000000).toFixed(decimals) + 'B';
    } else if (Math.abs(num) >= 1000000) {
        return '$' + (num / 1000000).toFixed(decimals) + 'M';
    } else if (Math.abs(num) >= 1000) {
        return '$' + (num / 1000).toFixed(decimals) + 'K';
    }
    
    // For regular amounts, format with thousand separators
    return '$' + num.toLocaleString('es-CL', { 
        minimumFractionDigits: decimals, 
        maximumFractionDigits: decimals 
    });
}

// Formatter for large Chilean Peso amounts with proper separators
function formatChileanPesos(value, showDecimals = false) {
    if (value === null || value === undefined) return '$0';
    
    const num = parseFloat(value);
    if (isNaN(num)) return '$0';
    
    return '$' + num.toLocaleString('es-CL', {
        minimumFractionDigits: showDecimals ? 2 : 0,
        maximumFractionDigits: showDecimals ? 2 : 0
    });
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
                speed: 800,
                animateGradually: {
                    enabled: true,
                    delay: 150
                },
                dynamicAnimation: {
                    enabled: true,
                    speed: 350
                }
            },
            dropShadow: {
                enabled: false
            }
        },
        grid: {
            borderColor: colors.borderColor,
            strokeDashArray: 3,
            opacity: isDark ? 0.3 : 0.2,
            xaxis: {
                lines: {
                    show: true
                }
            },
            yaxis: {
                lines: {
                    show: true
                }
            },
            padding: {
                top: 10,
                right: 10,
                bottom: 10,
                left: 10
            }
        },
        tooltip: {
            theme: isDark ? 'dark' : 'light',
            style: {
                fontSize: '12px',
                fontFamily: 'Inter, sans-serif'
            },
            custom: undefined,
            fillSeriesColor: false,
            marker: {
                show: true
            }
        },
        legend: {
            labels: {
                colors: colors.textSecondary,
                useSeriesColors: false
            },
            fontSize: '12px',
            fontWeight: 500,
            itemMargin: {
                horizontal: 12,
                vertical: 5
            }
        },
        stroke: {
            lineCap: 'round'
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
                cash_flow_30d: 36575000000,
                confidence: 85.2,
                risk_score: 4.8,
                projects_at_risk: 6
            },
            segmentation: {
                client_segments: [
                    {"name": "Premium", "count": 12, "dso": 68, "revenue": 42750000, "risk": "low"},
                    {"name": "Estándar", "count": 28, "dso": 95, "revenue": 33250000, "risk": "medium"},
                    {"name": "Básico", "count": 15, "dso": 145, "revenue": 19000000, "risk": "high"}
                ],
                size_segments: [
                    {"name": "Grande", "count": 8, "revenue": 57000000, "margin": 18},
                    {"name": "Mediano", "count": 25, "revenue": 28500000, "margin": 22},
                    {"name": "Pequeño", "count": 22, "revenue": 9500000, "margin": 15}
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
        const container = document.getElementById('dso-evolution-chart');
        console.log('🔍 Looking for dso-evolution-chart container:', container);
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
                const value = Math.max(60, baseValue + variation);
                return [timestamp, Math.round(value * 10) / 10]; // Max 1 decimal
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
                        text: 'Días',
                        style: {
                            color: themeConfig.colors.textSecondary,
                            fontSize: '12px',
                            fontWeight: 600
                        }
                    },
                    labels: {
                        formatter: function(value) {
                            return formatNumber(value, 0, 'd');
                        },
                        style: {
                            colors: themeConfig.colors.textSecondary,
                            fontSize: '11px'
                        }
                    },
                    min: 50,
                    tickAmount: 6
                },
                tooltip: {
                    shared: true,
                    intersect: false,
                    theme: themeConfig.tooltip.theme,
                    style: {
                        fontSize: '12px',
                        fontFamily: 'Inter, sans-serif'
                    },
                    x: {
                        format: 'dd MMM yyyy'
                    },
                    y: {
                        formatter: function(value, { seriesIndex }) {
                            if (seriesIndex === 0) {
                                return formatNumber(value, 0, ' días (Real)');
                            }
                            return formatNumber(value, 0, ' días (Objetivo)');
                        }
                    },
                    marker: {
                        show: true
                    }
                },
                dataLabels: {
                    enabled: false
                },
                markers: {
                    size: 4,
                    strokeWidth: 2,
                    strokeColors: '#ffffff',
                    hover: {
                        size: 6
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
        const container = document.getElementById('correlation-matrix');
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
                        borderRadius: 6,
                        horizontal: false,
                        distributed: true,
                        barHeight: '70%',
                        dataLabels: {
                            position: 'top'
                        }
                    }
                },
                colors: [themeConfig.colors.info, themeConfig.colors.warning, themeConfig.colors.danger],
                xaxis: {
                    categories: categories,
                    labels: {
                        style: {
                            fontSize: '11px',
                            colors: themeConfig.colors.textSecondary,
                            fontWeight: 500
                        },
                        rotate: -45,
                        maxHeight: 80
                    }
                },
                yaxis: {
                    title: {
                        text: 'Fuerza de Correlación (%)',
                        style: {
                            color: themeConfig.colors.textSecondary,
                            fontSize: '12px',
                            fontWeight: 600
                        }
                    },
                    max: 100,
                    labels: {
                        formatter: function(value) {
                            return formatNumber(value, 0, '%');
                        },
                        style: {
                            colors: themeConfig.colors.textSecondary,
                            fontSize: '11px'
                        }
                    },
                    tickAmount: 5
                },
                tooltip: {
                    ...themeConfig.tooltip,
                    y: {
                        formatter: function(value, { dataPointIndex }) {
                            const correlation = correlations[dataPointIndex].correlation;
                            const correlationValue = formatNumber(correlation, 1, '');
                            return `${formatNumber(value, 0, '%')} (${correlationValue})`;
                        }
                    }
                },
                dataLabels: {
                    enabled: true,
                    formatter: function(value) {
                        return formatNumber(value, 0, '%');
                    },
                    style: {
                        fontSize: '11px',
                        fontWeight: 600,
                        colors: ['#ffffff']
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
        const container = document.getElementById('cash-flow-prediction');
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
                const value = (base * (1 + (Math.random() - 0.5) * 0.3)) / 1000000; // Convert to millions
                return parseFloat(value.toFixed(1)); // Max 1 decimal
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
                    categories: months,
                    labels: {
                        style: {
                            colors: themeConfig.colors.textSecondary,
                            fontSize: '11px',
                            fontWeight: 500
                        }
                    }
                },
                yaxis: {
                    title: {
                        text: 'Millones (CLP)',
                        style: {
                            color: themeConfig.colors.textSecondary,
                            fontSize: '12px',
                            fontWeight: 600
                        }
                    },
                    labels: {
                        formatter: function(value) {
                            return formatCurrency(value * 1000000, 0);
                        },
                        style: {
                            colors: themeConfig.colors.textSecondary,
                            fontSize: '11px'
                        }
                    },
                    tickAmount: 6
                },
                tooltip: {
                    ...themeConfig.tooltip,
                    y: {
                        formatter: function(value) {
                            return formatCurrency(value * 1000000, 0) + ' CLP';
                        }
                    }
                },
                dataLabels: {
                    enabled: false
                },
                markers: {
                    size: 4,
                    strokeWidth: 2,
                    strokeColors: '#ffffff',
                    hover: {
                        size: 6
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
        const container = document.getElementById('risk-analysis');
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
                    position: 'bottom',
                    fontSize: '12px',
                    fontWeight: 500,
                    markers: {
                        width: 12,
                        height: 12,
                        radius: 6
                    }
                },
                plotOptions: {
                    pie: {
                        donut: {
                            size: '65%',
                            labels: {
                                show: true,
                                total: {
                                    show: true,
                                    label: 'Total Proyectos',
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: themeConfig.colors.textPrimary,
                                    formatter: function() {
                                        return '100%';
                                    }
                                }
                            }
                        },
                        dataLabels: {
                            offset: -10
                        }
                    }
                },
                tooltip: {
                    ...themeConfig.tooltip,
                    y: {
                        formatter: function(value) {
                            return formatNumber(value, 0, '%');
                        }
                    }
                },
                dataLabels: {
                    enabled: true,
                    formatter: function(val) {
                        return formatNumber(val, 0, '%');
                    },
                    style: {
                        fontSize: '12px',
                        fontWeight: 600,
                        colors: ['#ffffff']
                    },
                    dropShadow: {
                        enabled: false
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
        const container = document.getElementById('client-segmentation');
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
                        name: 'Revenue (CLP)',
                        data: segments.map(s => s.revenue / 1000000), // Convert to millions
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
                        borderRadius: 6,
                        horizontal: false,
                        columnWidth: '65%',
                        dataLabels: {
                            position: 'top'
                        }
                    }
                },
                xaxis: {
                    categories: segments.map(s => s.name),
                    labels: {
                        style: {
                            colors: themeConfig.colors.textSecondary,
                            fontSize: '12px',
                            fontWeight: 500
                        }
                    }
                },
                yaxis: {
                    title: {
                        text: 'Valores (DSO días / Revenue M CLP)',
                        style: {
                            color: themeConfig.colors.textSecondary,
                            fontSize: '12px',
                            fontWeight: 600
                        }
                    },
                    labels: {
                        formatter: function(value) {
                            return formatNumber(value, 1, '');
                        },
                        style: {
                            colors: themeConfig.colors.textSecondary,
                            fontSize: '11px'
                        }
                    },
                    tickAmount: 6
                },
                tooltip: {
                    ...themeConfig.tooltip,
                    shared: true,
                    intersect: false,
                    y: {
                        formatter: function(value, { seriesIndex }) {
                            if (seriesIndex === 0) {
                                return formatNumber(value, 0, ' días');
                            }
                            return formatNumber(value, 0, '%');
                        }
                    }
                },
                dataLabels: {
                    enabled: true,
                    formatter: function(value, { seriesIndex }) {
                        if (seriesIndex === 0) {
                            return formatNumber(value, 0, 'd');
                        }
                        return formatNumber(value, 0, '%');
                    },
                    style: {
                        fontSize: '10px',
                        fontWeight: 600,
                        colors: ['#ffffff']
                    }
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
        const container = document.getElementById('size-segmentation');
        console.log('🔍 Looking for sizeSegmentation container:', container);
        if (!container) {
            console.warn('❌ Size Segment chart container not found');
            return;
        }

        try {
            const segments = this.analyticsData.segmentation.size_segments;
            
            const themeConfig = getChartTheme();
            const options = {
                series: segments.map(s => s.revenue / 1000000), // Convert to millions
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
                    position: 'bottom',
                    fontSize: '12px',
                    fontWeight: 500,
                    markers: {
                        width: 12,
                        height: 12,
                        radius: 6
                    }
                },
                plotOptions: {
                    pie: {
                        donut: {
                            size: '50%',
                            labels: {
                                show: true,
                                total: {
                                    show: true,
                                    label: 'Total Revenue (M CLP)',
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: themeConfig.colors.textPrimary,
                                    formatter: function(w) {
                                        const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                                        return '$' + formatNumber(total, 1, 'M');
                                    }
                                }
                            }
                        }
                    }
                },
                tooltip: {
                    ...themeConfig.tooltip,
                    y: {
                        formatter: function(value) {
                            return '$' + formatNumber(value, 1, 'M CLP');
                        }
                    }
                },
                dataLabels: {
                    enabled: true,
                    formatter: function(val, opts) {
                        const value = opts.w.config.series[opts.seriesIndex];
                        return '$' + formatNumber(value, 1, 'M');
                    },
                    style: {
                        fontSize: '12px',
                        fontWeight: 600,
                        colors: ['#ffffff']
                    },
                    dropShadow: {
                        enabled: false
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

    /*
     * Get enhanced chart options with consistent styling
     */
    getEnhancedChartOptions(baseOptions, chartType = 'default') {
        const themeConfig = getChartTheme();
        
        // Common enhancements for all chart types
        const enhancements = {
            chart: {
                ...baseOptions.chart,
                fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                toolbar: {
                    show: false
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800,
                    animateGradually: {
                        enabled: true,
                        delay: 150
                    },
                    dynamicAnimation: {
                        enabled: true,
                        speed: 350
                    }
                },
                dropShadow: {
                    enabled: false
                }
            },
            dataLabels: {
                ...baseOptions.dataLabels,
                style: {
                    fontSize: '11px',
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 600,
                    colors: undefined
                }
            },
            legend: {
                ...baseOptions.legend,
                fontSize: '12px',
                fontFamily: 'Inter, sans-serif',
                fontWeight: 500,
                labels: {
                    colors: themeConfig.colors.textSecondary,
                    useSeriesColors: false
                },
                itemMargin: {
                    horizontal: 10,
                    vertical: 5
                }
            }
        };
        
        // Chart-specific enhancements
        if (chartType === 'bar') {
            enhancements.plotOptions = {
                ...baseOptions.plotOptions,
                bar: {
                    ...baseOptions.plotOptions?.bar,
                    borderRadius: 4,
                    borderRadiusApplication: 'end',
                    borderRadiusWhenStacked: 'last',
                    dataLabels: {
                        position: 'top'
                    }
                }
            };
        } else if (chartType === 'line' || chartType === 'area') {
            enhancements.stroke = {
                ...baseOptions.stroke,
                lineCap: 'round',
                width: chartType === 'area' ? 3 : 4
            };
            enhancements.markers = {
                size: 4,
                colors: undefined,
                strokeColors: '#fff',
                strokeWidth: 2,
                hover: {
                    size: 6
                }
            };
        } else if (chartType === 'donut' || chartType === 'pie') {
            enhancements.plotOptions = {
                ...baseOptions.plotOptions,
                pie: {
                    ...baseOptions.plotOptions?.pie,
                    expandOnClick: true,
                    donut: {
                        ...baseOptions.plotOptions?.pie?.donut,
                        labels: {
                            ...baseOptions.plotOptions?.pie?.donut?.labels,
                            name: {
                                fontSize: '14px',
                                fontFamily: 'Inter, sans-serif',
                                fontWeight: 600,
                                color: themeConfig.colors.textPrimary
                            },
                            value: {
                                fontSize: '16px',
                                fontFamily: 'Inter, sans-serif',
                                fontWeight: 700,
                                color: themeConfig.colors.textPrimary,
                                formatter: function(val) {
                                    return formatNumber(val, 0, '%');
                                }
                            }
                        }
                    }
                }
            };
        }
        
        return {
            ...baseOptions,
            ...enhancements
        };
    }

    /*
     * Get enhanced color palette for charts based on theme
     */
    getChartColorPalette() {
        const colors = getThemeColors();
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark' || 
                      (!document.documentElement.getAttribute('data-theme') && 
                       window.matchMedia('(prefers-color-scheme: dark)').matches);
        
        return {
            primary: isDark ? '#3b82f6' : '#2563eb',
            success: isDark ? '#10b981' : '#059669',
            warning: isDark ? '#f59e0b' : '#d97706',
            danger: isDark ? '#ef4444' : '#dc2626',
            info: isDark ? '#06b6d4' : '#0891b2',
            purple: isDark ? '#8b5cf6' : '#7c3aed',
            orange: isDark ? '#f97316' : '#ea580c',
            gradient: {
                primary: isDark ? ['#3b82f6', '#1d4ed8'] : ['#60a5fa', '#3b82f6'],
                success: isDark ? ['#10b981', '#047857'] : ['#34d399', '#10b981'],
                warning: isDark ? ['#f59e0b', '#b45309'] : ['#fbbf24', '#f59e0b'],
                info: isDark ? ['#06b6d4', '#0e7490'] : ['#22d3ee', '#06b6d4']
            }
        };
    }
}

// Global function for programmatic updates
function updateAnalytics() {
    if (window.analyticsDashboard) {
        window.analyticsDashboard.updateAnalytics();
    } else {
        console.error('❌ Analytics instance not found');
    }
}

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsDashboard;
}
