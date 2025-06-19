// === CONTROLLER KANBAN FILTERS & UI LOGIC ===

// Variables globales
window.filtersVisible = false;
window.dsoGlobal = window.dsoGlobal || 0;
window.userAccessLevel = window.userAccessLevel || 'none';
window.managerName = window.managerName || '';
window.currentUserRole = window.currentUserRole || '';
window.isRestrictedUser = window.isRestrictedUser || false;

// === INICIALIZACIÓN PRINCIPAL ===
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando Controller Kanban Filters...');
    
    // Obtener datos de filtros desde el DOM
    const filtrosData = getFilterDataFromDOM();
    const hasActiveFilters = checkActiveFilters(filtrosData);
    
    console.log('🔍 Datos de filtros:', filtrosData);
    console.log('🔍 Filtros activos:', hasActiveFilters);
    
    // Inicializar componentes
    initializeMetrics();
    initializeFilterToggle(hasActiveFilters);
    initializeBannerButtons();
    initializeViewToggle();
    initializeSearch();
    
    console.log('✅ Controller Kanban Filters inicializado correctamente');
});

// === FUNCIONES DE FILTROS ===
function getFilterDataFromDOM() {
    // Obtener datos de filtros desde atributos del DOM
    const body = document.body;
    return {
        mes: body.getAttribute('data-filter-mes') || '',
        jefe_proyecto: body.getAttribute('data-filter-jefe') || '',
        cliente: body.getAttribute('data-filter-cliente') || '',
        estado: body.getAttribute('data-filter-estado') || 'pendientes'
    };
}

function checkActiveFilters(filtros) {
    return (filtros.mes && filtros.mes !== '' && filtros.mes !== 'todos') ||
           (filtros.jefe_proyecto && filtros.jefe_proyecto !== '' && filtros.jefe_proyecto !== 'todos') ||
           (filtros.cliente && filtros.cliente !== '' && filtros.cliente !== 'todos') ||
           (filtros.estado && filtros.estado !== '' && filtros.estado !== 'todos' && filtros.estado !== 'pendientes');
}

function initializeFilterToggle(hasActiveFilters) {
    const toggleFiltersBtn = document.getElementById('toggle-filters-btn');
    const filtersSection = document.getElementById('filters-section');
    const filterText = document.getElementById('filter-text');
    const filterChevron = document.getElementById('filter-chevron');
    
    if (!toggleFiltersBtn || !filtersSection) {
        console.warn('⚠️ Elementos de filtros no encontrados');
        return;
    }
    
    console.log('🔍 Inicializando toggle de filtros...');
    
    // Función para mostrar/ocultar filtros
    window.toggleFilters = function() {
        window.filtersVisible = !window.filtersVisible;
        
        if (window.filtersVisible) {
            // Mostrar filtros
            filtersSection.classList.remove('hidden');
            filtersSection.style.opacity = '0';
            filtersSection.style.transform = 'translateY(-10px)';
            
            // Animación de entrada
            setTimeout(() => {
                filtersSection.style.transition = 'all 0.3s ease-out';
                filtersSection.style.opacity = '1';
                filtersSection.style.transform = 'translateY(0)';
            }, 10);
            
            // Actualizar botón
            if (filterText) filterText.textContent = 'Ocultar filtros';
            if (filterChevron) filterChevron.style.transform = 'rotate(180deg)';
            toggleFiltersBtn.classList.add('bg-blue-700');
            
        } else {
            // Ocultar filtros
            filtersSection.style.transition = 'all 0.3s ease-in';
            filtersSection.style.opacity = '0';
            filtersSection.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                filtersSection.classList.add('hidden');
            }, 300);
            
            // Actualizar botón
            if (filterText) filterText.textContent = 'Mostrar filtros';
            if (filterChevron) filterChevron.style.transform = 'rotate(0deg)';
            toggleFiltersBtn.classList.remove('bg-blue-700');
        }
    };
    
    // Event listener para el botón de filtros
    toggleFiltersBtn.addEventListener('click', window.toggleFilters);
    
    // Auto-mostrar filtros si hay filtros activos
    if (hasActiveFilters) {
        console.log('🔍 Filtros activos detectados, mostrando automáticamente');
        setTimeout(() => {
            if (!window.filtersVisible) {
                console.log('🔍 Mostrando filtros automáticamente...');
                window.toggleFilters();
            }
        }, 200);
    } else {
        console.log('🔍 No hay filtros activos, filtros permanecen ocultos');
    }
    
    // Manejar envío del formulario
    const filterForm = document.querySelector('form[method="GET"]');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            localStorage.setItem('filtersVisible', window.filtersVisible);
        });
    }
    
    // Limpiar localStorage si no hay filtros activos
    if (!hasActiveFilters) {
        localStorage.removeItem('filtersVisible');
        console.log('🔍 localStorage limpiado - sin filtros activos');
    }
}

