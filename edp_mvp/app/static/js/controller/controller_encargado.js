/* ==========================================================================
   Controller Encargado JavaScript
   ========================================================================== */

// ==========================================================================
// Global Variables
// ==========================================================================

let chartInstances = {};

// ==========================================================================
// Time and Update Management
// ==========================================================================

function updateTime() {
  const now = new Date();
  const timeString = now.toLocaleString("es-ES", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const lastUpdateString = now.toLocaleString("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
  });

  const timeElement = document.getElementById("current-time");
  const lastUpdateElement = document.getElementById("last-update");

  if (timeElement) {
    timeElement.textContent = timeString;
  }
  if (lastUpdateElement) {
    lastUpdateElement.textContent = lastUpdateString;
  }
}

// ==========================================================================
// Progress Ring Initialization
// ==========================================================================

function initializeProgressRings() {
  const progressRings = document.querySelectorAll(
    ".analytics-kpi-progress-fill"
  );
  progressRings.forEach((ring) => {
    const strokeDashoffset = ring.style.strokeDashoffset;
    ring.style.strokeDashoffset = "157";
    setTimeout(() => {
      ring.style.strokeDashoffset = strokeDashoffset;
    }, 500);
  });
}

// ==========================================================================
// Health Indicators Update
// ==========================================================================

function updateHealthIndicators() {
  const avanceGlobal = parseFloat(document.querySelector('[data-avance-global]')?.getAttribute('data-avance-global')) || 0;
  const riesgoScore = parseFloat(document.querySelector('[data-riesgo-score]')?.getAttribute('data-riesgo-score')) || 0;

  // Actualizar indicadores de salud
  const healthIndicators = document.querySelectorAll('[data-health-indicator]');
  healthIndicators.forEach(indicator => {
    const currentHealth = indicator.getAttribute('data-health-indicator');
    let newClass = '';

    if (avanceGlobal >= 80) {
      newClass = 'bg-green-500';
    } else if (avanceGlobal >= 60) {
      newClass = 'bg-yellow-500';
    } else {
      newClass = 'bg-red-500';
    }

    indicator.className = indicator.className.replace(/bg-\w+-\d+/, newClass);
  });
}

// ==========================================================================
// Analytics Dashboard Initialization
// ==========================================================================

function initializeAnalyticsDashboard() {
  try {
    // Get analytics data from window object (set by template)
    let analyticsData = {
      dso: { 
        current_dso: window.dsoEncargado || 0, 
        target_dso: 45, 
        trend: 0 
      },
      correlations: { key_correlations: [] },
      predictions: { 
        cash_flow_30d: window.montoPendienteGlobal || 0, 
        confidence: 85.2 
      },
      segmentation: { client_segments: [], size_segments: [] },
    };

    console.log("✅ Analytics data loaded:", analyticsData);

    // Check if Chart.js is available
    if (typeof Chart !== "undefined") {
      console.log("✅ Chart.js is available, initializing dashboard...");
      
      // Initialize dashboard with a small delay to ensure DOM is ready
      setTimeout(() => {
        console.log("✅ Analytics Dashboard initialized successfully");
      }, 500);
    } else {
      console.error("❌ Chart.js not loaded! Please check the CDN link.");
    }
  } catch (error) {
    console.error("❌ Error initializing Analytics Dashboard:", error);
  }
}

// ==========================================================================
// Update Analytics Function
// ==========================================================================

