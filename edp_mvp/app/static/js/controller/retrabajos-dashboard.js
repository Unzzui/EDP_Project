/**
 * Re-trabajos Dashboard JavaScript
 * Sistema de análisis de re-trabajos con funcionalidades avanzadas
 */

class RetrabajosDashboard {
  constructor() {
    this.colors = [
      'rgba(99, 102, 241, 0.85)',    // Indigo
      'rgba(16, 185, 129, 0.85)',    // Emerald
      'rgba(245, 158, 11, 0.85)',    // Amber
      'rgba(236, 72, 153, 0.85)',    // Pink
      'rgba(6, 182, 212, 0.85)',     // Cyan
      'rgba(139, 92, 246, 0.85)',    // Purple
      'rgba(202, 138, 4, 0.85)',     // Yellow-600
      'rgba(220, 38, 38, 0.85)',     // Red
      'rgba(5, 150, 105, 0.85)',     // Green
      'rgba(59, 130, 246, 0.85)'     // Blue
    ];
    
    // Table pagination properties
    this.currentPage = 1;
    this.rowsPerPage = 10;
    this.sortColumn = '';
    this.sortDirection = 'asc';
    this.tableRows = [];
    
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.initializeComponents();
    this.initializeCharts();
    this.initializeTable();
    this.updateTime();
    this.animateStatCards();
  }

  setupEventListeners() {
    // Filter toggle functionality
    const toggleButton = document.getElementById("toggleFilters");
    const filterPanel = document.getElementById("filterPanel");
    
    if (toggleButton && filterPanel) {
      toggleButton.addEventListener("click", () => {
        filterPanel.classList.toggle("hidden");
        const isVisible = !filterPanel.classList.contains("hidden");
        
        // Update button text and animation
        const icon = toggleButton.querySelector("svg");
        if (icon) {
          icon.style.transform = isVisible ? "rotate(180deg)" : "rotate(0deg)";
        }
      });
    }

    // Form reset functionality
    const resetButton = document.querySelector('button[type="reset"]');
    if (resetButton) {
      resetButton.addEventListener("click", () => {
        // Clear all form fields
        const form = resetButton.closest("form");
        if (form) {
          form.reset();
          // Clear hidden date fields
          const fechaDesde = document.getElementById("fecha_desde");
          const fechaHasta = document.getElementById("fecha_hasta");
          if (fechaDesde) fechaDesde.value = "";
          if (fechaHasta) fechaHasta.value = "";
          
          // Clear date range picker
          const dateRange = document.getElementById("dateRange");
          if (dateRange) dateRange.value = "";
        }
      });
    }

    // Table row hover effects
    document.querySelectorAll('.data-table tbody tr').forEach(row => {
      row.addEventListener('mouseenter', () => {
        row.style.backgroundColor = 'var(--bg-tertiary)';
      });
      
      row.addEventListener('mouseleave', () => {
        row.style.backgroundColor = '';
      });
    });

    // Setup chart download buttons
    this.setupChartDownloads();
    
    // Setup project toggle
    this.setupProjectToggle();
  }

  initializeComponents() {
    // Initialize date range picker
    this.initDateRangePicker();
    
    // Initialize tooltips
    this.initTooltips();
    
    // Initialize progress bars
    this.animateProgressBars();
  }

