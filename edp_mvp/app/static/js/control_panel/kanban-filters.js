// =============================================================================
// FILTROS EN TIEMPO REAL PARA KANBAN
// =============================================================================

class KanbanFilters {
  constructor() {
    this.filterSelects = {};
    this.searchInput = null;
    this.isInitialized = false;
    
    // Bind methods
    this.applyFilters = this.applyFilters.bind(this);
    this.clearFilters = this.clearFilters.bind(this);
    this.handleSearchInput = this.handleSearchInput.bind(this);
    this.handleSelectChange = this.handleSelectChange.bind(this);
  }

  // Inicializar el sistema de filtros
  init() {
    if (this.isInitialized) return;
    
    console.log('Inicializando filtros de kanban...');
    
    // Obtener elementos del DOM
    this.filterSelects = {
      mes: document.getElementById('mes'),
      jefe_proyecto: document.getElementById('jefe_proyecto'),
      cliente: document.getElementById('cliente'),
      estado: document.getElementById('estado')
    };

    this.searchInput = document.getElementById('buscar-edp');

    // Verificar que los elementos existen
    if (!this.validateElements()) {
      console.warn('Algunos elementos de filtros no se encontraron');
      return;
    }

    // Configurar event listeners
    this.setupEventListeners();
    
    // Aplicar filtros iniciales después de un breve delay
    setTimeout(() => {
      this.applyFilters();
    }, 100);
    
    this.isInitialized = true;
    console.log('Filtros de kanban inicializados correctamente');
  }

  // Validar que los elementos necesarios existen
  validateElements() {
    // Solo requerimos el input de búsqueda como elemento esencial
    if (!this.searchInput) {
      console.error('Input de búsqueda no encontrado (id: buscar-edp)');
      return false;
    }
    
    // Verificar que al menos tengamos algunos selects de filtro
    const availableSelects = Object.values(this.filterSelects).filter(el => el);
    if (availableSelects.length === 0) {
      console.warn('No se encontraron elementos de filtro, funcionalidad limitada');
    }
    
    console.log(`Filtros disponibles: ${availableSelects.length} selects + búsqueda`);
    return true;
  }