// === FUNCIONES DE MÉTRICAS ===
function initializeMetrics() {
    console.log('📊 Inicializando métricas...');
    
    // Las métricas se inicializan desde el HTML ya que necesitan datos del servidor
    // Esta función puede expandirse para cálculos adicionales del lado cliente
}

// === FUNCIONES DE BOTONES DEL BANNER ===
function initializeBannerButtons() {
    initializeRefreshButton();
    initializeExportButton();
}

function initializeRefreshButton() {
    const refreshBtn = document.getElementById('refresh-all-btn');
    if (!refreshBtn) return;
    
    refreshBtn.addEventListener('click', function() {
        // Mostrar indicador de carga
        const originalHTML = this.innerHTML;
        this.innerHTML = `
            <svg class="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span class="hidden sm:inline">Actualizando...</span>
        `;
        this.disabled = true;
        
        // Simular actualización (recargar página)
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    });
}

function initializeExportButton() {
    const exportBtn = document.getElementById('export-btn');
    if (!exportBtn) return;
    
    exportBtn.addEventListener('click', function() {
        // Crear modal de exportación
        const modalHTML = `
            <div id="export-modal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center animate__animated animate__fadeIn">
                <div class="bg-[color:var(--bg-card)] rounded-xl shadow-xl p-6 w-full max-w-md animate__animated animate__zoomIn">
                    <h3 class="text-lg font-bold mb-4">Exportar Datos</h3>
                    <p class="text-[color:var(--text-secondary)] mb-6">Selecciona el formato de exportación:</p>
                    
                    <div class="grid grid-cols-1 gap-3 mb-6">
                        <button class="export-option flex items-center p-4 border border-[color:var(--border-color)] rounded-lg hover:bg-[color:var(--bg-highlight)] transition-colors" data-format="csv">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-3 text-[color:var(--accent-green)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <div class="text-left">
                                <div class="font-medium">Exportar a CSV</div>
                                <div class="text-sm text-[color:var(--text-secondary)]">Archivo de Excel compatible</div>
                            </div>
                        </button>
                        
                        <button class="export-option flex items-center p-4 border border-[color:var(--border-color)] rounded-lg hover:bg-[color:var(--bg-highlight)] transition-colors" data-format="pdf">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mr-3 text-[color:var(--accent-red)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                            </svg>
                            <div class="text-left">
                                <div class="font-medium">Exportar a PDF</div>
                                <div class="text-sm text-[color:var(--text-secondary)]">Reporte ejecutivo</div>
                            </div>
                        </button>
                    </div>
                    
                    <div class="flex justify-end">
                        <button id="cancel-export-modal" class="px-4 py-2 text-[color:var(--text-secondary)] hover:text-[color:var(--text-primary)] transition-colors">
                            Cancelar
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Event listeners para el modal
        const modal = document.getElementById('export-modal');
        const cancelBtn = document.getElementById('cancel-export-modal');
        const exportOptions = document.querySelectorAll('.export-option');
        
        cancelBtn.addEventListener('click', () => modal.remove());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        
        exportOptions.forEach(option => {
            option.addEventListener('click', () => {
                const format = option.dataset.format;
                modal.remove();
                
                // Simular exportación
                showToast(`Exportando datos en formato ${format.toUpperCase()}...`, 'info');
                setTimeout(() => {
                    showToast(`Archivo ${format.toUpperCase()} exportado correctamente`, 'success');
                }, 2000);
            });
        });
    });
}

// === FUNCIONES DE TOGGLE DE VISTA ===
function initializeViewToggle() {
    const toggleKanban = document.getElementById('toggle-kanban');
    const toggleLista = document.getElementById('toggle-lista');
    const viewTitle = document.getElementById('view-title');
    const viewDescription = document.getElementById('view-description');
    
    if (!toggleKanban || !toggleLista) {
        console.warn('⚠️ Botones de toggle de vista no encontrados');
        return;
    }
    
    // Estado inicial
    let currentView = 'kanban';
    
    // Funciones para encontrar secciones del kanban
    function findKanbanSections() {
        const sections = [];
        const sectionIds = [
            'kanban-title-section',        // Título "📋 Tablero Kanban"
            'kanban-column-controls',      // Controles "Mostrar columnas:"
            'kanban-board',                // Tablero principal
            'kanban-search-section'        // Sección de búsqueda (si existe)
        ];
        
        sectionIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                sections.push(element);
                console.log('✅ Sección encontrada:', id);
            } else {
                console.warn('⚠️ Sección no encontrada:', id);
            }
        });
        
        // Buscar sección de búsqueda si no tiene ID
        if (!document.getElementById('kanban-search-section')) {
            const buscador = document.getElementById('buscar-edp');
            if (buscador) {
                let searchContainer = buscador.closest('div[class*="bg-"]');
                if (searchContainer) {
                    searchContainer.id = 'kanban-search-section';
                    sections.push(searchContainer);
                    console.log('✅ Sección de búsqueda encontrada y asignada ID');
                }
            }
        }
        
        console.log('🔍 Total de secciones de Kanban encontradas:', sections.length);
        return sections.filter(el => el !== null);
    }
    
    // Inicializar secciones del kanban y tabla
    let kanbanSections = findKanbanSections();
    const tablaContainer = document.getElementById('tabla-view');
    
    // Si no se encontraron secciones inicialmente, intentar de nuevo después de un breve delay
    if (kanbanSections.length === 0) {
        console.warn('⚠️ No se encontraron secciones de Kanban inicialmente, reintentando...');
        setTimeout(() => {
            kanbanSections = findKanbanSections();
            console.log('🔄 Segundo intento - Secciones encontradas:', kanbanSections.length);
        }, 500);
    }
    
    // Función para cambiar a vista Kanban
    function showKanbanView() {
        currentView = 'kanban';
        
        // Actualizar secciones de kanban si es necesario
        if (kanbanSections.length === 0) {
            kanbanSections = findKanbanSections();
        }
        
        // Actualizar botones
        toggleKanban.classList.remove('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
        toggleKanban.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
        toggleLista.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
        toggleLista.classList.add('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
        
        // Actualizar título
        if (viewTitle) viewTitle.textContent = 'Pagora';
        if (viewDescription) viewDescription.textContent = 'Centro de Comando - Gestión Visual de EDPs';
        
        // Mostrar secciones del kanban
        kanbanSections.forEach((section) => {
            if (section) {
                section.style.display = '';
                section.classList.remove('hidden');
                console.log('📋 Mostrando sección Kanban:', section.id || section.tagName);
            }
        });
        
        // Ocultar tabla
        if (tablaContainer) {
            tablaContainer.style.display = 'none';
            tablaContainer.classList.add('hidden');
        }
        
        console.log('✅ Vista Kanban activada - Secciones mostradas:', kanbanSections.length);
    }
    
    // Función para cambiar a vista Lista
    function showListaView() {
        currentView = 'lista';
        
        // Actualizar secciones de kanban si es necesario
        if (kanbanSections.length === 0) {
            kanbanSections = findKanbanSections();
        }
        
        // Actualizar botones
        toggleLista.classList.remove('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
        toggleLista.classList.add('bg-[color:var(--accent-blue)]', 'text-white');
        toggleKanban.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
        toggleKanban.classList.add('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
        
        // Actualizar título
        if (viewTitle) viewTitle.textContent = 'Vista Lista';
        if (viewDescription) viewDescription.textContent = 'Tabla detallada con filtros avanzados y funciones de exportación.';
        
        // Ocultar secciones del kanban
        kanbanSections.forEach((section) => {
            if (section) {
                section.style.display = 'none';
                section.classList.add('hidden');
                console.log('📋 Ocultando sección Kanban:', section.id || section.tagName);
            }
        });
        
        // Mostrar tabla
        if (tablaContainer) {
            tablaContainer.style.display = '';
            tablaContainer.classList.remove('hidden');
            
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 100);
        }
        
        console.log('✅ Vista Lista activada - Secciones ocultadas:', kanbanSections.length);
    }
    
    // Event listeners
    toggleKanban.addEventListener('click', function(e) {
        e.preventDefault();
        if (currentView !== 'kanban') {
            showKanbanView();
            localStorage.setItem('kanban_view_preference', 'kanban');
        }
    });
    
    toggleLista.addEventListener('click', function(e) {
        e.preventDefault();
        if (currentView !== 'lista') {
            showListaView();
            localStorage.setItem('kanban_view_preference', 'lista');
        }
    });
    
    // Atajos de teclado
    document.addEventListener('keydown', function(e) {
        if (e.altKey && e.key === 'k') {
            e.preventDefault();
            showKanbanView();
        }
        if (e.altKey && e.key === 'l') {
            e.preventDefault();
            showListaView();
        }
    });
    
    // Restaurar vista guardada
    const savedView = localStorage.getItem('kanban_view_preference');
    if (savedView === 'lista') {
        showListaView();
    } else {
        showKanbanView();
    }
}

// === FUNCIONES DE BÚSQUEDA ===
function initializeSearch() {
    const searchInput = document.getElementById('buscar-edp');
    const clearBtn = document.getElementById('limpiar-busqueda');
    const resultsDiv = document.getElementById('resultados-busqueda');
    
    if (!searchInput) return;
    
    // Lógica de búsqueda - se puede expandir según necesidades
    console.log('🔍 Búsqueda inicializada');
}

// === FUNCIONES UTILITARIAS ===
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg shadow-lg text-white z-50 animate__animated animate__fadeInUp`;
    
    if (type === 'success') {
        toast.classList.add('bg-green-600');
        message = `✅ ${message}`;
    } else if (type === 'error') {
        toast.classList.add('bg-red-600');
        message = `❌ ${message}`;
    } else if (type === 'warning') {
        toast.classList.add('bg-amber-500');
        message = `⚠️ ${message}`;
    } else {
        toast.classList.add('bg-blue-600');
        message = `ℹ️ ${message}`;
    }
    
    toast.innerHTML = `
        <div class="flex items-center">
            <span class="flex-grow">${message}</span>
            <button class="ml-4 hover:text-gray-300 focus:outline-none" onclick="this.parentElement.parentElement.remove()">
                &times;
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.replace('animate__fadeInUp', 'animate__fadeOutDown');
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 500);
    }, 5000);
}

// === ACTUALIZACIÓN DE TIMESTAMP ===
setInterval(() => {
    const lastUpdatedBanner = document.getElementById('last-updated-banner');
    const lastUpdated = document.getElementById('last-updated-date');
    const currentTime = new Date().toLocaleTimeString();
    
    if (lastUpdatedBanner) {
        lastUpdatedBanner.textContent = 'Actualizado: ' + currentTime;
    }
    if (lastUpdated) {
        lastUpdated.textContent = 'Actualizado: ' + currentTime;
    }
}, 60000);

console.log('📜 Controller Kanban Filters JS cargado correctamente'); 