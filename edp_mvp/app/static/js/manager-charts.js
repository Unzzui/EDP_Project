document.addEventListener('DOMContentLoaded', function() {
  console.log('🎯 Charts Manager iniciado');
  
  // ===== FUNCIONES PARA TEMA ADAPTATIVO =====
  
  function isDarkMode() {
    // ✅ DETECCIÓN MEJORADA
    const htmlElement = document.documentElement;
    
    // Prioridad 1: Clase específica de light
    if (htmlElement.classList.contains('light')) {
      return false;
    }
    
    // Prioridad 2: Clase específica de dark
    if (htmlElement.classList.contains('dark')) {
      return true;
    }
    
    // Prioridad 3: Preferencia del sistema
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  function getAdaptiveColors() {
    const root = getComputedStyle(document.documentElement);
    const dark = isDarkMode();
    
    console.log('🎨 Modo detectado:', dark ? 'DARK' : 'LIGHT');
    console.log('🎨 Clases en html:', document.documentElement.classList.toString());
    
    // Obtener las variables CSS
    const cssTextPrimary = root.getPropertyValue('--text-primary').trim();
    const cssTextSecondary = root.getPropertyValue('--text-secondary').trim();
    const cssBorderColor = root.getPropertyValue('--border-color').trim();
    
    console.log('📝 CSS Variables:');
    console.log('  --text-primary:', cssTextPrimary);
    console.log('  --text-secondary:', cssTextSecondary);
    
    // ✅ OVERRIDE PARA CHARTS - SIEMPRE USAR COLORES ÓPTIMOS
    if (dark) {
      return {
        textPrimary: '#FFFFFF',        // Blanco puro para títulos
        textSecondary: '#D1D5DB',      // Gris claro para ejes
        borderColor: cssBorderColor || '#374151',
        bgPrimary: root.getPropertyValue('--bg-card').trim() || '#1F2937',
        bgSecondary: root.getPropertyValue('--bg-subtle').trim() || '#111827',
        tooltipBg: 'rgba(17, 24, 39, 0.95)',
        gridColor: 'rgba(156, 163, 175, 0.3)'
      };
    } else {
      return {
        textPrimary: '#111827',        // Negro para títulos en light
        textSecondary: '#374151',      // Gris oscuro para ejes
        borderColor: cssBorderColor || '#D1D5DB',
        bgPrimary: root.getPropertyValue('--bg-card').trim() || '#FFFFFF',
        bgSecondary: root.getPropertyValue('--bg-subtle').trim() || '#F9FAFB',
        tooltipBg: 'rgba(255, 255, 255, 0.95)',
        gridColor: 'rgba(75, 85, 99, 0.3)'
      };
    }
  }


  function setupChartDefaults() {
    const adaptiveColors = getAdaptiveColors();
    
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    Chart.defaults.color = adaptiveColors.textSecondary;
    Chart.defaults.borderColor = adaptiveColors.borderColor;
    Chart.defaults.backgroundColor = adaptiveColors.bgPrimary;
    
    console.log('🎨 Chart defaults configurados para tema:', isDarkMode() ? 'dark' : 'light');
  }

// ===== FUNCIÓN MEJORADA PARA FORZAR ACTUALIZACIÓN =====
function updateChartsTheme() {
  const adaptiveColors = getAdaptiveColors();
  
  console.log('🔄 FORZANDO actualización de tema...');
  console.log('🎨 Colores a aplicar:', adaptiveColors);
  
  // Actualizar defaults globales
  Chart.defaults.color = adaptiveColors.textSecondary;
  Chart.defaults.borderColor = adaptiveColors.borderColor;
  Chart.defaults.backgroundColor = adaptiveColors.bgPrimary;
  
  // Método más agresivo para encontrar charts
  let chartInstances = [];
  
  // Buscar todos los canvas y obtener charts
  const canvasElements = document.querySelectorAll('canvas');
  console.log(`🔍 Encontrados ${canvasElements.length} canvas elements`);
  
  canvasElements.forEach((canvas, canvasIndex) => {
    try {
      // Método 1: Chart.getChart()
      let chart = Chart.getChart(canvas);
      if (chart) {
        chartInstances.push({ chart, source: 'getChart', canvas, canvasIndex });
      }
      
      // Método 2: canvas.chart property
      if (canvas.chart && typeof canvas.chart.update === 'function') {
        const existingIndex = chartInstances.findIndex(item => item.chart === canvas.chart);
        if (existingIndex === -1) {
          chartInstances.push({ chart: canvas.chart, source: 'canvas.chart', canvas, canvasIndex });
        }
      }
      
      // Método 3: Chart.instances si existe
      if (Chart.instances) {
        if (Array.isArray(Chart.instances)) {
          Chart.instances.forEach(instance => {
            if (instance.canvas === canvas) {
              const existingIndex = chartInstances.findIndex(item => item.chart === instance);
              if (existingIndex === -1) {
                chartInstances.push({ chart: instance, source: 'instances', canvas, canvasIndex });
              }
            }
          });
        } else if (typeof Chart.instances === 'object') {
          Object.values(Chart.instances).forEach(instance => {
            if (instance && instance.canvas === canvas) {
              const existingIndex = chartInstances.findIndex(item => item.chart === instance);
              if (existingIndex === -1) {
                chartInstances.push({ chart: instance, source: 'instances-object', canvas, canvasIndex });
              }
            }
          });
        }
      }
    } catch (e) {
      console.warn(`⚠️ Error buscando chart en canvas ${canvasIndex}:`, e);
    }
  });
  
  console.log(`📊 Charts encontrados: ${chartInstances.length}`);
  chartInstances.forEach((item, i) => {
    console.log(`  ${i}: Fuente=${item.source}, Canvas=${item.canvasIndex}, ID=${item.canvas.id}`);
  });
  
  // Actualizar cada chart de forma más agresiva
  chartInstances.forEach((item, index) => {
    try {
      const { chart, source, canvas } = item;
      
      if (!chart || !chart.options) {
        console.warn(`⚠️ Chart ${index} (${source}) no tiene opciones válidas`);
        return;
      }
      
      console.log(`🔧 Actualizando chart ${index} (${source}, canvas: ${canvas.id})`);
      
      // ===== ACTUALIZAR PLUGINS =====
      
      // Título
      if (chart.options.plugins) {
        if (!chart.options.plugins.title) {
          chart.options.plugins.title = {};
        }
        chart.options.plugins.title.color = adaptiveColors.textPrimary;
        console.log(`  ✅ Título actualizado a: ${adaptiveColors.textPrimary}`);
        
        // Leyenda
        if (chart.options.plugins.legend && chart.options.plugins.legend.labels) {
          chart.options.plugins.legend.labels.color = adaptiveColors.textSecondary;
          console.log(`  ✅ Leyenda actualizada a: ${adaptiveColors.textSecondary}`);
        }
        
        // Tooltip
        if (chart.options.plugins.tooltip) {
          chart.options.plugins.tooltip.backgroundColor = adaptiveColors.tooltipBg;
          chart.options.plugins.tooltip.titleColor = adaptiveColors.textPrimary;
          chart.options.plugins.tooltip.bodyColor = adaptiveColors.textSecondary;
          console.log(`  ✅ Tooltip actualizado`);
        }
      }
      
      // ===== ACTUALIZAR ESCALAS =====
      if (chart.options.scales) {
        Object.keys(chart.options.scales).forEach(scaleKey => {
          const scale = chart.options.scales[scaleKey];
          
          // Título de escala
          if (scale.title) {
            scale.title.color = adaptiveColors.textPrimary;
            console.log(`  ✅ Escala ${scaleKey} título actualizado a: ${adaptiveColors.textPrimary}`);
          }
          
          // Ticks
          if (scale.ticks) {
            scale.ticks.color = adaptiveColors.textSecondary;
            console.log(`  ✅ Escala ${scaleKey} ticks actualizado a: ${adaptiveColors.textSecondary}`);
          }
          
          // Grid
          if (scale.grid) {
            scale.grid.color = adaptiveColors.gridColor;
            console.log(`  ✅ Escala ${scaleKey} grid actualizado a: ${adaptiveColors.gridColor}`);
          }
          
          // Point labels (para radar charts)
          if (scale.pointLabels) {
            scale.pointLabels.color = adaptiveColors.textSecondary;
            console.log(`  ✅ Escala ${scaleKey} pointLabels actualizado`);
          }
        });
      }
      
      // ===== ACTUALIZAR ELEMENTOS ESPECÍFICOS =====
      if (chart.options.elements) {
        if (chart.options.elements.arc) {
          chart.options.elements.arc.borderColor = adaptiveColors.bgPrimary;
          console.log(`  ✅ Elementos arc actualizados`);
        }
      }
      
      // ===== FORZAR UPDATE =====
      console.log(`  🔄 Forzando update del chart ${index}...`);
      chart.update('none'); // Sin animación
      
      // Intentar segundo update si el primero no funcionó
      setTimeout(() => {
        try {
          chart.update('resize');
          console.log(`  ✅ Chart ${index} actualizado exitosamente`);
        } catch (e2) {
          console.warn(`  ⚠️ Error en segundo update del chart ${index}:`, e2);
        }
      }, 50);
      
    } catch (e) {
      console.error(`❌ Error actualizando chart ${index}:`, e);
    }
  });
  
  console.log(`✅ Proceso de actualización completado para ${chartInstances.length} charts`);
}
  // Configurar defaults iniciales
  setupChartDefaults();
  
  // Color scheme
  const colors = {
    blue: '#3B82F6',
    green: '#10B981',
    amber: '#F59E0B',
    red: '#EF4444',
    purple: '#8B5CF6',
    blueLight: '#60A5FA',
    greenLight: '#34D399', 
    amberLight: '#FBBF24',
    redLight: '#F87171',
    purpleLight: '#A78BFA'
  };
  
  // ===== OBTENER DATOS DE CHARTS =====
  let chartsData = {};
  
  if (typeof Chart === 'undefined') {
    console.error('❌ Chart.js no está disponible');
    return;
  }

  const chartsDataElement = document.getElementById('charts-data');
  if (chartsDataElement) {
    try {
      const jsonContent = chartsDataElement.textContent.trim();
      console.log('📊 JSON content length:', jsonContent.length);
      
      if (jsonContent && jsonContent !== '{}') {
        chartsData = JSON.parse(jsonContent);
        console.log('✅ Charts data parseado exitosamente');
        console.log('📊 Charts data keys:', Object.keys(chartsData));
      } else {
        console.warn('⚠️ JSON content está vacío o es objeto vacío');
      }
    } catch (e) {
      console.error('❌ Error parseando charts data:', e);
    }
  } else {
    console.error('❌ Elemento charts-data no encontrado');
  }
  
  // ===== CREAR CHARTS CON COLORES ADAPTATIVOS =====
  
  // 1. FINANCIAL TREND CHART 
  const financialTrendElement = document.getElementById('financialTrendChart');
  if (financialTrendElement) {
    try {
      const data = chartsData.tendencia_financiera;
      const adaptiveColors = getAdaptiveColors();
      
      if (!data || !data.datasets || data.datasets.length === 0) {
        console.warn('⚠️ No hay datos para financial trend chart');
        financialTrendElement.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">No hay datos disponibles</div>';
      } else {
        const config = {
          type: 'line',
          data: {
            labels: data.labels || [],
            datasets: data.datasets || []
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
              mode: 'index',
              intersect: false
            },
            plugins: {
              title: {
                display: true,
                text: 'Tendencia Financiera - Histórico y Proyecciones',
                font: {
                  size: 16,
                  weight: 'bold'
                },
                color: adaptiveColors.textPrimary
              },
              legend: {
                display: true,
                position: 'bottom',
                labels: {
                  usePointStyle: true,
                  padding: 10,
                  font: {
                    size: 12
                  },
                  color: adaptiveColors.textSecondary
                }
              },
              tooltip: {
                backgroundColor: adaptiveColors.tooltipBg,
                titleColor: adaptiveColors.textPrimary,
                bodyColor: adaptiveColors.textSecondary,
                borderColor: colors.blue,
                borderWidth: 1,
                cornerRadius: 8,
                callbacks: {
                  title: function(context) {
                    if (context && context[0] && context[0].label) {
                      const label = context[0].label;
                      return label + (label.includes('(P)') ? ' - Proyección' : ' - Real');
                    }
                    return '';
                  },
                  label: function(context) {
                    if (context && context.parsed && context.dataset) {
                      const value = context.parsed.y;
                      const label = context.dataset.label;
                      return label + ': $' + (value ? value.toFixed(1) : '0.0') + 'M';
                    }
                    return '';
                  }
                }
              }
            },
            scales: {
              x: {
                display: true,
                title: {
                  display: true,
                  text: 'Período (Últimos 6 meses + 3 proyecciones)',
                  font: {
                    size: 12,
                    weight: 'bold'
                  },
                  color: adaptiveColors.textPrimary
                },
                grid: {
                  color: adaptiveColors.gridColor
                },
                ticks: {
                  maxRotation: 45,
                  font: {
                    size: 11
                  },
                  color: adaptiveColors.textSecondary
                }
              },
              y: {
                display: true,
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Millones de pesos (M$)',
                  font: {
                    size: 12,
                    weight: 'bold'
                  },
                  color: adaptiveColors.textPrimary
                },
                grid: {
                  color: adaptiveColors.gridColor
                },
                ticks: {
                  callback: function(value) {
                    return '$' + (value ? value.toFixed(1) : '0.0') + 'M';
                  },
                  font: {
                    size: 11
                  },
                  color: adaptiveColors.textSecondary
                }
              }
            },
            elements: {
              point: {
                hoverRadius: 8,
                hoverBorderWidth: 3
              },
              line: {
                tension: 0.3
              }
            },
            animation: {
              duration: 1000,
              easing: 'easeInOutQuart'
            }
          }
        };
        
        new Chart(financialTrendElement, config);
        console.log('✅ Financial trend chart creado con tema adaptativo');
      }
    } catch (e) {
      console.error('❌ Error creando financial trend chart:', e);
    }
  }

  // 2. CASH FORECAST DETALLADO
  const cashForecastDetailedElement = document.getElementById('cashForecastDetailedChart');
  if (cashForecastDetailedElement) {
    try {
      const data = chartsData.cash_forecast_detallado;
      const adaptiveColors = getAdaptiveColors();
      
      if (data && data.datasets && data.datasets.length > 0) {
        new Chart(cashForecastDetailedElement, {
          type: 'bar',
          data: {
            labels: data.labels || [],
            datasets: data.datasets || []
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              title: {
                display: true,
                text: 'Proyección de Cash Flow - Múltiples Escenarios',
                color: adaptiveColors.textPrimary
              },
              legend: {
                position: 'top',
                labels: {
                  color: adaptiveColors.textSecondary
                }
              },
              tooltip: {
                backgroundColor: adaptiveColors.tooltipBg,
                titleColor: adaptiveColors.textPrimary,
                bodyColor: adaptiveColors.textSecondary,
                borderColor: colors.blue,
                borderWidth: 1,
                callbacks: {
                  label: function(context) {
                    return context.dataset.label + ': $' + context.parsed.y + 'M';
                  }
                }
              }
            },
            scales: {
              x: {
                title: {
                  display: true,
                  text: 'Períodos de Cobranza',
                  color: adaptiveColors.textPrimary
                },
                grid: {
                  color: adaptiveColors.gridColor
                },
                ticks: {
                  color: adaptiveColors.textSecondary
                }
              },
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Millones de pesos (M$)',
                  color: adaptiveColors.textPrimary
                },
                grid: {
                  color: adaptiveColors.gridColor
                },
                ticks: {
                  callback: function(value) {
                    return '$' + value + 'M';
                  },
                  color: adaptiveColors.textSecondary
                }
              }
            }
          }
        });
        console.log('✅ Cash forecast detallado creado con tema adaptativo');
      }
    } catch (e) {
      console.error('❌ Error creando cash forecast detallado:', e);
    }
  }