  initDateRangePicker() {
    if (typeof jQuery !== 'undefined' && typeof moment !== 'undefined') {
      const dateRangeElement = document.getElementById('dateRange');
      if (!dateRangeElement) return;

      jQuery(document).ready(($) => {
        if ($.fn.daterangepicker) {
          $('#dateRange').daterangepicker({
            autoUpdateInput: false,
            opens: 'left',
            locale: {
              format: 'DD/MM/YYYY',
              separator: ' - ',
              applyLabel: 'Aplicar',
              cancelLabel: 'Limpiar',
              fromLabel: 'Desde',
              toLabel: 'Hasta',
              customRangeLabel: 'Personalizado',
              weekLabel: 'S',
              daysOfWeek: ['Do', 'Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa'],
              monthNames: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
              firstDay: 1
            },
            ranges: {
              'Hoy': [moment(), moment()],
              'Ayer': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
              'Últimos 7 días': [moment().subtract(6, 'days'), moment()],
              'Últimos 30 días': [moment().subtract(29, 'days'), moment()],
              'Este mes': [moment().startOf('month'), moment().endOf('month')],
              'Último mes': [moment().subtract(1, 'month').startOf('month'), 
                            moment().subtract(1, 'month').endOf('month')]
            }
          });

          $('#dateRange').on('apply.daterangepicker', (ev, picker) => {
            $(ev.target).val(picker.startDate.format('YYYY-MM-DD') + ' - ' + picker.endDate.format('YYYY-MM-DD'));
            $('#fecha_desde').val(picker.startDate.format('YYYY-MM-DD'));
            $('#fecha_hasta').val(picker.endDate.format('YYYY-MM-DD'));
          });

          $('#dateRange').on('cancel.daterangepicker', (ev, picker) => {
            $(ev.target).val('');
            $('#fecha_desde').val('');
            $('#fecha_hasta').val('');
          });
        } else {
          console.warn('DateRangePicker no está disponible.');
        }
      });
    } else {
      console.warn('jQuery o Moment.js no están disponibles para DateRangePicker.');
      // Implementación alternativa sin jQuery
      const dateRange = document.getElementById('dateRange');
      if (dateRange) {
        dateRange.addEventListener('change', function() {
          const dateParts = this.value.split(' - ');
          if (dateParts.length === 2) {
            const fechaDesde = document.getElementById('fecha_desde');
            const fechaHasta = document.getElementById('fecha_hasta');
            if (fechaDesde) fechaDesde.value = dateParts[0];
            if (fechaHasta) fechaHasta.value = dateParts[1];
          }
        });
      }
    }
  }

  initTooltips() {
    // Enhanced tooltip functionality
    document.querySelectorAll('.custom-tooltip').forEach(tooltip => {
      const tooltipText = tooltip.querySelector('.tooltip-text');
      if (tooltipText) {
        tooltip.addEventListener('mouseenter', () => {
          tooltipText.style.visibility = 'visible';
          tooltipText.style.opacity = '1';
        });
        
        tooltip.addEventListener('mouseleave', () => {
          tooltipText.style.visibility = 'hidden';
          tooltipText.style.opacity = '0';
        });
      }
    });
  }

  animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar-fill, [style*="width:"]');
    
