/**
 * JP Dashboard JavaScript
 * Handles EDP flow charts, KPI animations, and interactive features
 */

class JPDashboard {
  constructor() {
    this.edpFlowChart = null;
    this.originalData = null;
    this.currentFilters = {
      project: 'all',
      period: 'monthly'
    };
    
    this.init();
  }

  init() {
    document.addEventListener('DOMContentLoaded', () => {
      this.initializeCharts();
      this.setupEventListeners();
      this.animateKPICards();
      this.setupTooltips();
      this.initializeWowFeatures();
    });
  }

  /**
   * Initialize all charts
   */
  initializeCharts() {
    this.initEDPFlowChart();
  }

  /**
   * Initialize EDP Flow Chart
   */
  initEDPFlowChart() {
    const ctx = document.getElementById('edpFlowChart');
    if (!ctx) {
      console.warn('EDP Flow Chart canvas not found');
      return;
    }

    // Get data from template (should be passed from backend)
    const trendsDataElement = document.getElementById('trends-data');
    let trendsData = [];
    
    if (trendsDataElement) {
      try {
        const rawData = trendsDataElement.textContent;
        console.log('Raw trends data:', rawData);
        trendsData = JSON.parse(rawData);
        console.log('Parsed trends data:', trendsData);
      } catch (e) {
        console.error('Error parsing trends data:', e);
        console.log('Using sample data instead');
        trendsData = this.generateSampleData();
      }
    } else {
      console.warn('No trends-data element found, using sample data');
      trendsData = this.generateSampleData();
    }

    // Validate data structure
    if (!Array.isArray(trendsData) || trendsData.length === 0) {
      console.warn('Invalid or empty trends data, using sample data');
      trendsData = this.generateSampleData();
    }

    this.originalData = trendsData;

    const chartConfig = {
      type: 'bar',
      data: {
        labels: trendsData.map(trend => trend.month),
        datasets: [
          {
            label: 'EDPs Enviados',
            data: trendsData.map(trend => trend.edps_sent || 0),
            backgroundColor: 'rgba(139, 92, 246, 0.8)',
            borderColor: '#8b5cf6',
            borderWidth: 2,
            borderRadius: 8,
            borderSkipped: false,
            hoverBackgroundColor: 'rgba(139, 92, 246, 0.9)',
            hoverBorderColor: '#7c3aed',
            hoverBorderWidth: 3,
          },
          {
            label: 'EDPs Aprobados',
            data: trendsData.map(trend => trend.edps_approved || 0),
            backgroundColor: 'rgba(59, 130, 246, 0.8)',
            borderColor: '#3b82f6',
            borderWidth: 2,
            borderRadius: 8,
            borderSkipped: false,
            hoverBackgroundColor: 'rgba(59, 130, 246, 0.9)',
            hoverBorderColor: '#2563eb',
            hoverBorderWidth: 3,
          },
          {
            label: 'EDPs Pagados',
            data: trendsData.map(trend => trend.edps_paid || 0),
            backgroundColor: 'rgba(16, 185, 129, 0.8)',
            borderColor: '#10b981',
            borderWidth: 2,
            borderRadius: 8,
            borderSkipped: false,
            hoverBackgroundColor: 'rgba(16, 185, 129, 0.9)',
            hoverBorderColor: '#059669',
            hoverBorderWidth: 3,
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
        layout: {
          padding: {
            top: 20,
            right: 20,
            bottom: 20,
            left: 20
          }
        },
        scales: {
          x: {
            display: true,
            grid: {
              display: true,
              color: 'rgba(0, 0, 0, 0.1)',
              drawBorder: false
            },
            ticks: {
              maxRotation: 45,
              minRotation: 0,
              font: {
                size: 12,
                weight: '500'
              },
              color: '#6b7280'
            },
            title: {
              display: true,
              text: 'Período',
              font: {
                size: 14,
                weight: '600'
              },
              color: '#374151'
            }
          },
          y: {
            display: true,
            beginAtZero: true,
            grid: {
              display: true,
              color: 'rgba(0, 0, 0, 0.1)',
              drawBorder: false
            },
            ticks: {
              font: {
                size: 12,
                weight: '500'
              },
              color: '#6b7280',
              callback: function(value) {
                return value + ' EDPs';
              }
            },
            title: {
              display: true,
              text: 'Cantidad de EDPs',
              font: {
                size: 14,
                weight: '600'
              },
              color: '#374151'
            }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            align: 'center',
            labels: {
              usePointStyle: true,
              padding: 20,
              font: {
                size: 13,
                weight: '600'
              },
              color: '#374151',
              generateLabels: function(chart) {
                const original = Chart.defaults.plugins.legend.labels.generateLabels;
                const labels = original.call(this, chart);
                
                labels.forEach((label, index) => {
                  label.pointStyle = 'rectRounded';
                  label.pointStyleWidth = 12;
                  label.pointStyleHeight = 12;
                });
                
                return labels;
              }
            }
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: 'rgba(255, 255, 255, 0.2)',
            borderWidth: 1,
            cornerRadius: 12,
            padding: 12,
            titleFont: {
              size: 14,
              weight: '600'
            },
            bodyFont: {
              size: 13,
              weight: '500'
            },
            callbacks: {
              title: function(context) {
                return `Período: ${context[0].label}`;
              },
              label: function(context) {
                const label = context.dataset.label || '';
                const value = context.parsed.y;
                return `${label}: ${value} EDPs`;
              },
              afterBody: function(context) {
                if (context.length > 0) {
                  const dataIndex = context[0].dataIndex;
                  const data = trendsData[dataIndex];
                  if (data && data.total_amount) {
                    return [``, `Monto total: ${this.formatCurrency(data.total_amount)}`];
                  }
                }
                return [];
              }
            }
          }
        },
        animation: {
          duration: 1000,
          easing: 'easeInOutQuart',
          onComplete: function() {
            // Animation complete callback
            console.log('EDP Flow Chart animation completed');
          }
        }
      }
    };

    this.edpFlowChart = new Chart(ctx, chartConfig);
  }

  /**
   * Generate sample data for development/testing
   */
  generateSampleData() {
    const currentDate = new Date();
    const months = [];
    
    // Generate last 6 months
    for (let i = 5; i >= 0; i--) {
      const monthDate = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
      const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
      const monthName = monthNames[monthDate.getMonth()];
      
      const edpsSent = Math.floor(Math.random() * 15) + 5;
      const edpsApproved = Math.floor(edpsSent * 0.8); // 80% approval rate
      const edpsPaid = Math.floor(edpsApproved * 0.7); // 70% payment rate
      
      months.push({
        month: monthName,
        month_key: monthDate.toISOString().slice(0, 7),
        edps_sent: edpsSent,
        edps_approved: edpsApproved,
        edps_paid: edpsPaid,
        amount_proposed: Math.floor(Math.random() * 50000000) + 10000000,
        amount_approved: Math.floor(Math.random() * 40000000) + 8000000,
        amount_paid: Math.floor(Math.random() * 30000000) + 5000000
      });
    }
    
    console.log('Generated sample data:', months);
    return months;
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // EDP Flow Chart filters
    const projectFilter = document.getElementById('edpFlowFilter');
    const periodFilter = document.getElementById('edpPeriodFilter');

    if (projectFilter) {
      projectFilter.addEventListener('change', (e) => {
        this.currentFilters.project = e.target.value;
        this.updateEDPChart();
      });
    }

    if (periodFilter) {
      periodFilter.addEventListener('change', (e) => {
        this.currentFilters.period = e.target.value;
        this.updateEDPChart();
      });
    }

    // Responsive chart resize
    window.addEventListener('resize', this.debounce(() => {
      if (this.edpFlowChart) {
        this.edpFlowChart.resize();
      }
    }, 250));

    // Enhanced table interactions
    this.setupTableInteractions();
  }

  /**
   * Update EDP Chart based on filters
   */
  updateEDPChart() {
    if (!this.edpFlowChart || !this.originalData) return;

    this.showChartLoading();

    // Simulate API call delay
    setTimeout(() => {
      let filteredData = [...this.originalData];

      // Apply project filter
      if (this.currentFilters.project !== 'all') {
        // In a real implementation, this would filter by project
        console.log(`Filtering by project: ${this.currentFilters.project}`);
      }

      // Apply period filter
      if (this.currentFilters.period === 'quarterly') {
        filteredData = this.aggregateToQuarterly(filteredData);
      }

      // Update chart data
      this.edpFlowChart.data.labels = filteredData.map(item => item.month);
      this.edpFlowChart.data.datasets[0].data = filteredData.map(item => item.edps_sent || 0);
      this.edpFlowChart.data.datasets[1].data = filteredData.map(item => item.edps_approved || 0);
      this.edpFlowChart.data.datasets[2].data = filteredData.map(item => item.edps_paid || 0);

      this.edpFlowChart.update('active');
      this.hideChartLoading();

      // Show success notification
      JPDashboardUtils.showNotification(
        `Gráfico actualizado: ${this.currentFilters.project === 'all' ? 'Todos los proyectos' : this.currentFilters.project} - ${this.currentFilters.period === 'monthly' ? 'Vista mensual' : 'Vista trimestral'}`,
        'success',
        2000
      );

      console.log('EDP Chart updated with filters:', this.currentFilters);
    }, 500);
  }

  /**
   * Aggregate monthly data to quarterly
   */
  aggregateToQuarterly(monthlyData) {
    const quarters = [];
    const quarterNames = ['Q1', 'Q2', 'Q3', 'Q4'];
    
    for (let i = 0; i < 4; i++) {
      const startIndex = i * 3;
      const quarterData = monthlyData.slice(startIndex, startIndex + 3);
      
      if (quarterData.length > 0) {
        quarters.push({
          month: quarterNames[i],
          edps_sent: quarterData.reduce((sum, item) => sum + (item.edps_sent || 0), 0),
          edps_approved: quarterData.reduce((sum, item) => sum + (item.edps_approved || 0), 0),
          edps_paid: quarterData.reduce((sum, item) => sum + (item.edps_paid || 0), 0),
          total_amount: quarterData.reduce((sum, item) => sum + (item.total_amount || 0), 0)
        });
      }
    }
    
    return quarters;
  }

  /**
   * Show chart loading state
   */
  showChartLoading() {
    const chartContainer = document.querySelector('#edpFlowChart').parentElement;
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chart-loading';
    loadingDiv.id = 'chart-loading';
    loadingDiv.innerHTML = 'Actualizando gráfico...';
    
    chartContainer.appendChild(loadingDiv);
    document.getElementById('edpFlowChart').style.opacity = '0.3';
  }

  /**
   * Hide chart loading state
   */
  hideChartLoading() {
    const loadingDiv = document.getElementById('chart-loading');
    if (loadingDiv) {
      loadingDiv.remove();
    }
    document.getElementById('edpFlowChart').style.opacity = '1';
  }

  /**
   * Animate KPI cards on load
   */
  animateKPICards() {
    const kpiCards = document.querySelectorAll('.kpi-card');
    kpiCards.forEach((card, index) => {
      card.style.opacity = '0';
      card.style.transform = 'translateY(30px)';
      
      setTimeout(() => {
        card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      }, index * 100);
    });
  }

  /**
   * Setup enhanced tooltips
   */
  setupTooltips() {
    const tooltipElements = document.querySelectorAll('[title]');
    tooltipElements.forEach(element => {
      const title = element.getAttribute('title');
      element.removeAttribute('title');
      element.setAttribute('data-tooltip', title);
      element.classList.add('tooltip');
    });
  }

  /**
   * Setup table interactions
   */
  setupTableInteractions() {
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(row => {
      row.classList.add('project-table-row');
      
      row.addEventListener('mouseenter', () => {
        row.style.transform = 'translateX(4px)';
        row.style.borderLeftColor = 'var(--accent-blue)';
      });
      
      row.addEventListener('mouseleave', () => {
        row.style.transform = 'translateX(0)';
        row.style.borderLeftColor = 'transparent';
      });
    });
  }

  /**
   * Format currency values
   */
  formatCurrency(amount) {
    return JPDashboardUtils.formatCurrency(amount);
  }

  /**
   * Debounce function for performance
   */
  debounce(func, wait) {
    return JPDashboardUtils.debounce(func, wait);
  }

  /**
   * Update chart theme based on system preference
   */
  updateChartTheme() {
    if (!this.edpFlowChart) return;

    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

    this.edpFlowChart.options.scales.x.ticks.color = textColor;
    this.edpFlowChart.options.scales.y.ticks.color = textColor;
    this.edpFlowChart.options.scales.x.grid.color = gridColor;
    this.edpFlowChart.options.scales.y.grid.color = gridColor;
    this.edpFlowChart.options.plugins.legend.labels.color = textColor;

    this.edpFlowChart.update('none');
  }

  /**
   * Export chart as image
   */
  exportChart(format = 'png') {
    if (!this.edpFlowChart) return;

    const link = document.createElement('a');
    link.download = `edp-flow-chart.${format}`;
    link.href = this.edpFlowChart.toBase64Image();
    link.click();
  }

  /**
   * Refresh dashboard data
   */
  refreshDashboard() {
    console.log('Refreshing dashboard data...');
    
    // Show loading state
    const refreshButton = document.querySelector('[data-refresh]');
    if (refreshButton) {
      refreshButton.disabled = true;
      refreshButton.innerHTML = '<span class="animate-spin">⟳</span> Actualizando...';
    }

    // Simulate API call
    setTimeout(() => {
      // In a real implementation, this would fetch new data from the server
      this.updateEDPChart();
      
      if (refreshButton) {
        refreshButton.disabled = false;
        refreshButton.innerHTML = '⟳ Actualizar';
      }
      
      console.log('Dashboard refreshed successfully');
    }, 1000);
  }

  /**
   * Initialize wow factor features
   */
  initializeWowFeatures() {
    // Add pulse effect to critical metrics
    this.addPulseEffects();
    
    // Initialize number counters
    this.initializeCounters();
    
    // Add interactive tooltips
    this.initializeAdvancedTooltips();
    
    // Initialize notification system
    this.initializeNotifications();
    
    // Add keyboard shortcuts
    this.initializeKeyboardShortcuts();
    
    // Initialize status circle animations
    this.initializeStatusCircles();
  }

  /**
   * Add pulse effects to critical metrics
   */
  addPulseEffects() {
    // Add pulse to overdue projects if > 0
    const overdueElement = document.querySelector('.project-status-circle.overdue');
    const overdueCount = parseInt(overdueElement?.querySelector('.status-number')?.textContent || '0');
    
    if (overdueCount > 0) {
      overdueElement?.classList.add('pulse');
    }
    
    // Add pulse to high pending amounts
    const pendingAmountElements = document.querySelectorAll('.kpi-value[data-value]');
    pendingAmountElements.forEach(element => {
      const value = parseFloat(element.dataset.value || '0');
      if (value > 50000000) { // 50M threshold
        element.closest('.kpi-card')?.classList.add('pulse');
      }
    });
  }

  /**
   * Initialize animated number counters
   */
  initializeCounters() {
    const kpiValues = document.querySelectorAll('.kpi-value[data-value]');
    
    kpiValues.forEach((element, index) => {
      const targetValue = parseFloat(element.dataset.value || '0');
      const originalText = element.textContent;
      const isPercentage = originalText.includes('%');
      const isCurrency = originalText.includes('$') || originalText.includes('CLP');
      const isDays = originalText.includes('d');
      
      // Reset to 0 for animation
      if (isCurrency) {
        element.textContent = JPDashboardUtils.formatCurrency(0);
      } else if (isPercentage) {
        element.textContent = '0%';
      } else if (isDays) {
        element.textContent = '0d';
      } else {
        element.textContent = '0';
      }
      
      setTimeout(() => {
        this.animateCounter(element, 0, targetValue, 1500, isPercentage, isCurrency, isDays);
      }, index * 200 + 500);
    });
  }

  /**
   * Animate counter from start to end value
   */
  animateCounter(element, start, end, duration, isPercentage = false, isCurrency = false, isDays = false) {
    const startTime = performance.now();
    
    const updateCounter = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      const currentValue = start + (end - start) * easeOutQuart;
      
      // Format the value based on type
      let displayValue;
      if (isCurrency) {
        displayValue = JPDashboardUtils.formatCurrency(currentValue);
      } else if (isPercentage) {
        displayValue = Math.round(currentValue) + '%';
      } else if (isDays) {
        displayValue = Math.round(currentValue) + 'd';
      } else {
        displayValue = Math.round(currentValue).toLocaleString();
      }
      
      element.textContent = displayValue;
      
      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      }
    };
    
    requestAnimationFrame(updateCounter);
  }