// 3. CASH FORECAST CHART
const cashForecastElement = document.getElementById('cashInForecastChart');
if (cashForecastElement) {
  try {
    const data = chartsData.cash_in_forecast;
    const adaptiveColors = getAdaptiveColors();
    console.log('💰 Creando cash forecast chart:', data);
    
    new Chart(cashForecastElement, {
      type: 'bar',
      data: data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Pronóstico de Cash Flow',
            color: adaptiveColors.textPrimary
          },
          legend: {
            position: 'top',
            labels: {
              color: adaptiveColors.textSecondary
            }
          },
          tooltip: {
            backgroundColor: adaptiveColors.tooltipBg,
            titleColor: adaptiveColors.textPrimary,
            bodyColor: adaptiveColors.textSecondary,
            borderColor: colors.blue,
            borderWidth: 1,
            cornerRadius: 8
          }
        },
        scales: {
          x: {
            grid: {
              color: adaptiveColors.gridColor
            },
            ticks: {
              color: adaptiveColors.textSecondary
            }
          },
          y: {
            beginAtZero: true,
            stacked: true,
            title: {
              display: true,
              text: 'Millones de pesos (M$)',
              color: adaptiveColors.textPrimary
            },
            grid: {
              color: adaptiveColors.gridColor
            },
            ticks: {
              callback: function(value) {
                return '$' + value + 'M';
              },
              color: adaptiveColors.textSecondary
            }
          }
        }
      }
    });
    console.log('✅ Cash forecast chart creado');
  } catch (e) {
    console.error('❌ Error creando cash forecast chart:', e);
  }
}