function updateAnalytics() {
  const overlay = document.createElement("div");
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    font-family: var(--font-mono);
  `;
  overlay.innerHTML =
    '<div style="text-align: center;"><div style="font-size: 24px; margin-bottom: 10px;">ACTUALIZANDO ANÁLISIS...</div><div>Sistema de análisis avanzado procesando datos</div></div>';
  document.body.appendChild(overlay);

  setTimeout(() => {
    document.body.removeChild(overlay);
    location.reload();
  }, 1500);
}

// ==========================================================================
// Table Management Functions
// ==========================================================================

function filterTable() {
  const buscarInput = document.getElementById("buscarProyecto");
  const filtroSelect = document.getElementById("filtroProyectos");
  
  if (!buscarInput || !filtroSelect) return;

  const searchTerm = buscarInput.value.toLowerCase();
  const filterType = filtroSelect.value;
  let visibleCount = 0;

  const rows = document.querySelectorAll("#tablaProyectos tbody tr");

  rows.forEach((row) => {
    const proyecto = row.getAttribute("data-proyecto")?.toLowerCase() || '';
    const criticos = row.querySelector("td:nth-child(3)")?.textContent.trim() || '';
    const validados = row.querySelector("td:nth-child(4)")?.textContent.trim() || '';
    const montoPendiente = parseFloat(
      row.querySelector("td:nth-child(9)")?.textContent.replace(/[$,\.]/g, "") || "0"
    );
    const montoPagado = parseFloat(
      row.querySelector("td:nth-child(8)")?.textContent.replace(/[$,\.]/g, "") || "0"
    );

    let shouldShow = proyecto.includes(searchTerm);

    if (filterType === "criticos") {
      shouldShow = shouldShow && criticos !== "-";
    } else if (filterType === "validados") {
      shouldShow = shouldShow && validados !== "-";
    } else if (filterType === "pendientes") {
      shouldShow = shouldShow && montoPendiente > 0;
    } else if (filterType === "pagados") {
      shouldShow = shouldShow && montoPagado > 0;
    }

    if (shouldShow) {
      row.style.display = "";
      visibleCount++;
    } else {
      row.style.display = "none";
    }
  });

  // Actualizar contador de resultados
  const countElement = document.getElementById("countResults");
  if (countElement) {
    countElement.textContent = visibleCount;
  }

  // Reiniciar paginación si existe
  updatePagination();
}

function sortTable(sortBy, ascending) {
  const tbody = document.querySelector("#tablaProyectos tbody");
  if (!tbody) return;

  const rows = Array.from(tbody.querySelectorAll("tr"));

  rows.sort((a, b) => {
    let valueA, valueB;

    // Obtener valores según la columna a ordenar
    switch (sortBy) {
      case "monto-prop":
        valueA = parseFloat(
          a.querySelector("td:nth-child(6)")?.textContent.replace(/[$,\.]/g, "") || "0"
        );
        valueB = parseFloat(
          b.querySelector("td:nth-child(6)")?.textContent.replace(/[$,\.]/g, "") || "0"
        );
        break;
      case "monto":
        valueA = parseFloat(
          a.querySelector("td:nth-child(7)")?.textContent.replace(/[$,\.]/g, "") || "0"
        );
        valueB = parseFloat(
          b.querySelector("td:nth-child(7)")?.textContent.replace(/[$,\.]/g, "") || "0"
        );
        break;
      case "total":
        valueA = parseInt(a.querySelector("td:nth-child(2)")?.textContent || "0");
        valueB = parseInt(b.querySelector("td:nth-child(2)")?.textContent || "0");
        break;
      case "criticos":
        valueA = a.querySelector("td:nth-child(3)")?.textContent.trim() === "-" ? 0 : parseInt(a.querySelector("td:nth-child(3)")?.textContent || "0");
        valueB = b.querySelector("td:nth-child(3)")?.textContent.trim() === "-" ? 0 : parseInt(b.querySelector("td:nth-child(3)")?.textContent || "0");
        break;
      case "validados":
        valueA = a.querySelector("td:nth-child(4)")?.textContent.trim() === "-" ? 0 : parseInt(a.querySelector("td:nth-child(4)")?.textContent || "0");
        valueB = b.querySelector("td:nth-child(4)")?.textContent.trim() === "-" ? 0 : parseInt(b.querySelector("td:nth-child(4)")?.textContent || "0");
        break;
      case "dias":
        valueA = parseInt(a.querySelector("td:nth-child(5)")?.textContent || "0");
        valueB = parseInt(b.querySelector("td:nth-child(5)")?.textContent || "0");
        break;
      case "pagado":
        valueA = parseFloat(
          a.querySelector("td:nth-child(7)")?.textContent.replace(/[$,\.]/g, "") || "0"
        );
        valueB = parseFloat(
          b.querySelector("td:nth-child(7)")?.textContent.replace(/[$,\.]/g, "") || "0"
        );
        break;
      case "pendiente":
        valueA = parseFloat(
          a.querySelector("td:nth-child(8)")?.textContent.replace(/[$,\.]/g, "") || "0"
        );
        valueB = parseFloat(
          b.querySelector("td:nth-child(8)")?.textContent.replace(/[$,\.]/g, "") || "0"
        );
        break;
      case "avance":
        valueA = parseInt(a.querySelector("td:nth-child(9)")?.textContent || "0");
        valueB = parseInt(b.querySelector("td:nth-child(9)")?.textContent || "0");
        break;
      default:
        valueA = a.querySelector("td:first-child")?.textContent.toLowerCase() || '';
        valueB = b.querySelector("td:first-child")?.textContent.toLowerCase() || '';
    }

    if (valueA < valueB) {
      return ascending ? -1 : 1;
    }
    if (valueA > valueB) {
      return ascending ? 1 : -1;
    }
    return 0;
  });

  // Reordenar filas
  rows.forEach((row) => {
    tbody.appendChild(row);
  });
}

function updatePagination() {
  // Implementación de la paginación si se necesita
  const prevPageElement = document.getElementById("prevPage");
  if (prevPageElement) {
    // Código de paginación aquí
  }
}

function exportToCSV() {
  let csvContent = "data:text/csv;charset=utf-8,";

  // Cabeceras
  const headers = Array.from(
    document.querySelectorAll("#tablaProyectos thead th")
  )
    .map((th) => th.textContent.trim())
    .join(",");
  csvContent += headers + "\r\n";

  // Datos
  const rows = document.querySelectorAll("#tablaProyectos tbody tr");
  rows.forEach((row) => {
    if (row.style.display !== "none") {
      const rowData = Array.from(row.querySelectorAll("td"))
        .map((td) => {
          return `"${td.textContent.trim().replace(/"/g, '""')}"`;
        })
        .join(",");
      csvContent += rowData + "\r\n";
    }
  });

  // Crear enlace de descarga
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute(
    "download",
    `proyectos_${new Date().toISOString().slice(0, 10)}.csv`
  );
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ==========================================================================
// Chart Management Functions
// ==========================================================================

