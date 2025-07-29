/**
 * Fullscreen Kanban & Table View Controller
 * Maneja la funcionalidad de vista completa para el Kanban y la vista de tabla
 */

// Variables globales para el control de vista completa
let isFullscreen = false;
let originalParent = null;
let originalNextSibling = null;
let currentView = 'kanban'; // 'kanban' o 'tabla'

// Variables para el manejo de modales en fullscreen
let shouldReturnToFullscreen = false;
let pendingModalData = null;

// Detectar vista actual
function getCurrentView() {
  const kanbanBoard = document.getElementById('kanban-board');
  const tablaView = document.getElementById('tabla-view');
  
  if (kanbanBoard && !kanbanBoard.closest('.hidden')) {
    return 'kanban';
  } else if (tablaView && !tablaView.classList.contains('hidden')) {
    return 'tabla';
  }
  return 'kanban'; // default
}

function createFullscreenHeader() {
  const view = getCurrentView();
  const title = view === 'kanban' ? 'Vista Completa - Tablero Kanban' : 'Vista Completa - Tabla de EDPs';
  
  const header = document.createElement('div');
  header.className = 'kanban-fullscreen-header';
  header.innerHTML = `
    <div class="kanban-fullscreen-title">
      <div class="flex items-center gap-3">
        <div class="w-3 h-3 bg-[color:var(--accent-green)] rounded-full animate-pulse"></div>
        ${title}
      </div>
    </div>
    <div class="kanban-fullscreen-controls">
      <!-- Toggle Vista Lista/Kanban en fullscreen -->
      <div class="flex items-center bg-[color:var(--bg-card)] rounded-xl border border-[color:var(--border-color)] p-1 shadow-lg mr-4">
        <button
          id="fullscreen-toggle-lista"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 view-toggle ${view === 'tabla' ? 'active' : ''}">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
          <span>Lista</span>
        </button>
        <button
          id="fullscreen-toggle-kanban"
          class="flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 view-toggle ${view === 'kanban' ? 'active' : ''}">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
          </svg>
          <span>Kanban</span>
        </button>
      </div>
      <div class="text-sm text-[color:var(--text-secondary)] mono-font mr-4">
        Presiona <kbd class="px-2 py-1 bg-[color:var(--bg-primary)] border border-[color:var(--border-primary)] rounded text-xs">ESC</kbd> para salir
      </div>
      <button class="fullscreen-exit-btn">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
        Salir de Vista Completa
      </button>
    </div>
  `;
  return header;
}

function createFullscreenFilters() {
  const filtersPanel = document.getElementById('filters-panel');
  if (!filtersPanel) return null;

  // Clonar el panel de filtros para la vista completa
  const filtersClone = filtersPanel.cloneNode(true);
  filtersClone.id = 'fullscreen-filters-panel';
  
  // SIEMPRE mostrar los filtros en vista completa, independientemente del estado original
  filtersClone.classList.remove('hidden');
  filtersClone.classList.remove('animate__fadeOutUp');
  filtersClone.classList.add('fullscreen-filters');
  
  // Agregar estilos específicos para vista completa
  filtersClone.style.marginBottom = '20px';
  filtersClone.style.background = 'var(--bg-card)';
  filtersClone.style.border = '1px solid var(--border-primary)';
  filtersClone.style.borderRadius = '12px';
  filtersClone.style.padding = '16px';
  filtersClone.style.display = 'block'; // Forzar que se muestre
  
  // Hacer que los filtros funcionen en la vista completa
  const selects = filtersClone.querySelectorAll('select');
  selects.forEach(select => {
    select.addEventListener('change', function() {
      // Sincronizar con el filtro original
      const originalSelect = document.querySelector(`#filters-panel select[name="${select.name}"]`);
      if (originalSelect) {
        originalSelect.value = select.value;
        // Disparar evento change en el filtro original
        originalSelect.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  });

  // Hacer que la búsqueda funcione
  const searchInput = filtersClone.querySelector('#busqueda-rapida');
  if (searchInput) {
    searchInput.id = 'fullscreen-busqueda-rapida';
    searchInput.addEventListener('input', function() {
      const originalSearch = document.querySelector('#filters-panel #busqueda-rapida');
      if (originalSearch) {
        originalSearch.value = searchInput.value;
        originalSearch.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
  }

  // Hacer que el botón limpiar funcione
  const clearBtn = filtersClone.querySelector('#limpiar-busqueda');
  if (clearBtn) {
    clearBtn.addEventListener('click', function() {
      const originalClearBtn = document.querySelector('#filters-panel #limpiar-busqueda');
      if (originalClearBtn) {
        originalClearBtn.click();
        // Limpiar también los filtros clonados
        selects.forEach(select => select.value = '');
        if (searchInput) searchInput.value = '';
      }
    });
  }

  // Hacer que los checkboxes de columnas funcionen (si existen)
  const columnCheckboxes = filtersClone.querySelectorAll('.toggle-column');
  columnCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      const originalCheckbox = document.querySelector(`#filters-panel .toggle-column[data-estado="${checkbox.dataset.estado}"]`);
      if (originalCheckbox) {
        originalCheckbox.checked = checkbox.checked;
        originalCheckbox.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  });

  // Sincronizar valores actuales de los filtros originales
  syncFiltersToFullscreen(filtersClone);

  return filtersClone;
}

// Función para sincronizar los valores de los filtros originales a la vista completa
function syncFiltersToFullscreen(filtersClone) {
  // Sincronizar selects
  const originalSelects = document.querySelectorAll('#filters-panel select');
  const clonedSelects = filtersClone.querySelectorAll('select');
  
  originalSelects.forEach((originalSelect, index) => {
    const clonedSelect = clonedSelects[index];
    if (clonedSelect && originalSelect.name) {
      const correspondingClonedSelect = filtersClone.querySelector(`select[name="${originalSelect.name}"]`);
      if (correspondingClonedSelect) {
        correspondingClonedSelect.value = originalSelect.value;
      }
    }
  });

  // Sincronizar búsqueda
  const originalSearch = document.querySelector('#filters-panel #busqueda-rapida');
  const clonedSearch = filtersClone.querySelector('#fullscreen-busqueda-rapida');
  if (originalSearch && clonedSearch) {
    clonedSearch.value = originalSearch.value;
  }

  // Sincronizar checkboxes de columnas
  const originalCheckboxes = document.querySelectorAll('#filters-panel .toggle-column');
  originalCheckboxes.forEach(originalCheckbox => {
    const clonedCheckbox = filtersClone.querySelector(`.toggle-column[data-estado="${originalCheckbox.dataset.estado}"]`);
    if (clonedCheckbox) {
      clonedCheckbox.checked = originalCheckbox.checked;
    }
  });
}

function switchViewInFullscreen(newView) {
  if (!isFullscreen) return;
  
  const fullscreenContainer = document.getElementById('kanban-fullscreen-container');
  const fullscreenContent = fullscreenContainer.querySelector('.kanban-fullscreen-content');
  
  if (!fullscreenContainer || !fullscreenContent) return;
  
  // Remover el elemento actual del contenedor fullscreen
  const currentElement = currentView === 'kanban' ? 
    document.getElementById('kanban-board') : 
    document.getElementById('tabla-view');
  
  if (currentElement) {
    // Restaurar elemento actual a su posición original temporalmente
    if (originalNextSibling) {
      originalParent.insertBefore(currentElement, originalNextSibling);
    } else {
      originalParent.appendChild(currentElement);
    }
  }
  
  // Salir de fullscreen temporalmente para cambiar la vista
  const wasFullscreen = isFullscreen;
  isFullscreen = false;
  
  // Cambiar a la nueva vista en la página principal
  const originalToggleBtn = newView === 'tabla' ? 
    document.getElementById('toggle-lista') : 
    document.getElementById('toggle-kanban');
  
  if (originalToggleBtn) {
    originalToggleBtn.click();
  }
  
  // Esperar un poco para que se complete el cambio de vista
  setTimeout(() => {
    // Restaurar estado de fullscreen
    isFullscreen = wasFullscreen;
    
    // Actualizar la vista actual
    currentView = newView;
    
    // Obtener el nuevo elemento
    const newElement = newView === 'kanban' ? 
      document.getElementById('kanban-board') : 
      document.getElementById('tabla-view');
    
    if (newElement) {
      // Guardar nueva posición original
      originalParent = newElement.parentNode;
      originalNextSibling = newElement.nextElementSibling;
      
      // Agregar el nuevo elemento al contenedor fullscreen
      fullscreenContent.appendChild(newElement);
      
      // Si es tabla, reinicializar los event listeners para los modales
      if (newView === 'tabla') {
        reinitializeTableEventListeners();
      } else if (newView === 'kanban') {
        reinitializeKanbanEventListeners();
      }
      
      // Actualizar el header con el nuevo título
      const header = fullscreenContent.querySelector('.kanban-fullscreen-header');
      if (header) {
        const titleElement = header.querySelector('.kanban-fullscreen-title > div');
        if (titleElement) {
          const newTitle = newView === 'kanban' ? 
            'Vista Completa - Tablero Kanban' : 
            'Vista Completa - Tabla de EDPs';
          titleElement.innerHTML = `
            <div class="w-3 h-3 bg-[color:var(--accent-green)] rounded-full animate-pulse"></div>
            ${newTitle}
          `;
        }
        
        // Actualizar botones de toggle
        const toggleButtons = header.querySelectorAll('.view-toggle');
        toggleButtons.forEach(btn => {
          btn.classList.remove('active');
          if ((btn.id === 'fullscreen-toggle-lista' && newView === 'tabla') ||
              (btn.id === 'fullscreen-toggle-kanban' && newView === 'kanban')) {
            btn.classList.add('active');
          }
        });
      }
    }
    
    console.log(`Vista cambiada en fullscreen a: ${newView}`);
  }, 200);
}

// Función para reinicializar los event listeners de la tabla cuando se mueve a fullscreen
function reinitializeTableEventListeners() {
  console.log('Preservando event listeners originales de la tabla...');
  
  // NO clonar ni reemplazar elementos - solo agregar detección de modales
  // Los botones de editar EDP deben mantener sus funciones originales
  
  const editButtons = document.querySelectorAll('#tabla-view .edp-edit-btn');
  
  editButtons.forEach(function(button) {
    // NO clonar el botón - solo agregar un listener adicional para detectar modales
    // Esto preserva toda la funcionalidad original
    
    // Agregar detector de modal que se ejecuta después del click original
    button.addEventListener('click', function() {
      console.log('Click detectado en botón editar EDP - esperando modal...');
      
      // Dar tiempo para que la función original abra el modal
      setTimeout(() => {
        const edpModal = document.getElementById('edp-modal');
        if (edpModal) {
          const isVisible = edpModal.offsetParent !== null || 
                           edpModal.style.display === 'block' || 
                           edpModal.style.display === 'flex';
          
          const hasContent = edpModal.innerHTML.trim().length > 0 && 
                            edpModal.querySelector('input, textarea, button, .modal-content, .modal-body, form');
          
          if (isVisible && hasContent) {
            console.log('Modal EDP original detectado - aplicando ajuste de z-index');
            
            // Marcar como ajustado para evitar procesos duplicados
            edpModal.setAttribute('data-fullscreen-adjusted', 'true');
            
            // Aplicar ajustes de z-index
            forceModalVisible();
            setupModalCloseDetector();
            adjustModalZIndex();
            
            // Múltiples intentos para asegurar que funcione
            setTimeout(() => adjustModalZIndex(), 50);
            setTimeout(() => adjustModalZIndex(), 100);
            setTimeout(() => adjustModalZIndex(), 200);
            setTimeout(() => adjustModalZIndex(), 300);
          }
        }
      }, 100);
    });
  });
  
  // Observer adicional para detectar cualquier modal que se abra en la tabla
  const tablaView = document.getElementById('tabla-view');
  if (tablaView) {
    const tableModalObserver = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        // Dar tiempo para que el modal se renderice
        setTimeout(() => {
          const edpModal = document.getElementById('edp-modal');
          if (edpModal && !edpModal.hasAttribute('data-fullscreen-adjusted')) {
            const isVisible = edpModal.offsetParent !== null || 
                             edpModal.style.display === 'block' || 
                             edpModal.style.display === 'flex';
            
            const hasContent = edpModal.innerHTML.trim().length > 0 && 
                              edpModal.querySelector('input, textarea, button, .modal-content, .modal-body, form');
            
            if (isVisible && hasContent) {
              console.log('Modal EDP detectado por observer - aplicando ajuste');
              edpModal.setAttribute('data-fullscreen-adjusted', 'true');
              forceModalVisible();
              setupModalCloseDetector();
              adjustModalZIndex();
            }
          }
        }, 50);
      });
    });
    
    // Observar cambios que puedan indicar apertura de modal
    tableModalObserver.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['style', 'class']
    });
    
    // Guardar referencia para limpieza
    tablaView.tableModalObserver = tableModalObserver;
  }
  
  console.log('Event listeners originales de tabla preservados, detectores de modal configurados para', editButtons.length, 'botones');
}