    progressBars.forEach((bar, index) => {
      const width = bar.style.width || bar.getAttribute('style').match(/width:\s*(\d+%)/)?.[1] || '0%';
      
      // Reset width for animation
      bar.style.width = '0%';
      bar.style.transition = 'width 1s ease-in-out';
      
      // Animate to target width
      setTimeout(() => {
        bar.style.width = width;
      }, index * 100 + 200);
    });
  }

  animateStatCards() {
    const statCards = document.querySelectorAll('.stat-card');
    
    statCards.forEach((card, index) => {
      card.style.setProperty('--order', index + 1);
      card.style.opacity = '0';
      card.style.transform = 'translateY(20px)';
      
      setTimeout(() => {
        card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      }, index * 100 + 300);
    });
  }

  updateTime() {
    const updateTimeDisplay = () => {
      const now = new Date();
      const timeString = now.toLocaleString("es-ES", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      
      const timeElement = document.getElementById("current-time");
      if (timeElement) {
        timeElement.textContent = timeString;
      }
    };
    
    updateTimeDisplay();
    setInterval(updateTimeDisplay, 1000);
  }

  // Chart initialization methods
  initializeCharts() {
    console.log('🚀 Initializing charts...');
    
    if (typeof Chart === 'undefined') {
      console.error('❌ Chart.js no está disponible');
      this.showNotification('Chart.js no está disponible', 'error');
      return;
    }

    console.log('✅ Chart.js is available');

    // Register Chart.js plugins
    if (typeof ChartDataLabels !== 'undefined') {
      Chart.register(ChartDataLabels);
      console.log('✅ Chart DataLabels plugin registered');
    } else {
      console.warn('⚠️ Chart DataLabels plugin not available');
    }

    // Check if window.chartData exists
    if (!window.chartData) {
      console.error('❌ window.chartData not found');
      this.showNotification('Chart data not available', 'error');
      // Initialize with sample data
      window.chartData = this.getSampleData();
    } else {
      // Check if data arrays are empty and provide sample data
      if (!window.chartData.motivos_labels || window.chartData.motivos_labels.length === 0) {
        console.warn('⚠️ Empty chart data detected, using sample data');
        window.chartData = this.getSampleData();
        this.showNotification('Mostrando datos de ejemplo', 'warning');
      }
    }

    console.log('📊 Chart data:', window.chartData);

    // Initialize all charts
    try {
      this.initMotivosChart();
      this.initTiposChart();
      this.initEncargadosChart();
      this.initTendenciaChart();
      console.log('✅ All charts initialized successfully');
    } catch (error) {
      console.error('❌ Error initializing charts:', error);
      this.showNotification('Error initializing charts: ' + error.message, 'error');
    }
  }

  formatLabels(labels) {
    return labels.map(label => {
      return label.replace(/_/g, ' ').split(' ').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ');
    });
  }

  getDonutOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        animateScale: true,
        animateRotate: true,
        duration: 1000
      },
      plugins: {
        legend: {
          display: false  // Usaremos leyenda personalizada
        },
        tooltip: {
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          titleColor: '#333',
          bodyColor: '#333',
          borderColor: 'rgba(200, 200, 200, 0.5)',
          borderWidth: 1,
          padding: 10,
          boxPadding: 5,
          cornerRadius: 6,
          displayColors: true,
          usePointStyle: true,
          callbacks: {
            label: function(context) {
              const label = context.label;
              const value = context.raw;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = Math.round((value / total) * 100);
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        },
        datalabels: {
          color: '#fff',
          font: {
            weight: 'bold',
            size: 11
          },
          formatter: function(value, context) {
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = Math.round((value / total) * 100);
            return percentage >= 8 ? `${percentage}%` : '';
          }
        }
      }
    };
  }

  initMotivosChart() {
    console.log('📊 Initializing Motivos Chart...');
    const ctx = document.getElementById('motivosChart');
    if (!ctx) {
      console.error('❌ motivosChart element not found');
      return;
    }

    console.log('✅ motivosChart element found:', ctx);

    const labels = this.formatLabels(window.chartData.motivos_labels || ['Sin datos']);
    const data = window.chartData.motivos_data || [1];

    console.log('📈 Motivos data:', { labels, data });

    try {
      this.motivosChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: data,
            backgroundColor: this.colors.slice(0, data.length),
            borderWidth: 1,
            borderColor: 'rgba(255, 255, 255, 0.6)'
          }]
        },
        options: this.getDonutOptions()
      });

      console.log('✅ Motivos chart created successfully');
      this.createCustomLegend(this.motivosChart, 'motivosLeyenda', 'motivos');
    } catch (error) {
      console.error('❌ Error creating motivos chart:', error);
      this.showNotification('Error creating motivos chart', 'error');
    }
  }

  initTiposChart() {
    console.log('📊 Initializing Tipos Chart...');
    const ctx = document.getElementById('tiposChart');
    if (!ctx) {
      console.error('❌ tiposChart element not found');
      return;
    }

    console.log('✅ tiposChart element found:', ctx);

    const labels = this.formatLabels(window.chartData.tipos_labels || ['Sin datos']);
    const data = window.chartData.tipos_data || [1];

    console.log('📈 Tipos data:', { labels, data });

    try {
      this.tiposChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: data,
            backgroundColor: this.colors.slice(0, data.length),
            borderWidth: 1,
            borderColor: 'rgba(255, 255, 255, 0.6)'
          }]
        },
        options: this.getDonutOptions()
      });

      console.log('✅ Tipos chart created successfully');
      this.createCustomLegend(this.tiposChart, 'tiposLeyenda', 'tipos');
    } catch (error) {
      console.error('❌ Error creating tipos chart:', error);
      this.showNotification('Error creating tipos chart', 'error');
    }
  }

  initEncargadosChart() {
    console.log('📊 Initializing Encargados Chart...');
    const ctx = document.getElementById('encargadosChart');
    if (!ctx) {
      console.error('❌ encargadosChart element not found');
      return;
    }

    console.log('✅ encargadosChart element found:', ctx);

    const encargados = window.chartData.encargados || ['Sin datos'];
    const eficiencia = window.chartData.eficiencia || [0];
    const retrabajos = window.chartData.retrabajos_encargado || [0];

    console.log('📈 Encargados data:', { encargados, eficiencia, retrabajos });

    try {
      this.encargadosChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: encargados,
          datasets: [{
            label: 'Eficiencia (%)',
            data: eficiencia,
            backgroundColor: '#4f46e5',
            borderColor: '#4338ca',
            borderWidth: 1,
            borderRadius: 8,
            barPercentage: 0.6,
          }, {
            label: 'Re-trabajos',
            data: retrabajos,
            backgroundColor: 'rgba(245, 158, 11, 0.7)',
            borderColor: 'rgba(217, 119, 6, 1)',
            borderWidth: 1,
            borderRadius: 8,
            barPercentage: 0.3,
            yAxisID: 'y1',
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            delay: function(context) {
              return context.dataIndex * 100;
            },
            duration: 800,
            easing: 'easeOutQuart'
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              grid: {
                display: true,
                drawBorder: false,
                color: 'rgba(200, 200, 200, 0.15)'
              },
              ticks: {
                font: { size: 10 },
                callback: function(value) {
                  return value + '%';
                }
              },
              title: {
                display: true,
                text: 'Eficiencia',
                color: 'rgba(79, 70, 229, 0.9)',
                font: { size: 11 }
              }
            },
            y1: {
              position: 'right',
              beginAtZero: true,
              grid: { display: false },
              ticks: { font: { size: 10 } },
              title: {
                display: true,
                text: 'Re-trabajos',
                color: 'rgba(245, 158, 11, 0.9)',
                font: { size: 11 }
              }
            },
            x: {
              grid: {
                display: false,
                drawBorder: false
              },
              ticks: {
                font: { size: 10 },
                maxRotation: 45,
                minRotation: 45
              }
            }
          },
          plugins: {
            tooltip: {
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              titleColor: '#333',
              bodyColor: '#333',
              borderColor: 'rgba(200, 200, 200, 0.5)',
              borderWidth: 1,
              padding: 10,
              cornerRadius: 6,
              displayColors: true,
              callbacks: {
                label: function(context) {
                  const label = context.dataset.label;
                  const value = context.raw;
                  if (label === 'Eficiencia (%)') {
                    return `${label}: ${value}%`;
                  }
                  return `${label}: ${value}`;
                }
              }
            },
            legend: {
              position: 'top',
              labels: {
                boxWidth: 12,
                usePointStyle: true,
                pointStyle: 'circle',
                font: { size: 11 }
              }
            },
            datalabels: {
              color: function(context) {
                return context.dataset.label === 'Eficiencia (%)' ? '#fff' : '#333';
              },
              font: {
                weight: 'bold',
                size: 10
              },
              formatter: function(value, context) {
                if (context.dataset.label === 'Eficiencia (%)') {
                  return value + '%';
                }
                return value;
              },
              display: function(context) {
                return context.dataIndex < 8;
              }
            }
          }
        }
      });

      console.log('✅ Encargados chart created successfully');
    } catch (error) {
      console.error('❌ Error creating encargados chart:', error);
      this.showNotification('Error creating encargados chart', 'error');
    }
  }

  initTendenciaChart() {
    console.log('📊 Initializing Tendencia Chart...');
    const ctx = document.getElementById('tendenciaChart');
    if (!ctx) {
      console.error('❌ tendenciaChart element not found');
      return;
    }

    console.log('✅ tendenciaChart element found:', ctx);

    const meses = window.chartData.tendencia_meses || ['Sin datos'];
    const valores = window.chartData.tendencia_valores || [0];

    console.log('📈 Tendencia data:', { meses, valores });

    try {
      this.tendenciaChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: meses,
          datasets: [{
            label: 'Re-trabajos',
            data: valores,
            fill: true,
            backgroundColor: 'rgba(79, 70, 229, 0.15)',
            borderColor: 'rgba(79, 70, 229, 0.8)',
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: 'rgba(79, 70, 229, 1)',
            pointBorderColor: '#fff',
            pointBorderWidth: 1,
            pointHoverRadius: 6,
            pointHoverBackgroundColor: 'rgba(79, 70, 229, 1)',
            pointHoverBorderColor: '#fff',
            pointHoverBorderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animations: {
            tension: {
              duration: 1000,
              easing: 'linear',
              from: 0.5,
              to: 0.3,
              loop: false
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: {
                display: true,
                drawBorder: false,
                color: 'rgba(200, 200, 200, 0.15)'
              },
              ticks: { font: { size: 10 } },
              title: {
                display: true,
                text: 'Número de Re-trabajos',
                font: { size: 11 }
              }
            },
            x: {
              grid: {
                display: false,
                drawBorder: false
              },
              ticks: {
                font: { size: 10 },
                maxRotation: 45,
                minRotation: 45
              }
            }
          },
          plugins: {
            tooltip: {
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              titleColor: '#333',
              bodyColor: '#333',
              borderColor: 'rgba(200, 200, 200, 0.5)',
              borderWidth: 1,
              padding: 10,
              cornerRadius: 6,
              displayColors: true,
              callbacks: {
                title: function(tooltipItems) {
                  return tooltipItems[0].label;
                },
                label: function(context) {
                  const value = context.raw;
                  return `Re-trabajos: ${value}`;
                }
              }
            },
            legend: { display: false },
            datalabels: {
              color: 'rgba(79, 70, 229, 1)',
              anchor: 'end',
              align: 'top',
              offset: 5,
              font: {
                weight: 'bold',
                size: 10
              },
              formatter: function(value) {
                return value;
              },
              display: function(context) {
                const datapoints = context.chart.data.datasets[0].data;
                const currentValue = datapoints[context.dataIndex];
                const isMax = currentValue === Math.max(...datapoints);
                const isMin = currentValue === Math.min(...datapoints);
                const showEveryNth = context.dataIndex % 2 === 0;
                return isMax || isMin || showEveryNth;
              }
            }
          }
        }
      });

      console.log('✅ Tendencia chart created successfully');
    } catch (error) {
      console.error('❌ Error creating tendencia chart:', error);
      this.showNotification('Error creating tendencia chart', 'error');
    }
  }

  createCustomLegend(chart, containerId, type) {
    const legendContainer = document.getElementById(containerId);
    if (!legendContainer) return;

    legendContainer.innerHTML = '';

    const items = chart.data.labels.map((label, index) => {
      const color = chart.data.datasets[0].backgroundColor[index];
      const value = chart.data.datasets[0].data[index];
      const total = chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
      const percentage = Math.round((value / total) * 100);

      const item = document.createElement('div');
      item.className = 'flex items-center space-x-1 px-2 py-1 rounded-md transition-colors hover:bg-[color:var(--bg-hover)] cursor-pointer';
      item.dataset.index = index;

      const colorBox = document.createElement('span');
      colorBox.className = 'inline-block w-3 h-3 rounded-sm';
      colorBox.style.backgroundColor = color;

      const labelSpan = document.createElement('span');
      if (type === 'motivos' || type === 'tipos') {
        labelSpan.textContent = `${label} (${percentage}%)`;
      } else {
        labelSpan.textContent = `${label}`;
      }

      item.appendChild(colorBox);
      item.appendChild(labelSpan);

      // Añadir interactividad
      item.addEventListener('click', () => {
        const isDatasetVisible = chart.getDatasetMeta(0).hidden !== true;
        chart.getDatasetMeta(0).hidden = isDatasetVisible ? true : false;

        if (isDatasetVisible) {
          item.classList.add('opacity-50');
        } else {
          item.classList.remove('opacity-50');
        }

        chart.update();
      });

      item.addEventListener('mouseenter', () => {
        chart.setActiveElements([{datasetIndex: 0, index: index}]);
        chart.update();
      });

      item.addEventListener('mouseleave', () => {
        chart.setActiveElements([]);
        chart.update();
      });

      return item;
    });

    items.forEach(item => legendContainer.appendChild(item));
  }

  setupChartDownloads() {
    const downloads = [
      { buttonId: 'downloadMotivosPNG', chartProp: 'motivosChart', filename: 'motivos_rechazo' },
      { buttonId: 'downloadTiposPNG', chartProp: 'tiposChart', filename: 'tipos_falla' },
      { buttonId: 'downloadEncargadosPNG', chartProp: 'encargadosChart', filename: 'eficiencia_encargados' },
      { buttonId: 'downloadTendenciaPNG', chartProp: 'tendenciaChart', filename: 'tendencia_retrabajos' }
    ];

    downloads.forEach(({ buttonId, chartProp, filename }) => {
      const button = document.getElementById(buttonId);
      if (!button || !this[chartProp]) return;

      button.addEventListener('click', () => {
        const canvas = this[chartProp].canvas;
        const link = document.createElement('a');
        link.download = filename + '_' + new Date().toISOString().split('T')[0] + '.png';
        link.href = canvas.toDataURL('image/png', 1.0);
        link.click();
      });
    });
  }

  // Table functionality
  initializeTable() {
    const tabla = document.getElementById('tablaRetrabajos');
    if (!tabla) return;

    this.tableRows = Array.from(tabla.querySelectorAll('tbody tr'));
    this.setupTableSearch();
    this.setupTableSort();
    this.setupTablePagination();
    
    // Initialize table visibility
    this.tableRows.forEach(fila => {
      fila.dataset.visible = 'true';
    });
    this.renderTable();
  }

  setupTableSearch() {
    const searchInput = document.getElementById('searchRetrabajos');
    if (!searchInput) return;

    searchInput.addEventListener('input', () => {
      const searchTerm = searchInput.value.toLowerCase();

      this.tableRows.forEach(fila => {
        const texto = fila.textContent.toLowerCase();
        fila.dataset.visible = texto.includes(searchTerm) ? 'true' : 'false';
      });

      this.currentPage = 1;
      this.renderTable();
    });
  }

  setupTableSort() {
    const tabla = document.getElementById('tablaRetrabajos');
    if (!tabla) return;

    tabla.querySelectorAll('thead th[data-sort]').forEach(header => {
      header.addEventListener('click', () => {
        this.sortTable(header.dataset.sort);
      });
    });
  }

  sortTable(column) {
    const tabla = document.getElementById('tablaRetrabajos');
    const headerCells = tabla.querySelectorAll('thead th');

    headerCells.forEach(cell => {
      if (cell.dataset.sort === column) {
        if (this.sortColumn === column) {
          this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
          this.sortDirection = 'asc';
        }
        this.sortColumn = column;
      }
    });

    this.tableRows.sort((a, b) => {
      const cellA = a.querySelector(`td:nth-child(${Array.from(headerCells).findIndex(cell => cell.dataset.sort === column) + 1})`).textContent.trim();
      const cellB = b.querySelector(`td:nth-child(${Array.from(headerCells).findIndex(cell => cell.dataset.sort === column) + 1})`).textContent.trim();

      if (!isNaN(cellA) && !isNaN(cellB)) {
        return this.sortDirection === 'asc' ? Number(cellA) - Number(cellB) : Number(cellB) - Number(cellA);
      } else {
        return this.sortDirection === 'asc' ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
      }
    });

    this.renderTable();
  }

  setupTablePagination() {
    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');

    if (prevPage) {
      prevPage.addEventListener('click', () => {
        if (this.currentPage > 1) {
          this.currentPage--;
          this.renderTable();
        }
      });
    }

    if (nextPage) {
      nextPage.addEventListener('click', () => {
        const filasVisibles = this.tableRows.filter(fila => fila.dataset.visible !== 'false');
        const totalPages = Math.ceil(filasVisibles.length / this.rowsPerPage);

        if (this.currentPage < totalPages) {
          this.currentPage++;
          this.renderTable();
        }
      });
    }
  }

  renderTable() {
    const tabla = document.getElementById('tablaRetrabajos');
    if (!tabla) return;

    // Filtrar las filas visibles
    const filasVisibles = this.tableRows.filter(fila => fila.dataset.visible !== 'false');

    // Calcular paginación
    const totalPages = Math.ceil(filasVisibles.length / this.rowsPerPage);
    const start = (this.currentPage - 1) * this.rowsPerPage;
    const end = start + this.rowsPerPage;

    // Actualizar información de paginación
    const mostrandoDesde = document.getElementById('mostrandoDesde');
    const mostrandoHasta = document.getElementById('mostrandoHasta');
    const totalRegistros = document.getElementById('totalRegistros');

    if (mostrandoDesde) mostrandoDesde.textContent = filasVisibles.length > 0 ? start + 1 : 0;
    if (mostrandoHasta) mostrandoHasta.textContent = Math.min(end, filasVisibles.length);
    if (totalRegistros) totalRegistros.textContent = filasVisibles.length;

    // Actualizar el contenido de la tabla
    const tbody = tabla.querySelector('tbody');
    tbody.innerHTML = '';

    filasVisibles.slice(start, end).forEach(fila => {
      tbody.appendChild(fila);
    });

    // Actualizar botones de paginación
    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');

    if (prevPage) prevPage.disabled = this.currentPage === 1;
    if (nextPage) nextPage.disabled = this.currentPage === totalPages || totalPages === 0;

    // Actualizar números de página
    this.updatePageNumbers(totalPages);
  }

  updatePageNumbers(totalPages) {
    const pageNumbers = document.getElementById('pageNumbers');
    if (!pageNumbers) return;

    pageNumbers.innerHTML = '';

    const maxVisiblePages = 5;
    let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    if (startPage > 1) {
      const firstPageBtn = document.createElement('button');
      firstPageBtn.className = 'w-8 h-8 text-sm rounded flex items-center justify-center hover:bg-[color:var(--bg-hover)]';
      firstPageBtn.textContent = '1';
      firstPageBtn.addEventListener('click', () => {
        this.currentPage = 1;
        this.renderTable();
      });
      pageNumbers.appendChild(firstPageBtn);

      if (startPage > 2) {
        const ellipsis = document.createElement('span');
        ellipsis.className = 'text-[color:var(--text-secondary)]';
        ellipsis.textContent = '...';
        pageNumbers.appendChild(ellipsis);
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      const pageBtn = document.createElement('button');
      pageBtn.className = `w-8 h-8 text-sm rounded flex items-center justify-center ${i === this.currentPage ? 'bg-[color:var(--accent-blue)] text-white' : 'hover:bg-[color:var(--bg-hover)]'}`;
      pageBtn.textContent = i;
      pageBtn.addEventListener('click', () => {
        this.currentPage = i;
        this.renderTable();
      });
      pageNumbers.appendChild(pageBtn);
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        const ellipsis = document.createElement('span');
        ellipsis.className = 'text-[color:var(--text-secondary)]';
        ellipsis.textContent = '...';
        pageNumbers.appendChild(ellipsis);
      }

      const lastPageBtn = document.createElement('button');
      lastPageBtn.className = 'w-8 h-8 text-sm rounded flex items-center justify-center hover:bg-[color:var(--bg-hover)]';
      lastPageBtn.textContent = totalPages;
      lastPageBtn.addEventListener('click', () => {
        this.currentPage = totalPages;
        this.renderTable();
      });
      pageNumbers.appendChild(lastPageBtn);
    }
  }

  setupProjectToggle() {
    const toggleProyectosTable = document.getElementById('toggleProyectosTable');
    const verMasProyectos = document.getElementById('verMasProyectos');
    let showAllProjects = false;

    if (toggleProyectosTable) {
      toggleProyectosTable.addEventListener('click', () => {
        showAllProjects = !showAllProjects;

        const proyectosTable = toggleProyectosTable.closest('div').querySelector('table');
        const proyectosFilas = proyectosTable.querySelectorAll('tbody tr:not(#verMasProyectos)');

        proyectosFilas.forEach((fila, index) => {
          if (index >= 5) {
            fila.style.display = showAllProjects ? 'table-row' : 'none';
          }
        });

        toggleProyectosTable.textContent = showAllProjects ? 'Mostrar menos' : 'Ver todos';
        if (verMasProyectos) {
          verMasProyectos.style.display = showAllProjects ? 'none' : 'table-row';
        }
      });
    }

    if (verMasProyectos) {
      verMasProyectos.addEventListener('click', () => {
        if (toggleProyectosTable) {
          toggleProyectosTable.click();
        }
      });
    }
  }

  // Utility methods
  formatNumber(num) {
    return new Intl.NumberFormat('es-ES').format(num);
  }

  formatCurrency(amount) {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0
    }).format(amount);
  }

  showLoading(element) {
    if (element) {
      element.style.opacity = '0.6';
      element.style.pointerEvents = 'none';
    }
  }

  hideLoading(element) {
    if (element) {
      element.style.opacity = '1';
      element.style.pointerEvents = 'auto';
    }
  }

  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 6px;
      color: white;
      font-weight: 500;
      font-size: 14px;
      z-index: 1000;
      transform: translateX(100%);
      transition: transform 0.3s ease;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;
    
    const colors = {
      info: 'var(--accent-primary)',
      success: 'var(--status-success)',
      warning: 'var(--status-warning)',
      error: 'var(--status-danger)'
    };
    
    notification.style.backgroundColor = colors[type] || colors.info;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
    }, 100);
    
    setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }, 3000);
  }

  getSampleData() {
    return {
      motivos_labels: ['Diseño Incompleto', 'Falta Información', 'Cambio Requisitos', 'Error Técnico', 'Revisión Cliente'],
      motivos_data: [15, 12, 8, 10, 5],
      tipos_labels: ['Documentación', 'Planos', 'Cálculos', 'Especificaciones', 'Otros'],
      tipos_data: [18, 14, 9, 6, 3],
      encargados: ['Juan Pérez', 'María García', 'Carlos López', 'Ana Martín', 'Luis Torres'],
      eficiencia: [95, 88, 92, 85, 90],
      retrabajos_encargado: [3, 7, 4, 9, 5],
      tendencia_meses: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
      tendencia_valores: [12, 8, 15, 10, 6, 11]
    };
  }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  try {
    window.retrabajosDashboard = new RetrabajosDashboard();
    console.log('✅ Re-trabajos Dashboard initialized successfully');
  } catch (error) {
    console.error('❌ Error initializing Re-trabajos Dashboard:', error);
  }
});

// Export for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = RetrabajosDashboard;
}