function setupThemeChangeListener() {
  const themeObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'attributes' &&
          (mutation.attributeName === 'data-theme' || mutation.attributeName === 'class')) {
        console.log('Theme changed, reinitializing charts...');
        setTimeout(() => {
          initializeCharts();
        }, 100);
      }
    });
  });

  // Observe theme changes on html element
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme', 'class']
  });

  // Also observe body for class changes
  themeObserver.observe(document.body, {
    attributes: true,
    attributeFilter: ['class']
  });

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    console.log('System theme changed, reinitializing charts...');
    setTimeout(() => {
      initializeCharts();
    }, 100);
  });
}

function getCSSProperty(property) {
  try {
    const value = getComputedStyle(document.documentElement).getPropertyValue(property).trim();
    return value.replace(/['"]/g, '') || getDefaultColor(property);
  } catch (error) {
    console.warn(`Failed to get CSS property ${property}:`, error);
    return getDefaultColor(property);
  }
}

function getDefaultColor(property) {
  const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark' ||
                    document.body.classList.contains('dark') ||
                    window.matchMedia('(prefers-color-scheme: dark)').matches;

  const lightColors = {
    '--text-primary': '#111827',
    '--text-secondary': '#4b5563',
    '--text-tertiary': '#6b7280',
    '--bg-card': '#f9f9f7',
    '--bg-secondary': '#ff0f4f8',
    '--border-color': '#d1d5db',
    '--border-color-subtle': '#f3f4f6',
    '--accent-green': '#059669',
    '--accent-blue': '#2563eb',
    '--accent-amber': '#d97706',
    '--accent-purple': '#7c3aed',
    '--accent-red': '#dc2626'
  };

  const darkColors = {
    '--text-primary': '#f9fafb',
    '--text-secondary': '#d1d5db',
    '--text-tertiary': '#9ca3af',
    '--bg-card': '#1f2937',
    '--bg-secondary': '#111827',
    '--border-color': '#374151',
    '--border-color-subtle': '#4b5563',
    '--accent-green': '#10b981',
    '--accent-blue': '#3b82f6',
    '--accent-amber': '#f59e0b',
    '--accent-purple': '#8b5cf6',
    '--accent-red': '#ef4444'
  };

  const colors = isDarkMode ? darkColors : lightColors;
  return colors[property] || (isDarkMode ? '#9ca3af' : '#6b7280');
}

function initializeCharts() {
  // Gráfico 1: Tendencia Semanal de Cobranza
  Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";

  // Get theme colors
  const colors = {
    textPrimary: getCSSProperty('--text-primary'),
    textSecondary: getCSSProperty('--text-secondary'),
    textTertiary: getCSSProperty('--text-tertiary'),
    bgCard: getCSSProperty('--bg-card'),
    bgSecondary: getCSSProperty('--bg-secondary'),
    borderColor: getCSSProperty('--border-color'),
    borderColorSubtle: getCSSProperty('--border-color-subtle'),
    accentGreen: getCSSProperty('--accent-green'),
    accentBlue: getCSSProperty('--accent-blue'),
    accentAmber: getCSSProperty('--accent-amber')
  };
  
  console.log('Theme colors loaded:', colors);

  // Destroy existing charts before creating new ones
  Object.values(chartInstances).forEach(chart => {
    if (chart && typeof chart.destroy === 'function') {
      chart.destroy();
    }
  });
  chartInstances = {};

  // Initialize specific charts
  initializeTendenciaChart(colors);
  initializeTopEdpsChart(colors);
  initializeAgingChart();
}

function initializeTendenciaChart(colors) {
  const tendenciaCtx = document.getElementById('tendenciaCobranzaChart');
  if (!tendenciaCtx) return;

  // Get data from window object (set by template)
  const tendenciaSemanal = window.tendenciaSemanal || [];
  const weeklyData = processWeeklyTrendData(tendenciaSemanal);

  if (weeklyData.hasData) {
    chartInstances.tendencia = new Chart(tendenciaCtx, {
      type: 'line',
      data: {
        labels: weeklyData.labels,
        datasets: [{
          label: 'Cobranza Semanal',
          data: weeklyData.values,
          borderColor: colors.accentGreen,
          backgroundColor: colors.accentGreen + '40',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: colors.accentGreen,
          pointBorderColor: colors.bgCard,
          pointBorderWidth: 3,
          pointRadius: 6,
          pointHoverRadius: 10,
          pointHoverBackgroundColor: colors.accentGreen,
          pointHoverBorderColor: colors.bgCard,
          pointHoverBorderWidth: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: colors.bgCard,
            titleColor: colors.textPrimary,
            bodyColor: colors.textPrimary,
            borderColor: colors.accentGreen,
            borderWidth: 2,
            cornerRadius: 12,
            displayColors: false,
            padding: 12,
            titleFont: {
              size: 14,
              weight: '600',
              family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
            },
            bodyFont: {
              size: 13,
              family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
            },
            callbacks: {
              title: function(context) {
                return `📊 ${context[0].label}`;
              },
              label: function(context) {
                const value = context.parsed.y;
                return `💰 Cobranza: $${(value/1000000).toFixed(2)}M`;
              },
              afterLabel: function(context) {
                const dataIndex = context.dataIndex;
                const isSimulated = weeklyData.isSimulated && weeklyData.isSimulated[dataIndex];
                return isSimulated ? '⚠️ Datos simulados' : '✅ Datos reales';
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: colors.borderColorSubtle + '80',
              lineWidth: 0.5,
              drawBorder: false
            },
            border: { display: false },
            ticks: {
              callback: function(value) {
                return '$' + (value / 1000000).toFixed(1) + 'M';
              },
              color: colors.textSecondary,
              font: {
                size: 12,
                family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
                weight: '500'
              },
              padding: 8
            }
          },
          x: {
            grid: { display: false },
            border: { color: colors.borderColorSubtle + '40' },
            ticks: {
              color: colors.textSecondary,
              font: {
                size: 11,
                family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
                weight: '500'
              },
              maxTicksLimit: 8,
              padding: 8
            }
          }
        },
        elements: {
          point: { hoverRadius: 10 },
          line: {
            borderJoinStyle: 'round',
            borderCapStyle: 'round'
          }
        },
        animation: {
          duration: 1000,
          easing: 'easeInOutQuart'
        }
      }
    });
  } else {
    // Show no data message
    tendenciaCtx.style.display = 'none';
    const noDataMessage = document.createElement('div');
    noDataMessage.className = 'flex flex-col items-center justify-center h-64 text-center bg-gradient-to-br from-transparent to-[color:var(--bg-subtle)] rounded-lg border-2 border-dashed border-[color:var(--border-color-subtle)]';
    noDataMessage.innerHTML = `
      <div class="text-[color:var(--text-secondary)] space-y-3">
        <div class="relative">
          <svg class="mx-auto h-16 w-16 text-[color:var(--accent-green)] opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
          </svg>
          <div class="absolute -top-1 -right-1 w-6 h-6 bg-[color:var(--accent-green)] rounded-full flex items-center justify-center">
            <svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
        <div>
          <p class="text-base font-semibold text-[color:var(--text-primary)] mb-1">Sin datos de tendencia semanal</p>
          <p class="text-sm text-[color:var(--text-secondary)]">Los gráficos aparecerán cuando se registre información de cobranza</p>
        </div>
        <div class="flex items-center justify-center space-x-2 text-xs text-[color:var(--text-secondary)]">
          <div class="w-2 h-2 bg-[color:var(--accent-green)] rounded-full animate-pulse"></div>
          <span>Esperando datos reales</span>
        </div>
      </div>
    `;
    tendenciaCtx.parentNode.appendChild(noDataMessage);
  }
}

function initializeTopEdpsChart(colors) {
  const topEdpsCtx = document.getElementById('topEdpsPendientesChart');
  if (!topEdpsCtx) return;

  const topEdpsData = generateTopEdpsData();

  if (topEdpsData.hasData) {
    const amberColors = [];
    for (let i = 0; i < 10; i++) {
      const opacity = 1 - (i * 0.075);
      amberColors.push(colors.accentAmber + Math.floor(opacity * 255).toString(16).padStart(2, '0'));
    }

    chartInstances.topEdps = new Chart(topEdpsCtx, {
      type: 'bar',
      data: {
        labels: topEdpsData.labels,
        datasets: [{
          label: 'Monto Pendiente',
          data: topEdpsData.values,
          backgroundColor: amberColors,
          borderColor: colors.accentAmber,
          borderWidth: 1,
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: colors.bgCard,
            titleColor: colors.textPrimary,
            bodyColor: colors.textPrimary,
            borderColor: colors.accentAmber,
            borderWidth: 1,
            cornerRadius: 8,
            displayColors: false,
            titleFont: {
              family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
              size: 14,
              weight: '600'
            },
            bodyFont: {
              family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
              size: 13
            },
            callbacks: {
              title: function(context) {
                const dataIndex = context[0].dataIndex;
                const edpData = topEdpsData.edpsInfo[dataIndex];
                return `📊 EDP: ${edpData.n_edp}`;
              },
              beforeBody: function(context) {
                const dataIndex = context[0].dataIndex;
                const edpData = topEdpsData.edpsInfo[dataIndex];
                return [
                  `🏗️ Proyecto: ${edpData.proyecto}`,
                  `👥 Cliente: ${edpData.cliente}`,
                  `🔄 Estado: ${edpData.estado}`,
                  edpData.es_critico ? '⚠️ CRÍTICO' : '✅ Normal'
                ];
              },
              label: function(context) {
                return '💰 Pendiente: $' + (context.parsed.x/1000000).toFixed(1) + 'M';
              }
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return '$' + (value / 1000000).toFixed(1) + 'M';
              },
              color: colors.textSecondary,
              font: {
                size: 11,
                weight: '500',
                family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
              },
              padding: 8
            },
            grid: {
              color: colors.borderColorSubtle + '40',
              lineWidth: 0.5,
              drawBorder: false
            },
            border: { color: colors.borderColorSubtle + '30' }
          },
          y: {
            ticks: {
              color: colors.textSecondary,
              font: {
                size: 10,
                weight: '500',
                family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
              },
              padding: 8
            },
            grid: { display: false },
            border: { color: colors.borderColorSubtle + '30' }
          }
        },
        elements: {
          bar: {
            borderRadius: 6,
            borderSkipped: false
          }
        },
        animation: {
          delay: function(context) {
            return context.dataIndex * 100;
          },
          duration: 1000,
          easing: 'easeOutQuart'
        }
      }
    });
  } else {
    // Show no data message
    topEdpsCtx.style.display = 'none';
    const noDataMessage = document.createElement('div');
    noDataMessage.className = 'flex items-center justify-center h-64 text-center';
    noDataMessage.innerHTML = `
      <div class="text-[color:var(--text-secondary)]">
        <svg class="mx-auto h-12 w-12 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <p class="text-sm font-medium">¡Excelente! No hay EDPs pendientes</p>
        <p class="text-xs mt-1">Todos los EDPs están al día con sus pagos</p>
      </div>
    `;
    topEdpsCtx.parentNode.appendChild(noDataMessage);
  }
}

function initializeAgingChart() {
  const agingCtx = document.getElementById('agingChart');
  if (!agingCtx) return;

  // Get data from window object (set by template)
  const agingData = window.distribucionAging || { reciente: 0, medio: 0, critico: 0 };
  
  new Chart(agingCtx, {
    type: 'doughnut',
    data: {
      labels: ['≤15 días', '16-30 días', '+30 días'],
      datasets: [{
        data: [agingData.reciente || 0, agingData.medio || 0, agingData.critico || 0],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)'
        ],
        borderColor: [
          'rgb(34, 197, 94)',
          'rgb(245, 158, 11)',
          'rgb(239, 68, 68)'
        ],
        borderWidth: 2,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 15,
            font: {
              size: 11
            },
            color: 'rgba(107, 114, 128, 1)'
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: 'rgba(59, 130, 246, 0.5)',
          borderWidth: 1,
          cornerRadius: 8,
          callbacks: {
            label: function(context) {
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((context.parsed / total) * 100).toFixed(1);
              return context.label + ': ' + context.parsed + ' EDPs (' + percentage + '%)';
            }
          }
        }
      },
      cutout: '60%'
    }
  });
}

