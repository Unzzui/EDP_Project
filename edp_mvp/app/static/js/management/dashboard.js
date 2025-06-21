/**
 * Dashboard Manager JavaScript
 * Maneja todas las interacciones del dashboard ejecutivo
 */

class DashboardManager {
    constructor() {
        this.refreshCount = 0;
        this.currentPeriod = '30D';
        this.chartData = {};
        this.kpiData = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeDashboard();
        this.setupAutoRefresh();
        this.setupKeyboardShortcuts();
    }

    setupEventListeners() {
        // Analytics period controls
        document.querySelectorAll(".analytics-button").forEach((button) => {
            button.addEventListener("click", (e) => {
                this.handlePeriodChange(e.target);
            });
        });

        // Alert card interactions
        document.querySelectorAll(".alert-card").forEach((card) => {
            card.addEventListener("click", (e) => {
                this.handleAlertClick(e);
            });
        });

        // Alert action buttons
        document.querySelectorAll(".alert-action").forEach((button) => {
            button.addEventListener("click", (e) => {
                this.handleAlertAction(e);
            });
        });

        // Team member interactions
        document.querySelectorAll(".team-member").forEach((member) => {
            member.addEventListener("click", (e) => {
                this.handleTeamMemberClick(e);
            });
        });
    }

    handlePeriodChange(button) {
        // Remove active class from all buttons
        document.querySelectorAll(".analytics-button").forEach(b => 
            b.classList.remove("active")
        );
        
        // Add active class to clicked button
        button.classList.add("active");
        
        // Update current period
        this.currentPeriod = button.textContent.trim();
        
        // Update chart data based on period
        this.updateChartForPeriod(this.currentPeriod);
        
        // Animate chart bars
        this.animateChartBars();
    }

    updateChartForPeriod(period) {
        const chartContainer = document.querySelector('#dynamicChart');
        if (!chartContainer) return;

        // Generate data based on period
        const data = this.generateChartDataForPeriod(period);
        
        // Clear existing bars
        chartContainer.innerHTML = '';
        
        // Calculate max value for scaling
        const maxValue = Math.max(...data.map(d => d.value));
        
        // Create new bars
        data.forEach((item, index) => {
            const percentage = maxValue > 0 ? (item.value / maxValue * 100) : 0;
            
            const barElement = document.createElement('div');
            barElement.className = 'chart-bar';
            barElement.style.height = `${percentage}%`;
            barElement.setAttribute('data-value', item.value);
            barElement.setAttribute('data-label', item.label);
            
            barElement.innerHTML = `
                <div class="bar-value">$${item.value.toFixed(1)}M</div>
                <div class="bar-label">${item.label}</div>
            `;
            
            chartContainer.appendChild(barElement);
        });
        
        // Add animation delay for visual effect
        setTimeout(() => {
            this.animateChartBars();
        }, 100);
    }

    generateChartDataForPeriod(period) {
        // Get real data from global variables if available
        const hasRealData = window.chartsData && window.chartsData.cash_in_forecast;
        
        if (hasRealData && period === '30D') {
            return this.processRealChartData(period);
        }
        
        // Generate realistic mock data based on period and KPIs
        const baseValue = window.kpisData && window.kpisData.monto_pendiente 
            ? window.kpisData.monto_pendiente / 1000000 
            : window.kpisData && window.kpisData.ingresos_totales
            ? window.kpisData.ingresos_totales * 0.3
            : 5.0;

        switch (period) {
            case '7D':
                return [
                    { value: baseValue * 0.6, label: 'Lun' },
                    { value: baseValue * 1.2, label: 'Mar' },
                    { value: baseValue * 0.9, label: 'Mié' },
                    { value: baseValue * 1.6, label: 'Jue' },
                    { value: baseValue * 2.1, label: 'Vie' },
                    { value: baseValue * 0.3, label: 'Sáb' },
                    { value: baseValue * 0.1, label: 'Dom' }
                ];
            case '30D':
            default:
                return [
                    { value: baseValue * 0.4, label: '1-10 días' },
                    { value: baseValue * 0.6, label: '11-20 días' },
                    { value: baseValue * 0.8, label: '21-30 días' }
                ];
            case '90D':
                return [
                    { value: baseValue * 1.2, label: 'Mes 1' },
                    { value: baseValue * 1.8, label: 'Mes 2' },
                    { value: baseValue * 2.2, label: 'Mes 3' }
                ];
            case '1Y':
                const yearlyBase = baseValue * 3;
                return [
                    { value: yearlyBase * 0.8, label: 'Q1 2025' },
                    { value: yearlyBase * 1.1, label: 'Q2 2025' },
                    { value: yearlyBase * 1.3, label: 'Q3 2025' },
                    { value: yearlyBase * 1.0, label: 'Q4 2025' }
                ];
        }
    }

    processRealChartData(period) {
        const cashForecast = window.chartsData.cash_in_forecast;
        if (!cashForecast || !cashForecast.datasets || !cashForecast.datasets[0]) {
            return this.generateChartDataForPeriod(period);
        }

        const data = cashForecast.datasets[0].data;
        const labels = cashForecast.labels;

        // Adapt data based on period
        return data.map((value, index) => ({
            value: value,
            label: labels[index] || `Período ${index + 1}`
        }));
    }

    handleAlertClick(event) {
        if (!event.target.classList.contains("alert-action")) {
            const card = event.currentTarget;
            card.style.transform = "translateY(-8px)";
            card.style.boxShadow = "var(--shadow-elevated)";

            setTimeout(() => {
                card.style.transform = "";
                card.style.boxShadow = "";
            }, 300);
        }
    }