  // Configurar todos los event listeners
  setupEventListeners() {
    // Filtrado automático en tiempo real al cambiar selects
    Object.values(this.filterSelects).forEach(select => {
      if (select) {
        select.addEventListener('change', this.handleSelectChange);
      }
    });

    // Búsqueda en tiempo real con debounce
    if (this.searchInput) {
      this.searchInput.addEventListener('input', this.handleSearchInput);
    }

    // Botón limpiar filtros
    const clearBtn = document.getElementById('clear-filters-btn');
    if (clearBtn) {
      clearBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.clearFilters();
      });
    }

    // Botón limpiar búsqueda
    const clearSearchBtn = document.getElementById('limpiar-busqueda');
    if (clearSearchBtn) {
      clearSearchBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (this.searchInput) {
          this.searchInput.value = '';
          this.applyFilters();
        }
      });
    }

    // Botón refrescar
    const refreshBtn = document.getElementById('refresh-all-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.applyFilters();
        
        // Animación de rotación
        const icon = refreshBtn.querySelector('svg');
        if (icon) {
          icon.style.transform = 'rotate(360deg)';
          setTimeout(() => {
            icon.style.transform = 'rotate(0deg)';
          }, 500);
        }
      });
    }

    // Botones de cambio de vista (Kanban/Tabla)
    const toggleKanban = document.getElementById('toggle-kanban');
    const toggleLista = document.getElementById('toggle-lista');
    
    if (toggleKanban) {
      toggleKanban.addEventListener('click', () => {
        setTimeout(() => this.applyFilters(), 100);
      });
    }
    
    if (toggleLista) {
      toggleLista.addEventListener('click', () => {
        setTimeout(() => this.applyFilters(), 100);
      });
    }
  }

  // Manejar cambios en selects con delay
  handleSelectChange() {
    clearTimeout(this.selectTimeout);
    this.selectTimeout = setTimeout(() => {
      this.applyFilters();
    }, 100);
  }

  // Manejar input de búsqueda con debounce
  handleSearchInput() {
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.applyFilters();
    }, 300);
  }

  // Obtener valores actuales de todos los filtros
  getCurrentFilters() {
    return {
      mes: this.filterSelects.mes?.value || '',
      jefe_proyecto: this.filterSelects.jefe_proyecto?.value || '',
      cliente: this.filterSelects.cliente?.value || '',
      estado: this.filterSelects.estado?.value || '',
      search: this.searchInput?.value?.toLowerCase() || ''
    };
  }

  // Función principal para aplicar todos los filtros
  applyFilters() {
    const filters = this.getCurrentFilters();
    console.log('Aplicando filtros:', filters);

    // Determinar qué vista está activa
    const kanbanView = document.getElementById('kanban-board');
    const tableView = document.getElementById('tabla-view');
    const isTableView = tableView && !tableView.classList.contains('hidden');
    
    let visibleCount = 0;
    let hiddenCount = 0;

    if (isTableView) {
      // Aplicar filtros a la tabla
      const tableRows = document.querySelectorAll('#edp-table tbody tr');
      
      tableRows.forEach(row => {
        // Saltar la fila de "no hay registros" si existe
        if (row.cells.length === 1 && row.cells[0].getAttribute('colspan')) {
          return;
        }
        
        const isVisible = this.shouldShowTableRow(row, filters);
        
        if (isVisible) {
          this.showTableRow(row);
          visibleCount++;
        } else {
          this.hideTableRow(row);
          hiddenCount++;
        }
      });
      
      // Actualizar información de la tabla
      this.updateTableMetrics(visibleCount, hiddenCount);
      
    } else {
      // Aplicar filtros al kanban (lógica original)
      const kanbanItems = document.querySelectorAll('.kanban-item');
      const columns = document.querySelectorAll('.kanban-column');
      
      kanbanItems.forEach(item => {
        const isVisible = this.shouldShowItem(item, filters);
        
        if (isVisible) {
          this.showItem(item);
          visibleCount++;
        } else {
          this.hideItem(item);
          hiddenCount++;
        }
      });

      // Actualizar contadores y totales de columnas
      this.updateColumnMetrics(columns);
    }

    // Actualizar métricas principales del sidebar (común para ambas vistas)
    this.updateSidebarMetrics();

    // Mostrar resultado del filtrado
    this.showFilterResults(visibleCount, hiddenCount);
    
    // Actualizar contador de filtros activos
    this.updateFilterCounter(filters);
    
    // Actualizar marca de tiempo
    this.updateTimestamp();
  }

  // Determinar si una tarjeta debe mostrarse según los filtros
  shouldShowItem(item, filters) {
    // Filtro por mes
    if (filters.mes && filters.mes !== '') {
      const itemMes = item.getAttribute('data-mes') || '';
      if (itemMes !== filters.mes) return false;
    }

    // Filtro por jefe de proyecto
    if (filters.jefe_proyecto && filters.jefe_proyecto !== '') {
      const itemJP = item.getAttribute('data-responsable') || '';
      if (itemJP !== filters.jefe_proyecto) return false;
    }

    // Filtro por cliente
    if (filters.cliente && filters.cliente !== '') {
      const itemCliente = item.getAttribute('data-cliente') || '';
      if (itemCliente !== filters.cliente) return false;
    }

    // Filtro por estado
    if (filters.estado && filters.estado !== '' && filters.estado !== 'todos') {
      const itemEstado = item.getAttribute('data-estado') || '';
      if (filters.estado === 'pendientes') {
        // Solo mostrar revisión y enviado
        if (!['revisión', 'enviado'].includes(itemEstado)) return false;
      } else if (itemEstado !== filters.estado) {
        return false;
      }
    }

    // Filtro por búsqueda de texto
    if (filters.search && filters.search !== '') {
      const searchableText = [
        item.getAttribute('data-n-edp') || '',
        item.getAttribute('data-cliente') || '',
        item.getAttribute('data-responsable') || '',
        item.getAttribute('data-proyecto') || ''
      ].join(' ').toLowerCase();
      
      if (!searchableText.includes(filters.search)) return false;
    }

    return true;
  }

  // Mostrar una tarjeta
  showItem(item) {
    item.style.display = 'block';
    item.classList.remove('hidden');
  }

  // Ocultar una tarjeta
  hideItem(item) {
    item.style.display = 'none';
    item.classList.add('hidden');
  }

  // Determinar si una fila de tabla debe mostrarse según los filtros
  shouldShowTableRow(row, filters) {
    // Filtro por mes
    if (filters.mes && filters.mes !== '') {
      const itemMes = row.getAttribute('data-mes') || '';
      if (itemMes !== filters.mes) return false;
    }

    // Filtro por jefe de proyecto
    if (filters.jefe_proyecto && filters.jefe_proyecto !== '') {
      const itemJP = row.getAttribute('data-jefe') || '';
      if (itemJP !== filters.jefe_proyecto) return false;
    }

    // Filtro por cliente
    if (filters.cliente && filters.cliente !== '') {
      const itemCliente = row.getAttribute('data-cliente') || '';
      if (itemCliente !== filters.cliente) return false;
    }

    // Filtro por estado
    if (filters.estado && filters.estado !== '' && filters.estado !== 'todos') {
      const itemEstado = row.getAttribute('data-estado') || '';
      if (filters.estado === 'pendientes') {
        // Solo mostrar revisión y enviado
        if (!['revisión', 'enviado'].includes(itemEstado)) return false;
      } else if (itemEstado !== filters.estado) {
        return false;
      }
    }

    // Filtro por búsqueda de texto
    if (filters.search && filters.search !== '') {
      const searchableText = [
        row.getAttribute('data-edp') || '',
        row.getAttribute('data-cliente') || '',
        row.getAttribute('data-jefe') || '',
        row.getAttribute('data-proyecto') || ''
      ].join(' ').toLowerCase();
      
      if (!searchableText.includes(filters.search)) return false;
    }

    return true;
  }

  // Mostrar una fila de tabla
  showTableRow(row) {
    row.style.display = '';
    row.classList.remove('hidden');
  }

  // Ocultar una fila de tabla
  hideTableRow(row) {
    row.style.display = 'none';
    row.classList.add('hidden');
  }

  // Actualizar métricas de las columnas
  updateColumnMetrics(columns) {
    columns.forEach(column => {
      const visibleItems = column.querySelectorAll('.kanban-item:not(.hidden)');
      const totalElement = column.querySelector('[data-columna-total]');
      const countElement = column.querySelector('[data-columna-count]');
      const placeholder = column.querySelector('.empty-placeholder');

      // Actualizar contador
      if (countElement) {
        countElement.textContent = visibleItems.length;
      }

      // Calcular total de monto
      let totalMonto = 0;
      visibleItems.forEach(item => {
        const monto = parseFloat(item.getAttribute('data-monto') || '0');
        if (!isNaN(monto)) {
          totalMonto += monto;
        }
      });

      // Actualizar total con formato
      if (totalElement) {
        const formattedTotal = this.formatMonto(totalMonto);
        totalElement.textContent = formattedTotal;
      }

      // Mostrar/ocultar placeholder
      if (placeholder) {
        placeholder.style.display = visibleItems.length === 0 ? 'block' : 'none';
      }
    });
  }

  // Actualizar métricas del sidebar
  updateSidebarMetrics() {
    // Determinar qué vista está activa y obtener elementos visibles
    const tableView = document.getElementById('tabla-view');
    const isTableView = tableView && !tableView.classList.contains('hidden');
    
    let visibleItems;
    if (isTableView) {
      visibleItems = document.querySelectorAll('#edp-table tbody tr:not(.hidden)');
    } else {
      visibleItems = document.querySelectorAll('.kanban-item:not(.hidden)');
    }
    
    let totalMontoReal = 0;
    let totalDiasReal = 0;
    let tarjetasConDiasReal = 0;
    let edpsCriticosReal = 0;
    let edpsAtencionReal = 0;
    let edpsProximosVencimientoReal = 0;
    let totalEdpsReal = 0;
    let totalPagadosReal = 0;
    let totalPendientesReal = 0;

    // Contar por jefe de proyecto
    const jpCounts = {};

    visibleItems.forEach(item => {
      // Saltar fila vacía de "no hay registros"
      if (isTableView && item.cells && item.cells.length === 1 && item.cells[0].getAttribute('colspan')) {
        return;
      }
      
      totalEdpsReal++;
      
      // Obtener datos dependiendo del tipo de elemento
      let monto, dias, estado, responsable;
      
      if (isTableView) {
        monto = parseFloat(item.getAttribute('data-monto-aprobado') || '0');
        dias = parseInt(item.getAttribute('data-dias') || '0');
        estado = item.getAttribute('data-estado') || '';
        responsable = item.getAttribute('data-jefe') || '';
      } else {
        monto = parseFloat(item.getAttribute('data-monto') || '0');
        dias = parseInt(item.getAttribute('data-dias') || '0');
        estado = item.getAttribute('data-estado') || '';
        responsable = item.getAttribute('data-responsable') || '';
      }

      // Calcular monto total
      if (!isNaN(monto)) {
        totalMontoReal += monto;
      }

      // Calcular DSO y críticos
      if (!isNaN(dias) && dias > 0) {
        totalDiasReal += dias;
        tarjetasConDiasReal++;
        
        if (dias > 30) {
          edpsCriticosReal++;
        } else if (dias >= 20 && dias <= 30) {
          edpsAtencionReal++;
        } else if (dias >= 5 && dias <= 10) {
          edpsProximosVencimientoReal++;
        }
      }

      // Contar por estado
      if (estado === 'pagado') {
        totalPagadosReal++;
      } else if (['revisión', 'enviado', 'validado'].includes(estado)) {
        totalPendientesReal++;
      }

      // Contar por responsable
      if (responsable) {
        jpCounts[responsable] = (jpCounts[responsable] || 0) + 1;
      }
    });

    // Calcular DSO promedio
    const dsoPromedioReal = tarjetasConDiasReal > 0 ? Math.round(totalDiasReal / tarjetasConDiasReal) : 0;

    // ACTUALIZAR TODAS LAS MÉTRICAS

    // 1. Header principal
    this.updateSidebarElement('total-edps-banner', totalEdpsReal);
    this.updateSidebarElement('pendientes-banner', totalPendientesReal);
    this.updateSidebarElement('pagados-banner', totalPagadosReal);
    this.updateSidebarElement('meta-mensual', '$' + Math.round(totalMontoReal / 1000000) + 'M');

    // 2. Panel de alertas rápidas
    this.updateSidebarElement('alertas-criticas', edpsCriticosReal);
    this.updateSidebarElement('proximos-vencimientos', edpsProximosVencimientoReal);
    
    // Calcular rendimiento (ratio de pagados vs total)
    const ratioPagados = totalEdpsReal > 0 ? (totalPagadosReal / totalEdpsReal) * 100 : 0;
    const rendimiento = Math.round(ratioPagados - 30); // Comparar con 30% base
    const rendimientoElement = document.getElementById('rendimiento-hoy');
    if (rendimientoElement) {
      rendimientoElement.textContent = (rendimiento > 0 ? '+' : '') + rendimiento + '%';
      rendimientoElement.className = rendimiento > 0 ?
        'text-lg font-bold text-[color:var(--accent-green)] mono-font' :
        'text-lg font-bold text-[color:var(--accent-danger)] mono-font';
    }

    // 3. Sidebar métricas principales
    this.updateSidebarElement('monto-total', '$' + Math.round(totalMontoReal / 1000000) + 'M');
    this.updateSidebarElement('dso-principal', dsoPromedioReal + ' días');
    this.updateSidebarElement('total-criticos', edpsCriticosReal);

    // 4. Panel de escalación crítica
    this.updateSidebarElement('edps-criticos-escalacion', edpsCriticosReal);
    this.updateSidebarElement('edps-atencion-escalacion', edpsAtencionReal);
    
    // Encontrar JP con más EDPs
    let maxJP = '';
    let maxCount = 0;
    for (const [jp, count] of Object.entries(jpCounts)) {
      if (count > maxCount) {
        maxCount = count;
        maxJP = jp;
      }
    }
    this.updateSidebarElement('jp-mas-edps', maxJP ? `${maxJP} (${maxCount})` : '-');

    // 5. Actividad del día (calculada proporcionalmente)
    const baseEDPsHoy = Math.max(1, Math.floor(totalEdpsReal / 25));
    const basePagosHoy = Math.max(0, Math.floor(totalPagadosReal * 0.12));
    const alertasActivasHoy = edpsCriticosReal + Math.floor(edpsProximosVencimientoReal * 0.3);
    
    this.updateSidebarElement('edps-procesados-hoy', baseEDPsHoy);
    this.updateSidebarElement('validaciones-hoy', basePagosHoy);
    this.updateSidebarElement('alertas-activas', alertasActivasHoy);

    // 6. Actualizar barras de progreso y meta
    this.updateProgressBars(totalMontoReal, dsoPromedioReal, edpsCriticosReal, totalEdpsReal);
    this.updateMetaProgress(totalMontoReal);
  }

  // Actualizar un elemento del sidebar
  updateSidebarElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  }

  // Actualizar barras de progreso
  updateProgressBars(totalMonto, dsoPromedio, criticos, totalEdps) {
    // Barra de monto
    const montoBar = document.getElementById('monto-bar');
    if (montoBar) {
      const metaObjetivo = Math.max(5000000000, totalMonto * 1.2);
      const progresoMonto = Math.min(100, Math.round((totalMonto / metaObjetivo) * 100));
      montoBar.style.width = progresoMonto + '%';
    }

    // Barra de DSO
    const dsoBar = document.getElementById('dso-bar');
    const dsoPrincipal = document.getElementById('dso-principal');
    if (dsoBar) {
      const dsoProgress = Math.min(100, Math.round((dsoPromedio / 60) * 100));
      dsoBar.style.width = dsoProgress + '%';
      
      // Cambiar color según DSO
      if (dsoPromedio <= 30) {
        dsoBar.className = 'bg-[color:var(--accent-green)] h-2 rounded-full transition-all duration-1000';
        if (dsoPrincipal) dsoPrincipal.className = 'text-lg font-bold text-[color:var(--accent-green)] mono-font';
      } else if (dsoPromedio <= 45) {
        dsoBar.className = 'bg-[color:var(--accent-warning)] h-2 rounded-full transition-all duration-1000';
        if (dsoPrincipal) dsoPrincipal.className = 'text-lg font-bold text-[color:var(--accent-warning)] mono-font';
      } else {
        dsoBar.className = 'bg-[color:var(--accent-danger)] h-2 rounded-full transition-all duration-1000';
        if (dsoPrincipal) dsoPrincipal.className = 'text-lg font-bold text-[color:var(--accent-danger)] mono-font';
      }
    }

    // Barra de críticos
    const criticosBar = document.getElementById('criticos-bar');
    const totalCriticos = document.getElementById('total-criticos');
    if (criticosBar) {
      const criticosProgress = totalEdps > 0 ? Math.min(100, Math.round((criticos / totalEdps) * 100)) : 0;
      criticosBar.style.width = criticosProgress + '%';
      
      // Cambiar color según porcentaje de críticos
      if (criticosProgress <= 10) {
        criticosBar.className = 'bg-[color:var(--accent-green)] h-2 rounded-full transition-all duration-1000';
        if (totalCriticos) totalCriticos.className = 'text-lg font-bold text-[color:var(--accent-green)] mono-font';
      } else if (criticosProgress <= 20) {
        criticosBar.className = 'bg-[color:var(--accent-warning)] h-2 rounded-full transition-all duration-1000';
        if (totalCriticos) totalCriticos.className = 'text-lg font-bold text-[color:var(--accent-warning)] mono-font';
      } else {
        criticosBar.className = 'bg-[color:var(--accent-danger)] h-2 rounded-full transition-all duration-1000';
        if (totalCriticos) totalCriticos.className = 'text-lg font-bold text-[color:var(--accent-danger)] mono-font';
      }
    }

    // Actualizar indicador de rendimiento de actividad
    const rendimientoActividad = document.getElementById('rendimiento-actividad');
    const barraRendimiento = document.getElementById('barra-rendimiento');
    
    if (rendimientoActividad && barraRendimiento) {
      // Calcular rendimiento basado en la actividad actual
      const rendimientoPorcentaje = Math.min(100, Math.max(0, Math.floor((totalEdps / 50) * 100)));
      
      let estadoRendimiento = 'Normal';
      let colorClase = 'text-[color:var(--accent-blue)]';
      
      if (rendimientoPorcentaje >= 80) {
        estadoRendimiento = 'Excelente';
        colorClase = 'text-[color:var(--accent-green)]';
      } else if (rendimientoPorcentaje >= 60) {
        estadoRendimiento = 'Bueno';
        colorClase = 'text-[color:var(--accent-blue)]';
      } else if (rendimientoPorcentaje >= 40) {
        estadoRendimiento = 'Regular';
        colorClase = 'text-[color:var(--accent-warning)]';
      } else {
        estadoRendimiento = 'Bajo';
        colorClase = 'text-[color:var(--accent-danger)]';
      }
      
      rendimientoActividad.textContent = estadoRendimiento;
      rendimientoActividad.className = `text-xs font-bold mono-font ${colorClase}`;
      barraRendimiento.style.width = rendimientoPorcentaje + '%';
    }
  }

  // Actualizar progreso de meta mensual
  updateMetaProgress(totalMonto) {
    const metaProgress = document.getElementById('meta-progress');
    const metaInfoSidebar = document.getElementById('meta-info-sidebar');
    const montoBar = document.getElementById('monto-bar');
    
    if (metaProgress || metaInfoSidebar || montoBar) {
      // Establecer meta realista basada en el monto total
      const metaObjetivo = Math.max(5000000000, totalMonto * 1.2);
      const progress = Math.min(100, Math.round((totalMonto / metaObjetivo) * 100));
      
      // Actualizar barra de progreso principal
      if (metaProgress) {
        metaProgress.style.width = progress + '%';
      }
      
      // Actualizar barra del sidebar
      if (montoBar) {
        montoBar.style.width = progress + '%';
      }
      
      // Actualizar texto informativo
      if (metaInfoSidebar) {
        metaInfoSidebar.textContent = `Meta: $${Math.round(metaObjetivo / 1000000)}M • Progreso: ${progress}%`;
      }
    }
  }

  // Formatear monto
  formatMonto(monto) {
    if (monto >= 1000000) {
      return '$' + Math.round(monto / 1000000) + 'M';
    } else if (monto >= 1000) {
      return '$' + Math.round(monto / 1000) + 'K';
    } else {
      return '$' + Math.round(monto);
    }
  }

  // Mostrar resultados del filtrado
  showFilterResults(visible, hidden) {
    const total = visible + hidden;
    let message = `Mostrando ${visible} de ${total} EDPs`;
    
    if (hidden > 0) {
      message += ` (${hidden} ocultos por filtros)`;
    }

    // Determinar qué vista está activa
    const tableView = document.getElementById('tabla-view');
    const isTableView = tableView && !tableView.classList.contains('hidden');

    // Crear o actualizar indicador de filtros
    let filterIndicator = document.getElementById('filter-results-indicator');
    if (!filterIndicator) {
      filterIndicator = document.createElement('div');
      filterIndicator.id = 'filter-results-indicator';
      filterIndicator.className = 'text-xs text-[color:var(--text-secondary)] bg-[color:var(--bg-highlight)] px-3 py-1 rounded-full border border-[color:var(--border-primary)] mb-4';
      
      // Insertar en el lugar apropiado según la vista
      if (isTableView) {
        const tableContainer = document.querySelector('.table-responsive');
        if (tableContainer) {
          tableContainer.parentNode.insertBefore(filterIndicator, tableContainer);
        }
      } else {
        const kanbanBoard = document.getElementById('kanban-board');
        if (kanbanBoard) {
          kanbanBoard.parentNode.insertBefore(filterIndicator, kanbanBoard);
        }
      }
    }
    
    filterIndicator.textContent = message;
    filterIndicator.style.display = hidden > 0 ? 'block' : 'none';
  }

  // Actualizar contador de filtros activos
  updateFilterCounter(filters) {
    const filterCount = document.getElementById('filter-count');
    if (!filterCount) return;
    
    let activeFilters = 0;
    if (filters.mes && filters.mes !== '') activeFilters++;
    if (filters.jefe_proyecto && filters.jefe_proyecto !== '') activeFilters++;
    if (filters.cliente && filters.cliente !== '') activeFilters++;
    if (filters.estado && filters.estado !== '' && filters.estado !== 'todos') activeFilters++;
    if (filters.search && filters.search !== '') activeFilters++;
    
    const filterBtn = document.getElementById('toggle-filters-btn');
    
    if (activeFilters > 0) {
      filterCount.textContent = activeFilters;
      filterCount.classList.remove('hidden');
      
      // Cambiar color del botón cuando hay filtros activos
      if (filterBtn) {
        filterBtn.classList.add('bg-[color:var(--accent-warning)]');
        filterBtn.classList.remove('bg-[color:var(--accent-blue)]');
      }
    } else {
      filterCount.classList.add('hidden');
      
      // Restaurar color original del botón
      if (filterBtn) {
        filterBtn.classList.remove('bg-[color:var(--accent-warning)]');
        filterBtn.classList.add('bg-[color:var(--accent-blue)]');
      }
    }
  }

  // Actualizar marca de tiempo de última actualización
  updateTimestamp() {
    const elements = [
      document.getElementById('ultima-actualizacion'),
      document.getElementById('last-updated-banner')
    ];
    
    const ahora = new Date();
    const hora = ahora.toLocaleTimeString('es-CL', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
    
    elements.forEach(element => {
      if (element) {
        element.textContent = `Actualizado: ${hora}`;
      }
    });
  }

  // Actualizar métricas específicas de la tabla
  updateTableMetrics(visibleCount, hiddenCount) {
    const totalCount = visibleCount + hiddenCount;
    
    // Actualizar contadores de paginación
    const showingFrom = document.getElementById('showing-from');
    const showingTo = document.getElementById('showing-to');
    const totalCountElement = document.getElementById('total-count');
    const filteredInfo = document.getElementById('filtered-info');
    const originalCount = document.getElementById('original-count');

    if (showingFrom && showingTo && totalCountElement) {
      const pageSize = parseInt(document.getElementById('page-size')?.value || '10');
      
      const from = visibleCount > 0 ? 1 : 0;
      const to = Math.min(pageSize, visibleCount);
      
      showingFrom.textContent = from;
      showingTo.textContent = to;
      totalCountElement.textContent = visibleCount;
      
      // Mostrar información de filtrado si hay filtros activos
      if (hiddenCount > 0) {
        if (filteredInfo) {
          filteredInfo.classList.remove('hidden');
          if (originalCount) {
            originalCount.textContent = totalCount;
          }
        }
      } else {
        if (filteredInfo) {
          filteredInfo.classList.add('hidden');
        }
      }
    }
  }

  // Limpiar todos los filtros
  clearFilters() {
    // Limpiar selects
    Object.values(this.filterSelects).forEach(select => {
      if (select) select.selectedIndex = 0;
    });
    
    // Limpiar búsqueda
    if (this.searchInput) this.searchInput.value = '';
    
    // Aplicar filtros (mostrará todos los elementos)
    this.applyFilters();
    
    console.log('Filtros limpiados');
  }

  // Método público para aplicar filtros desde fuera
  refresh() {
    this.applyFilters();
  }
}

// =============================================================================
// INICIALIZACIÓN GLOBAL
// =============================================================================

// Instancia global
let kanbanFilters = null;

// Función de inicialización
function initializeKanbanFilters() {
  if (kanbanFilters) return kanbanFilters;
  
  kanbanFilters = new KanbanFilters();
  
  // Intentar inicializar cuando el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        try {
          kanbanFilters.init();
        } catch (error) {
          console.error('Error inicializando filtros kanban:', error);
        }
      }, 500);
    });
  } else {
    setTimeout(() => {
      try {
        kanbanFilters.init();
      } catch (error) {
        console.error('Error inicializando filtros kanban:', error);
      }
    }, 500);
  }
  
  return kanbanFilters;
}

// Auto-inicialización
initializeKanbanFilters();

// Exportar para uso global
window.KanbanFilters = KanbanFilters;
window.kanbanFilters = kanbanFilters; 