// Función para reinicializar los event listeners del kanban cuando se mueve a fullscreen
function reinitializeKanbanEventListeners() {
  console.log('Configurando interceptor de SortableJS para kanban en fullscreen...');
  
  // Guardar la función original mostrarModalContextual si no está guardada
  if (typeof mostrarModalContextual === 'function' && !window.originalMostrarModalContextual) {
    window.originalMostrarModalContextual = mostrarModalContextual;
    console.log('Función original mostrarModalContextual guardada');
  }
  
  // Interceptar mostrarModalContextual globalmente
  if (typeof mostrarModalContextual === 'function') {
    // Reemplazar la función global
    window.mostrarModalContextual = function(edpId, tipoModal, estadoOrigen, estadoDestino, edpData, callback, item = null) {
      console.log('mostrarModalContextual interceptado - detectando contexto...');
      
      // Si estamos en fullscreen, salir temporalmente
      if (isFullscreen) {
        console.log('🎯 En fullscreen - saliendo temporalmente para mostrar modal...');
        console.log('📊 Estado antes del cambio:', { isFullscreen, shouldReturnToFullscreen });
        
        shouldReturnToFullscreen = true;
        console.log('🔧 VARIABLE CONFIGURADA: shouldReturnToFullscreen =', shouldReturnToFullscreen);
        
        pendingModalData = {
          edpId, tipoModal, estadoOrigen, estadoDestino, edpData, callback, item
        };
        
        console.log('✅ Variables configuradas:', { shouldReturnToFullscreen, pendingModalData: !!pendingModalData });
        
        // Salir del fullscreen
        exitFullscreen();
        
        // Esperar a que se complete la salida del fullscreen y luego abrir el modal
        setTimeout(() => {
          console.log('🔄 Abriendo modal normal después de salir del fullscreen...');
          console.log('📊 Estado durante apertura de modal:', { isFullscreen, shouldReturnToFullscreen });
          
          // Usar la función original
          if (window.originalMostrarModalContextual) {
            window.originalMostrarModalContextual(edpId, tipoModal, estadoOrigen, estadoDestino, edpData, callback, item);
            console.log('✅ Modal abierto con función original');
          } else {
            // Fallback en caso de que no tengamos la original
            console.error('❌ Función original no disponible');
          }
          
          // Configurar detector para cuando se cierre el modal
          console.log('🔧 Configurando detector de cierre de modal...');
          setupModalCloseReturnToFullscreen();
        }, 600);
      } else {
        // Si no estamos en fullscreen, usar la función original
        if (window.originalMostrarModalContextual) {
          window.originalMostrarModalContextual(edpId, tipoModal, estadoOrigen, estadoDestino, edpData, callback, item);
        }
      }
    };
    
    // También hacer que la función esté disponible globalmente sin window
    window.mostrarModalContextual = window.mostrarModalContextual;
    mostrarModalContextual = window.mostrarModalContextual;
    
    console.log('Interceptor de mostrarModalContextual configurado globalmente');
  } else {
    console.error('Función mostrarModalContextual no encontrada - el interceptor no funcionará');
  }
  
  // Preservar el sistema de drag and drop original (SortableJS)
  if (typeof initSortableColumns === 'function') {
    try {
      initSortableColumns();
      console.log('Sistema de SortableJS preservado');
    } catch (e) {
      console.log('Error preservando SortableJS:', e);
    }
  }
  
  console.log('Interceptor configurado - Los modales del kanban saldrán temporalmente del fullscreen');
}

