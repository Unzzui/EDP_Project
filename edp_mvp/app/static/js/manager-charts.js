document.addEventListener('DOMContentLoaded', function() {
  // Set Chart.js defaults for consistent styling
  Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
  Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary');
  Chart.defaults.borderColor = getComputedStyle(document.documentElement).getPropertyValue('--border-color-subtle');
  Chart.defaults.plugins.tooltip.backgroundColor = getComputedStyle(document.documentElement).getPropertyValue('--bg-card');
  Chart.defaults.plugins.tooltip.titleColor = getComputedStyle(document.documentElement).getPropertyValue('--text-primary');
  Chart.defaults.plugins.tooltip.bodyColor = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary');
  Chart.defaults.plugins.tooltip.borderColor = getComputedStyle(document.documentElement).getPropertyValue('--border-color');
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  
  // Color scheme - uses CSS variables for theme compatibility
  const colors = {
    blue: getComputedStyle(document.documentElement).getPropertyValue('--accent-blue'),
    green: getComputedStyle(document.documentElement).getPropertyValue('--accent-green'),
    amber: getComputedStyle(document.documentElement).getPropertyValue('--accent-amber'),
    red: getComputedStyle(document.documentElement).getPropertyValue('--accent-red'),
    purple: getComputedStyle(document.documentElement).getPropertyValue('--accent-purple'),
    blueLight: '#60A5FA',
    greenLight: '#34D399', 
    amberLight: '#FBBF24',
    redLight: '#F87171',
    purpleLight: '#A78BFA'
  };
  
  // Helper function to get gradient
  function getGradient(ctx, chartArea, colorStart, colorEnd) {
    const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
    gradient.addColorStop(0, colorStart);
    gradient.addColorStop(1, colorEnd);
    return gradient;
  }
  
  // Helper to safely access data
  function safeParse(jsonString) {
    try {
      return JSON.parse(jsonString.replace(/'/g, '"'));
    } catch (e) {
      console.error("Error parsing data:", e);
      return null;
    }
  }
  
// Replace your current chartsData parsing code with this:
const chartsDataElement = document.getElementById('charts-data');
let chartsData = {};

if (chartsDataElement) {
  try {
    // Try to get the data from the data attribute (more reliable)
    const jsonContent = chartsDataElement.dataset.chartsContent;
    if (jsonContent) {
      chartsData = JSON.parse(jsonContent);
      console.log("Successfully parsed charts data from data attribute");
    } 
    // Fallback to textContent if data attribute is not available
    else if (chartsDataElement.textContent) {
      chartsData = JSON.parse(chartsDataElement.textContent);
      console.log("Successfully parsed charts data from text content");
    }
  } catch (e) {
    console.error("Error parsing charts data:", e);
    
    // Log the problematic character for debugging
    if (chartsDataElement.dataset.chartsContent || chartsDataElement.textContent) {
      const content = chartsDataElement.dataset.chartsContent || chartsDataElement.textContent;
      const errorMatch = e.message.match(/position (\d+)/);
      
      if (errorMatch && errorMatch[1]) {
        const pos = parseInt(errorMatch[1]);
        const problemChar = content.charAt(pos);
        const context = content.substring(Math.max(0, pos - 20), Math.min(content.length, pos + 20));
        console.error(`Problem at position ${pos}: "${problemChar}" (ASCII: ${problemChar.charCodeAt(0)})`);
        console.error(`Context: "...${context}..."`);
      }
      
      // Try a more robust approach with common JSON fixes
try {
  // Enhanced cleanup for numpy values
  const cleanedJson = content
    .replace(/np\.float\d*\(([\d.]+)\)/g, '$1')  // Replace np.float64(96.559965) with 96.559965
    .replace(/\bNaN\b/g, 'null')
    .replace(/\bnan\b/g, 'null')
    .replace(/\bn(?=\s*[,\]}])/g, 'null')
    .replace(/\bInfinity\b/g, 'null')
    .replace(/\bundefined\b/g, 'null')
    .replace(/,(\s*[\]}])/g, '$1');
    
  chartsData = JSON.parse(cleanedJson);
  console.log("Successfully parsed data after cleanup");
} catch (e2) {
        console.error("Failed second parsing attempt:", e2);
        
        // Use default empty data structure as fallback
        chartsData = {
          tendencia_financiera: {labels: [], datasets: []},
          estado_proyectos: {labels: [], datasets: [{data: [], backgroundColor: []}]},
          cash_in_forecast: {labels: [], datasets: [{data: [], backgroundColor: []}]},
          rentabilidad_departamentos: {labels: [], datasets: [{data: []}]},
          presupuesto_categorias: {labels: [], datasets: [{data: []}]},
          aging_buckets: {labels: [], datasets: [{data: []}]},
          concentracion_clientes: {labels: [], datasets: [{data: []}, {data: []}]}
        };
      }
    }
  }
}

