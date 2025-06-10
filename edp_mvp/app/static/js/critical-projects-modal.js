/**
 * Modal para Proyectos Críticos
 * Maneja la visualización y carga de datos para el modal de proyectos críticos
 */
const CriticalProjectsModal = (function() {
  // Referencias DOM
  const modal = document.getElementById('critical-projects-modal');
  const showModalBtn = document.getElementById('show-critical-projects-btn');
  const closeModalBtn = document.getElementById('close-critical-modal');
  const content = document.getElementById('critical-projects-content');
  const loadingSpinner = document.getElementById('loading-spinner');
  const criticalCount = document.getElementById('critical-projects-count');
  const totalValue = document.getElementById('total-critical-value');
  const exportBtn = document.getElementById('export-critical-projects');
  
  // Estado
  let projects = [];
  
  /**
   * Carga los datos de proyectos críticos desde el servidor
   */
  function loadCriticalProjects() {
    // Muestra spinner de carga
    setLoading(true);
    
    // Cargar datos reales desde el backend
    fetch('/manager/api/critical_projects')
      .then(response => {
        if (!response.ok) {
          throw new Error('Error en la respuesta del servidor');
        }
        return response.json();
      })
      .then(data => {
        projects = data.projects;
        totalValue.textContent = `$${data.total_value}M`;
        criticalCount.textContent = data.count;
        renderProjects();
      })
      .catch(err => {
        console.error('Error loading critical projects:', err);
        content.innerHTML = `<div class="text-center py-10 text-red-500">
          Error al cargar proyectos: ${err.message}. Intente nuevamente.
        </div>`;
        setLoading(false);
      });
  }
  
  /**
   * Renderiza los proyectos críticos en el contenido del modal con mejor visualización
   */
  function renderProjects() {
    if (!projects.length) {
      content.innerHTML = `
        <div class="text-center py-10">
          <svg class="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <p class="mt-4" style="color: var(--text-secondary)">No hay proyectos críticos en este momento</p>
        </div>
      `;
      setLoading(false);
      return;
    }

    // Ordenar por días de retraso (más críticos primero)
    projects.sort((a, b) => b.delay - a.delay);
    
    // Crear tarjetas visuales para cada proyecto
    const projectsHTML = `
      <div class="grid grid-cols-1 gap-5">
        ${projects.map((project, index) => `
          <div class="rounded-lg overflow-hidden border shadow-sm" style="border-color: var(--border-color)">
            <!-- Barra superior de color según criticidad -->
            <div class="h-1.5" style="background-color: ${getDaysColor(project.delay)}"></div>
            
            <!-- Cabecera del proyecto -->
            <div class="p-4 flex flex-wrap justify-between gap-4" style="background-color: var(--bg-card)">
              <div class="flex-grow">
                <div class="flex items-center">
                  <h3 class="font-bold" style="color: var(--text-primary)">${project.name}</h3>
                  <span class="ml-2 px-1.5 py-0.5 text-xs rounded" style="background-color: ${getDaysBackground(project.delay)}; color: ${getDaysColor(project.delay)}">
                    ${project.delay} días
                  </span>
                </div>
                <div class="mt-1 text-sm" style="color: var(--text-secondary)">
                  Cliente: ${project.client} • Gestor: ${project.manager}
                </div>
              </div>
              <div class="flex flex-col items-end">
                <div class="font-bold text-lg" style="color: var(--text-primary)">$${project.value}M</div>
                <div class="mt-1 text-xs" style="color: var(--text-secondary)">${project.edps.length} EDPs pendientes</div>
              </div>
            </div>
            
            <!-- Barra de acciones -->
            <div class="px-4 py-2 flex justify-between" style="background-color: var(--bg-subtle)">
              <button onclick="CriticalProjectsModal.toggleEDPs(${index})" class="text-xs flex items-center hover:underline" style="color: var(--accent-blue)">
                <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"></path>
                  <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"></path>
                </svg>
                Ver detalle de EDPs
              </button>
              <button class="text-xs py-1 px-2 rounded text-white" style="background-color: var(--accent-blue)">
                Gestionar
              </button>
            </div>
            
            <!-- Contenido expandible de EDPs -->
            <div id="edps-row-${index}" class="hidden">
              <div class="overflow-x-auto" style="background-color: var(--bg-subtle)">
                <table class="min-w-full text-sm">
                  <thead>
                    <tr style="background-color: var(--bg-card)">
                      <th class="px-3 py-2 text-left" style="color: var(--text-secondary)">EDP</th>
                      <th class="px-3 py-2 text-left" style="color: var(--text-secondary)">Emisión</th>
                      <th class="px-3 py-2 text-right" style="color: var(--text-secondary)">Monto</th>
                      <th class="px-3 py-2 text-right" style="color: var(--text-secondary)">Días</th>
                      <th class="px-3 py-2 text-center" style="color: var(--text-secondary)">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${project.edps.map((edp, i) => `
                      <tr class="${i % 2 === 0 ? '' : 'bg-[color:var(--bg-card)]'}">
                        <td class="px-3 py-2 border-t" style="color: var(--text-primary); border-color: var(--border-color-subtle)">${edp.id}</td>
                        <td class="px-3 py-2 border-t" style="color: var(--text-secondary); border-color: var(--border-color-subtle)">${edp.date}</td>
                        <td class="px-3 py-2 text-right border-t" style="color: var(--text-primary); border-color: var(--border-color-subtle)">$${edp.amount}M</td>
                        <td class="px-3 py-2 text-right font-medium border-t" style="color: ${getDaysTextColor(edp.days)}; border-color: var(--border-color-subtle)">${edp.days}d</td>
                        <td class="px-3 py-2 text-center border-t" style="border-color: var(--border-color-subtle)">
                          <span class="inline-block px-2 py-0.5 text-xs rounded-full ${getStatusClass(edp.status)}">
                            ${edp.status}
                          </span>
                        </td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    
    content.innerHTML = projectsHTML;
    setLoading(false);
  }

  /**
   * Función para mostrar/ocultar la lista de EDPs de un proyecto
   */
  function toggleEDPs(index) {
    const edpsRow = document.getElementById(`edps-row-${index}`);
    if (edpsRow) {
      edpsRow.classList.toggle('hidden');
    }
  }

  /**
   * Funciones auxiliares para colores dinámicos basados en días
   */
  function getDaysColor(days) {
    if (days > 90) return 'var(--danger)';
    if (days > 60) return 'var(--warning)';
    if (days > 30) return 'var(--accent-blue)';
    return 'var(--accent-green)';
  }

  function getDaysBackground(days) {
    if (days > 90) return 'var(--danger-bg)';
    if (days > 60) return 'var(--warning-bg)';
    if (days > 30) return 'var(--info-bg)';
    return 'var(--success-bg)';
  }

  function getDaysTextColor(days) {
    if (days > 90) return 'var(--danger)';
    if (days > 60) return 'var(--warning)';
    if (days > 30) return 'var(--accent-blue)';
    return 'var(--accent-green)';
  }

  function getStatusClass(status) {
    switch(status.toLowerCase()) {
      case 'crítico':
        return 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300';
      case 'riesgo':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300';
      case 'pendiente':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/50 dark:text-gray-300';
    }
  }
  
  /**
   * Establece el estado de carga del modal
   */
  function setLoading(loading) {
    if (loading) {
      loadingSpinner.classList.remove('hidden');
      content.classList.add('hidden');
    } else {
      loadingSpinner.classList.add('hidden');
      content.classList.remove('hidden');
    }
  }
  
  /**
   * Abre el modal y carga los datos
   */
  function openModal() {
    modal.classList.remove('hidden');
    document.body.classList.add('overflow-hidden'); // Previene scroll en el body
    loadCriticalProjects();
  }
  
  /**
   * Cierra el modal
   */
  function closeModal() {
    modal.classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
  }
  
  /**
   * Inicializa los event listeners
   */
  function init() {
    // Verificar si los elementos existen
    if (!modal || !showModalBtn || !closeModalBtn) {
      console.error('Elementos del modal no encontrados');
      return;
    }
    
    // Event listeners
    showModalBtn.addEventListener('click', openModal);
    closeModalBtn.addEventListener('click', closeModal);
    
    // Cerrar al hacer click fuera del contenido del modal
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });
    
    // Cerrar con la tecla Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.classList.contains('hidden')) closeModal();
    });
    
    // Botón de exportar
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        alert('Exportando reporte de proyectos críticos...');
      });
    }
  }
  
  // Inicialización con verificación de estado del DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // Si el DOM ya está cargado, inicializar inmediatamente
    setTimeout(init, 500); // Pequeño retraso para asegurar que todo esté disponible
  }
  
  // API pública del módulo
  return {
    open: openModal,
    close: closeModal,
    toggleEDPs: toggleEDPs
  };
})();