// Función para configurar el detector de cierre de modal y regreso al fullscreen
function setupModalCloseReturnToFullscreen() {
  console.log('Configurando detector de cierre de modal para regresar al fullscreen...');
  
  let modalCheckInterval;
  let escHandler;
  
  // Función para detectar cuando se cierra el modal
  const checkModalClosed = () => {
    // Buscar modales contextuales abiertos con selectores MÁS ESPECÍFICOS
    const contextualOverlay = document.querySelector('div.fixed.inset-0.bg-black\\/60.backdrop-blur-sm');
    const modalForm = document.getElementById('modal-contextual-form');
    const anyBackdropModal = document.querySelector('.fixed.inset-0[class*="bg-black"]');
    const cancelarModal = document.getElementById('cancelar-modal');
    const cancelarCambio = document.getElementById('cancelar-cambio');
    
    // El modal está abierto si existe cualquiera de estos elementos
    const modalAbierto = contextualOverlay || modalForm || anyBackdropModal || cancelarModal || cancelarCambio;
    
    console.log('🔍 Verificando modales:', {
      contextualOverlay: !!contextualOverlay,
      modalForm: !!modalForm,
      anyBackdropModal: !!anyBackdropModal,
      cancelarModal: !!cancelarModal,
      cancelarCambio: !!cancelarCambio,
      modalAbierto: !!modalAbierto,
      shouldReturn: shouldReturnToFullscreen
    });
    
    // Si no hay modales abiertos Y debemos regresar al fullscreen
    if (!modalAbierto && shouldReturnToFullscreen) {
      console.log('✅ Todos los modales cerrados - regresando al fullscreen...');
      
      // Limpiar el interval
      if (modalCheckInterval) {
        clearInterval(modalCheckInterval);
        modalCheckInterval = null;
      }
      
      // Limpiar el handler de ESC
      if (escHandler) {
        document.removeEventListener('keydown', escHandler);
        escHandler = null;
      }
      
      // Regresar al fullscreen después de un pequeño delay
      setTimeout(() => {
        if (shouldReturnToFullscreen) {
          console.log('🔄 Ejecutando regreso al fullscreen...');
          shouldReturnToFullscreen = false;
          pendingModalData = null;
          enterFullscreen();
        }
      }, 500);
    }
  };
  
  // Verificar cada 300ms si el modal se cerró (aumentado para dar más tiempo)  
  modalCheckInterval = setInterval(checkModalClosed, 300);
  
  // Agregar un verificador adicional que se ejecute menos frecuentemente para debug
  const debugInterval = setInterval(() => {
    if (shouldReturnToFullscreen) {
      console.log('🔄 Estado debug:', {
        shouldReturnToFullscreen,
        isFullscreen,
        pendingModalData: !!pendingModalData,
        timestamp: new Date().toISOString().split('T')[1].split('.')[0]
      });
    } else {
      clearInterval(debugInterval);
    }
  }, 2000);
  
  // También detectar clicks en botones de cerrar - con mejor detección
  setTimeout(() => {
    // Buscar botones de cerrar con selectores más amplios
    const closeButtons = document.querySelectorAll(`
      #cancelar-modal, 
      #cancelar-cambio, 
      button[onclick*="cerrarModal"],
      button[onclick*="cerrar"],
      .btn-close,
      .close,
      [data-dismiss="modal"],
      button:contains("Cancelar"),
      button:contains("×"),
      button:contains("Cerrar")
    `.replace(/button:contains\([^)]*\)/g, 'button')); // Remover :contains que no es válido
    
    // También buscar botones por texto
    const allButtons = document.querySelectorAll('button');
    const textBasedCloseButtons = Array.from(allButtons).filter(btn => {
      const text = btn.textContent || btn.innerText || '';
      return text.includes('Cancelar') || text.includes('×') || text.includes('✕') || text.includes('Cerrar');
    });
    
    const allCloseButtons = [...closeButtons, ...textBasedCloseButtons];
    
    console.log(`Configurando listeners para ${allCloseButtons.length} botones de cerrar`);
    
    allCloseButtons.forEach((button, index) => {
      button.addEventListener('click', () => {
        console.log(`🔘 Botón de cerrar clickeado (${index + 1}): "${button.textContent?.trim()}" - programando regreso al fullscreen...`);
        
        // Dar más tiempo para que se complete el cierre del modal
        setTimeout(() => {
          console.log('⏱️ Verificando si debe regresar al fullscreen después del click...');
          if (shouldReturnToFullscreen) {
            console.log('🔄 Forzando regreso al fullscreen por click en botón');
            shouldReturnToFullscreen = false;
            pendingModalData = null;
            
            // Limpiar interval si existe
            if (modalCheckInterval) {
              clearInterval(modalCheckInterval);
              modalCheckInterval = null;
            }
            
            enterFullscreen();
          }
        }, 800); // Más tiempo para asegurar que el modal se cierre completamente
      });
    });
  }, 500); // Dar más tiempo para que los botones se rendericen
  
  // Detectar tecla ESC
  escHandler = (e) => {
    if (e.key === 'Escape' && shouldReturnToFullscreen) {
      console.log('⌨️ Tecla ESC detectada - regresando al fullscreen...');
      
      setTimeout(() => {
        if (shouldReturnToFullscreen) {
          console.log('🔄 Forzando regreso al fullscreen por ESC');
          shouldReturnToFullscreen = false;
          pendingModalData = null;
          
          // Limpiar interval si existe
          if (modalCheckInterval) {
            clearInterval(modalCheckInterval);
            modalCheckInterval = null;
          }
          
          enterFullscreen();
        }
      }, 500);
      
      // Remover el handler después de usarlo
      document.removeEventListener('keydown', escHandler);
      escHandler = null;
    }
  };
  
  document.addEventListener('keydown', escHandler);
  
  console.log('✅ Detector de cierre de modal configurado con múltiples métodos de detección');
}

// Función para forzar la visibilidad del modal de manera extrema
function forceModalVisible() {
  if (!isFullscreen) return;
  
  console.log('forceModalVisible ejecutándose en vista completa');
  
  // Asegurar que la vista completa permanezca visible
  const fullscreenContainer = document.getElementById('kanban-fullscreen-container');
  if (fullscreenContainer) {
    // FORZAR que la vista completa permanezca visible y con el z-index correcto (intermedio)
    fullscreenContainer.style.setProperty('z-index', '10000', 'important');
    fullscreenContainer.style.setProperty('display', 'block', 'important');
    fullscreenContainer.style.setProperty('visibility', 'visible', 'important');
    fullscreenContainer.style.setProperty('opacity', '1', 'important');
    fullscreenContainer.style.setProperty('position', 'fixed', 'important');
    fullscreenContainer.style.setProperty('pointer-events', 'auto', 'important');
    console.log('Vista completa FORZADA a permanecer visible con z-index intermedio (10000)');
  }
  
  // Crear un estilo CSS UNIVERSAL para TODOS los modales
  let forceModalStyle = document.getElementById('force-modal-style');
  if (!forceModalStyle) {
    forceModalStyle = document.createElement('style');
    forceModalStyle.id = 'force-modal-style';
    forceModalStyle.type = 'text/css';
    document.head.appendChild(forceModalStyle);
  }
  
  forceModalStyle.textContent = `
    /* Vista completa permanece visible como capa intermedia */
    #kanban-fullscreen-container {
      z-index: 10000 !important;
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      width: 100% !important;
      height: 100% !important;
      background: var(--bg-primary, #ffffff) !important;
      pointer-events: auto !important;
    }
    
    /* TODOS los modales posibles - z-index superior */
    #edp-modal,
    .kanban-card-modal,
    #modal-contextual-form,
    [id*="modal"]:not(#kanban-fullscreen-container),
    .modal:not(.kanban-fullscreen),
    [role="dialog"],
    [aria-modal="true"],
    .modal-overlay,
    div[class*="fixed"]:not(.kanban-fullscreen) {
      z-index: 10001 !important;
    }
    
    /* Z-index para elementos dentro de TODOS los modales */
    #edp-modal *,
    .kanban-card-modal *,
    #modal-contextual-form *,
    [id*="modal"]:not(#kanban-fullscreen-container) *,
    .modal:not(.kanban-fullscreen) *,
    [role="dialog"] *,
    [aria-modal="true"] * {
      z-index: inherit !important;
    }
    
    /* Contenido principal por debajo */
    body > *:not(#kanban-fullscreen-container):not([id*="modal"]):not(.modal):not([role="dialog"]) {
      z-index: 1 !important;
    }
  `;
  
  console.log('Estilo CSS UNIVERSAL aplicado para todos los modales');
}