// Add this after your chartsData parsing code - temporary debugging only
function analyzeJsonError(jsonStr, position) {
  if (!jsonStr) return;
  
  // Look at characters around the error position
  const start = Math.max(0, position - 30);
  const end = Math.min(jsonStr.length, position + 30);
  const context = jsonStr.substring(start, end);
  
  console.log('JSON context around error:');
  console.log(context);
  

}

// Call it if there's an error
const content = chartsDataElement.dataset.chartsContent || chartsDataElement.textContent;
if (content) {
  analyzeJsonError(content, 520); // Position from error message
  analyzeJsonError(content, 24);  // Position from second error
}
// Add this after your existing error handling code
function debugJsonString(jsonString) {
  if (!jsonString) return;
  
  // Log exact error position for debugging
  try {
    JSON.parse(jsonString);
  } catch (e) {
    if (e instanceof SyntaxError) {
      const errorMsg = e.message;
      const posMatch = errorMsg.match(/position (\d+)/);
      if (posMatch && posMatch[1]) {
        const pos = parseInt(posMatch[1]);
        const problemChar = jsonString.charAt(pos);
        const context = jsonString.substring(Math.max(0, pos - 20), Math.min(jsonString.length, pos + 20));
        console.error(`Problem at position ${pos}: "${problemChar}" (ASCII: ${problemChar.charCodeAt(0)})`);
        console.error(`Context: "...${context}..."`);
      }
    }
  }
}

