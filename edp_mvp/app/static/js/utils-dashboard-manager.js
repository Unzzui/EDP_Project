
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Iniciando Dashboard Manager...');
    
    // ================================
    // 1. INICIALIZACIÓN DE ELEMENTOS
    // ================================
    
    // Elementos de filtros
    const toggleAdvanced = document.getElementById('toggle-advanced');
    const advancedFilters = document.getElementById('advanced-filters');
    const advancedText = document.getElementById('advanced-text');
    const quickDateBtns = document.querySelectorAll('.quick-date-btn');
    const fechaInicio = document.getElementById('fecha_inicio');
    const fechaFin = document.getElementById('fecha_fin');
    
    // Elementos de proyectos
    const projectActionsBtn = document.getElementById('project-actions-btn');
    const projectActionsMenu = document.getElementById('project-actions-menu');
    const viewButtons = document.querySelectorAll('[data-view]');
    
    // Elementos de Pareto
    const paretoIngresos = document.getElementById('pareto-toggle-ingresos');
    const paretoPendiente = document.getElementById('pareto-toggle-pendiente');
    
    // Elementos de charts
    const chartViewButtons = document.querySelectorAll('[data-chart-view]');
    
    // Elementos de proyectos críticos
    const showCriticalProjectsBtn = document.getElementById('show-critical-projects-btn');
    
    console.log('✅ Elementos inicializados');
    
    // ================================
    // 2. GESTIÓN DE FILTROS
    // ================================
    
    // Toggle filtros avanzados
    if (toggleAdvanced && advancedFilters && advancedText) {
        toggleAdvanced.addEventListener('click', function() {
            advancedFilters.classList.toggle('hidden');
            const isHidden = advancedFilters.classList.contains('hidden');
            advancedText.textContent = isHidden ? 'Filtros avanzados' : 'Ocultar filtros avanzados';
            
            // Animación suave
            if (!isHidden) {
                advancedFilters.style.opacity = '0';
                setTimeout(() => {
                    advancedFilters.style.transition = 'opacity 0.3s ease';
                    advancedFilters.style.opacity = '1';
                }, 10);
            }
            
            console.log('🔧 Filtros avanzados:', isHidden ? 'ocultados' : 'mostrados');
        });
    }
    
    // Botones de fecha rápida
    if (quickDateBtns.length > 0 && fechaInicio && fechaFin) {
        quickDateBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                // Prevenir envío automático del formulario
                e.preventDefault();
                
                const days = parseInt(this.value);
                const today = new Date();
                const startDate = new Date(today.getTime() - (days * 24 * 60 * 60 * 1000));
                
                // Establecer fechas
                fechaFin.value = today.toISOString().split('T')[0];
                fechaInicio.value = startDate.toISOString().split('T')[0];
                
                // Actualizar estado visual de botones
                quickDateBtns.forEach(b => {
                    b.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
                    b.classList.add('bg-[color:var(--bg-subtle)]');
                });
                this.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
                this.classList.remove('bg-[color:var(--bg-subtle)]');
                
                console.log(`📅 Filtro de fecha aplicado: ${days} días`);
                
                // Enviar formulario después de un breve delay para mostrar el cambio visual
                setTimeout(() => {
                    this.closest('form').submit();
                }, 200);
            });
        });
    }
    
    // ================================
    // 3. GESTIÓN DE PROYECTOS
    // ================================
    
    // Menú de acciones de proyecto
    if (projectActionsBtn && projectActionsMenu) {
        projectActionsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            projectActionsMenu.classList.toggle('hidden');
            
            // Rotar flecha del botón
            const arrow = this.querySelector('svg');
            if (arrow) {
                if (projectActionsMenu.classList.contains('hidden')) {
                    arrow.style.transform = 'rotate(0deg)';
                } else {
                    arrow.style.transform = 'rotate(180deg)';
                }
            }
            
            console.log('🎯 Menú de acciones de proyecto toggled');
        });
        
        // Cerrar menú al hacer clic fuera
        document.addEventListener('click', function(e) {
            if (!projectActionsBtn.contains(e.target) && !projectActionsMenu.contains(e.target)) {
                projectActionsMenu.classList.add('hidden');
                const arrow = projectActionsBtn.querySelector('svg');
                if (arrow) arrow.style.transform = 'rotate(0deg)';
            }
        });
    }
    
    // Toggle entre vistas de proyectos (Chart vs Bubble)
    if (viewButtons.length > 0) {
        viewButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Actualizar estado activo de botones
                viewButtons.forEach(btn => {
                    btn.classList.remove('active-view-btn', 'bg-[color:var(--accent-blue)]', 'text-white');
                    btn.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]');
                });
                
                this.classList.add('active-view-btn', 'bg-[color:var(--accent-blue)]', 'text-white');
                this.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]');
                
                // Mostrar vista correspondiente con animación
                const viewToShow = this.getAttribute('data-view');
                const chartView = document.getElementById('project-chart-view');
                const bubbleView = document.getElementById('project-bubble-view');
                
                if (chartView && bubbleView) {
                    if (viewToShow === 'chart') {
                        bubbleView.classList.add('hidden');
                        setTimeout(() => {
                            chartView.classList.remove('hidden');
                        }, 100);
                    } else {
                        chartView.classList.add('hidden');
                        setTimeout(() => {
                            bubbleView.classList.remove('hidden');
                        }, 100);
                    }
                }
                
                console.log(`👁️ Vista de proyectos cambiada a: ${viewToShow}`);
            });
        });
    }
    
    // ================================
    // 4. GESTIÓN DE GRÁFICOS PARETO
    // ================================
    
    if (paretoIngresos && paretoPendiente) {
        // Toggle Pareto - Ingresos
        paretoIngresos.addEventListener('click', function() {
            // Activar botón de ingresos
            paretoIngresos.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
            paretoIngresos.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border');
            
            // Desactivar botón de pendiente
            paretoPendiente.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
            paretoPendiente.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border', 'border-[color:var(--border-color)]');
            
            console.log('📊 Pareto cambiado a: Ingresos');
            
            // Aquí se actualizaría el gráfico Pareto
            updateParetoChart('ingresos');
        });
        
        // Toggle Pareto - Pendiente
        paretoPendiente.addEventListener('click', function() {
            // Activar botón de pendiente
            paretoPendiente.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
            paretoPendiente.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border');
            
            // Desactivar botón de ingresos
            paretoIngresos.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
            paretoIngresos.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]', 'border', 'border-[color:var(--border-color)]');
            
            console.log('📊 Pareto cambiado a: Pendiente');
            
            // Aquí se actualizaría el gráfico Pareto
            updateParetoChart('pendiente');
        });
    }
    
    // ================================
    // 5. GESTIÓN DE VISTAS DE CHARTS
    // ================================
    
    if (chartViewButtons.length > 0) {
        chartViewButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Actualizar estado activo
                chartViewButtons.forEach(btn => {
                    btn.classList.remove('active-chart-btn', 'bg-[color:var(--accent-blue)]', 'text-white');
                    btn.classList.add('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]');
                });
                
                this.classList.add('active-chart-btn', 'bg-[color:var(--accent-blue)]', 'text-white');
                this.classList.remove('bg-[color:var(--bg-subtle)]', 'text-[color:var(--text-secondary)]');
                
                const chartView = this.getAttribute('data-chart-view');
                console.log(`📈 Vista de chart cambiada a: ${chartView}`);
                
                // Actualizar gráfico financiero
                updateFinancialChart(chartView);
            });
        });
    }
    
    // ================================
    // 6. MODAL DE PROYECTOS CRÍTICOS
    // ================================
    
    if (showCriticalProjectsBtn) {
        showCriticalProjectsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🚨 Abriendo modal de proyectos críticos');
            
            // Buscar el modal
            const modal = document.getElementById('modal-proyectos-criticos');
            if (modal) {
                modal.classList.remove('hidden');
                modal.classList.add('flex');
                
                // Animación de entrada
                setTimeout(() => {
                    const modalContent = modal.querySelector('.modal-content');
                    if (modalContent) {
                        modalContent.style.transform = 'scale(1)';
                        modalContent.style.opacity = '1';
                    }
                }, 10);
                
                // Cargar datos de proyectos críticos
                loadCriticalProjectsData();
            } else {
                console.warn('⚠️ Modal de proyectos críticos no encontrado');
            }
        });
    }
    
    // ================================
    // 7. UTILIDADES Y FUNCIONES HELPER
    // ================================
    
    // Función para resetear filtros
    window.resetFilters = function() {
        console.log('🔄 Reseteando filtros');
        
        const form = document.querySelector('form[method="GET"]');
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
            
            // Restablecer inputs numéricos
            form.querySelectorAll('input[type="number"]').forEach(input => {
                input.value = '';
            });
            
            // Remover estado activo de botones de fecha rápida
            quickDateBtns.forEach(btn => {
                btn.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
                btn.classList.add('bg-[color:var(--bg-subtle)]');
            });
            
            // Enviar formulario
            setTimeout(() => {
                form.submit();
            }, 100);
        }
    };
    
    // Función para actualizar gráfico Pareto
    function updateParetoChart(tipo) {
        console.log(`📊 Actualizando gráfico Pareto: ${tipo}`);
        
        // Aquí iría la lógica para actualizar el gráfico
        // Por ejemplo, usando Chart.js o la librería que estés usando
        
        const chart = Chart.getChart('paretoClientChart');
        if (chart) {
            // Simular cambio de datos
            if (tipo === 'ingresos') {
                // Actualizar con datos de ingresos
                chart.data.datasets[0].label = 'Ingresos por Cliente';
                chart.data.datasets[0].backgroundColor = 'rgba(59, 130, 246, 0.8)';
            } else {
                // Actualizar con datos pendientes
                chart.data.datasets[0].label = 'Monto Pendiente por Cliente';
                chart.data.datasets[0].backgroundColor = 'rgba(239, 68, 68, 0.8)';
            }
            chart.update('active');
        }
    }
    
    // Función para actualizar gráfico financiero
    function updateFinancialChart(vista) {
        console.log(`📈 Actualizando gráfico financiero: ${vista}`);
        
        const chart = Chart.getChart('financialTrendChart');
        if (chart) {
            // Simular cambio de datos según la vista
            switch(vista) {
                case 'ingresos':
                    chart.data.datasets[0].label = 'Ingresos';
                    chart.data.datasets[0].borderColor = 'rgb(34, 197, 94)';
                    break;
                case 'margen':
                    chart.data.datasets[0].label = 'Margen';
                    chart.data.datasets[0].borderColor = 'rgb(168, 85, 247)';
                    break;
                case 'cashflow':
                    chart.data.datasets[0].label = 'Cash Flow';
                    chart.data.datasets[0].borderColor = 'rgb(59, 130, 246)';
                    break;
            }
            chart.update('active');
        }
    }
    
    // Función para cargar datos de proyectos críticos
    function loadCriticalProjectsData() {
        console.log('📋 Cargando datos de proyectos críticos');
        
        // Aquí iría una llamada AJAX para cargar los datos
        // Por ahora simulamos la carga
        
        const loadingElement = document.getElementById('critical-projects-loading');
        const contentElement = document.getElementById('critical-projects-content');
        
        if (loadingElement && contentElement) {
            loadingElement.classList.remove('hidden');
            contentElement.classList.add('hidden');
            
            // Simular carga
            setTimeout(() => {
                loadingElement.classList.add('hidden');
                contentElement.classList.remove('hidden');
                console.log('✅ Datos de proyectos críticos cargados');
            }, 1000);
        }
    }
    
    // ================================
    // 8. INICIALIZACIÓN DE TOOLTIPS
    // ================================
    
    // Agregar tooltips a elementos con data-tooltip
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this, this.getAttribute('data-tooltip'));
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
    
    function showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.id = 'dashboard-tooltip';
        tooltip.className = 'absolute z-50 px-2 py-1 text-xs bg-gray-900 text-white rounded shadow-lg pointer-events-none';
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
    }
    
    function hideTooltip() {
        const tooltip = document.getElementById('dashboard-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }
    
    // ================================
    // 9. MANEJO DE ERRORES Y CLEANUP
    // ================================
    
    // Manejo global de errores para el dashboard
    window.addEventListener('error', function(e) {
        console.error('❌ Error en dashboard:', e.error);
        
        // Mostrar notificación de error al usuario
        showNotification('Ha ocurrido un error. Por favor, recarga la página.', 'error');
    });
    
    // Función para mostrar notificaciones
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg transition-opacity duration-300 ${
            type === 'error' ? 'bg-red-500 text-white' : 
            type === 'success' ? 'bg-green-500 text-white' : 
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remover después de 5 segundos
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
    
    // Cleanup al cerrar la página
    window.addEventListener('beforeunload', function() {
        console.log('🧹 Limpiando recursos del dashboard');
        
        // Limpiar intervalos si los hay
        // Limpiar event listeners si es necesario
        // Etc.
    });
    
    // ================================
    // 10. FUNCIONALIDADES ADICIONALES
    // ================================
    
    // Auto-refresh de datos cada 5 minutos (opcional)
    let autoRefreshInterval;
    
    function startAutoRefresh() {
        autoRefreshInterval = setInterval(() => {
            console.log('🔄 Auto-refresh de datos');
            
            // Aquí se podría hacer una llamada AJAX para actualizar solo los datos
            // sin recargar toda la página
            
        }, 5 * 60 * 1000); // 5 minutos
    }
    
    function stopAutoRefresh() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    }
    
    // Iniciar auto-refresh (comentado por defecto)
    // startAutoRefresh();
    
    // Detener auto-refresh cuando la página no está visible
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopAutoRefresh();
        } else {
            // startAutoRefresh();
        }
    });
    
    // ================================
    // 11. FINALIZACIÓN
    // ================================
    
    console.log('✅ Dashboard Manager inicializado completamente');
    
    
    // Exponer funciones útiles al objeto window para debugging
    window.dashboardUtils = {
        resetFilters,
        updateParetoChart,
        updateFinancialChart,
        loadCriticalProjectsData,
        showNotification,
        startAutoRefresh,
        stopAutoRefresh
    };
});