// Función para detectar cuando se cierra el modal y restaurar la vista completa
function setupModalCloseDetector() {
  // Limpiar detector anterior si existe
  if (window.modalCloseObserver) {
    window.modalCloseObserver.disconnect();
  }
  
  // Crear observer para detectar cuando se remueve el modal
  window.modalCloseObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        mutation.removedNodes.forEach(function(node) {
          if (node.nodeType === Node.ELEMENT_NODE && 
              (node.id === 'edp-modal' || 
               node.classList?.contains('kanban-card-modal') ||
               (node.querySelector && (node.querySelector('#edp-modal') || node.querySelector('.kanban-card-modal'))))) {
            // Modal fue removido, limpiar estilos
            restoreFullscreenAfterModal();
            window.modalCloseObserver.disconnect();
          }
        });
        
        // También detectar cambios en atributos (como style.display)
        if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
          const target = mutation.target;
          if ((target.id === 'edp-modal' || target.classList?.contains('kanban-card-modal')) && 
              (target.style.display === 'none' || !target.offsetParent)) {
            restoreFullscreenAfterModal();
            window.modalCloseObserver.disconnect();
          }
        }
      }
    });
  });
  
  // Observer para detectar cambios en modales
  window.modalCloseObserver.observe(document.body, { 
    childList: true, 
    subtree: true, 
    attributes: true, 
    attributeFilter: ['style', 'class'] 
  });
  
  // Detectar clicks en botones de cerrar de cualquier modal
  const detectCloseButtons = () => {
    const allModals = document.querySelectorAll(`
      #edp-modal, 
      .kanban-card-modal, 
      #modal-contextual-form
    `);
    allModals.forEach(modal => {
      // Usar selectores CSS válidos - sin :contains()
      const closeButtons = modal.querySelectorAll(`
        [data-dismiss="modal"], 
        .btn-close, 
        .close, 
        [onclick*="close"], 
        .modal-close, 
        .close-modal,
        #cancelar-modal,
        #cancelar-cambio,
        button[type="button"]
      `);
      
      closeButtons.forEach(button => {
        // Verificar manualmente el contenido del texto para botones de cancelar/cerrar
        const buttonText = button.textContent || button.innerText || '';
        const isCloseButton = buttonText.includes('Cancelar') || 
                             buttonText.includes('×') || 
                             buttonText.includes('✕') ||
                             buttonText.includes('Cerrar') ||
                             button.hasAttribute('data-dismiss') ||
                             button.className.includes('close') ||
                             button.id.includes('cancelar');
        
        if (isCloseButton) {
          button.addEventListener('click', function() {
            console.log('Botón de cerrar modal detectado:', this.id || this.className);
            setTimeout(() => {
              restoreFullscreenAfterModal();
            }, 100);
          }, { once: true });
        }
      });
    });
  };
  
  // Ejecutar detección inicial y repetir cada 500ms para nuevos modales
  detectCloseButtons();
  const buttonDetectionInterval = setInterval(() => {
    if (document.querySelector('#edp-modal, .kanban-card-modal, #modal-contextual-form')) {
      detectCloseButtons();
    } else {
      clearInterval(buttonDetectionInterval);
    }
  }, 500);
  
  // Detectar tecla ESC para cualquier modal específico
  const escapeHandler = function(e) {
    if (e.key === 'Escape') {
      // Detectar tecla ESC para modales específicos
      const openModal = document.querySelector(`
        #edp-modal:not([style*="display: none"]), 
        .kanban-card-modal:not([style*="display: none"]),
        #modal-contextual-form:not([style*="display: none"])
      `);
      if (openModal) {
        setTimeout(() => {
          restoreFullscreenAfterModal();
        }, 100);
      }
    }
  };
  document.addEventListener('keydown', escapeHandler);
  
  // Guardar referencia para limpieza posterior
  setupModalCloseDetector.escapeHandler = escapeHandler;
  setupModalCloseDetector.buttonDetectionInterval = buttonDetectionInterval;
  
  console.log('Detector de cierre de modal mejorado configurado para todos los tipos de modal');
}

// Función para restaurar la vista completa después de cerrar el modal
function restoreFullscreenAfterModal() {
  // ASEGURAR que la vista completa permanezca visible
  const fullscreenContainer = document.getElementById('kanban-fullscreen-container');
  if (fullscreenContainer && isFullscreen) {
    // FORZAR que la vista completa permanezca visible con z-index intermedio
    fullscreenContainer.style.setProperty('z-index', '10000', 'important');
    fullscreenContainer.style.setProperty('display', 'block', 'important');
    fullscreenContainer.style.setProperty('visibility', 'visible', 'important');
    fullscreenContainer.style.setProperty('opacity', '1', 'important');
    fullscreenContainer.style.setProperty('position', 'fixed', 'important');
    fullscreenContainer.style.setProperty('pointer-events', 'auto', 'important');
    console.log('Vista completa RESTAURADA y FORZADA a permanecer visible con z-index intermedio');
  }
  
  // NO remover clase del body ya que no la agregamos
  
  // Remover el estilo CSS forzado
  const forceModalStyle = document.getElementById('force-modal-style');
  if (forceModalStyle) {
    forceModalStyle.remove();
  }
  
  // Limpiar event handlers
  if (setupModalCloseDetector.escapeHandler) {
    document.removeEventListener('keydown', setupModalCloseDetector.escapeHandler);
    setupModalCloseDetector.escapeHandler = null;
  }
  
  if (setupModalCloseDetector.buttonDetectionInterval) {
    clearInterval(setupModalCloseDetector.buttonDetectionInterval);
    setupModalCloseDetector.buttonDetectionInterval = null;
  }
  
  // Limpiar monitor de visibilidad
  if (window.fullscreenVisibilityMonitor) {
    clearInterval(window.fullscreenVisibilityMonitor);
    window.fullscreenVisibilityMonitor = null;
  }
  
  console.log('Estilos de modal limpiados, vista completa FORZADA a permanecer visible');
}

// Función auxiliar para ajustar z-index del modal en vista completa
function adjustModalZIndex() {
  if (!isFullscreen) return false;
  
  // Primero asegurar que la vista completa permanezca visible con z-index intermedio
  const fullscreenContainer = document.getElementById('kanban-fullscreen-container');
  if (fullscreenContainer) {
    fullscreenContainer.style.setProperty('z-index', '10000', 'important');
    fullscreenContainer.style.setProperty('display', 'block', 'important');
    fullscreenContainer.style.setProperty('visibility', 'visible', 'important');
    fullscreenContainer.style.setProperty('opacity', '1', 'important');
    fullscreenContainer.style.setProperty('pointer-events', 'auto', 'important');
  }
  
  // Buscar TODOS los modales posibles
  const allModalSelectors = [
    '#edp-modal',
    '.kanban-card-modal', 
    '#modal-contextual-form',
    '[id*="modal"]:not(#kanban-fullscreen-container)',
    '.modal:not(.kanban-fullscreen)',
    '[role="dialog"]',
    '[aria-modal="true"]',
    '.modal-overlay',
    // Selector ESPECÍFICO para modales contextuales del kanban (overlay completo)
    'div.fixed.inset-0[class*="bg-black"]'
  ];
  
  let allModals = [];
  allModalSelectors.forEach(selector => {
    try {
      const modals = document.querySelectorAll(selector);
      allModals.push(...modals);
    } catch (e) {
      // Ignorar errores de selector
    }
  });
  
  // Filtrar solo modales únicos y visibles
  const uniqueModals = Array.from(new Set(allModals)).filter(modal => {
    if (!modal || modal.id === 'kanban-fullscreen-container' || 
        modal.classList?.contains('kanban-fullscreen')) {
      return false;
    }
    
    // Verificar visibilidad
    const isVisible = modal.offsetParent !== null || 
                     modal.style.display === 'block' || 
                     modal.style.display === 'flex' ||
                     window.getComputedStyle(modal).display !== 'none';
    
    return isVisible;
  });
  
  if (uniqueModals.length === 0) return false;
  
  console.log('Ajustando z-index para', uniqueModals.length, 'modales detectados');
  
  let adjusted = false;
  
  uniqueModals.forEach(modal => {
    // Evitar procesamiento múltiple
    if (modal.hasAttribute('data-z-index-adjusted') && 
        modal.getAttribute('data-z-index-adjusted') === 'true') {
      return;
    }
    
    console.log('Ajustando modal:', modal.id || modal.className);
    
    // Marcar como ajustado
    modal.setAttribute('data-z-index-adjusted', 'true');
    
    // DETECTAR si es un modal contextual (overlay dinámico)
    const isContextualModal = modal.classList && 
                             (modal.classList.contains('fixed') && 
                              modal.classList.contains('inset-0') &&
                              (modal.querySelector('#modal-contextual-form') ||
                               modal.querySelector('[class*="bg-"]') || // Overlay con background
                               modal.className.includes('bg-black')));  // Fondo oscuro típico
    
    // VERIFICAR si es el overlay completo del modal contextual
    const isModalOverlay = isContextualModal && 
                          modal.querySelector('div[class*="bg-"][class*="rounded"]'); // Modal content inside overlay
    
    if (isModalOverlay) {
      console.log('OVERLAY COMPLETO del modal contextual detectado:', modal.className);
      console.log('Contenido del modal:', modal.innerHTML.substring(0, 200) + '...');
    }
    
    // SOLO mover al body si NO es un modal contextual (que ya está en el body)
    if (!isContextualModal && modal.parentNode !== document.body) {
      document.body.appendChild(modal);
      console.log('Modal movido al body:', modal.id || modal.className);
    } else if (isContextualModal) {
      console.log('Modal contextual detectado - NO mover, ya está en posición correcta:', modal.id || modal.className);
    }
    
    // SOLO ajustar z-index - NO tocar nada más
    modal.style.setProperty('z-index', '10001', 'important');
    
      // Para modales contextuales, también ajustar el contenedor interno
      if (isContextualModal) {
        const modalContent = modal.querySelector('div');
        if (modalContent) {
          modalContent.style.setProperty('z-index', 'inherit', 'important');
        }
        
        // SOLO ajustar elementos básicos sin forzar display
        const modalForm = modal.querySelector('#modal-contextual-form');
        const modalButtons = modal.querySelectorAll('button');
        const modalInputs = modal.querySelectorAll('input, textarea, select');
        
        console.log(`Modal contextual - Form: ${modalForm ? 'SÍ' : 'NO'}, Botones: ${modalButtons.length}, Inputs: ${modalInputs.length}`);
        
        // Solo ajustar visibilidad básica sin forzar display
        [modalForm, ...modalButtons, ...modalInputs].forEach(element => {
          if (element) {
            element.style.setProperty('visibility', 'visible', 'important');
            element.style.setProperty('opacity', '1', 'important');
          }
        });
        
        // FORZAR visibilidad adicional para todos los elementos del modal contextual
        const allFormElements = modal.querySelectorAll('div, p, label, span');
        allFormElements.forEach(element => {
          element.style.setProperty('visibility', 'visible', 'important');
          element.style.setProperty('opacity', '1', 'important');
        });
        
        console.log(`✅ Visibilidad forzada para modal contextual - Total elementos: ${allFormElements.length + modalButtons.length + modalInputs.length}`);
      }    // Ajustar elementos hijos
    const allElements = modal.querySelectorAll('*');
    allElements.forEach(element => {
      element.style.setProperty('z-index', 'inherit', 'important');
    });
    
    adjusted = true;
    console.log('Modal ajustado exitosamente:', modal.id || modal.className);
  });
  
  if (adjusted) {
    console.log('Modales ajustados - jerarquía: Página(1) → Vista completa(10000) → Modal(10001)');
  }
  
  return adjusted;
}