// ==========================================================================
// Data Processing Functions
// ==========================================================================

function processWeeklyTrendData(tendenciaSemanal) {
  console.log('🔍 Tendencia semanal recibida:', tendenciaSemanal);

  const labels = [];
  const values = [];
  const isSimulated = [];

  if (tendenciaSemanal && Array.isArray(tendenciaSemanal) && tendenciaSemanal.length > 0) {
    tendenciaSemanal.forEach(semana => {
      if (!semana.es_simulado) {
        labels.push(semana.semana);
        values.push(semana.monto);
        isSimulated.push(false);
      }
    });
  }

  return {
    labels: labels,
    values: values,
    isSimulated: isSimulated,
    hasData: labels.length > 0
  };
}

function generateTopEdpsData() {
  const topEdpsPendientes = window.topEdpsPendientes || [];
  console.log('🔍 Top EDPs pendientes recibidos:', topEdpsPendientes);

  const edpsData = [];

  if (topEdpsPendientes && Array.isArray(topEdpsPendientes) && topEdpsPendientes.length > 0) {
    topEdpsPendientes.forEach(edp => {
      const montoPendiente = edp.monto_pendiente || 0;
      console.log(`📊 EDP: ${edp.n_edp}, Monto Pendiente: ${montoPendiente}`);

      if (montoPendiente > 0) {
        edpsData.push({
          nombre: `EDP-${edp.n_edp}`,
          monto: montoPendiente,
          proyecto: edp.proyecto || 'Sin Proyecto',
          cliente: edp.cliente || 'Sin Cliente',
          estado: edp.estado || 'pendiente',
          esCritico: edp.es_critico || false
        });
      }
    });
  }

  console.log('✅ EDPs procesados:', edpsData);

  edpsData.sort((a, b) => b.monto - a.monto);
  const top10Edps = edpsData.slice(0, 10);

  console.log('✅ Top 10 EDPs finales:', top10Edps);

  return {
    labels: top10Edps.map(edp => {
      const nombreCorto = edp.nombre.length > 18 ? edp.nombre.substring(0, 15) + '...' : edp.nombre;
      return nombreCorto;
    }),
    values: top10Edps.map(edp => edp.monto),
    edpsInfo: top10Edps.map(edp => ({
      n_edp: edp.nombre,
      proyecto: edp.proyecto,
      cliente: edp.cliente || 'Cliente Confidencial',
      estado: edp.estado,
      es_critico: edp.esCritico
    })),
    hasData: top10Edps.length > 0
  };
}