// 4. DEPARTMENT PROFIT CHART
const departmentProfitElement = document.getElementById('departmentProfitChart');
if (departmentProfitElement) {
  try {
    const data = chartsData.rentabilidad_departamentos;
    const adaptiveColors = getAdaptiveColors();
    console.log('📈 Creando department profit chart:', data);
    
    new Chart(departmentProfitElement, {
      type: 'bar',
      data: data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          title: {
            display: true,
            text: 'Rentabilidad por Departamento',
            color: adaptiveColors.textPrimary
          },
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: adaptiveColors.tooltipBg,
            titleColor: adaptiveColors.textPrimary,
            bodyColor: adaptiveColors.textSecondary,
            borderColor: colors.green,
            borderWidth: 1,
            cornerRadius: 8,
            callbacks: {
              label: function(context) {
                return context.dataset.label + ': ' + context.parsed.x + '%';
              }
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Rentabilidad (%)',
              color: adaptiveColors.textPrimary
            },
            grid: {
              color: adaptiveColors.gridColor
            },
            ticks: {
              callback: function(value) {
                return value + '%';
              },
              color: adaptiveColors.textSecondary
            }
          },
          y: {
            grid: {
              color: adaptiveColors.gridColor
            },
            ticks: {
              color: adaptiveColors.textSecondary
            }
          }
        }
      }
    });
    console.log('✅ Department profit chart creado');
  } catch (e) {
    console.error('❌ Error creando department profit chart:', e);
  }
}