// Función para restaurar z-index del modal
function restoreModalZIndex() {
  // SOLO buscar modales específicos que sabemos que existen
  const specificModals = [
    document.getElementById('edp-modal'),
    document.getElementById('modal-contextual-form')
  ].filter(modal => modal !== null);
  
  const kanbanCardModals = document.querySelectorAll('.kanban-card-modal');
  const allModals = [...specificModals, ...kanbanCardModals];
  
  allModals.forEach(modal => {
    // Restaurar SOLO las propiedades que modificamos (solo z-index)
    modal.style.removeProperty('z-index');
    
    // Restaurar z-index de elementos hijos
    const allModalElements = modal.querySelectorAll('*');
    allModalElements.forEach(element => {
      element.style.removeProperty('z-index');
    });
    
    // Restaurar contenido del modal
    const modalContent = modal.querySelector('.modal-content, .modal-dialog, .modal-body, div:first-child');
    if (modalContent) {
      modalContent.style.removeProperty('z-index');
    }
    
    // Remover atributos de seguimiento
    modal.removeAttribute('data-fullscreen-priority');
    modal.removeAttribute('data-moved-to-body');
    modal.removeAttribute('data-fullscreen-adjusted');
    modal.removeAttribute('data-fullscreen-processed');
    modal.removeAttribute('data-z-index-adjusted');
    modal.removeAttribute('data-processed-by-main-observer');
    modal.removeAttribute('data-processed-by-global-observer');
  });
  
  // NO remover clase del body ya que no la agregamos
  
  console.log('Z-index de modales específicos completamente restaurados');
}