// ==========================================================================
// Risk Management Functions
// ==========================================================================

function initializeRiskIndicators() {
  const globalRisk = parseFloat(document.querySelector('[data-global-risk]')?.getAttribute('data-global-risk')) || 0;
  const agingRisk = parseFloat(document.querySelector('[data-aging-risk]')?.getAttribute('data-aging-risk')) || 0;
  const volumeRisk = parseFloat(document.querySelector('[data-volume-risk]')?.getAttribute('data-volume-risk')) || 0;

  updateCircularProgress('globalRiskIndicator', globalRisk, getRiskColor(globalRisk));
  updateCircularProgress('agingRiskIndicator', agingRisk, getRiskColor(agingRisk));
  updateCircularProgress('volumeRiskIndicator', volumeRisk, getRiskColor(volumeRisk));
}

function updateCircularProgress(elementId, percentage, color) {
  const element = document.getElementById(elementId);
  if (!element) return;

  const circle = element.querySelector('.progress-ring__circle');
  const text = element.querySelector('.progress-text');

  if (circle && text) {
    const radius = circle.r.baseVal.value;
    const circumference = radius * 2 * Math.PI;

    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference;

    const offset = circumference - (percentage / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    circle.style.stroke = color;

    text.textContent = `${Math.round(percentage)}%`;
  }
}

function getRiskColor(risk) {
  if (risk >= 70) return '#ef4444';
  if (risk >= 40) return '#f59e0b';
  return '#22c55e';
}

// ==========================================================================
// Animation Functions
// ==========================================================================

function initializeAnimations() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate__animated', 'animate__fadeInUp');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.metric-card').forEach((card) => {
    observer.observe(card);
  });
}

