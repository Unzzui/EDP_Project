

      // === FUNCIONES DE ATENCIÓN INMEDIATA SIMPLIFICADAS ===
      function initializeCriticalPendingSection() {
        const allRows = Array.from(document.querySelectorAll('#edp-table tbody tr'));

        // Filtrar EDPs pendientes (revisión y enviado)
        const pendingRows = allRows.filter(row => {
          const estado = (row.getAttribute('data-estado') || '').toLowerCase();
          return estado === 'revisión' || estado === 'enviado';
        });

        // Estadísticas
        const criticalCount = pendingRows.filter(row => {
          const dias = parseInt(row.getAttribute('data-dias')) || 0;
          return dias > 30;
        }).length;

        const revisionCount = pendingRows.filter(row =>
          (row.getAttribute('data-estado') || '').toLowerCase() === 'revisión'
        ).length;

        const sentCount = pendingRows.filter(row =>
          (row.getAttribute('data-estado') || '').toLowerCase() === 'enviado'
        ).length;

        // Si no hay EDPs críticos, ocultar la sección
        if (criticalCount === 0 && pendingRows.length === 0) {
          const criticalSection = document.getElementById('critical-alert-section');
          if (criticalSection) {
            criticalSection.style.display = 'none';
          }
          return;
        }

        // Actualizar resumen de alerta
        const alertSummary = document.getElementById('alert-summary');
        if (alertSummary) {
          if (criticalCount > 0) {
            alertSummary.textContent = `${criticalCount} EDPs con +30 días de espera`;
            alertSummary.className = 'text-[color:var(--accent-red)] ml-2 font-medium';
          } else {
            alertSummary.textContent = `${pendingRows.length} EDPs pendientes de atención`;
            alertSummary.className = 'text-[color:var(--accent-amber)] ml-2 font-medium';
          }
        }

        // Generar mini badges
        generateQuickStats(revisionCount, sentCount, criticalCount);

        // EDPs más críticos (tomar solo los primeros 4 para el detalle)
        const criticalEdps = pendingRows
          .sort((a, b) => {
            const diasA = parseInt(a.getAttribute('data-dias')) || 0;
            const diasB = parseInt(b.getAttribute('data-dias')) || 0;
            return diasB - diasA;
          })
          .slice(0, 4);

        // Generar cards simplificadas
        generateSimpleCriticalCards(criticalEdps);

        // Event listeners
        setupCriticalAlertEvents();
      }

      function generateQuickStats(revisionCount, sentCount, criticalCount) {
        const container = document.getElementById('quick-stats');
        if (!container) {
          console.warn('Element with ID "quick-stats" not found');
          return;
        }
        
        container.innerHTML = '';

        const stats = [
          { count: revisionCount, label: 'Revisión', color: 'bg-[color:var(--accent-blue)]' },
          { count: sentCount, label: 'Enviado', color: 'bg-[color:var(--accent-purple)]' },
          { count: criticalCount, label: '+30d', color: 'bg-[color:var(--accent-red)]' }
        ];

        stats.forEach(stat => {
          if (stat.count > 0) {
            const badge = document.createElement('span');
            badge.className = `inline-flex items-center px-1.5 py-0.5 md:px-2 md:py-1 rounded-full text-xs font-medium text-white ${stat.color} whitespace-nowrap`;
            badge.textContent = `${stat.count} ${stat.label}`;
            container.appendChild(badge);
          }
        });
      }

      function setupCriticalAlertEvents() {
        // Toggle para expandir detalles
        const expandBtn = document.getElementById('expand-critical-alert');
        if (expandBtn) {
          expandBtn.addEventListener('click', () => {
            const details = document.getElementById('critical-details');
            const button = document.getElementById('expand-critical-alert');

            if (details && details.classList.contains('hidden')) {
              details.classList.remove('hidden');
              if (button) button.textContent = 'Ocultar detalles';
            } else if (details) {
              details.classList.add('hidden');
              if (button) button.textContent = 'Ver detalles';
            }
          });
        }

        // Botón para ocultar toda la alerta
        const hideBtn = document.getElementById('hide-critical-alert');
        if (hideBtn) {
          hideBtn.addEventListener('click', () => {
            const alertSection = document.getElementById('critical-alert-section');
            if (alertSection) {
              alertSection.style.display = 'none';
              // Guardar preferencia en localStorage
              localStorage.setItem('hideCriticalAlert', 'true');
            }
          });
        }

        // Event listener para el botón "Ver todos los pendientes"
        const showAllBtn = document.getElementById('show-all-pending');
        if (showAllBtn) {
          showAllBtn.addEventListener('click', () => {
            const btnPendientes = document.getElementById('filter-pendientes');
            if (btnPendientes) {
              btnPendientes.click();
            }

            // Scroll suave hacia la tabla
            const table = document.getElementById('edp-table');
            if (table) {
              table.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
              });
            }
          });
        }

        // Verificar si el usuario había ocultado la alerta anteriormente
        if (localStorage.getItem('hideCriticalAlert') === 'true') {
          const alertSection = document.getElementById('critical-alert-section');
          const restoreBtn = document.getElementById('restore-alert-btn');
          if (alertSection) alertSection.style.display = 'none';
          if (restoreBtn) restoreBtn.classList.remove('hidden');
        }

        // Botón para restaurar la alerta
        const restoreBtn = document.getElementById('restore-alert-btn');
        if (restoreBtn) {
          restoreBtn.addEventListener('click', () => {
            const alertSection = document.getElementById('critical-alert-section');
            const restoreButton = document.getElementById('restore-alert-btn');
            if (alertSection) alertSection.style.display = 'block';
            if (restoreButton) restoreButton.classList.add('hidden');
            localStorage.removeItem('hideCriticalAlert');
          });
        }
      }

      function generateSimpleCriticalCards(criticalEdps) {
        const container = document.getElementById('critical-edps-container');
        if (!container) {
          console.warn('Element with ID "critical-edps-container" not found');
          return;
        }
        
        container.innerHTML = '';

        if (criticalEdps.length === 0) {
          container.innerHTML = `
            <div class="col-span-full text-center py-4">
              <span class="text-[color:var(--text-secondary)] text-sm">No hay EDPs críticos para mostrar</span>
            </div>
          `;
          return;
        }

        criticalEdps.forEach(row => {
          const proyecto = row.getAttribute('data-proyecto') || '-';
          const edpNumber = row.getAttribute('data-edp') || '-';
          const jefe_proyecto = row.getAttribute('data-jefe') || '-';
          const estado = row.getAttribute('data-estado') || '-';
          const dias = parseInt(row.getAttribute('data-dias')) || 0;
          const monto = parseFloat(row.getAttribute('data-monto-aprobado')) || 0;

          // Determinar color según días
          let indicatorColor = 'bg-[color:var(--accent-amber)]';
          if (dias > 45) {
            indicatorColor = 'bg-[color:var(--accent-red)]';
          } else if (dias > 30) {
            indicatorColor = 'bg-[color:var(--accent-orange)]';
          }

          const card = document.createElement('div');
          card.className = `critical-edp-card bg-[color:var(--bg-card-hover)] border border-[color:var(--border-color-subtle)] rounded-lg p-3 hover:shadow-md transition-all cursor-pointer`;

          card.innerHTML = `
            <div class="flex items-start space-x-3">
              <div class="w-3 h-3 rounded-full ${indicatorColor} mt-1 flex-shrink-0"></div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm font-medium text-[color:var(--text-primary)] truncate pr-2">EDP #${edpNumber}</span>
                  <span class="text-xs text-[color:var(--accent-red)] font-bold whitespace-nowrap">${dias}d</span>
                </div>
                <div class="flex items-start justify-between">
                  <div class="flex flex-col space-y-1 min-w-0 flex-1 pr-2">
                    <span class="text-xs text-[color:var(--text-secondary)] truncate" title="${proyecto}">📁 ${proyecto}</span>
                    <span class="text-xs text-[color:var(--text-secondary)] truncate" title="${jefe_proyecto}">👤 ${jefe_proyecto}</span>
                  </div>
                  <span class="text-xs px-2 py-1 rounded flex-shrink-0 ${estado === 'revisión' ? 'bg-[color:var(--accent-blue)] text-white' : 'bg-[color:var(--accent-purple)] text-white'} whitespace-nowrap">
                    ${estado}
                  </span>
                </div>
              </div>
            </div>
          `;

          // Hacer la card clickeable para ver detalles
          card.addEventListener('click', () => {
            // Buscar la fila correspondiente en la tabla y hacer clic en ella
            const tableRow = document.querySelector(`#edp-table tbody tr[data-edp="${edpNumber}"]`);
            if (tableRow) {
              tableRow.click();
            }
          });

          container.appendChild(card);
        });
      }

      // Función para mostrar notificaciones toast
  function showToast(message, type = 'info') {
    // Crear elemento toast
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg shadow-lg text-white z-50 animate__animated animate__fadeInUp`;

    // Estilos según el tipo
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

    // Contenido y estructura
    toast.innerHTML = `
      <div class="flex items-center">
        <span class="flex-grow">${message}</span>
        <button class="ml-4 hover:text-gray-300 focus:outline-none" onclick="this.parentElement.parentElement.remove()">
          &times;
        </button>
      </div>
    `;

    // Añadir al DOM
    document.body.appendChild(toast);

    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
      toast.classList.replace('animate__fadeInUp', 'animate__fadeOutDown');
      setTimeout(() => {
        if (document.body.contains(toast)) {
          document.body.removeChild(toast);
        }
      }, 500);
    }, 5000);
  }


  window.addEventListener("DOMContentLoaded", () => {
    console.log("🚀 Table controller JavaScript cargado");
    
    // Aplicamos el filtro correspondiente según el estado seleccionado en el backend
    // IMPORTANTE: No mostramos los filtros automáticamente aquí
    let filterApplied = false;
    // rows will be declared later after table is found

    // IMPORTANTE: Primero limpiamos los estilos de TODOS los botones de filtro para evitar duplicados
    const allFilterButtons = document.querySelectorAll('#filter-all, #filter-criticos, #filter-recientes, #filter-pendientes, #filter-validados');
    console.log(`🔍 Botones de filtro encontrados: ${allFilterButtons.length}`);
    
    allFilterButtons.forEach(btn => {
      btn.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
      btn.classList.add('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
    });

    // Obtener el estado inicial desde un atributo del DOM o localStorage
    const initialFilter = document.body.getAttribute('data-initial-filter') || 'pendientes';
    console.log(`📋 Filtro inicial: ${initialFilter}`);

    // Define essential variables first - but check if table exists
    const detailPagePrefix = '/dashboard/detalle/';
    const table = document.getElementById('edp-table');
    
    // If table doesn't exist, exit early (probably in Kanban mode)
    if (!table) {
      console.log("⚠️ Tabla no encontrada - probablemente en modo Kanban");
      return;
    }
    
    console.log("✅ Tabla encontrada, inicializando controlador");
    
    const tableBody = table.querySelector('tbody');
    const headers = table.querySelectorAll('th.sortable');
    // Declare rows here to be used throughout the function
    const rows = Array.from(tableBody.querySelectorAll('tr'));
    const searchInput = document.getElementById('table-search');
    
    // Intentamos encontrar y activar el botón de filtro correspondiente pero sin expandir los filtros
    if (initialFilter === 'pendientes') {
      const btnPendientes = document.getElementById("filter-pendientes");
      if (btnPendientes) {
        // Simulamos el comportamiento del clic sin ejecutar el evento real
        // para evitar que se muestren los filtros
        btnPendientes.classList.remove('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
        btnPendientes.classList.add('bg-[color:var(--accent-blue)]', 'text-white');

        // Aplicar el filtro directamente a las filas
        rows.forEach(row => {
          const estado = row.getAttribute('data-estado') || '';
          row.classList.toggle('hidden', estado === 'validado' || estado === 'pagado');
        });

        filterApplied = true;
      }
    } else if (initialFilter === 'validado') {
      const btnValidados = document.getElementById("filter-validados");
      if (btnValidados) {
        // Aplicamos estilos sin clic real
        btnValidados.classList.remove('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
        btnValidados.classList.add('bg-[color:var(--accent-blue)]', 'text-white');

        // Aplicar el filtro directamente a las filas
        rows.forEach(row => {
          const estado = (row.getAttribute('data-estado') || '').toLowerCase();
          row.classList.toggle('hidden', estado !== 'validado');
        });

        filterApplied = true;
      }
    } else if (['todos', 'enviado', 'pagado', 'revisión'].includes(initialFilter)) {
      // Filtros que no tienen un botón específico, activamos "todos"
      const btnAll = document.getElementById("filter-all");
      if (btnAll) {
        // Aplicamos estilos sin clic real
        btnAll.classList.remove('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
        btnAll.classList.add('bg-[color:var(--accent-blue)]', 'text-white');

        // Mostrar todas las filas
        rows.forEach(row => { row.classList.remove('hidden'); });

        filterApplied = true;
      }
    }

    // Si no se aplicó ningún filtro específico, usamos 'pendientes' como predeterminado
    if (!filterApplied) {
      if (initialFilter === 'todos') {
        const btnAll = document.getElementById("filter-all");
        if (btnAll) {
          // Aplicamos estilos sin clic real para "todos"
          btnAll.classList.remove('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
          btnAll.classList.add('bg-[color:var(--accent-blue)]', 'text-white');

          // Mostrar todas las filas
          rows.forEach(row => { row.classList.remove('hidden'); });
        }
      } else {
        const btnPendientes = document.getElementById("filter-pendientes");
        if (btnPendientes) {
          // Aplicamos estilos sin clic real para "pendientes" (predeterminado)
          btnPendientes.classList.remove('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
          btnPendientes.classList.add('bg-[color:var(--accent-blue)]', 'text-white');

          // Aplicar el filtro de pendientes (ocultar validados y pagados)
          rows.forEach(row => {
            const estado = row.getAttribute('data-estado') || '';
            row.classList.toggle('hidden', estado === 'validado' || estado === 'pagado');
          });
        }
      }
    }
    const toggleColumnsBtn = document.getElementById('toggle-columns');
    const columnsDropdown = document.getElementById('columns-dropdown');
    const columnCheckboxes = columnsDropdown ? columnsDropdown.querySelectorAll('input[type="checkbox"]') : [];
    const quickFilterButtons = document.querySelectorAll('#filter-all, #filter-criticos, #filter-recientes, #filter-pendientes, #filter-validados');
    const showingCount = document.getElementById('showing-count');
    const exportBtn = document.getElementById('exportar-excel');

    // Inicializar filas filtradas para la paginación
    let filteredRows = rows.filter(row => !row.classList.contains('hidden'));

    // Inicializar la sección de atención inmediata
    initializeCriticalPendingSection();

    // Mostrar en consola el estado del filtro (para depuración)
    console.log("Estado del filtro: " + initialFilter);
        // Add these console logs for debugging

      // Toggle dropdown de columnas
      toggleColumnsBtn.addEventListener('click', () => {
        columnsDropdown.classList.toggle('hidden');
      });

      // Ocultar dropdown al hacer clic fuera de él
      document.addEventListener('click', (event) => {
        if (!toggleColumnsBtn.contains(event.target) && !columnsDropdown.contains(event.target)) {
          columnsDropdown.classList.add('hidden');
        }
      });

      // Manejo de visibilidad de columnas
      columnCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
          const columnName = checkbox.getAttribute('data-column');
          const columnIndex = getColumnIndexByName(columnName);

          if (columnIndex > -1) {
            const cells = table.querySelectorAll(`tr > :nth-child(${columnIndex + 1})`);
            cells.forEach(cell => {
              cell.style.display = checkbox.checked ? '' : 'none';
            });
          }
        });
      });

      // Helper para obtener índice de columna por nombre
      function getColumnIndexByName(name) {
        const headers = Array.from(table.querySelectorAll('thead th'));
        return headers.findIndex(header => {
          const sortAttr = header.getAttribute('data-sort');
          return sortAttr && sortAttr.includes(name);
        });
      }

      // Función de búsqueda en tabla
      searchInput.addEventListener('input', filterTable);

      // Variable global para controlar si los filtros deben permanecer visibles
      window.keepFiltersVisible = false;

      // Filtros rápidos
      quickFilterButtons.forEach(button => {
        button.addEventListener('click', () => {
          // Reiniciar estado de botones
          quickFilterButtons.forEach(btn => {
            btn.classList.remove('bg-[color:var(--accent-blue)]', 'text-white');
            btn.classList.add('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
          });

          // Aplicar estilo al botón seleccionado
          button.classList.remove('bg-[color:var(--bg-card-hover)]', 'text-[color:var(--text-primary)]');
          button.classList.add('bg-[color:var(--accent-blue)]', 'text-white');

          // Verificar si la sección de filtros está visible antes de aplicar el filtro
          const filtersSection = document.getElementById('filters-section');
          const filtersWereVisible = filtersSection ? !filtersSection.classList.contains('hidden') : false;

          // Aplicar filtro según el botón y guardar el estado actual
          if (button.id === 'filter-all') {
            // Para "Todos", mostramos todas las filas
            rows.forEach(row => { row.classList.remove('hidden'); });

            // Actualizar el select de estado en el formulario si existe
            const estadoSelect = document.getElementById('estado');
            if (estadoSelect) {
              estadoSelect.value = 'todos';
            }
          } else if (button.id === 'filter-criticos') {
            // Para "Críticos", filtramos por el atributo data-critico
            rows.forEach(row => {
              const isCritical = row.getAttribute('data-critico') === '1';
              row.classList.toggle('hidden', !isCritical);
            });
          } else if (button.id === 'filter-recientes') {
            // Para "Recientes", filtramos por días menor a 30
            rows.forEach(row => {
              const dias = parseInt(row.getAttribute('data-dias')) || 0;
              row.classList.toggle('hidden', dias > 30);
            });
          } else if (button.id === 'filter-pendientes') {
            // Para "Pendientes", ocultamos estados validado o pagado
            rows.forEach(row => {
              const estado = row.getAttribute('data-estado') || '';
              row.classList.toggle('hidden', estado === 'validado' || estado === 'pagado');
            });

            // Actualizar el select de estado en el formulario si existe
            const estadoSelect = document.getElementById('estado');
            if (estadoSelect) {
              estadoSelect.value = 'pendientes';
            }
          } else if (button.id === 'filter-validados') {
            // Para "Validados", mostramos solo estado validado
            rows.forEach(row => {
              const estado = (row.getAttribute('data-estado') || '').toLowerCase();
              row.classList.toggle('hidden', estado !== 'validado');
            });

            // Actualizar el select de estado en el formulario si existe
            const estadoSelect = document.getElementById('estado');
            if (estadoSelect) {
              estadoSelect.value = 'validado';
            }
          }

          // Mantener los filtros visibles si ya estaban visibles
          if (filtersWereVisible && filtersSection) {
            // Asegurarnos de que los filtros permanezcan visibles
            if (filtersSection.classList.contains('hidden')) {
              // Si se ocultaron por alguna razón, mostrarlos de nuevo
              if (typeof window.toggleFilters === 'function') {
                window.toggleFilters();
              }
            }
          }

          // Usar la función mejorada para actualizar la paginación
          applyFiltersAndUpdatePagination();
        });
      });

      function filterTable() {
        const searchTerm = searchInput.value.toLowerCase();

        rows.forEach(row => {
          const text = row.textContent.toLowerCase();
          const isMatch = text.includes(searchTerm);

          row.classList.toggle('hidden', !isMatch);
        });

        // Usar la función mejorada para actualizar la paginación
        applyFiltersAndUpdatePagination();
      }

      // === PAGINACIÓN ===
      let currentPage = 1;
      let pageSize = 10;
      // filteredRows is already declared above, just update it
      filteredRows = [...rows]; // Filas después de aplicar filtros

      // Elementos de paginación
      const pageSizeSelect = document.getElementById('page-size');
      const prevPageBtn = document.getElementById('prev-page');
      const nextPageBtn = document.getElementById('next-page');
      const pageNumbersContainer = document.getElementById('page-numbers');
      const gotoPageInput = document.getElementById('goto-page');
      const gotoPageBtn = document.getElementById('goto-page-btn');
      const showingFrom = document.getElementById('showing-from');
      const showingTo = document.getElementById('showing-to');
      const totalCount = document.getElementById('total-count');
      const filteredInfo = document.getElementById('filtered-info');
      const originalCount = document.getElementById('original-count');
      
      // Verificar que existen elementos críticos para el funcionamiento
      if (!pageSizeSelect || !pageNumbersContainer) {
        console.warn('⚠️ Elementos de paginación no encontrados, algunas funciones pueden no funcionar');
      }

      function updatePagination() {
        // PRIMERO: Actualizar la lista de filas filtradas ANTES de calcular totales
        filteredRows = rows.filter(row => !row.classList.contains('hidden'));
        
        // CRÍTICO: Verificar que pageSize esté configurado correctamente
        if (!pageSize || pageSize <= 0) {
          pageSize = parseInt(document.getElementById('page-size')?.value) || 10;
          console.warn(`⚠️ pageSize no válido, usando valor por defecto: ${pageSize}`);
        }
        
        // Calcular totales
        const totalPages = Math.ceil(filteredRows.length / pageSize);
        const startIndex = (currentPage - 1) * pageSize;
        const endIndex = Math.min(startIndex + pageSize, filteredRows.length);

        console.log(`📊 Paginación: Página ${currentPage}/${totalPages}, mostrando ${startIndex + 1}-${endIndex} de ${filteredRows.length} filas`);

        // PASO 1: Ocultar TODAS las filas primero (incluyendo las filtradas)
        rows.forEach(row => {
          row.style.display = 'none';
        });

        // PASO 2: Mostrar SOLO las filas de la página actual
        let actuallyShown = 0;
        for (let i = startIndex; i < endIndex && i < filteredRows.length; i++) {
          if (filteredRows[i]) {
            filteredRows[i].style.display = '';
            actuallyShown++;
          }
        }
        
        console.log(`✅ Filas mostradas: ${actuallyShown} (máximo permitido: ${pageSize})`);
        
        // VERIFICACIÓN: Si se muestran más filas de las esperadas, forzar ocultación
        if (actuallyShown > pageSize) {
          console.error(`🚨 ERROR: Se están mostrando ${actuallyShown} filas cuando el máximo es ${pageSize}`);
          // Forzar corrección ocultando las filas extras
          for (let i = startIndex + pageSize; i < endIndex; i++) {
            if (filteredRows[i]) {
              filteredRows[i].style.display = 'none';
            }
          }
        }

        // Actualizar información de registros
        if (showingFrom) showingFrom.textContent = filteredRows.length > 0 ? startIndex + 1 : 0;
        if (showingTo) showingTo.textContent = Math.min(startIndex + pageSize, filteredRows.length);
        if (totalCount) totalCount.textContent = filteredRows.length;

        // Mostrar información de filtrado si es necesario
        if (filteredRows.length < rows.length) {
          if (filteredInfo) filteredInfo.classList.remove('hidden');
          if (originalCount) originalCount.textContent = rows.length;
        } else {
          if (filteredInfo) filteredInfo.classList.add('hidden');
        }

        // Actualizar botones de navegación
        if (prevPageBtn) prevPageBtn.disabled = currentPage <= 1;
        if (nextPageBtn) nextPageBtn.disabled = currentPage >= totalPages;

        // Actualizar números de página
        if (pageNumbersContainer) updatePageNumbers(totalPages);

        // Actualizar input de ir a página si existe
        if (gotoPageInput) {
          gotoPageInput.max = totalPages;
          gotoPageInput.placeholder = currentPage.toString();
        }
      }

      function updatePageNumbers(totalPages) {
        pageNumbersContainer.innerHTML = '';

        if (totalPages <= 1) return;

        const maxVisiblePages = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        // Ajustar si estamos cerca del final
        if (endPage - startPage < maxVisiblePages - 1) {
          startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        // Botón primera página si es necesario
        if (startPage > 1) {
          const firstPageBtn = createPageButton(1, false);
          pageNumbersContainer.appendChild(firstPageBtn);

          if (startPage > 2) {
            const dots = document.createElement('span');
            dots.textContent = '...';
            dots.className = 'px-2 py-1 text-xs text-[color:var(--text-secondary)]';
            pageNumbersContainer.appendChild(dots);
          }
        }

        // Números de página visibles
        for (let i = startPage; i <= endPage; i++) {
          const pageBtn = createPageButton(i, i === currentPage);
          pageNumbersContainer.appendChild(pageBtn);
        }

        // Botón última página si es necesario
        if (endPage < totalPages) {
          if (endPage < totalPages - 1) {
            const dots = document.createElement('span');
            dots.textContent = '...';
            dots.className = 'px-2 py-1 text-xs text-[color:var(--text-secondary)]';
            pageNumbersContainer.appendChild(dots);
          }

          const lastPageBtn = createPageButton(totalPages, false);
          pageNumbersContainer.appendChild(lastPageBtn);
        }
      }

      function createPageButton(pageNum, isActive) {
        const button = document.createElement('button');
        button.textContent = pageNum;
        button.className = `px-3 py-1 text-xs border rounded transition-colors ${
          isActive
            ? 'bg-[color:var(--accent-blue)] text-white border-[color:var(--accent-blue)]'
            : 'bg-[color:var(--bg-card)] text-[color:var(--text-primary)] border-[color:var(--border-color)] hover:bg-[color:var(--bg-highlight)]'
        }`;

        button.addEventListener('click', () => goToPage(pageNum));
        return button;
      }

      function goToPage(pageNum) {
        const totalPages = Math.ceil(filteredRows.length / pageSize);
        if (pageNum >= 1 && pageNum <= totalPages) {
          currentPage = pageNum;
          updatePagination();
        }
      }

      function applyFiltersAndUpdatePagination() {
        // Recopilar filas visibles (no ocultas por filtros)
        filteredRows = rows.filter(row => !row.classList.contains('hidden'));

        // Resetear a la primera página si no hay elementos en la página actual
        const totalPages = Math.ceil(filteredRows.length / pageSize);
        if (currentPage > totalPages && totalPages > 0) {
          currentPage = totalPages;
        } else if (filteredRows.length > 0 && currentPage < 1) {
          currentPage = 1;
        }

        // Actualizar paginación
        updatePagination();
      }

      function applyInitialFilter(filterType) {
        console.log(`🎯 Aplicando filtro inicial: ${filterType}`);
        
        rows.forEach(row => {
          const estado = row.getAttribute('data-estado') || '';
          let shouldShow = true;
          
          switch(filterType) {
            case 'pendientes':
              shouldShow = estado !== 'validado' && estado !== 'pagado';
              break;
            case 'criticos':
              const dias = parseInt(row.getAttribute('data-dias')) || 0;
              shouldShow = dias > 15;
              break;
            case 'recientes':
              const dias_recientes = parseInt(row.getAttribute('data-dias')) || 0;
              shouldShow = dias_recientes <= 7;
              break;
            case 'validados':
              shouldShow = estado === 'validado';
              break;
            default:
              shouldShow = true;
          }
          
          row.classList.toggle('hidden', !shouldShow);
        });
        
        // Actualizar filas filtradas
        filteredRows = rows.filter(row => !row.classList.contains('hidden'));
        console.log(`🔍 Filtro aplicado: ${filteredRows.length} filas visibles de ${rows.length} total`);
      }

      // Event listeners para paginación
      if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', () => {
          pageSize = parseInt(pageSizeSelect.value);
          currentPage = 1;
          updatePagination();
        });
      }

      if (prevPageBtn) {
        prevPageBtn.addEventListener('click', () => {
          if (currentPage > 1) {
            goToPage(currentPage - 1);
          }
        });
      }

      if (nextPageBtn) {
        nextPageBtn.addEventListener('click', () => {
          const totalPages = Math.ceil(filteredRows.length / pageSize);
          if (currentPage < totalPages) {
            goToPage(currentPage + 1);
          }
        });
      }

      if (gotoPageBtn && gotoPageInput) {
        gotoPageBtn.addEventListener('click', () => {
          const pageNum = parseInt(gotoPageInput.value);
          if (!isNaN(pageNum)) {
            goToPage(pageNum);
            gotoPageInput.value = '';
          }
        });

        gotoPageInput.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            gotoPageBtn.click();
          }
        });
      }

      // Función eliminada - ahora se usa applyFiltersAndUpdatePagination() directamente

      // Agregar eventos de clic a los encabezados para ordenar
    headers.forEach(header => {
      header.addEventListener('click', function () {
        const sortBy = this.dataset.sort;               // data-sort
        const asc    = !this.classList.contains('sort-asc');

        // reset clases
        headers.forEach(h => h.classList.remove('sort-asc','sort-desc'));
        this.classList.add(asc ? 'sort-asc' : 'sort-desc');

        sortTable(sortBy, asc);
      });
    });

      // Función mejorada para ordenar la tabla
   // Función mejorada para ordenar la tabla
  function sortTable(sortBy, ascending) {
    console.log(`Sorting by ${sortBy}, ascending: ${ascending}`); // Debug line

    const rowsToSort = Array.from(tableBody.querySelectorAll('tr'));
    console.log(`Found ${rowsToSort.length} rows to sort`); // Debug line

            try {
          rowsToSort.sort((a, b) => {
            let valueA, valueB;

            // Helper function to safely get cell content
            function getCellContent(row, index, defaultValue = '') {
              const cell = row.querySelector(`td:nth-child(${index})`);
              return cell ? cell.textContent.trim() : defaultValue;
            }

            // Helper function to safely get numeric value
            function getNumericValue(row, index, defaultValue = 0) {
              const content = getCellContent(row, index);
              if (!content) return defaultValue;
              
              // For monetary values, remove currency symbols and commas
              const cleanContent = content.replace(/[$,\.]/g, "");
              const numValue = parseFloat(cleanContent);
              return isNaN(numValue) ? defaultValue : numValue;
            }

            // Helper function to extract numeric value from EDP format (e.g., "OT2226" -> 2226)
            function getEdpNumericValue(row, index, defaultValue = 0) {
              const content = getCellContent(row, index);
              if (!content) return defaultValue;
              
              // Extract numeric part from EDP format (e.g., "OT2226" -> "2226")
              const numericPart = content.replace(/[^0-9]/g, "");
              const numValue = parseInt(numericPart);
              return isNaN(numValue) ? defaultValue : numValue;
            }

            // Detect table type and adjust column mappings
            const isRetrabajoTable = tableBody.closest('table')?.id === 'tablaRetrabajos';
            
            if (isRetrabajoTable) {
              // Column mapping for retrabajos table:
              // 1: N° EDP, 2: Proyecto, 3: Encargado, 4: Motivo, 5: Tipo Falla, 6: Acciones
              switch (sortBy) {
                case "N° EDP":
                case "edp":
                  valueA = getEdpNumericValue(a, 1);
                  valueB = getEdpNumericValue(b, 1);
                  break;
                case "Proyecto":
                case "proyecto":
                  valueA = getCellContent(a, 2).toLowerCase();
                  valueB = getCellContent(b, 2).toLowerCase();
                  break;
                case "Encargado":
                case "jefe":
                  valueA = getCellContent(a, 3).toLowerCase();
                  valueB = getCellContent(b, 3).toLowerCase();
                  break;
                case "Motivo":
                  valueA = getCellContent(a, 4).toLowerCase();
                  valueB = getCellContent(b, 4).toLowerCase();
                  break;
                case "Tipo Falla":
                  valueA = getCellContent(a, 5).toLowerCase();
                  valueB = getCellContent(b, 5).toLowerCase();
                  break;
                default:
                  valueA = getEdpNumericValue(a, 1);
                  valueB = getEdpNumericValue(b, 1);
              }
                         } else {
               // Corrected column mapping for main control panel table:
               // 1: N° EDP, 2: Proyecto, 3: Encargado, 4: Cliente, 5: Estado, 6: Días, 7: M. Aprobado, 8: Acciones
               switch (sortBy) {
                 case "edp":
                   valueA = getEdpNumericValue(a, 1);
                   valueB = getEdpNumericValue(b, 1);
                   break;

                 case "proyecto":
                   valueA = getCellContent(a, 2).toLowerCase();
                   valueB = getCellContent(b, 2).toLowerCase();
                   break;

                 case "jefe":
                   valueA = getCellContent(a, 3).toLowerCase();
                   valueB = getCellContent(b, 3).toLowerCase();
                   break;

                 case "cliente":
                   valueA = getCellContent(a, 4).toLowerCase();
                   valueB = getCellContent(b, 4).toLowerCase();
                   break;

                 case "estado":
                   valueA = getCellContent(a, 5).toLowerCase();
                   valueB = getCellContent(b, 5).toLowerCase();
                   break;

                 case "dias":
                   valueA = getNumericValue(a, 6);
                   valueB = getNumericValue(b, 6);
                   break;

                 case "monto-aprobado":
                   valueA = getNumericValue(a, 7);
                   valueB = getNumericValue(b, 7);
                   break;

                 default:
                   valueA = getEdpNumericValue(a, 1);
                   valueB = getEdpNumericValue(b, 1);
               }
             }

        // Compare values
        if (valueA < valueB) {
          return ascending ? -1 : 1;
        }
        if (valueA > valueB) {
          return ascending ? 1 : -1;
        }
        return 0;
      });

      // Clear table body first
      while (tableBody.firstChild) {
        tableBody.removeChild(tableBody.firstChild);
      }

      // Append sorted rows
      rowsToSort.forEach((row) => {
        tableBody.appendChild(row);
      });

      // Actualizar las filas filtradas y la paginación después del ordenamiento
      filteredRows = rows.filter(row => !row.classList.contains('hidden'));
      updatePagination();

      console.log("Sorting completed successfully");
    } catch (error) {
      console.error("Error during sorting:", error);
    }
  }
      // Make rows clickable for detail view
      rows.forEach(row => {
        // Add visual indication that rows are clickable
        row.classList.add('cursor-pointer', 'hover:shadow-md', 'transition-all');

        // Get IDs for this row - ALWAYS prioritize internal ID for API calls
        const internalId = row.getAttribute('data-internal-id');
        const nEdp = row.getAttribute('data-edp'); // Only for display purposes

        // Make the entire row clickable except for elements that already have click handlers
        // Make the entire row clickable except for elements that already have click handlers
  row.addEventListener('click', function (e) {
    // Don't trigger if clicking on an element that's already a link or button
    if (e.target.closest('a, button')) {
      return;
    }

    // CRITICAL: Verify we have internal ID before proceeding
    if (!internalId) {
      console.error(`🚨 ERROR CRÍTICO: EDP ${nEdp} no tiene ID interno disponible. No se puede abrir modal de forma segura.`);
      // Show error modal instead
      document.getElementById('edpModalOverlay').classList.remove('hidden');
      document.getElementById('edpModalContent').innerHTML = `
        <div class="text-center p-8">
          <div class="text-[color:var(--accent-red)] text-5xl mb-4">⚠️</div>
          <h3 class="text-xl font-bold mb-2">Error de Sistema</h3>
          <p class="mb-4">Este EDP no tiene ID interno válido. No se puede proceder de forma segura.</p>
          <p class="text-sm text-[color:var(--text-secondary)] mb-4">EDP: ${nEdp}</p>
          <button class="btn-primary" onclick="document.getElementById('edpModalOverlay').classList.add('hidden')">
            Cerrar
          </button>
        </div>
      `;
      return;
    }

    // Show modal with loading state
    document.getElementById('edpModalOverlay').classList.remove('hidden');
    document.getElementById('edpModalContent').innerHTML = `
      <div class="flex justify-center items-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[color:var(--accent-blue)]"></div>
      </div>
    `;

    // Load EDP details via AJAX using INTERNAL ID (safe and unique)
    console.log(`🔍 Abriendo modal para EDP ${nEdp} usando ID interno ${internalId} (SEGURO Y ÚNICO)`);
    fetch(`/dashboard/api/edp-details-by-id/${internalId}`)
      .then(response => response.json())
      .then(data => {
        renderEdpModalContent(data);
      })
      .catch(error => {
        document.getElementById('edpModalContent').innerHTML = `
          <div class="text-center p-8">
            <div class="text-[color:var(--accent-red)] text-5xl mb-4">⚠️</div>
            <h3 class="text-xl font-bold mb-2">Error al cargar datos</h3>
            <p class="mb-4">${error.message || 'No se pudieron cargar los detalles del EDP'}</p>
            <p class="text-sm text-[color:var(--text-secondary)] mb-4">EDP: ${nEdp} (ID: ${internalId})</p>
            <button class="btn-primary" onclick="document.getElementById('edpModalOverlay').classList.add('hidden')">
              Cerrar
            </button>
          </div>
        `;
      });
  });

  // Tooltip para indicar que la fila es clickeable
  row.setAttribute('title', 'Haz clic para ver detalles del EDP');

  // Efecto visual en hover
  row.addEventListener('mouseenter', function () {
    this.classList.add('bg-[color:var(--bg-highlight)]');
  });
  row.addEventListener('mouseleave', function () {
    if (
      !this.classList.contains('data-table-row-critical') &&
      !this.classList.contains('data-table-row-validated')
    ) {
      this.classList.remove('bg-[color:var(--bg-highlight)]');
    }
  });
}); // End of rows.forEach loop

  // Exportar a CSV - Solución definitiva con modal de selección
  // Use the exportBtn already declared above

  // Usamos una técnica más robusta: eliminamos el listener y lo añadimos como atributo
  if (exportBtn) {
    // Eliminar todos los event listeners existentes
    exportBtn.replaceWith(exportBtn.cloneNode(true));

    // Obtener la nueva referencia después del clonado
    const newExportBtn = document.getElementById('exportar-excel');

    // Aplicar un solo event listener
    newExportBtn.addEventListener('click', function() {
      // Prevenir múltiples clics rápidos
      if (this.getAttribute('data-processing') === 'true') {
        return;
      }

      // Crear el modal de selección
      const modalHTML = `
        <div id="export-modal-overlay" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center animate__animated animate__fadeIn">
          <div class="bg-[color:var(--bg-card)] rounded-xl shadow-lg p-6 w-full max-w-md animate__animated animate__zoomIn">
            <h3 class="text-lg font-bold mb-4">Exportar datos a CSV</h3>
            <p class="text-[color:var(--text-secondary)] mb-5">Seleccione qué datos desea exportar:</p>

            <div class="grid grid-cols-1 gap-3 mb-6">
              <button id="export-all" class="btn-outline flex items-center justify-between p-4 border border-[color:var(--border-color)] rounded-lg hover:bg-[color:var(--bg-highlight)] transition-colors">
                <div class="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-3 text-[color:var(--accent-blue)]" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clip-rule="evenodd" />
                  </svg>
                  <div class="text-left">
                    <div class="font-medium">Todos los datos</div>
                    <div class="text-xs text-[color:var(--text-secondary)]">Exportar todos los registros</div>
                  </div>
                </div>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-[color:var(--text-secondary)]" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                </svg>
              </button>

              <button id="export-filtered" class="btn-outline flex items-center justify-between p-4 border border-[color:var(--border-color)] rounded-lg hover:bg-[color:var(--bg-highlight)] transition-colors">
                <div class="flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-3 text-[color:var(--accent-green)]" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clip-rule="evenodd" />
                  </svg>
                  <div class="text-left">
                    <div class="font-medium">Datos filtrados</div>
                    <div class="text-xs text-[color:var(--text-secondary)]">Exportar registros visibles (${document.querySelectorAll('#edp-table tbody tr:not(.hidden)').length})</div>
                  </div>
                </div>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-[color:var(--text-secondary)]" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>

            <div class="flex justify-end border-t border-[color:var(--border-color-subtle)] pt-4">
              <button id="cancel-export" class="px-4 py-2 text-[color:var(--text-secondary)] hover:text-[color:var(--text-primary)] transition-colors">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      `;

      // Insertar el modal en el DOM
      document.body.insertAdjacentHTML('beforeend', modalHTML);

      // Obtener referencias a los elementos del modal
      const modalOverlay = document.getElementById('export-modal-overlay');
      const exportAllBtn = document.getElementById('export-all');
      const exportFilteredBtn = document.getElementById('export-filtered');
      const cancelExportBtn = document.getElementById('cancel-export');

      // Función para cerrar el modal
      function closeModal() {
        modalOverlay.classList.remove('animate__fadeIn');
        modalOverlay.classList.add('animate__fadeOut');
        modalOverlay.querySelector('div').classList.remove('animate__zoomIn');
        modalOverlay.querySelector('div').classList.add('animate__zoomOut');

        setTimeout(() => {
          modalOverlay.remove();
        }, 300);
      }

      // Manejar clic en Cancelar
      cancelExportBtn.addEventListener('click', closeModal);

      // Manejar clic fuera del modal
      modalOverlay.addEventListener('click', function(e) {
        if (e.target === modalOverlay) {
          closeModal();
        }
      });

  // Función para iniciar la exportación
  function startExport(exportAll = false) {
    // Cerrar el modal
    closeModal();

    // Marcar como en proceso
    newExportBtn.setAttribute('data-processing', 'true');
    newExportBtn.disabled = true;
    newExportBtn.innerHTML = `
      <svg class="animate-spin h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Exportando...
    `;
      // Función para restaurar el botón a su estado original
    function restoreButton() {
      console.log("Restaurando botón de exportación");
      setTimeout(() => {
        newExportBtn.disabled = false;
        newExportBtn.setAttribute('data-processing', 'false');
        newExportBtn.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Exportar a CSV
        `;
      }, 500);
    }

      // Si exportamos todos los datos, hacemos una petición al servidor
    if (exportAll) {
      fetch('/dashboard/api/export-all-csv')
        .then(response => {
          if (!response.ok) {
            throw new Error('Error en la respuesta del servidor: ' + response.status);
          }
          return response.blob();
        })
        .then(blob => {
          try {
            // Crear y descargar archivo
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;

            // Nombre del archivo con timestamp
            const today = new Date().toISOString().slice(0, 10);
            link.download = `edp_export_completo_${today}.csv`;

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            // Mostrar notificación de éxito
            showToast('Archivo CSV completo exportado correctamente', 'success');
          } catch (err) {
            console.error("Error procesando blob:", err);
            showToast('Error al procesar el archivo', 'error');
          } finally {
            // Siempre restaurar el botón
            restoreButton();
          }
        })
        .catch(error => {
          console.error('Error al exportar datos completos:', error);
          showToast('Error al exportar los datos: ' + error.message, 'error');
          restoreButton();
        });
    } else {
      // Exportar solo los datos filtrados (desde la interfaz)
      setTimeout(() => {
        try {
          // Generar contenido CSV
          let csvContent = "data:text/csv;charset=utf-8,";

          // Obtener cabeceras visibles
          const visibleHeaders = Array.from(table.querySelectorAll('thead th'))
            .filter(th => th.style.display !== 'none')
            .map(th => `"${th.textContent.trim().replace(/"/g, '""')}"`);

          csvContent += visibleHeaders.join(',') + '\r\n';

          // Exportar solo filas visibles (filtradas)
          const rowsToExport = Array.from(tableBody.querySelectorAll('tr:not(.hidden)'));

          // Agregar datos de filas
          rowsToExport.forEach(row => {
            const rowData = Array.from(row.querySelectorAll('td'))
              .filter((cell, index) => {
                const header = table.querySelector(`thead th:nth-child(${index + 1})`);
                return header && header.style.display !== 'none';
              })
              .map(cell => `"${cell.textContent.trim().replace(/"/g, '""')}"`);

            csvContent += rowData.join(',') + '\r\n';
          });

          // Usar Blob para mejor manejo de archivos grandes
          const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
          const url = URL.createObjectURL(blob);

          // Crear enlace de descarga
          const link = document.createElement('a');
          link.setAttribute('href', url);

          // Nombre del archivo con fecha actual
          const today = new Date().toISOString().slice(0, 10);
          link.setAttribute('download', `edp_export_filtrado_${today}.csv`);

          // Descargar el archivo
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);

          // Liberar URL
          URL.revokeObjectURL(url);

          // Mostrar notificación de éxito
          showToast('Archivo CSV filtrado exportado correctamente', 'success');
        } catch (error) {
          console.error('Error al exportar datos filtrados:', error);
          showToast('Hubo un error al exportar los datos: ' + error.message, 'error');
        } finally {
          // Siempre restaurar el botón, incluso si hay un error
          restoreButton();
        }
      }, 300);
    }
  }

      // Manejar clic en Exportar Todo
      exportAllBtn.addEventListener('click', () => startExport(true));

      // Manejar clic en Exportar Filtrado
      exportFilteredBtn.addEventListener('click', () => startExport(false));
    });
  }

      // Initialize the table with sorting by days in descending order
    const diasHeader = table.querySelector('th[data-sort="dias"]');
    if (diasHeader) {
      diasHeader.classList.add('sort-desc');
      sortTable('dias', false);          // false → descendente
    }

          // CRÍTICO: Aplicar paginación inmediatamente al cargar la página
      // Primero configurar el tamaño de página desde el select
      if (pageSizeSelect) {
        pageSize = parseInt(pageSizeSelect.value) || 10;
        console.log(`📏 Tamaño de página configurado: ${pageSize}`);
      }
      
      // Asegurar que todas las filas estén inicialmente visibles para el filtro
      filteredRows = [...rows];
      
      // Aplicar cualquier filtro inicial si existe
      if (initialFilter !== 'todos') {
        // Aplicar filtro pero sin cambiar la página
        applyInitialFilter(initialFilter);
      }
      
      // FORZAR aplicación inmediata de la paginación
      console.log(`🔄 Aplicando paginación inicial: ${filteredRows.length} filas, ${pageSize} por página`);
      updatePagination();
      
      // Verificar que la paginación se aplicó correctamente
      setTimeout(() => {
        const visibleRows = rows.filter(row => row.style.display !== 'none');
        console.log(`✅ Verificación paginación: ${visibleRows.length} filas visibles de ${filteredRows.length} total`);
        if (visibleRows.length > pageSize) {
          console.warn(`⚠️ PROBLEMA: Se muestran ${visibleRows.length} filas pero deberían ser máximo ${pageSize}`);
          // Forzar corrección
          updatePagination();
        }
      }, 100);

      // Hacer funciones disponibles globalmente para acceso desde otros módulos
      window.updatePagination = updatePagination;
      window.applyFiltersAndUpdatePagination = applyFiltersAndUpdatePagination;
      window.goToPage = goToPage;

      // Mostrar en consola el estado del filtro (para depuración)
      console.log("Estado del filtro: " + initialFilter);
  }); // End of DOMContentLoaded event listener