function enterFullscreen() {
  if (isFullscreen) return;

  currentView = getCurrentView();
  const targetElement = currentView === 'kanban' ? 
    document.getElementById('kanban-board') : 
    document.getElementById('tabla-view');
    
  if (!targetElement) return;

  // Guardar posición original
  originalParent = targetElement.parentNode;
  originalNextSibling = targetElement.nextElementSibling;

  // Crear contenedor fullscreen
  const fullscreenContainer = document.createElement('div');
  fullscreenContainer.id = 'kanban-fullscreen-container';
  fullscreenContainer.className = 'kanban-fullscreen';
  
  // Asegurar que el contenedor fullscreen tenga un z-index intermedio (por encima de la página principal, por debajo de modales)
  fullscreenContainer.style.setProperty('z-index', '10000', 'important');
  fullscreenContainer.style.setProperty('pointer-events', 'auto', 'important');

  // Crear contenido fullscreen
  const fullscreenContent = document.createElement('div');
  fullscreenContent.className = 'kanban-fullscreen-content';

  // Agregar header
  const header = createFullscreenHeader();
  fullscreenContent.appendChild(header);

  // Agregar filtros clonados - SIEMPRE intentar mostrarlos si existen
  const filtersClone = createFullscreenFilters();
  if (filtersClone) {
    fullscreenContent.appendChild(filtersClone);
    fullscreenContainer.classList.add('with-filters');
    console.log('Filtros agregados a vista completa');
  } else {
    console.log('No se pudieron crear filtros para vista completa');
  }

  // Mover elemento al contenedor fullscreen
  fullscreenContent.appendChild(targetElement);
  fullscreenContainer.appendChild(fullscreenContent);

  // Agregar al body
  document.body.appendChild(fullscreenContainer);

  // Actualizar estado
  isFullscreen = true;
  
  console.log('Vista completa creada exitosamente - NO debe activar modales automáticamente');

  // Si estamos en vista de tabla, reinicializar los event listeners
  if (currentView === 'tabla') {
    reinitializeTableEventListeners();
  } else if (currentView === 'kanban') {
    reinitializeKanbanEventListeners();
  }

  // Observer para detectar cuando se abre el modal y ajustar su z-index
  const modalObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        // Revisar nodos agregados
        mutation.addedNodes.forEach(function(node) {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // EXCLUIR el contenedor de fullscreen para evitar falsos positivos
            if (node.id === 'kanban-fullscreen-container' || 
                node.classList?.contains('kanban-fullscreen') ||
                node.querySelector?.('#kanban-fullscreen-container')) {
              return; // Ignorar el contenedor de fullscreen
            }
            
            // SOLO verificar modales específicos que sabemos que existen
            let modals = [];
            
            // DETECCIÓN ESPECIAL para modales contextuales del kanban (overlay completo)
            if (node.classList && 
                node.classList.contains('fixed') && 
                node.classList.contains('inset-0') &&
                (node.className.includes('bg-black') || node.className.includes('backdrop-blur')) &&
                node.querySelector('#modal-contextual-form')) {
              // Este es el overlay completo del modal contextual
              console.log('🎯 OVERLAY COMPLETO del modal contextual detectado:', node.className);
              console.log('Contenido del overlay (primeros 500 chars):', node.innerHTML.substring(0, 500));
              modals.push(node);
            }
            // FILTRAR elementos que NO son modales completos
            else if (node.id === 'modalTitle' || 
                     node.className === 'modalTitle' ||
                     (node.classList && node.classList.contains('absolute') && !node.querySelector('form'))) {
              // IGNORAR: estos son elementos internos del modal, no el modal completo
              console.log('🚫 IGNORANDO elemento interno del modal:', node.id || node.className);
              return; // No procesar elementos internos
            }
            // Verificar específicamente por ID y clase de modales reales
            else if (node.id === 'edp-modal') {
              modals.push(node);
            } else if (node.classList?.contains('kanban-card-modal')) {
              modals.push(node);
            } else if (node.id === 'modal-contextual-form') {
              modals.push(node);
            } else if (node.querySelector) {
              // Buscar dentro del nodo SOLO modales específicos
              const edpModal = node.querySelector('#edp-modal');
              const contextualModal = node.querySelector('#modal-contextual-form');
              const kanbanModals = node.querySelectorAll('.kanban-card-modal');
              
              // BUSCAR el overlay completo que contiene el form contextual
              const contextualOverlay = node.querySelector('div.fixed.inset-0[class*="bg-black"] #modal-contextual-form') ? 
                                       node.querySelector('div.fixed.inset-0[class*="bg-black"]') : null;
              
              if (edpModal) modals.push(edpModal);
              if (contextualModal) modals.push(contextualModal);
              if (contextualOverlay) {
                console.log('🎯 Overlay contextual encontrado dentro del nodo:', contextualOverlay.className);
                modals.push(contextualOverlay);
              }
              modals.push(...kanbanModals);
            }
            
            modals.forEach(modal => {
              // Doble verificación para asegurar que NO es el contenedor de fullscreen
              if (modal.id === 'kanban-fullscreen-container' || 
                  modal.classList?.contains('kanban-fullscreen')) {
                return;
              }
              
              // Verificar que el modal tiene contenido real
              const hasContent = modal.innerHTML.trim().length > 50 && 
                                (modal.querySelector('input, textarea, button, .modal-content, .modal-body, form, select') ||
                                 modal.textContent.trim().length > 20);
              
              // VERIFICACIÓN ESPECIAL para overlays contextuales del kanban
              const isContextualOverlay = modal.classList && 
                                         modal.classList.contains('fixed') && 
                                         modal.classList.contains('inset-0') &&
                                         modal.querySelector('#modal-contextual-form') &&
                                         modal.querySelector('button'); // Debe tener botones
              
              // IGNORAR elementos que claramente son internos del modal (títulos, etc.)
              if (modal.id === 'modalTitle' || 
                  modal.className === 'modalTitle' ||
                  (modal.classList && modal.classList.contains('absolute') && 
                   !modal.querySelector('#modal-contextual-form') && 
                   !modal.querySelector('button'))) {
                console.log('🚫 IGNORANDO elemento interno del modal:', modal.id || modal.className);
                return; // Skip este elemento
              }
              
              if (isContextualOverlay) {
                console.log('✅ OVERLAY CONTEXTUAL COMPLETO detectado con form y botones');
                console.log('Contenido del overlay (primeros 500 chars):', modal.innerHTML.substring(0, 500));
                
                // ESPERAR a que el contenido se renderice COMPLETAMENTE
                const waitForCompleteContent = (attempts = 0, maxAttempts = 10) => {
                  const form = modal.querySelector('#modal-contextual-form');
                  const buttons = modal.querySelectorAll('button');
                  const inputs = modal.querySelectorAll('input');
                  const title = modal.querySelector('h3');
                  
                  // Verificar que el contenido esté COMPLETO - CRITERIOS MÁS FLEXIBLES
                  const hasTitle = title && title.textContent.trim().length > 0;
                  const hasForm = form && form.innerHTML.trim().length > 50; // Reducido de 100 a 50
                  const hasButtons = buttons.length >= 1; // Reducido de 2 a 1 (al menos 1 botón)
                  const hasInputs = inputs.length >= 0; // Cambiado a 0 (no requiere inputs obligatorios)
                  
                  // CRITERIO MÁS PERMISIVO: Si tiene título Y (form O botones), es suficiente
                  const isContentComplete = hasTitle && (hasForm || hasButtons);
                  
                  console.log(`🔍 Verificando contenido completo (intento ${attempts + 1}/${maxAttempts}):`);
                  console.log(`- Título: ${hasTitle ? '✅' : '❌'} "${title ? title.textContent.trim() : 'NO ENCONTRADO'}"`);
                  console.log(`- Form completo: ${hasForm ? '✅' : '❌'} (${form ? form.innerHTML.length : 0} chars)`);
                  console.log(`- Botones: ${hasButtons ? '✅' : '❌'} (${buttons.length} encontrados)`);
                  console.log(`- Inputs: ${hasInputs ? '✅' : '❌'} (${inputs.length} encontrados)`);
                  console.log(`- CRITERIO CUMPLIDO: ${isContentComplete ? '✅ SÍ' : '❌ NO'} (Título + (Form O Botones))`);
                  
                  if (isContentComplete) {
                    console.log('🎯 CONTENIDO SUFICIENTE DETECTADO - Aplicando ajustes ahora');
                    buttons.forEach((btn, i) => {
                      console.log(`  Botón ${i + 1}: "${btn.textContent.trim()}" (ID: ${btn.id})`);
                    });
                    return true; // Contenido suficiente
                  } else if (attempts < maxAttempts) {
                    console.log(`⏳ Contenido insuficiente, esperando más renderizado...`);
                    setTimeout(() => waitForCompleteContent(attempts + 1, maxAttempts), 200);
                    return false; // Seguir esperando
                  } else {
                    console.log('⚠️ Tiempo agotado esperando contenido, aplicando ajustes de todas formas');
                    return true; // Timeout, aplicar de todos modos
                  }
                };
                
                // Solo continuar si el contenido está completo
                if (!waitForCompleteContent()) {
                  return; // Salir y esperar a que waitForCompleteContent llame a los ajustes
                }
              }
              
              if (!modal.hasAttribute('data-fullscreen-adjusted') && (hasContent || isContextualOverlay)) {
                console.log('Modal real específico detectado por observer:', modal.id || modal.className, 'Contenido length:', modal.innerHTML.length);
                
                // Función para aplicar ajustes (se puede llamar desde waitForCompleteContent también)
                const applyModalAdjustments = () => {
                  // Marcar inmediatamente para evitar procesamiento duplicado
                  modal.setAttribute('data-fullscreen-adjusted', 'true');
                  modal.setAttribute('data-processed-by-main-observer', 'true');
                  
                  // DESACTIVAR temporalmente el observer global para evitar duplicados
                  if (window.globalModalObserver) {
                    window.globalModalObserver.disconnect();
                    console.log('Observer global desactivado temporalmente para evitar duplicados');
                  }
                  
                  // Aplicar ajustes con múltiples intentos y más tiempo
                  setTimeout(() => {
                    console.log('Primer intento de ajuste modal...');
                    adjustModalZIndex();
                    forceModalVisible();
                    setupModalCloseDetector();
                  }, 100);
                  
                  setTimeout(() => {
                    console.log('Segundo intento de ajuste modal...');
                    adjustModalZIndex();
                  }, 300);
                  
                  setTimeout(() => {
                    console.log('Tercer intento de ajuste modal...');
                    adjustModalZIndex();
                  }, 600);
                  
                  setTimeout(() => {
                    console.log('Cuarto intento de ajuste modal...');
                    adjustModalZIndex();
                    
                    // Reactivar observer global después del procesamiento
                    setTimeout(() => {
                      if (!window.globalModalObserver) {
                        setupGlobalModalDetection();
                        console.log('Observer global reactivado');
                      }
                    }, 1000);
                  }, 1000);
                };
                
                // Para modales contextuales, modificar waitForCompleteContent para aplicar ajustes
                if (isContextualOverlay) {
                  // Redefinir waitForCompleteContent para aplicar ajustes cuando esté listo
                  const waitForCompleteContent = (attempts = 0, maxAttempts = 10) => {
                    const form = modal.querySelector('#modal-contextual-form');
                    const buttons = modal.querySelectorAll('button');
                    const inputs = modal.querySelectorAll('input');
                    const title = modal.querySelector('h3');
                    
                    // Verificar que el contenido esté SUFICIENTE - CRITERIOS FLEXIBLES
                    const hasTitle = title && title.textContent.trim().length > 0;
                    const hasForm = form && form.innerHTML.trim().length > 50;
                    const hasButtons = buttons.length >= 1;
                    const hasInputs = inputs.length >= 0;
                    
                    // CRITERIO PERMISIVO: Título + (Form O Botones)
                    const isContentComplete = hasTitle && (hasForm || hasButtons);
                    
                    console.log(`🔍 Re-verificando contenido completo (intento ${attempts + 1}/${maxAttempts}):`);
                    console.log(`- Título: ${hasTitle ? '✅' : '❌'} "${title ? title.textContent.trim() : 'NO ENCONTRADO'}"`);
                    console.log(`- Form completo: ${hasForm ? '✅' : '❌'} (${form ? form.innerHTML.length : 0} chars)`);
                    console.log(`- Botones: ${hasButtons ? '✅' : '❌'} (${buttons.length} encontrados)`);
                    console.log(`- Inputs: ${hasInputs ? '✅' : '❌'} (${inputs.length} encontrados)`);
                    console.log(`- CRITERIO CUMPLIDO: ${isContentComplete ? '✅ SÍ' : '❌ NO'} (Título + (Form O Botones))`);
                    
                    if (isContentComplete) {
                      console.log('🎯 CONTENIDO SUFICIENTE DETECTADO - Aplicando ajustes ahora');
                      buttons.forEach((btn, i) => {
                        console.log(`  Botón ${i + 1}: "${btn.textContent.trim()}" (ID: ${btn.id})`);
                      });
                      applyModalAdjustments(); // APLICAR AJUSTES AQUÍ
                      return true;
                    } else if (attempts < maxAttempts) {
                      console.log(`⏳ Contenido insuficiente, esperando más renderizado...`);
                      setTimeout(() => waitForCompleteContent(attempts + 1, maxAttempts), 200);
                      return false;
                    } else {
                      console.log('⚠️ Tiempo agotado esperando contenido, aplicando ajustes de todas formas');
                      applyModalAdjustments(); // APLICAR AJUSTES AQUÍ también
                      return true;
                    }
                  };
                  
                  waitForCompleteContent(); // Iniciar verificación
                } else {
                  // Para modales normales (como tabla), aplicar ajustes inmediatamente
                  applyModalAdjustments();
                }
              }
            });
          }
        });
        
        // También verificar si ya existe algún modal específico (por si se creó antes)
        const existingSpecificModals = [
          document.getElementById('edp-modal'),
          document.getElementById('modal-contextual-form'),
          ...document.querySelectorAll('.kanban-card-modal')
        ].filter(modal => modal !== null);
        
        existingSpecificModals.forEach(modal => {
          const hasContent = modal.innerHTML.trim().length > 0 && 
                            modal.querySelector('input, textarea, button, .modal-content, .modal-body, form');
          
          if (modal.offsetParent && !modal.hasAttribute('data-fullscreen-adjusted') && hasContent) {
            console.log('Modal específico existente detectado:', modal.id || modal.className);
            adjustModalZIndex();
            modal.setAttribute('data-fullscreen-adjusted', 'true');
            
            setTimeout(() => {
              forceModalVisible();
              setupModalCloseDetector();
            }, 10);
          }
        });
      }
    });
  });
  
  // Observar cambios en el body para detectar cuando se agrega cualquier modal
  modalObserver.observe(document.body, { childList: true, subtree: true });
  
  // Guardar referencia del observer para limpiarlo después
  fullscreenContainer.modalObserver = modalObserver;

  // Agregar event listeners para los botones de toggle en fullscreen
  const fullscreenToggleLista = fullscreenContainer.querySelector('#fullscreen-toggle-lista');
  const fullscreenToggleKanban = fullscreenContainer.querySelector('#fullscreen-toggle-kanban');
  const fullscreenExitBtn = fullscreenContainer.querySelector('.fullscreen-exit-btn');
  
  if (fullscreenToggleLista) {
    fullscreenToggleLista.addEventListener('click', function() {
      if (currentView !== 'tabla') {
        switchViewInFullscreen('tabla');
      }
    });
  }
  
  if (fullscreenToggleKanban) {
    fullscreenToggleKanban.addEventListener('click', function() {
      if (currentView !== 'kanban') {
        switchViewInFullscreen('kanban');
      }
    });
  }
  
  if (fullscreenExitBtn) {
    fullscreenExitBtn.addEventListener('click', function() {
      exitFullscreen();
    });
  }

  // Actualizar botón principal
  const fullscreenIcon = document.getElementById('fullscreen-icon');
  const fullscreenText = document.getElementById('fullscreen-text');
  
  if (fullscreenIcon) {
    fullscreenIcon.innerHTML = `
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9V4.5M9 9H4.5M9 9L3.5 3.5M15 9h4.5M15 9V4.5M15 9l5.5-5.5M9 15v4.5M9 15H4.5M9 15l-5.5 5.5M15 15h4.5M15 15v4.5m0-4.5l5.5 5.5" />
    `;
  }
  if (fullscreenText) {
    fullscreenText.textContent = 'Salir';
  }

  // NO agregar overflow hidden al body para permitir scroll natural
  // document.body.style.overflow = 'hidden'; // REMOVIDO

  // Focus en el contenedor para keyboard navigation
  fullscreenContainer.focus();

  console.log(`Vista completa activada para: ${currentView}`);
}