// 5. BUDGET DISTRIBUTION CHART
const budgetDistributionElement = document.getElementById('budgetDistributionChart');
if (budgetDistributionElement) {
  try {
    const data = chartsData.presupuesto_categorias;
    const adaptiveColors = getAdaptiveColors();
    console.log('🥧 Creando budget distribution chart:', data);
    
    new Chart(budgetDistributionElement, {
      type: 'pie',
      data: data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Distribución del Presupuesto',
            color: adaptiveColors.textPrimary
          },
          legend: {
            position: 'right',
            labels: {
              color: adaptiveColors.textSecondary,
              padding: 15,
              usePointStyle: true
            }
          },
          tooltip: {
            backgroundColor: adaptiveColors.tooltipBg,
            titleColor: adaptiveColors.textPrimary,
            bodyColor: adaptiveColors.textSecondary,
            borderColor: colors.purple,
            borderWidth: 1,
            cornerRadius: 8,
            callbacks: {
              label: function(context) {
                const value = context.parsed;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                return context.label + ': $' + value + 'M (' + percentage + '%)';
              }
            }
          }
        },
        elements: {
          arc: {
            borderWidth: 2,
            borderColor: adaptiveColors.bgPrimary
          }
        }
      }
    });
    console.log('✅ Budget distribution chart creado');
  } catch (e) {
    console.error('❌ Error creando budget distribution chart:', e);
  }
}