// And add this call in your error handling section
if (chartsDataElement && chartsDataElement.textContent) {
  debugJsonString(chartsDataElement.textContent);
}
  
  // ===== FINANCIAL TREND CHART =====
  const financialTrendChart = document.getElementById('financialTrendChart');
  let financialChart;
  
  if (financialTrendChart && chartsData.tendencia_financiera) {
    const financialData = {
      labels: chartsData.tendencia_financiera.labels,
      datasets: chartsData.tendencia_financiera.datasets.map(dataset => ({
        ...dataset,
        borderColor: dataset.borderColor || colors.blue,
        pointBackgroundColor: dataset.label === 'Real' ? colors.blue : 'transparent',
        pointRadius: dataset.label === 'Real' ? 4 : 0,
        tension: 0.3
      }))
    };
    
    const financialOptions = {
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 12,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const value = context.parsed.y || 0;
              return context.dataset.label + ': $' + value.toFixed(1) + 'M';
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
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return '$' + value + 'M';
            }
          }
        }
      }
    };
    
    financialChart = new Chart(financialTrendChart, {
      type: 'line',
      data: financialData,
      options: financialOptions
    });
    
    // Handle financial chart view toggle buttons
    const chartButtons = document.querySelectorAll('[data-chart-view]');
    chartButtons.forEach(button => {
      button.addEventListener('click', function() {
        chartButtons.forEach(btn => {
          btn.classList.remove('active-chart-btn', 'bg-[color:var(--accent-blue)]', 'text-white');
          btn.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]');
        });
        
        button.classList.add('active-chart-btn');
        button.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]');
        button.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
      });
    });
  }
  
  // ===== PROJECT STATUS CHART =====
  const projectStatusChart = document.getElementById('projectStatusChart');
  let projectChart;
  
  if (projectStatusChart && chartsData.estado_proyectos) {
    const projectData = {
      labels: chartsData.estado_proyectos.labels || [],
      datasets: [{
        data: chartsData.estado_proyectos.datasets[0].data || [],
        backgroundColor: chartsData.estado_proyectos.datasets[0].backgroundColor || [
          colors.greenLight,
          colors.amberLight,
          colors.redLight,
          colors.blueLight
        ],
        borderWidth: 0,
        hoverOffset: 4
      }]
    };
    
    const projectOptions = {
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = Math.round((context.parsed * 100) / total);
              return `${context.label}: ${context.parsed} (${percentage}%)`;
            }
          }
        }
      }
    };
    
    projectChart = new Chart(projectStatusChart, {
      type: 'doughnut',
      data: projectData,
      options: projectOptions
    });
  }
  
  // ===== CASH-IN FORECAST CHART =====
  const cashInForecastChart = document.getElementById('cashInForecastChart');
  let cashForecastChart;
  
  if (cashInForecastChart && chartsData.cash_in_forecast) {
    const cashForecastData = {
      labels: chartsData.cash_in_forecast.labels || [],
      datasets: chartsData.cash_in_forecast.datasets.map(dataset => ({
        ...dataset,
        borderWidth: 0,
        borderRadius: 5,
        borderSkipped: false,
      }))
    };
    
    const cashForecastOptions = {
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 12,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return context.dataset.label + ': $' + context.parsed.y.toFixed(1) + 'M';
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
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return '$' + value + 'M';
            }
          },
          stacked: true
        }
      }
    };
    
    cashForecastChart = new Chart(cashInForecastChart, {
      type: 'bar',
      data: cashForecastData,
      options: cashForecastOptions
    });
  }
  
  // ===== DEPARTMENT PROFIT CHART =====
  const departmentProfitChart = document.getElementById('departmentProfitChart');
  let departmentChart;
  
  if (departmentProfitChart && chartsData.rentabilidad_departamentos) {
    const departmentData = {
      labels: chartsData.rentabilidad_departamentos.labels || [],
      datasets: [{
        label: 'Rentabilidad',
        data: chartsData.rentabilidad_departamentos.datasets[0].data || [],
        backgroundColor: function(context) {
          const value = context.raw;
          if (value > 40) return colors.greenLight;
          if (value > 35) return colors.amberLight;
          return colors.redLight;
        },
        borderWidth: 0,
        borderRadius: 5,
        borderSkipped: false,
      }]
    };
    
    const departmentOptions = {
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return 'Rentabilidad: ' + context.parsed.x + '%';
            }
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          max: Math.max(...departmentData.datasets[0].data) * 1.2 || 50,
          ticks: {
            callback: function(value) {
              return value + '%';
            }
          }
        },
        y: {
          grid: {
            display: false
          }
        }
      }
    };
    
    departmentChart = new Chart(departmentProfitChart, {
      type: 'bar',
      data: departmentData,
      options: departmentOptions
    });
    
    // Handle profit view toggle
    const toggleProfitView = document.getElementById('toggle-profit-view');
    if (toggleProfitView) {
      toggleProfitView.addEventListener('click', function() {
        const isPercent = toggleProfitView.innerText === 'Vista %';
        
        if (isPercent) {
          toggleProfitView.innerText = 'Vista $';
          // Show percentage values
          if (chartsData.rentabilidad_departamentos && chartsData.rentabilidad_departamentos.datasets[0].data) {
            departmentChart.data.datasets[0].data = chartsData.rentabilidad_departamentos.datasets[0].data;
          }
          departmentChart.options.scales.x.ticks.callback = function(value) { return value + '%'; };
          departmentChart.options.plugins.tooltip.callbacks.label = function(context) {
            return 'Rentabilidad: ' + context.parsed.x + '%';
          };
        } else {
          toggleProfitView.innerText = 'Vista %';
          // Show monetary values (derived from percentages)
          if (chartsData.rentabilidad_departamentos && chartsData.rentabilidad_departamentos.datasets[0].data) {
            const percentValues = chartsData.rentabilidad_departamentos.datasets[0].data;
            // Convert percentages to monetary values (simplified calculation)
            departmentChart.data.datasets[0].data = percentValues.map(val => val / 30);
          }
          departmentChart.options.scales.x.ticks.callback = function(value) { return '$' + value.toFixed(1) + 'M'; };
          departmentChart.options.plugins.tooltip.callbacks.label = function(context) {
            return 'Rentabilidad: $' + context.parsed.x.toFixed(1) + 'M';
          };
        }
        
        departmentChart.update();
      });
    }
  }
  
  // ===== BUDGET DISTRIBUTION CHART =====
  const budgetDistributionChart = document.getElementById('budgetDistributionChart');
  let budgetChart;
  
  if (budgetDistributionChart && chartsData.presupuesto_categorias) {
    const budgetData = {
      labels: chartsData.presupuesto_categorias.labels || [],
      datasets: [{
        data: chartsData.presupuesto_categorias.datasets[0].data || [],
        backgroundColor: chartsData.presupuesto_categorias.datasets[0].backgroundColor || [
          colors.blue,
          colors.green,
          colors.amber,
          colors.purple,
          'rgba(100, 116, 139, 0.5)'
        ],
        borderWidth: 0,
        hoverOffset: 4
      }]
    };
    
    const budgetOptions = {
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            boxWidth: 12,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return context.label + ': ' + context.parsed.toFixed(1) + '%';
            }
          }
        }
      }
    };
    
    budgetChart = new Chart(budgetDistributionChart, {
      type: 'pie',
      data: budgetData,
      options: budgetOptions
    });
  }
  
  // ===== AGING BUCKETS CHART =====
  const agingBucketsChart = document.getElementById('agingBucketsChart');
  let agingChart;
  
  if (agingBucketsChart && chartsData.aging_buckets) {
    const agingData = {
      labels: chartsData.aging_buckets.labels || [],
      datasets: [{
        label: chartsData.aging_buckets.datasets[0].label || 'EDPs',
        data: chartsData.aging_buckets.datasets[0].data || [],
        backgroundColor: chartsData.aging_buckets.datasets[0].backgroundColor || [
          'rgba(16, 185, 129, 0.7)',  // green
          'rgba(59, 130, 246, 0.7)',  // blue
          'rgba(245, 158, 11, 0.7)',  // amber
          'rgba(239, 68, 68, 0.7)',   // red
        ],
        borderColor: chartsData.aging_buckets.datasets[0].borderColor,
        borderWidth: 0,
        borderRadius: 5,
        borderSkipped: false,
      }]
    };
    
    const agingOptions = {
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return 'Cantidad: ' + context.parsed.y;
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
          beginAtZero: true
        }
      }
    };
    
    agingChart = new Chart(agingBucketsChart, {
      type: 'bar',
      data: agingData,
      options: agingOptions
    });
    
    // Handle aging view toggle
    const toggleAgingView = document.getElementById('toggle-aging-view');
    if (toggleAgingView) {
      toggleAgingView.addEventListener('click', function() {
        const isBarChart = agingChart.config.type === 'bar';
        
        if (isBarChart) {
          // Switch to line chart for trend view (using simulated trend data)
          agingChart.destroy();
          
          // Create trend data (last 6 months) using the aging data as a base
          const currentData = chartsData.aging_buckets.datasets[0].data || [0, 0, 0, 0];
          
          // Generate 6 months of data with slight variations
          const historicalBuckets = [];
          for (let i = 0; i < 6; i++) {
            const monthData = currentData.map(val => {
              // Add random variation between -20% and +20%
              const variation = 0.8 + Math.random() * 0.4;
              return Math.max(0, Math.round(val * variation / (i / 2 + 1)));
            });
            historicalBuckets.unshift(monthData);
          }
          // Replace the last item with the current data
          historicalBuckets[5] = currentData;
          
          const months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"];
          
          const trendData = {
            labels: months,
            datasets: [
              {
                label: '0-15 días',
                data: historicalBuckets.map(month => month[0]),
                borderColor: 'rgba(16, 185, 129, 0.7)',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.3,
                fill: true
              },
              {
                label: '16-30 días',
                data: historicalBuckets.map(month => month[1]),
                borderColor: 'rgba(59, 130, 246, 0.7)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.3,
                fill: true
              },
              {
                label: '31-60 días',
                data: historicalBuckets.map(month => month[2]),
                borderColor: 'rgba(245, 158, 11, 0.7)',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                tension: 0.3,
                fill: true
              },
              {
                label: '> 60 días',
                data: historicalBuckets.map(month => month[3]),
                borderColor: 'rgba(239, 68, 68, 0.7)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.3,
                fill: true
              }
            ]
          };
          
          const trendOptions = {
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'top',
                align: 'end',
                labels: {
                  boxWidth: 12,
                  usePointStyle: true,
                  pointStyle: 'circle'
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
                beginAtZero: true,
                stacked: true
              }
            }
          };
          
          agingChart = new Chart(agingBucketsChart, {
            type: 'line',
            data: trendData,
            options: trendOptions
          });
          
          toggleAgingView.innerText = 'Ver buckets';
        } else {
          // Switch back to bar chart with real data
          agingChart.destroy();
          
          agingChart = new Chart(agingBucketsChart, {
            type: 'bar',
            data: agingData,
            options: agingOptions
          });
          
          toggleAgingView.innerText = 'Ver tendencia';
        }
      });
    }
  }
  
  // ===== PARETO CLIENT CHART =====
  const paretoClientChart = document.getElementById('paretoClientChart');
  let paretoChart;
  
  if (paretoClientChart && chartsData.concentracion_clientes) {
    const paretoData = {
      labels: chartsData.concentracion_clientes.labels || [],
      datasets: [
        {
          type: 'bar',
          label: chartsData.concentracion_clientes.datasets[0].label || 'Monto',
          data: chartsData.concentracion_clientes.datasets[0].data || [],
          backgroundColor: chartsData.concentracion_clientes.datasets[0].backgroundColor || 'rgba(59, 130, 246, 0.7)',
          borderColor: colors.blue,
          borderWidth: 1,
          borderRadius: 5,
          barPercentage: 0.6,
          order: 2
        },
        {
          type: 'line',
          label: chartsData.concentracion_clientes.datasets[1].label || 'Acumulado',
          data: chartsData.concentracion_clientes.datasets[1].data || [],
          borderColor: chartsData.concentracion_clientes.datasets[1].borderColor || colors.amber,
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: colors.amber,
          order: 1,
          yAxisID: 'percentage'
        }
      ]
    };
    
    const paretoOptions = {
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 12,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const datasetLabel = context.dataset.label;
              const value = context.parsed.y;
              if (datasetLabel === 'Acumulado (%)') {
                return datasetLabel + ': ' + value.toFixed(1) + '%';
              }
              return datasetLabel + ': $' + value.toFixed(1) + 'M';
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
          position: 'left',
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return '$' + value + 'M';
            }
          },
          title: {
            display: true,
            text: 'Monto'
          }
        },
        percentage: {
          position: 'right',
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: function(value) {
              return value + '%';
            }
          },
          title: {
            display: true,
            text: 'Acumulado'
          },
          grid: {
            drawOnChartArea: false
          }
        }
      }
    };
    
    paretoChart = new Chart(paretoClientChart, {
      type: 'bar',
      data: paretoData,
      options: paretoOptions
    });
    
    // Handle pareto toggle between ingresos and pendiente
    const paretoIngresos = document.getElementById('pareto-toggle-ingresos');
    const paretoPendiente = document.getElementById('pareto-toggle-pendiente');
    
    if (paretoIngresos && paretoPendiente) {
      paretoIngresos.addEventListener('click', function() {
        paretoIngresos.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
        paretoIngresos.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border');
        
        paretoPendiente.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
        paretoPendiente.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border', 'border-[color:var(--border-color)]');
        
        // Here we would ideally switch to income data
        // For now, we'll keep the existing data but change labels
        paretoChart.data.datasets[0].label = 'Ingresos';
        paretoChart.options.scales.y.title.text = 'Ingresos';
        paretoChart.update();
      });
      
      paretoPendiente.addEventListener('click', function() {
        paretoPendiente.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
        paretoPendiente.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border');
        
        paretoIngresos.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
        paretoIngresos.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border', 'border-[color:var(--border-color)]');
        
        // Here we would ideally switch to pending amount data
        // For now, we'll keep the existing data but change labels and color
        paretoChart.data.datasets[0].label = 'Pendiente';
        paretoChart.data.datasets[0].backgroundColor = 'rgba(239, 68, 68, 0.7)';
        paretoChart.data.datasets[0].borderColor = colors.red;
        paretoChart.options.scales.y.title.text = 'Pendiente';
        paretoChart.update();
      });
    }
  }
  
  // Función para resetear filtros
  window.resetFilters = function() {
    const form = document.getElementById('dashboard-filters');
    if (form) {
      // Restablecer campos de fecha
      form.querySelectorAll('input[type="date"]').forEach(input => {
        input.value = '';
      });
      
      // Restablecer selects al primer valor
      form.querySelectorAll('select').forEach(select => {
        if (select.options.length) {
          select.selectedIndex = 0;
        }
      });
      
      // Enviar formulario
      form.submit();
    }
  };
  
  // Toggle entre vistas de proyectos
  const viewButtons = document.querySelectorAll('[data-view]');
  if (viewButtons.length) {
    viewButtons.forEach(button => {
      button.addEventListener('click', function() {
        // Cambiar estado activo de botones
        document.querySelectorAll('[data-view]').forEach(btn => {
          btn.classList.remove('active-view-btn');
          btn.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]');
        });
        this.classList.add('active-view-btn');
        this.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]');
        
        // Mostrar vista correspondiente
        const viewToShow = this.getAttribute('data-view');
        if (viewToShow === 'chart') {
          document.getElementById('project-chart-view').classList.remove('hidden');
          document.getElementById('project-bubble-view').classList.add('hidden');
        } else {
          document.getElementById('project-chart-view').classList.add('hidden');
          document.getElementById('project-bubble-view').classList.remove('hidden');
        }
      });
    });
  }
  
  // Project actions menu toggle
  const projectActionsBtn = document.getElementById('project-actions-btn');
  const projectActionsMenu = document.getElementById('project-actions-menu');
  
  if (projectActionsBtn && projectActionsMenu) {
    projectActionsBtn.addEventListener('click', function() {
      projectActionsMenu.classList.toggle('hidden');
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
      if (!projectActionsBtn.contains(event.target) && !projectActionsMenu.contains(event.target)) {
        projectActionsMenu.classList.add('hidden');
      }
    });
  }
  
  // Handle theme changes - update charts when theme changes
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.attributeName === 'class') {
        // Always update charts when the class changes, regardless of whether dark is added or removed
        updateChartsTheme();
      }
    });
  });
  
  observer.observe(document.documentElement, { attributes: true });
  
  // Replace your current updateChartsTheme function with this enhanced version
  function updateChartsTheme() {
    // Get current theme colors from CSS variables
    const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim();
    const textSecondary = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim();
    const borderColor = getComputedStyle(document.documentElement).getPropertyValue('--border-color').trim();
    const bgCard = getComputedStyle(document.documentElement).getPropertyValue('--bg-card').trim();
    
    // Update Chart.js global defaults
    Chart.defaults.color = textSecondary;
    Chart.defaults.borderColor = borderColor;
    Chart.defaults.plugins.tooltip.backgroundColor = bgCard;
    Chart.defaults.plugins.tooltip.titleColor = textColor;
    Chart.defaults.plugins.tooltip.bodyColor = textSecondary;
    Chart.defaults.plugins.tooltip.borderColor = borderColor;
    
    // Collection of all chart instances
    const charts = [
      financialChart, 
      projectChart, 
      cashForecastChart, 
      departmentChart, 
      budgetChart, 
      agingChart, 
      paretoChart
    ];
    
    // Update each chart's specific options
    charts.forEach(chart => {
      if (!chart) return;
      
      // Update scale colors
      if (chart.options.scales) {
        Object.keys(chart.options.scales).forEach(scaleID => {
          const scale = chart.options.scales[scaleID];
          
          // Update tick colors
          if (scale.ticks) {
            scale.ticks.color = textSecondary;
          }
          
          // Update grid colors
          if (scale.grid) {
            scale.grid.color = borderColor;
          }
          
          // Update axis title
          if (scale.title) {
            scale.title.color = textColor;
          }
        });
      }
      
      // Update legend colors
      if (chart.options.plugins && chart.options.plugins.legend) {
        chart.options.plugins.legend.labels.color = textSecondary;
      }
      
      // Update tooltip colors
      if (chart.options.plugins && chart.options.plugins.tooltip) {
        chart.options.plugins.tooltip.backgroundColor = bgCard;
        chart.options.plugins.tooltip.titleColor = textColor;
        chart.options.plugins.tooltip.bodyColor = textSecondary;
        chart.options.plugins.tooltip.borderColor = borderColor;
      }
      
      // Apply changes
      chart.update();
    });
    
    // Log the update for debugging
    console.log('Charts updated for theme change');
  }
});