  /**
   * Initialize advanced interactive tooltips
   */
  initializeAdvancedTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
      element.addEventListener('mouseenter', (e) => {
        this.showAdvancedTooltip(e.target, e.target.dataset.tooltip);
      });
      
      element.addEventListener('mouseleave', () => {
        this.hideAdvancedTooltip();
      });
    });
  }

  /**
   * Show advanced tooltip
   */
  showAdvancedTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip-popup';
    tooltip.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 14px;">💡</span>
        <span>${text}</span>
      </div>
    `;
    tooltip.style.cssText = `
      position: absolute;
      background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(30, 30, 30, 0.9));
      color: white;
      padding: 12px 16px;
      border-radius: 8px;
      font-size: 13px;
      white-space: nowrap;
      z-index: 1000;
      pointer-events: none;
      opacity: 0;
      transform: translateY(10px) scale(0.9);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.1);
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 12 + 'px';
    
    // Animate in
    setTimeout(() => {
      tooltip.style.opacity = '1';
      tooltip.style.transform = 'translateY(0) scale(1)';
    }, 10);
    
    this.currentTooltip = tooltip;
  }

  /**
   * Hide advanced tooltip
   */
  hideAdvancedTooltip() {
    if (this.currentTooltip) {
      this.currentTooltip.style.opacity = '0';
      this.currentTooltip.style.transform = 'translateY(10px) scale(0.9)';
      
      setTimeout(() => {
        if (this.currentTooltip && this.currentTooltip.parentNode) {
          this.currentTooltip.parentNode.removeChild(this.currentTooltip);
        }
        this.currentTooltip = null;
      }, 300);
    }
  }

  /**
   * Initialize notification system
   */
  initializeNotifications() {
    // Show welcome notification
    setTimeout(() => {
      this.showNotification('🚀 Dashboard cargado exitosamente', 'success', 3000);
    }, 2000);
  }

  /**
   * Show notification
   */
  showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 16px;">${this.getNotificationIcon(type)}</span>
        <span style="font-weight: 500;">${message}</span>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Auto remove
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, duration);
  }

  /**
   * Get notification icon
   */
  getNotificationIcon(type) {
    const icons = {
      success: '✅',
      warning: '⚠️',
      error: '❌',
      info: 'ℹ️'
    };
    return icons[type] || icons.info;
  }

  /**
   * Initialize keyboard shortcuts
   */
  initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl/Cmd + E: Export data
      if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        this.exportDashboardData();
      }
      
      // Escape: Hide tooltips
      if (e.key === 'Escape') {
        this.hideAdvancedTooltip();
      }
    });
  }

  /**
   * Initialize status circle animations
   */
  initializeStatusCircles() {
    const statusCircles = document.querySelectorAll('.project-status-circle');
    
    statusCircles.forEach((circle, index) => {
      const number = circle.querySelector('.status-number');
      if (number) {
        // Initial state for animation
        circle.style.transform = 'scale(0.8)';
        circle.style.opacity = '0.5';
        
        // Add click animation
        circle.addEventListener('click', () => {
          number.classList.add('animate');
          setTimeout(() => number.classList.remove('animate'), 600);
          
          // Show contextual notification
          const status = circle.classList.contains('overdue') ? 'vencidos' :
                        circle.classList.contains('completed') ? 'completados' :
                        circle.classList.contains('in-progress') ? 'en progreso' : 'pendientes';
          
          this.showNotification(`📊 ${number.textContent} proyectos ${status}`, 'info', 2000);
        });
        
        // Staggered entrance animation
        setTimeout(() => {
          circle.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
          circle.style.transform = 'scale(1)';
          circle.style.opacity = '1';
        }, index * 150 + 1000);
      }
    });
  }

  /**
   * Export dashboard data
   */
  exportDashboardData() {
    const data = {
      timestamp: new Date().toISOString(),
      chartData: this.originalData,
      filters: {
        project: document.getElementById('edpFlowFilter')?.value,
        period: document.getElementById('edpPeriodFilter')?.value
      }
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dashboard-data-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    this.showNotification('📁 Datos exportados exitosamente', 'success', 3000);
  }

}

// Initialize dashboard when DOM is ready
const jpDashboard = new JPDashboard();

// Listen for theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  jpDashboard.updateChartTheme();
});

// Global functions for external access
window.jpDashboard = jpDashboard; 