// 6. AGING BUCKETS CHART
const agingBucketsElement = document.getElementById('agingBucketsChart');
if (agingBucketsElement) {
  try {
    const data = chartsData.aging_buckets;
    const adaptiveColors = getAdaptiveColors();
    console.log('📅 Creando aging buckets chart:', data);
    
    new Chart(agingBucketsElement, {
      type: 'bar',
      data: data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Análisis de Antigüedad - Aging Buckets',
            color: adaptiveColors.textPrimary
          },
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: adaptiveColors.tooltipBg,
            titleColor: adaptiveColors.textPrimary,
            bodyColor: adaptiveColors.textSecondary,
            borderColor: colors.amber,
            borderWidth: 1,
            cornerRadius: 8,
            callbacks: {
              label: function(context) {
                return context.label + ': ' + context.parsed.y + ' EDPs';
              },
              afterLabel: function(context) {
                const label = context.label;
                if (label.includes('0-30')) {
                  return 'Estado: Recientes ✅';
                } else if (label.includes('31-60')) {
                  return 'Estado: En seguimiento 🔄';
                } else if (label.includes('60+')) {
                  return 'Estado: Críticos ⚠️';
                }
                return '';
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Días de Antigüedad',
              color: adaptiveColors.textPrimary
            },
            grid: {
              color: adaptiveColors.gridColor
            },
            ticks: {
              color: adaptiveColors.textSecondary
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Cantidad de EDPs',
              color: adaptiveColors.textPrimary
            },
            grid: {
              color: adaptiveColors.gridColor
            },
            ticks: {
              stepSize: 1,
              color: adaptiveColors.textSecondary
            }
          }
        }
      }
    });
    console.log('✅ Aging buckets chart creado');
  } catch (e) {
    console.error('❌ Error creando aging buckets chart:', e);
  }
}