    handleAlertAction(event) {
        event.stopPropagation();
        const action = event.target.textContent;
        console.log(`Executing action: ${action}`);

        // Visual feedback
        event.target.style.transform = "scale(0.95)";
        setTimeout(() => {
            event.target.style.transform = "";
        }, 150);

        // Here you could add actual action handling
        this.executeAlertAction(action);
    }

    executeAlertAction(action) {
        // Placeholder for actual alert actions
        switch (action.toLowerCase()) {
            case 'resolver':
                console.log('Resolviendo alerta...');
                break;
            case 'delegar':
                console.log('Delegando alerta...');
                break;
            case 'reasignar':
                console.log('Reasignando recursos...');
                break;
            case 'acelerar':
                console.log('Acelerando proyecto...');
                break;
            default:
                console.log(`Acción: ${action}`);
        }
    }

    handleTeamMemberClick(event) {
        const member = event.currentTarget;
        member.style.background = "rgba(0, 255, 136, 0.1)";
        member.style.borderColor = "rgba(0, 255, 136, 0.2)";

        setTimeout(() => {
            member.style.background = "";
            member.style.borderColor = "";
        }, 300);
    }

    // Real-time clock
    updateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString("es-ES", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
        const dateString = now.toLocaleDateString("es-ES", {
            weekday: "long",
            year: "numeric",
            month: "short",
            day: "numeric",
        });

        const timeElement = document.getElementById("currentTime");
        const dateElement = document.getElementById("currentDate");
        
        if (timeElement) {
            timeElement.textContent = timeString;
        }
        if (dateElement) {
            dateElement.textContent = dateString.charAt(0).toUpperCase() + dateString.slice(1);
        }
    }

    // Animated KPI counter
    animateKPI() {
        const element = document.getElementById("kpiValue");
        if (!element) return;

        const target = window.kpisData && window.kpisData.ingresos_totales 
            ? parseFloat(window.kpisData.ingresos_totales) 
            : 0.0;
        
        let current = 0;
        const increment = target / 100;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = `${current.toFixed(1)}M`;
        }, 30);
    }

    // Chart bar animations
    animateChartBars() {
        const bars = document.querySelectorAll(".chart-bar");
        bars.forEach((bar, index) => {
            const originalHeight = bar.style.height;
            bar.style.height = "0%";

            setTimeout(() => {
                bar.style.height = originalHeight;
            }, index * 100);
        });
    }

    // Progress bar animations
    animateProgressBars() {
        const progressBars = document.querySelectorAll(".progress-bar-fill");
        progressBars.forEach((bar, index) => {
            const originalWidth = bar.style.width;
            bar.style.width = "0%";

            setTimeout(() => {
                bar.style.width = originalWidth;
            }, index * 200);
        });
    }

    // Initialize dashboard
    initializeDashboard() {
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);

        setTimeout(() => {
            this.animateKPI();
            this.animateProgressBars();
            this.initializeChart();
            this.animateChartBars();
        }, 500);
    }

    // Initialize chart with default period
    initializeChart() {
        // Find active button or default to 30D
        const activeButton = document.querySelector('.analytics-button.active');
        if (activeButton) {
            this.currentPeriod = activeButton.textContent.trim();
        }
        
        // Update chart with current period
        this.updateChartForPeriod(this.currentPeriod);
    }

    setupKeyboardShortcuts() {
        document.addEventListener("keydown", (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case "r":
                        e.preventDefault();
                        window.location.reload();
                        break;
                    case "d":
                        e.preventDefault();
                        console.log("Dashboard debug mode");
                        this.toggleDebugMode();
                        break;
                }
            }
        });
    }

    toggleDebugMode() {
        console.log("=== DASHBOARD DEBUG INFO ===");
        console.log("Current Period:", this.currentPeriod);
        console.log("Charts Data:", window.chartsData);
        console.log("KPIs Data:", window.kpisData);
        console.log("Equipo Data:", window.equipoData);
        console.log("Alertas Data:", window.alertasData);
        console.log("Refresh Count:", this.refreshCount);
        console.log("Chart Bars Count:", document.querySelectorAll('.chart-bar').length);
        
        // Test chart data generation
        console.log("Generated Data for Current Period:", this.generateChartDataForPeriod(this.currentPeriod));
        console.log("============================");
    }

    setupAutoRefresh() {
        setInterval(() => {
            this.refreshCount++;
            const syncStatus = document.querySelector(".sync-status span:last-child");
            if (syncStatus) {
                syncStatus.textContent = `Última actualización: hace ${Math.floor(Math.random() * 30) + 1}s`;
            }

            // Simulate data updates
            if (this.refreshCount % 5 === 0) {
                document.querySelectorAll(".context-dot").forEach(dot => {
                    dot.style.opacity = "0.5";
                    setTimeout(() => {
                        dot.style.opacity = "1";
                    }, 200);
                });
            }
        }, 10000);
    }

    // Public method to update data from external sources
    updateData(kpis, charts) {
        console.log("Updating dashboard data...");
        window.kpisData = kpis;
        window.chartsData = charts;
        
        // Update chart with new data
        this.updateChartForPeriod(this.currentPeriod);
        
        // Update KPI animation
        this.animateKPI();
        
        console.log("Dashboard data updated successfully");
    }

    // Refresh dashboard data via AJAX (optional)
    async refreshData() {
        try {
            const response = await fetch('/management/dashboard/refresh');
            if (response.ok) {
                const data = await response.json();
                this.updateData(data.kpis, data.charts);
            }
        } catch (error) {
            console.error('Error refreshing dashboard data:', error);
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    window.dashboardManager = new DashboardManager();
});
