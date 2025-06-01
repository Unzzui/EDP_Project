document.addEventListener('DOMContentLoaded', function() {
  console.log('🎯 Charts Manager iniciado');
  
  // Set Chart.js defaults
  Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
  Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary');
  
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
  
  // ===== OBTENER DATOS DE CHARTS DE FORMA SIMPLE =====
  let chartsData = {};
  
  // Método 1: Intentar obtener desde el elemento script
  const chartsDataElement = document.getElementById('charts-data');
  if (chartsDataElement) {
    try {
      const jsonContent = chartsDataElement.textContent.trim();
      console.log('📊 JSON content length:', jsonContent.length);
      console.log('📊 JSON preview:', jsonContent.substring(0, 200));
      
      if (jsonContent && jsonContent !== '{}') {
        chartsData = JSON.parse(jsonContent);
        console.log('✅ Charts data parseado exitosamente');
        console.log('📊 Charts data keys:', Object.keys(chartsData));
      } else {
        console.warn('⚠️ JSON content está vacío o es objeto vacío');
        
      }
    } catch (e) {
      console.error('❌ Error parseando charts data:', e);
      console.error('❌ JSON problemático:', chartsDataElement.textContent.substring(0, 500));
      
    }
  } else {
    console.error('❌ Elemento charts-data no encontrado');
    
  }
  

  
  // ===== CREAR GRÁFICOS UNO POR UNO =====
  
  // 1. FINANCIAL TREND CHART
  const financialTrendElement = document.getElementById('financialTrendChart');
  if (financialTrendElement) {
    try {
      const data = chartsData.tendencia_financiera;
      console.log('📈 Creando financial trend chart:', data);
      
      new Chart(financialTrendElement, {
        type: 'line',
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top'
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: function(value) {
                  return '$' + value + 'M';
                }
              }
            }
          }
        }
      });
      console.log('✅ Financial trend chart creado');
    } catch (e) {
      console.error('❌ Error creando financial trend chart:', e);
    }
  }
  
  // 2. PROJECT STATUS CHART
  const projectStatusElement = document.getElementById('projectStatusChart');
  if (projectStatusElement) {
    try {
      const data = chartsData.estado_proyectos;
      console.log('📊 Creando project status chart:', data);
      
      new Chart(projectStatusElement, {
        type: 'doughnut',
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '65%',
          plugins: {
            legend: {
              display: false
            }
          }
        }
      });
      console.log('✅ Project status chart creado');
    } catch (e) {
      console.error('❌ Error creando project status chart:', e);
    }
  }
  
  // 3. CASH FORECAST CHART
  const cashForecastElement = document.getElementById('cashInForecastChart');
  if (cashForecastElement) {
    try {
      const data = chartsData.cash_in_forecast;
      console.log('💰 Creando cash forecast chart:', data);
      
      new Chart(cashForecastElement, {
        type: 'bar',
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top'
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              stacked: true,
              ticks: {
                callback: function(value) {
                  return '$' + value + 'M';
                }
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
      console.log('📈 Creando department profit chart:', data);
      
      new Chart(departmentProfitElement, {
        type: 'bar',
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y',
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            x: {
              beginAtZero: true,
              ticks: {
                callback: function(value) {
                  return value + '%';
                }
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
      console.log('🥧 Creando budget distribution chart:', data);
      
      new Chart(budgetDistributionElement, {
        type: 'pie',
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right'
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
      console.log('📅 Creando aging buckets chart:', data);
      
      new Chart(agingBucketsElement, {
        type: 'bar',
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
      console.log('✅ Aging buckets chart creado');
    } catch (e) {
      console.error('❌ Error creando aging buckets chart:', e);
    }
  }
  
  // 7. PARETO CLIENT CHART
  const paretoClientElement = document.getElementById('paretoClientChart');
  if (paretoClientElement) {
    try {
      const data = chartsData.concentracion_clientes;
      console.log('📈 Creando pareto client chart:', data);
      
      new Chart(paretoClientElement, {
        type: 'bar',
        data: data,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top'
            }
          },
          scales: {
            y: {
              position: 'left',
              beginAtZero: true,
              ticks: {
                callback: function(value) {
                  return '$' + value + 'M';
                }
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
              grid: {
                drawOnChartArea: false
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
  
  console.log('🎉 Todos los charts procesados');
});