// 7. PROJECT STATUS CHART (ACTUALIZADO)
const projectStatusElement = document.getElementById('projectStatusChart');
if (projectStatusElement) {
  try {
    const data = chartsData.estado_proyectos;
    const adaptiveColors = getAdaptiveColors();
    console.log('📊 Creando project status chart:', data);
    
    if (data && data.datasets && data.datasets.length > 0) {
      new Chart(projectStatusElement, {
        type: 'doughnut',
        data: {
          labels: data.labels || [],
          datasets: data.datasets || []
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: 'Estado de Proyectos EDP',
              color: adaptiveColors.textPrimary
            },
            legend: {
              position: 'bottom',
              labels: {
                padding: 15,
                usePointStyle: true,
                font: {
                  size: 12
                },
                color: adaptiveColors.textSecondary
              }
            },
            tooltip: {
              backgroundColor: adaptiveColors.tooltipBg,
              titleColor: adaptiveColors.textPrimary,
              bodyColor: adaptiveColors.textSecondary,
              borderColor: colors.blue,
              borderWidth: 1,
              cornerRadius: 8,
              callbacks: {
                label: function(context) {
                  if (context && context.parsed !== undefined) {
                    const value = context.parsed;
                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                    return context.label + ': ' + value + ' EDPs (' + percentage + '%)';
                  }
                  return '';
                },
                afterLabel: function(context) {
                  // Agregar información adicional según el estado
                  const label = context.label;
                  if (label.includes('Pagado') || label.includes('Validado')) {
                    return 'Estado: Completado ✅';
                  } else if (label.includes('Enviado') || label.includes('Revisión')) {
                    return 'Estado: En proceso 🔄';
                  } else if (label.includes('Critico') || label.includes('Crítico')) {
                    return 'Estado: Requiere atención ⚠️';
                  }
                  return '';
                }
              }
            }
          },
          cutout: '50%', // Para hacer un donut chart
          elements: {
            arc: {
              borderWidth: 2,
              borderColor: adaptiveColors.bgPrimary
            }
          },
          animation: {
            animateRotate: true,
            animateScale: true,
            duration: 1000,
            easing: 'easeInOutQuart'
          }
        }
      });
      console.log('✅ Project status chart creado');
    } else {
      console.warn('⚠️ No hay datos para project status chart');
      projectStatusElement.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">No hay datos de estado disponibles</div>';
    }
  } catch (e) {
    console.error('❌ Error creando project status chart:', e);
    projectStatusElement.innerHTML = `
      <div class="flex items-center justify-center h-full text-red-500">
        <div class="text-center">
          <div class="text-2xl mb-2">⚠️</div>
          <div>Error cargando gráfico de estado</div>
          <div class="text-sm text-gray-500 mt-1">Ver consola para detalles</div>
        </div>
      </div>
    `;
  }
}