// ==========================================================================
// Event Listeners Setup
// ==========================================================================

function setupEventListeners() {
  // Sortable table headers
  const sortableHeaders = document.querySelectorAll(".sortable");
  sortableHeaders.forEach((header) => {
    header.addEventListener("click", function () {
      const sortBy = this.getAttribute("data-sort");
      const isAsc = this.classList.contains("sort-asc");

      sortableHeaders.forEach((h) => {
        h.classList.remove("sort-asc", "sort-desc");
      });

      this.classList.add(isAsc ? "sort-desc" : "sort-asc");
      sortTable(sortBy, !isAsc);
    });
  });

  // Search and filter inputs
  const buscarInput = document.getElementById("buscarProyecto");
  if (buscarInput) {
    buscarInput.addEventListener("input", filterTable);
  }

  const filtroSelect = document.getElementById("filtroProyectos");
  if (filtroSelect) {
    filtroSelect.addEventListener("change", filterTable);
  }

  // Export button
  const exportButton = document.getElementById("exportarDatos");
  if (exportButton) {
    exportButton.addEventListener("click", exportToCSV);
  }
}

// ==========================================================================
// Document Ready Initialization
// ==========================================================================

document.addEventListener("DOMContentLoaded", function () {
  // Initialize time updates
  updateTime();
  setInterval(updateTime, 1000);

  // Initialize progress rings
  initializeProgressRings();

  // Initialize analytics dashboard
  initializeAnalyticsDashboard();

  // Initialize charts
  initializeCharts();
  setupThemeChangeListener();

  // Initialize risk indicators
  initializeRiskIndicators();

  // Initialize animations
  initializeAnimations();

  // Setup event listeners
  setupEventListeners();

  // Update health indicators
  updateHealthIndicators();
});

// ==========================================================================
// Export Functions for Global Access
// ==========================================================================

window.updateTime = updateTime;
window.updateAnalytics = updateAnalytics;
window.updateHealthIndicators = updateHealthIndicators;
window.filterTable = filterTable;
window.sortTable = sortTable;
window.exportToCSV = exportToCSV;