function exitFullscreen() {
  if (!isFullscreen) return;

  const fullscreenContainer = document.getElementById('kanban-fullscreen-container');
  const targetElement = currentView === 'kanban' ? 
    document.getElementById('kanban-board') : 
    document.getElementById('tabla-view');
  
  if (!fullscreenContainer || !targetElement) return;

  // Agregar animación de salida
  fullscreenContainer.classList.add('kanban-fullscreen-exit');

  setTimeout(() => {
    // Restaurar elemento a su posición original
    if (originalNextSibling) {
      originalParent.insertBefore(targetElement, originalNextSibling);
    } else {
      originalParent.appendChild(targetElement);
    }

    // Limpiar observer del modal principal
    if (fullscreenContainer.modalObserver) {
      fullscreenContainer.modalObserver.disconnect();
    }
    
    // Limpiar observers específicos de kanban y tabla
    const kanbanContainer = document.getElementById('kanban-board');
    if (kanbanContainer && kanbanContainer.kanbanModalObserver) {
      kanbanContainer.kanbanModalObserver.disconnect();
      kanbanContainer.kanbanModalObserver = null;
    }
    
    const tablaView = document.getElementById('tabla-view');
    if (tablaView && tablaView.tableModalObserver) {
      tablaView.tableModalObserver.disconnect();
      tablaView.tableModalObserver = null;
    }
    
    // Limpiar detector de cierre de modal
    if (window.modalCloseObserver) {
      window.modalCloseObserver.disconnect();
      window.modalCloseObserver = null;
    }
    
    // Limpiar observer global de modales
    if (window.globalModalObserver) {
      window.globalModalObserver.disconnect();
      window.globalModalObserver = null;
    }
    
    // Limpiar monitor de visibilidad
    if (window.fullscreenVisibilityMonitor) {
      clearInterval(window.fullscreenVisibilityMonitor);
      window.fullscreenVisibilityMonitor = null;
    }

    // Remover contenedor fullscreen
    fullscreenContainer.remove();

    // Restaurar z-index del modal si existe
    restoreModalZIndex();
    
    // Remover el estilo CSS forzado
    const forceModalStyle = document.getElementById('force-modal-style');
    if (forceModalStyle) {
      forceModalStyle.remove();
    }
    
    // Remover clase del body si existe
    document.body.classList.remove('modal-open');

    // Actualizar estado
    isFullscreen = false;
    
    // Restaurar función original del modal contextual si fue interceptada
    if (window.originalMostrarModalContextual) {
      mostrarModalContextual = window.originalMostrarModalContextual;
      window.mostrarModalContextual = window.originalMostrarModalContextual;
      console.log('Función original mostrarModalContextual restaurada globalmente');
    }
    
    // Limpiar variables de estado del modal - SOLO si NO estamos esperando regresar al fullscreen
    console.log('🔄 exitFullscreen - Estado actual:', { shouldReturnToFullscreen, pendingModalData: !!pendingModalData });
    
    if (!shouldReturnToFullscreen) {
      console.log('✅ Limpiando variables porque NO se debe regresar al fullscreen');
      pendingModalData = null;
    } else {
      console.log('⚠️ MANTENIENDO variables porque SÍ se debe regresar al fullscreen');
    }
    
    // NO resetear shouldReturnToFullscreen aquí porque podemos estar saliendo temporalmente para mostrar un modal

    // Restaurar botón
    const fullscreenIcon = document.getElementById('fullscreen-icon');
    const fullscreenText = document.getElementById('fullscreen-text');
    
    if (fullscreenIcon) {
      fullscreenIcon.innerHTML = `
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
      `;
    }
    if (fullscreenText) {
      fullscreenText.textContent = 'Vista Completa';
    }

    console.log(`Vista completa desactivada para: ${currentView} - Event listeners originales preservados`);
  }, 300);
}

// Inicialización cuando el DOM esté listo
function initFullscreenKanban() {
  const fullscreenToggleBtn = document.getElementById('fullscreen-toggle-btn');
  
  // Event listeners
  if (fullscreenToggleBtn) {
    fullscreenToggleBtn.addEventListener('click', function() {
      if (isFullscreen) {
        exitFullscreen();
      } else {
        enterFullscreen();
      }
    });
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', function(e) {
    // ESC para salir de fullscreen
    if (e.key === 'Escape' && isFullscreen) {
      e.preventDefault();
      exitFullscreen();
    }
    
    // F11 o Ctrl+Shift+F para toggle fullscreen
    if ((e.key === 'F11' || (e.ctrlKey && e.shiftKey && e.key === 'F')) && 
        (document.getElementById('kanban-board') || document.getElementById('tabla-view'))) {
      e.preventDefault();
      if (isFullscreen) {
        exitFullscreen();
      } else {
        enterFullscreen();
      }
    }
  });

  // Función global para salir de fullscreen (usada por el botón)
  window.exitFullscreen = exitFullscreen;
  
  // Configurar detección automática de modales cuando estemos en fullscreen
  setupGlobalModalDetection();
  
  console.log('Fullscreen Kanban Controller inicializado');
}