// 8. PARETO CLIENT CHART (ACTUALIZADO)
const paretoClientElement = document.getElementById('paretoClientChart');
if (paretoClientElement) {
  try {
    const data = chartsData.concentracion_clientes;
    const adaptiveColors = getAdaptiveColors();
    console.log('📈 Creando pareto client chart:', data);
    
    new Chart(paretoClientElement, {
      type: 'bar',
      data: data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Concentración de Clientes - Análisis Pareto',
            color: adaptiveColors.textPrimary
          },
          legend: {
            position: 'top',
            labels: {
              color: adaptiveColors.textSecondary
            }
          },
          tooltip: {
            backgroundColor: adaptiveColors.tooltipBg,
            titleColor: adaptiveColors.textPrimary,
            bodyColor: adaptiveColors.textSecondary,
            borderColor: colors.blue,
            borderWidth: 1,
            cornerRadius: 8,
            callbacks: {
              label: function(context) {
                if (context.datasetIndex === 0) {
                  return 'Monto: $' + context.parsed.y + 'M';
                } else {
                  return 'Acumulado: ' + context.parsed.y + '%';
                }
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Clientes (Top 10)',
              color: adaptiveColors.textPrimary
            },
            grid: {
              color: adaptiveColors.gridColor
            },
            ticks: {
              maxRotation: 45,
              color: adaptiveColors.textSecondary
            }
          },
          y: {
            position: 'left',
            beginAtZero: true,
            title: {
              display: true,
              text: 'Millones de pesos (M$)',
              color: adaptiveColors.textPrimary
            },
            grid: {
              color: adaptiveColors.gridColor
            },
            ticks: {
              callback: function(value) {
                return '$' + value + 'M';
              },
              color: adaptiveColors.textSecondary
            }
          },
          percentage: {
            position: 'right',
            beginAtZero: true,
            max: 100,
            title: {
              display: true,
              text: 'Porcentaje Acumulado (%)',
              color: adaptiveColors.textPrimary
            },
            grid: {
              drawOnChartArea: false,
              color: adaptiveColors.gridColor
            },
            ticks: {
              callback: function(value) {
                return value + '%';
              },
              color: adaptiveColors.textSecondary
            }
          }
        }
      }
    });
    console.log('✅ Pareto client chart creado');
  } catch (e) {
    console.error('❌ Error creando pareto client chart:', e);
  }
}

// 9. MANAGER PERFORMANCE CHART (SI EXISTE)
const managerPerformanceElement = document.getElementById('managerPerformanceChart');
if (managerPerformanceElement) {
  try {
    const data = chartsData.rendimiento_gestores;
    const adaptiveColors = getAdaptiveColors();
    console.log('👨‍💼 Creando manager performance chart:', data);
    
    if (data && data.datasets && data.datasets.length > 0) {
      new Chart(managerPerformanceElement, {
        type: 'radar',
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: 'Rendimiento de Gestores',
              color: adaptiveColors.textPrimary
            },
            legend: {
              position: 'top',
              labels: {
                color: adaptiveColors.textSecondary
              }
            },
            tooltip: {
              backgroundColor: adaptiveColors.tooltipBg,
              titleColor: adaptiveColors.textPrimary,
              bodyColor: adaptiveColors.textSecondary,
              borderColor: colors.purple,
              borderWidth: 1,
              cornerRadius: 8
            }
          },
          scales: {
            r: {
              beginAtZero: true,
              max: 100,
              grid: {
                color: adaptiveColors.gridColor
              },
              pointLabels: {
                color: adaptiveColors.textSecondary
              },
              ticks: {
                color: adaptiveColors.textSecondary,
                backdropColor: adaptiveColors.bgPrimary
              }
            }
          }
        }
      });
      console.log('✅ Manager performance chart creado');
    }
  } catch (e) {
    console.error('❌ Error creando manager performance chart:', e);
  }
}

