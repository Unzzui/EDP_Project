/**
 * Dashboard Toggle Filters - Funcionalidad de mostrar/ocultar filtros
 * Versión con animaciones suaves y elegantes
 */

(function() {
    'use strict';
    
    // Función principal para inicializar el toggle
    function initializeFilterToggle() {
        console.log('🎨 Inicializando toggle de filtros con animaciones...');
        
        // Obtener elementos del DOM
        const toggleBtn = document.getElementById('toggle-filters-btn');
        const filtersSection = document.getElementById('filters-section');
        const filterText = document.getElementById('filter-text');
        const filterTextMobile = document.getElementById('filter-text-mobile');
        const filterChevron = document.getElementById('filter-chevron');
        const advancedToggle = document.getElementById('toggle-advanced');
        const advancedFilters = document.getElementById('advanced-filters');
        const advancedText = document.getElementById('advanced-text');
        
        // Verificar elementos críticos
        if (!toggleBtn) {
            console.error('❌ Botón toggle-filters-btn no encontrado');
            return;
        }
        
        if (!filtersSection) {
            console.error('❌ Sección filters-section no encontrada');
            return;
        }
        
        // Estado inicial
        let filtersVisible = false;
        let isAnimating = false;
        
        // Función para obtener la altura del contenido
        function getContentHeight(element) {
            const clone = element.cloneNode(true);
            clone.style.position = 'absolute';
            clone.style.visibility = 'hidden';
            clone.style.height = 'auto';
            clone.style.maxHeight = 'none';
            clone.classList.remove('hidden');
            document.body.appendChild(clone);
            const height = clone.offsetHeight;
            document.body.removeChild(clone);
            return height;
        }
        
        // Función para alternar filtros principales con animaciones suaves
        function toggleMainFilters() {
            if (isAnimating) return; // Prevenir clicks durante animación
            
            isAnimating = true;
            filtersVisible = !filtersVisible;
            
            // Agregar clase de animación al botón
            toggleBtn.classList.add('filter-btn-animating');
            
            if (filtersVisible) {
                // Mostrar filtros con animación slide-down
                console.log('🎬 Mostrando filtros con animación...');
                
                // Preparar para la animación
                filtersSection.classList.remove('filter-hidden');
                filtersSection.classList.add('filter-showing');
                filtersSection.style.display = 'block';
                
                // Obtener altura del contenido
                const contentHeight = getContentHeight(filtersSection);
                
                // Configurar estado inicial de la animación
                filtersSection.style.maxHeight = '0px';
                filtersSection.style.opacity = '0';
                filtersSection.style.transform = 'translateY(-10px)';
                
                // Force reflow
                filtersSection.offsetHeight;
                
                // Animar hacia el estado final
                filtersSection.style.transition = 'all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1)';
                filtersSection.style.maxHeight = contentHeight + 'px';
                filtersSection.style.opacity = '1';
                filtersSection.style.transform = 'translateY(0)';
                
                // Actualizar textos del botón con fade
                setTimeout(() => {
                    if (filterText) {
                        filterText.style.opacity = '0';
                        setTimeout(() => {
                            filterText.textContent = 'Ocultar filtros';
                            filterText.style.opacity = '1';
                        }, 150);
                    }
                    if (filterTextMobile) {
                        filterTextMobile.style.opacity = '0';
                        setTimeout(() => {
                            filterTextMobile.textContent = 'Ocultar';
                            filterTextMobile.style.opacity = '1';
                        }, 150);
                    }
                }, 100);
                
                // Rotar chevron
                if (filterChevron) {
                    filterChevron.style.transform = 'rotate(180deg)';
                }
                
                // Cleanup después de la animación
                setTimeout(() => {
                    filtersSection.style.maxHeight = 'none';
                    filtersSection.classList.remove('filter-showing');
                    filtersSection.classList.add('filter-visible');
                    isAnimating = false;
                    toggleBtn.classList.remove('filter-btn-animating');
                }, 400);
                
            } else {
                // Ocultar filtros con animación slide-up
                console.log('🎬 Ocultando filtros con animación...');
                
                filtersSection.classList.remove('filter-visible');
                filtersSection.classList.add('filter-hiding');
                
                // Configurar altura actual
                const currentHeight = filtersSection.offsetHeight;
                filtersSection.style.maxHeight = currentHeight + 'px';
                
                // Force reflow
                filtersSection.offsetHeight;
                
                // Animar hacia oculto
                filtersSection.style.transition = 'all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1)';
                filtersSection.style.maxHeight = '0px';
                filtersSection.style.opacity = '0';
                filtersSection.style.transform = 'translateY(-10px)';
                
                // Actualizar textos del botón con fade
                setTimeout(() => {
                    if (filterText) {
                        filterText.style.opacity = '0';
                        setTimeout(() => {
                            filterText.textContent = 'Mostrar filtros';
                            filterText.style.opacity = '1';
                        }, 100);
                    }
                    if (filterTextMobile) {
                        filterTextMobile.style.opacity = '0';
                        setTimeout(() => {
                            filterTextMobile.textContent = 'Filtros';
                            filterTextMobile.style.opacity = '1';
                        }, 100);
                    }
                }, 50);
                
                // Rotar chevron de vuelta
                if (filterChevron) {
                    filterChevron.style.transform = 'rotate(0deg)';
                }
                
                // Cleanup después de la animación
                setTimeout(() => {
                    filtersSection.style.display = 'none';
                    filtersSection.classList.remove('filter-hiding');
                    filtersSection.classList.add('filter-hidden');
                    filtersSection.style.maxHeight = '';
                    filtersSection.style.opacity = '';
                    filtersSection.style.transform = '';
                    filtersSection.style.transition = '';
                    isAnimating = false;
                    toggleBtn.classList.remove('filter-btn-animating');
                }, 300);
            }
        }
        
        // Función para alternar filtros avanzados con animación
        function toggleAdvancedFilters() {
            if (!advancedFilters) return;
            
            const isHidden = advancedFilters.classList.contains('hidden');
            
            if (isHidden) {
                // Mostrar filtros avanzados
                advancedFilters.classList.remove('hidden');
                advancedFilters.style.opacity = '0';
                advancedFilters.style.transform = 'translateY(-5px)';
                advancedFilters.style.transition = 'all 0.3s ease-out';
                
                // Force reflow
                advancedFilters.offsetHeight;
                
                advancedFilters.style.opacity = '1';
                advancedFilters.style.transform = 'translateY(0)';
                
                if (advancedText) {
                    advancedText.style.opacity = '0';
                    setTimeout(() => {
                        advancedText.textContent = 'Ocultar filtros avanzados';
                        advancedText.style.transition = 'opacity 0.2s ease';
                        advancedText.style.opacity = '1';
                    }, 150);
                }
            } else {
                // Ocultar filtros avanzados
                advancedFilters.style.transition = 'all 0.2s ease-in';
                advancedFilters.style.opacity = '0';
                advancedFilters.style.transform = 'translateY(-5px)';
                
                if (advancedText) {
                    advancedText.style.opacity = '0';
                    setTimeout(() => {
                        advancedText.textContent = 'Filtros avanzados';
                        advancedText.style.opacity = '1';
                    }, 100);
                }
                
                setTimeout(() => {
                    advancedFilters.classList.add('hidden');
                    advancedFilters.style.opacity = '';
                    advancedFilters.style.transform = '';
                    advancedFilters.style.transition = '';
                }, 200);
            }
            
            console.log('🎨 Filtros avanzados', isHidden ? 'mostrados' : 'ocultos', 'con animación');
        }
        
        // Agregar event listeners con efectos hover
        toggleBtn.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            // Efecto de click visual
            toggleBtn.style.transform = 'scale(0.95)';
            setTimeout(() => {
                toggleBtn.style.transform = 'scale(1)';
            }, 100);
            
            toggleMainFilters();
        });
        
        // Efectos hover para el botón principal
        toggleBtn.addEventListener('mouseenter', function() {
            if (!isAnimating) {
                this.style.transform = 'scale(1.02)';
                this.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
            }
        });
        
        toggleBtn.addEventListener('mouseleave', function() {
            if (!isAnimating) {
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '';
            }
        });
        
        // Event listener para filtros avanzados
        if (advancedToggle) {
            advancedToggle.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                
                // Efecto de click visual
                this.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 80);
                
                toggleAdvancedFilters();
            });
            
            // Hover effect para filtros avanzados
            advancedToggle.addEventListener('mouseenter', function() {
                this.style.color = 'rgb(37, 99, 235)';
            });
            
            advancedToggle.addEventListener('mouseleave', function() {
                this.style.color = '';
            });
        }
        
        // Auto-mostrar filtros si hay filtros activos (detectar desde el server)
        window.autoShowFilters = function() {
            if (!filtersVisible) {
                setTimeout(toggleMainFilters, 500);
            }
        };
        
        // Exponer funciones globalmente para uso desde el template
        window.dashboardToggle = {
            showFilters: function() {
                if (!filtersVisible && !isAnimating) toggleMainFilters();
            },
            hideFilters: function() {
                if (filtersVisible && !isAnimating) toggleMainFilters();
            },
            toggleFilters: function() {
                if (!isAnimating) toggleMainFilters();
            },
            isFiltersVisible: function() {
                return filtersVisible;
            },
            isAnimating: function() {
                return isAnimating;
            }
        };
        
        // Configurar estado inicial
        filtersSection.classList.add('filter-hidden');
        
        // Configurar transiciones CSS para los textos
        if (filterText) filterText.style.transition = 'opacity 0.3s ease';
        if (filterTextMobile) filterTextMobile.style.transition = 'opacity 0.3s ease';
        if (advancedText) advancedText.style.transition = 'opacity 0.2s ease';
        
        // Configurar transición del botón principal
        toggleBtn.style.transition = 'transform 0.2s ease, box-shadow 0.2s ease';
        
        // Configurar transición del chevron
        if (filterChevron) {
            filterChevron.style.transition = 'transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1)';
        }
        
        console.log('✨ Toggle de filtros con animaciones inicializado exitosamente');
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeFilterToggle);
    } else {
        // DOM ya está listo
        initializeFilterToggle();
    }
    
})(); 