// Función para configurar detección global de modales
function setupGlobalModalDetection() {
  // Observer global para detectar cualquier modal que se abra mientras estamos en fullscreen
  const globalModalObserver = new MutationObserver(function(mutations) {
    if (!isFullscreen) return; // Solo actuar si estamos en fullscreen
    
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(function(node) {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // EXCLUIR completamente el contenedor de fullscreen y sus elementos
            if (node.id === 'kanban-fullscreen-container' || 
                node.classList?.contains('kanban-fullscreen') ||
                node.querySelector?.('#kanban-fullscreen-container')) {
              return; // Ignorar completamente el contenedor de fullscreen
            }
            
            // Buscar modales en el nodo agregado
            let foundModals = [];
            
            // Diferentes patrones de modales - SIN referencias Tailwind específicas
            const modalSelectors = [
              '#edp-modal',
              '.kanban-card-modal', 
              '[id*="modal"]:not(#kanban-fullscreen-container)',
              '.modal:not(.kanban-fullscreen)',
              '[role="dialog"]',
              '[aria-modal="true"]',
              'div[class*="fixed"]:not(.kanban-fullscreen)', // Modales con position fixed
              'div[class*="inset-0"]:not(.kanban-fullscreen)', // Modales fullscreen
              '.modal-overlay',
              '#modal-contextual-form'
            ];
            
            modalSelectors.forEach(selector => {
              try {
                if (node.matches && node.matches(selector)) {
                  foundModals.push(node);
                } else if (node.querySelector) {
                  const elements = node.querySelectorAll(selector);
                  foundModals.push(...elements);
                }
              } catch (e) {
                // Ignorar errores de selector
              }
            });
            
        // También verificar si el nodo mismo es un overlay o backdrop - PERO NO el fullscreen
        if (node.classList && !node.classList.contains('kanban-fullscreen') && (
            node.classList.contains('fixed') || 
            node.classList.contains('modal-overlay') ||
            Array.from(node.classList).some(cls => cls.includes('inset-0'))
          )) {
          // SOLO agregar si tiene el contenido del modal contextual
          if (node.querySelector('#modal-contextual-form') && node.querySelector('button')) {
            console.log('🎯 Overlay del modal contextual detectado como nodo principal:', node.className);
            foundModals.push(node);
          } else {
            console.log('🚫 IGNORANDO overlay sin contenido completo:', node.className);
          }
        }
        
        // Procesar modales encontrados - con doble verificación
        foundModals.forEach(modal => {
          // Doble verificación para asegurar que NO es el contenedor de fullscreen
          if (modal.id === 'kanban-fullscreen-container' || 
              modal.classList?.contains('kanban-fullscreen')) {
            return;
          }
          
          // FILTRAR elementos internos del modal que no son el modal completo
          if (modal.id === 'modalTitle' || 
              modal.className === 'modalTitle' ||
              (modal.classList && modal.classList.contains('absolute') && 
               !modal.querySelector('#modal-contextual-form') && 
               !modal.querySelector('button'))) {
            console.log('🚫 IGNORANDO por observer global elemento interno:', modal.id || modal.className);
            return; // Skip elementos internos
          }
          
          // NO procesar modales que ya fueron procesados por el observer principal
          if (modal.hasAttribute('data-processed-by-main-observer') || 
              modal.hasAttribute('data-fullscreen-adjusted')) {
            return;
          }
              
              // Verificar si el modal está visible o se está mostrando
              const isVisible = modal.offsetParent !== null || 
                               modal.style.display === 'block' || 
                               modal.style.display === 'flex' ||
                               window.getComputedStyle(modal).display !== 'none';
              
              if (isVisible) {
                console.log('Modal detectado automáticamente por observer global:', modal.id || modal.className, 'Clases:', Array.from(modal.classList || []));
                
                // Marcar para evitar procesamiento duplicado
                modal.setAttribute('data-fullscreen-adjusted', 'true');
                modal.setAttribute('data-processed-by-global-observer', 'true');
                
                // Aplicar ajustes de z-index con delay diferente según el tipo de modal
                const isKanbanModal = modal.classList.contains('fixed') || 
                                    Array.from(modal.classList).some(cls => cls.includes('inset-0'));
                
                const delay = isKanbanModal ? 50 : 10;
                
                setTimeout(() => {
                  adjustModalZIndex();
                  forceModalVisible();
                  setupModalCloseDetector();
                  setupFullscreenVisibilityMonitor();
                }, delay);
                
                // Múltiples intentos con tiempos ajustados para modales del kanban
                setTimeout(() => adjustModalZIndex(), delay + 100);
                setTimeout(() => adjustModalZIndex(), delay + 300);
                setTimeout(() => adjustModalZIndex(), delay + 500);
              }
            });
          }
        });
      }
      
      // También detectar cambios en atributos que pueden mostrar/ocultar modales
      if (mutation.type === 'attributes') {
        const target = mutation.target;
        
        // EXCLUIR completamente el contenedor de fullscreen
        if (target.id === 'kanban-fullscreen-container' || 
            target.classList?.contains('kanban-fullscreen')) {
          return; // Ignorar cambios en el contenedor de fullscreen
        }
        
        if (target && (target.id?.includes('modal') || 
                      Array.from(target.classList || []).some(cls => cls.includes('modal')) ||
                      target.classList?.contains('fixed') ||
                      Array.from(target.classList || []).some(cls => cls.includes('inset-0')))) {
          
          // Si el modal se hizo visible
          const isVisible = target.offsetParent !== null || 
                           target.style.display === 'block' || 
                           target.style.display === 'flex' ||
                           window.getComputedStyle(target).display !== 'none';
          
          if (isVisible && !target.hasAttribute('data-fullscreen-processed') && 
              !target.hasAttribute('data-processed-by-main-observer')) {
            target.setAttribute('data-fullscreen-processed', 'true');
            target.setAttribute('data-processed-by-global-observer', 'true');
            
            console.log('Modal detectado por cambio de atributo:', target.id || target.className);
            
            setTimeout(() => {
              adjustModalZIndex();
              forceModalVisible();
              setupModalCloseDetector();
              setupFullscreenVisibilityMonitor();
            }, 100);
          }
        }
      }
    });
  });
  
  // Observar todo el documento
  globalModalObserver.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['style', 'class', 'aria-hidden', 'data-show', 'display']
  });
  
  // Guardar referencia global
  window.globalModalObserver = globalModalObserver;
  
  console.log('Detección global de modales configurada (sin dependencias de Tailwind)');
}

// Función para monitorear continuamente que la vista completa permanezca visible
function setupFullscreenVisibilityMonitor() {
  // Limpiar monitor anterior si existe
  if (window.fullscreenVisibilityMonitor) {
    clearInterval(window.fullscreenVisibilityMonitor);
  }
  
  window.fullscreenVisibilityMonitor = setInterval(() => {
    if (!isFullscreen) {
      clearInterval(window.fullscreenVisibilityMonitor);
      window.fullscreenVisibilityMonitor = null;
      return;
    }
    
    const fullscreenContainer = document.getElementById('kanban-fullscreen-container');
    if (fullscreenContainer) {
      const computedStyle = window.getComputedStyle(fullscreenContainer);
      
      // Verificar si la vista completa se ha ocultado o perdido z-index
      if (computedStyle.display === 'none' || 
          computedStyle.visibility === 'hidden' || 
          computedStyle.opacity === '0' ||
          parseInt(computedStyle.zIndex) < 10000) {
        
        console.log('DETECTADO: Vista completa se ocultó, restaurando...');
        
        // FORZAR que la vista completa sea visible con z-index intermedio
        fullscreenContainer.style.setProperty('z-index', '10000', 'important');
        fullscreenContainer.style.setProperty('display', 'block', 'important');
        fullscreenContainer.style.setProperty('visibility', 'visible', 'important');
        fullscreenContainer.style.setProperty('opacity', '1', 'important');
        fullscreenContainer.style.setProperty('position', 'fixed', 'important');
        fullscreenContainer.style.setProperty('top', '0', 'important');
        fullscreenContainer.style.setProperty('left', '0', 'important');
        fullscreenContainer.style.setProperty('width', '100%', 'important');
        fullscreenContainer.style.setProperty('height', '100%', 'important');
        fullscreenContainer.style.setProperty('pointer-events', 'auto', 'important');
        
        console.log('Vista completa RESTAURADA por el monitor con z-index intermedio (10000)');
      }
    }
    
    // Si no hay modales abiertos, detener el monitor
    const openModals = document.querySelectorAll('#edp-modal, .kanban-card-modal, [id*="modal"]:not(#kanban-fullscreen-container), [class*="modal"]:not(.kanban-fullscreen)');
    const hasVisibleModal = Array.from(openModals).some(modal => modal.offsetParent !== null || modal.style.display === 'block');
    
    if (!hasVisibleModal) {
      clearInterval(window.fullscreenVisibilityMonitor);
      window.fullscreenVisibilityMonitor = null;
      console.log('Monitor de visibilidad detenido - no hay modales abiertos');
    }
  }, 250); // Verificar cada 250ms
  
  console.log('Monitor de visibilidad de vista completa iniciado');
}

// Auto-inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initFullscreenKanban);
} else {
  initFullscreenKanban();
}