// 10. TIMELINE CHART (SI EXISTE)
const timelineElement = document.getElementById('timelineChart');
if (timelineElement) {
  try {
    const data = chartsData.timeline_proyectos;
    const adaptiveColors = getAdaptiveColors();
    console.log('📅 Creando timeline chart:', data);
    
    if (data && data.datasets && data.datasets.length > 0) {
      new Chart(timelineElement, {
        type: 'line',
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: 'Timeline de Proyectos',
              color: adaptiveColors.textPrimary
            },
            legend: {
              position: 'top',
              labels: {
                color: adaptiveColors.textSecondary
              }
            },
            tooltip: {
              backgroundColor: adaptiveColors.tooltipBg,
              titleColor: adaptiveColors.textPrimary,
              bodyColor: adaptiveColors.textSecondary,
              borderColor: colors.green,
              borderWidth: 1,
              cornerRadius: 8
            }
          },
          scales: {
            x: {
              title: {
                display: true,
                text: 'Tiempo',
                color: adaptiveColors.textPrimary
              },
              grid: {
                color: adaptiveColors.gridColor
              },
              ticks: {
                color: adaptiveColors.textSecondary
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Cantidad de Proyectos',
                color: adaptiveColors.textPrimary
              },
              grid: {
                color: adaptiveColors.gridColor
              },
              ticks: {
                color: adaptiveColors.textSecondary
              }
            }
          },
          elements: {
            point: {
              hoverRadius: 8,
              hoverBorderWidth: 3
            },
            line: {
              tension: 0.2
            }
          }
        }
      });
      console.log('✅ Timeline chart creado');
    }
  } catch (e) {
    console.error('❌ Error creando timeline chart:', e);
  }
}


 // Observer para cambios en el DOM (clase dark)
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
        const newClasses = document.documentElement.classList.toString();
        console.log('🎭 Cambio de clase detectado:', newClasses);
        console.log('🎭 Nuevo modo:', isDarkMode() ? 'DARK' : 'LIGHT');
        
        setTimeout(() => {
          updateChartsTheme();
        }, 150); // Dar tiempo para que CSS se aplique
      }
    });
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class', 'data-theme']
  });

  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ['class', 'data-theme']
  });

 // Listener específico para tu botón de toggle
  document.addEventListener('click', function(e) {
    if (e.target.closest('#themeToggle')) {
      console.log('🔄 Toggle theme button clicked');
      setTimeout(() => {
        console.log('🔄 Actualizando charts después de toggle...');
        const newMode = isDarkMode() ? 'DARK' : 'LIGHT';
        console.log('🔄 Nuevo modo detectado:', newMode);
        updateChartsTheme();
      }, 200);
    }
  });

  // También detectar cambios en localStorage (usado por tu script de toggle)
  window.addEventListener('storage', function(e) {
    if (e.key === 'managerTheme') {
      console.log('🔄 Theme changed in localStorage:', e.newValue);
      setTimeout(() => {
        updateChartsTheme();
      }, 200);
    }
  });
  
  // Listener para detectar cuando se modifica localStorage directamente
  const originalSetItem = localStorage.setItem;
  localStorage.setItem = function(key, value) {
    if (key === 'managerTheme') {
      console.log('🔄 managerTheme localStorage changed to:', value);
      setTimeout(() => {
        updateChartsTheme();
      }, 250);
    }
    originalSetItem.apply(this, arguments);
  };
  console.log('🎉 Charts Manager inicializado con tema adaptativo automático');
});