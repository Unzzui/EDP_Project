// Funciones para manejar el modal de EDP
document.addEventListener('DOMContentLoaded', function() {
  // Configurar botón de cierre del modal
  const closeButton = document.getElementById('closeEdpModal');
  if (closeButton) {
    closeButton.addEventListener('click', function() {
      document.getElementById('edpModalOverlay').classList.add('hidden');
    });
  }

  // Cerrar modal al hacer clic fuera de él
  const modalOverlay = document.getElementById('edpModalOverlay');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', function(e) {
      if (e.target === this) {
        this.classList.add('hidden');
      }
    });
  }
});

/**
 * Renderiza el contenido del modal con los datos del EDP
 * @param {Object} data - Datos del EDP recibidos del API
 */

// Actualiza el resumen superior del modal
function updateModalSummary(data) {
  document.querySelector('[data-display-field="N° EDP"]').textContent = data['N° EDP'] || 'N/A';
  document.querySelector('[data-display-field="Proyecto"]').textContent = data['Proyecto'] || 'N/A';
  document.querySelector('[data-display-field="Cliente"]').textContent = data['Cliente'] || 'N/A';
  
  // Actualizar la fecha de última actualización si existe
  if (data['Última Actualización']) {
    document.querySelector('[data-display-field="Última Actualización"]').textContent = 
      `Última actualización: ${data['Última Actualización']}`;
  }
  
  // Actualizar el indicador de estado
  const statusBadge = document.querySelector('[data-status-badge]');
  const statusText = data['Estado'] || 'pendiente';
  const statusDot = statusBadge.querySelector('span:first-child');
  
  // Definir colores según estado
  const statusColors = {
    'revisión': 'bg-yellow-500 text-yellow-800 bg-yellow-100',
    'enviado': 'bg-blue-500 text-blue-800 bg-blue-100',
    'pagado': 'bg-green-500 text-green-800 bg-green-100',
    'validado': 'bg-purple-500 text-purple-800 bg-purple-100',
    'default': 'bg-gray-500 text-gray-800 bg-gray-100'
  };
  
  // Aplicar clases de color
  const colorKey = statusText.toLowerCase() in statusColors ? statusText.toLowerCase() : 'default';
  const [dotColor, textColor, bgColor] = statusColors[colorKey].split(' ');
  
  statusDot.className = `w-2 h-2 rounded-full ${dotColor}`;
  statusBadge.className = `inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm font-medium ${bgColor} ${textColor}`;
  
  // Actualizar texto
  statusBadge.querySelector('span:last-child').textContent = statusText.charAt(0).toUpperCase() + statusText.slice(1);
}

// Currency formatting utilities
function formatCurrency(value) {
  // Remove non-digits and convert to number
  const number = parseInt(value.toString().replace(/[^\d]/g, '')) || 0;
  // Format with locale settings
  return number.toLocaleString('es-CL');
}

// Setup currency input with formatting
function setupCurrencyInput(formattedInputId, hiddenValueId) {
  const formattedInput = document.getElementById(formattedInputId);
  const hiddenValue = document.getElementById(hiddenValueId);
  
  if (!formattedInput || !hiddenValue) return;
  
  // Format on input
  formattedInput.addEventListener('input', (e) => {
    // Extract raw numeric value
    const rawValue = e.target.value.replace(/[^\d]/g, '');
    // Update hidden field with raw value
    hiddenValue.value = rawValue;
    // Update display with formatted value
    formattedInput.value = formatCurrency(rawValue);
  });
  
  // Format initial value
  formattedInput.value = formatCurrency(hiddenValue.value);
  
  // Show hint on focus
  const hintId = formattedInputId + '-format-hint';
  const hint = document.getElementById(hintId);
  if (hint) {
    formattedInput.addEventListener('focus', () => {
      hint.classList.remove('hidden');
    });
    formattedInput.addEventListener('blur', () => {
      hint.classList.add('hidden');
    });
  }
}


/**
 * Setup de campos condicionales basados en Estado Detallado
 */
function setupConditionalFields(modalContent) {
  // Buscar elementos dentro del modal actual
  const estadoDetallado = modalContent.querySelector('#estado_detallado');
  const wrapMotivo = modalContent.querySelector('#wrap_motivo');
  const wrapFalla = modalContent.querySelector('#wrap_falla');
  
  if (!estadoDetallado || !wrapMotivo || !wrapFalla) return;
  
  function updateFieldVisibility() {
    const showReTrabajo = estadoDetallado.value === 're-trabajo solicitado';
    
    // Toggle both fields together with the same animation timing
    if (showReTrabajo) {
      // Primero mostramos los contenedores
      wrapMotivo.style.display = 'block';
      wrapFalla.style.display = 'block';
      
      // Luego, después de un pequeño delay, quitamos la clase hidden para la animación
      setTimeout(() => {
        wrapMotivo.classList.remove('hidden');
        wrapFalla.classList.remove('hidden');
      }, 10);
    } else {
      // Primero aplicamos la clase hidden para iniciar la transición
      wrapMotivo.classList.add('hidden');
      wrapFalla.classList.add('hidden');
      
      // Después de la transición, ocultamos completamente
      setTimeout(() => {
        wrapMotivo.style.display = 'none';
        wrapFalla.style.display = 'none';
      }, 200); // duración de la transición
    }
  }
  
  // Update on change
  estadoDetallado.addEventListener('change', updateFieldVisibility);
  
  // Asegurar que el estado inicial sea correcto
  updateFieldVisibility();
  
  // Re-verificar después de un momento para casos donde otras scripts
  // podrían estar afectando la visibilidad
  setTimeout(updateFieldVisibility, 100);
}

/**
 * Setup de validación para campos de Conformidad
 */
function setupConformidadFields(modalContent) {
  // Buscar elementos dentro del modal actual
  const conformidadSelect = modalContent.querySelector('#conformidad_enviada');
  const fechaConformidad = modalContent.querySelector('#fecha_conformidad');
  const numConformidad = modalContent.querySelector('#n_conformidad');
  
  // Mensaje de notificación que crearemos dinámicamente
  let notificationDiv = null;
  
  if (!conformidadSelect || !fechaConformidad || !numConformidad) return;
  
  // Crear elemento de notificación
  function createNotification() {
    notificationDiv = document.createElement('div');
    notificationDiv.id = 'conformidadNotification';
    notificationDiv.className = 'mt-4 mb-2 p-3 rounded-md bg-[color:var(--state-warning-bg)] text-[color:var(--accent-amber-dark)] border border-[color:var(--accent-amber)] animate__animated animate__fadeIn';
    notificationDiv.innerHTML = `
      <div class="flex items-start">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <div>
          <p class="font-medium">Campos obligatorios para conformidad</p>
          <p class="text-sm mt-1">Al marcar "Conformidad Emitida" como "Sí", debes completar tanto el <strong>N° de Conformidad</strong> como la <strong>Fecha de Conformidad</strong>.</p>
        </div>
        <button type="button" id="closeConformidadNotification" class="ml-auto text-[color:var(--accent-amber-dark)] hover:text-[color:var(--accent-amber)]">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    `;
    
    // Insertar después del selector de conformidad
    const formGroup = conformidadSelect.closest('.form-group');
    formGroup.parentNode.insertBefore(notificationDiv, formGroup.nextSibling);
    
    // Configurar botón cerrar
    modalContent.querySelector('#closeConformidadNotification').addEventListener('click', removeNotification);
  }
  
  // Remover notificación
  function removeNotification() {
    if (notificationDiv) {
      notificationDiv.classList.add('animate__fadeOut');
      setTimeout(() => {
        if (notificationDiv && notificationDiv.parentNode) {
          notificationDiv.parentNode.removeChild(notificationDiv);
          notificationDiv = null;
        }
      }, 300);
    }
  }
  
  // Resaltar campos requeridos
  function highlightRequiredFields(isRequired) {
    const requiredClass = 'border-[color:var(--accent-amber)] bg-[color:var(--state-warning-bg-subtle)]';
    const labelClass = 'text-[color:var(--accent-amber-dark)] font-medium';
    
    if (isRequired) {
      // Resaltar campos
      fechaConformidad.classList.add(...requiredClass.split(' '));
      numConformidad.classList.add(...requiredClass.split(' '));
      
      // Resaltar etiquetas
      fechaConformidad.previousElementSibling.classList.add(...labelClass.split(' '));
      numConformidad.previousElementSibling.classList.add(...labelClass.split(' '));
      
      // Agregar indicador visual de requerido
      addRequiredIndicator(fechaConformidad);
      addRequiredIndicator(numConformidad);
    } else {
      // Quitar resaltado
      fechaConformidad.classList.remove(...requiredClass.split(' '));
      numConformidad.classList.remove(...requiredClass.split(' '));
      
      // Quitar resaltado de etiquetas
      fechaConformidad.previousElementSibling.classList.remove(...labelClass.split(' '));
      numConformidad.previousElementSibling.classList.remove(...labelClass.split(' '));
      
      // Quitar indicador visual
      removeRequiredIndicator(fechaConformidad);
      removeRequiredIndicator(numConformidad);
    }
  }
  
  // Agregar indicador de campo requerido
  function addRequiredIndicator(field) {
    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('required-indicator')) {
      const indicator = document.createElement('span');
      indicator.className = 'required-indicator text-xs text-[color:var(--accent-amber-dark)] mt-1 block animate__animated animate__fadeIn';
      indicator.textContent = 'Campo requerido';
      field.parentNode.insertBefore(indicator, field.nextSibling);
    }
  }
  
  // Quitar indicador de campo requerido
  function removeRequiredIndicator(field) {
    const indicator = field.nextElementSibling;
    if (indicator && indicator.classList.contains('required-indicator')) {
      indicator.remove();
    }
  }
  
  // Función principal que actualiza la UI según la selección
  function updateConformidadUI() {
    const isConformidadSi = conformidadSelect.value === 'Sí';
    
    if (isConformidadSi) {
      // Si no existe la notificación, crearla
      if (!notificationDiv) {
        createNotification();
      }
      highlightRequiredFields(true);
    } else {
      // Quitar notificación
      removeNotification();
      highlightRequiredFields(false);
    }
  }
  
  // Escuchar cambios en el selector
  conformidadSelect.addEventListener('change', updateConformidadUI);
  
  // Establecer estado inicial
  updateConformidadUI();
}


function renderEdpModalContent(data) {
  const modalContent = document.getElementById('edpModalContent');
  const template = document.getElementById('edpModalTemplate');
  
  // Actualizar título del modal
  document.getElementById('modalTitle').textContent = `Detalle de EDP: ${data['N° EDP']}`;
  
  // Clonar template
  const content = template.content.cloneNode(true);
  
  // Llenar los campos del formulario
  const form = content.querySelector('#edpModalForm');
  const fields = form.querySelectorAll('[data-field]');
  
  fields.forEach(field => {
    const fieldName = field.getAttribute('data-field');
    
    if (data[fieldName] !== undefined) {
      // Manejar tipos especiales de campos
      if (field.type === 'checkbox') {
        field.checked = data[fieldName] === true || 
                       data[fieldName] === 'true' || 
                       data[fieldName] === 'Sí';
      } else if (field.type === 'select-one') {
        // Para campos select, buscar y seleccionar la opción correspondiente
        const value = data[fieldName]?.toString() || '';
        const option = Array.from(field.options).find(opt => 
          opt.value.toLowerCase() === value.toLowerCase());
        if (option) {
          option.selected = true;
        }
      } else if (field.type === 'date' && data[fieldName]) {
        // Formatear fecha como YYYY-MM-DD para inputs de tipo date
        field.value = data[fieldName];
      } else {
        // Campos de texto, textareas, etc.
        field.value = data[fieldName] || '';
      }
    }
  });
  
  // Configurar envío del formulario
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Mostrar estado de carga
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = `
      <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Guardando...
    `;

    // Recolectar datos del formulario
    const formData = new FormData(form);
    const edpId = data['N° EDP'];
    
    // Enviar petición AJAX
    fetch(`/controller/api/update-edp/${edpId}`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Error en la respuesta del servidor');
      }
      return response.json();
    })
    .then(result => {
      if (result.success) {
        // Mostrar mensaje de éxito
        showNotification('Cambios guardados correctamente', 'success');
        
        // Cerrar modal después de breve delay
        setTimeout(() => {
          document.getElementById('edpModalOverlay').classList.add('hidden');
          // Refrescar datos si es necesario
          location.reload();
        }, 1500);
      } else {
        throw new Error(result.message || 'Error al guardar los cambios');
      }
    })
    .catch(error => {
      // Restaurar botón
      submitButton.disabled = false;
      submitButton.innerHTML = originalText;
      
      // Mostrar error
      showNotification(error.message || 'Error al guardar los cambios', 'error');
      console.error('Error:', error);
    });
  });
  
  // Manejar botón de cancelar
  const cancelButton = content.querySelector('#cancelEdpChanges');
  if (cancelButton) {
    cancelButton.addEventListener('click', function() {
      document.getElementById('edpModalOverlay').classList.add('hidden');
    });
  }

  // Limpiar contenido existente y agregar el nuevo formulario
  modalContent.innerHTML = '';
  modalContent.appendChild(content);

   updateModalSummary(data);
  // Configurar campos de moneda DESPUÉS de añadir el contenido al DOM
  setupCurrencyInput('monto_propuesto_formatted', 'monto_propuesto');
  setupCurrencyInput('monto_aprobado_formatted', 'monto_aprobado');
  

   // NUEVO: Inicializar campos dinámicos
  setupConditionalFields(modalContent);
  setupConformidadFields(modalContent);
  // También inicializar los valores formateados a partir de los datos recibidos
  const montoP = document.getElementById('monto_propuesto');
  const montoA = document.getElementById('monto_aprobado');
  
  if (montoP && data['Monto Propuesto']) {
    const rawValue = data['Monto Propuesto'].toString().replace(/[^\d]/g, '');
    montoP.value = rawValue;
    document.getElementById('monto_propuesto_formatted').value = formatCurrency(rawValue);
  }
  
  if (montoA && data['Monto Aprobado']) {
    const rawValue = data['Monto Aprobado'].toString().replace(/[^\d]/g, '');
    montoA.value = rawValue;
    document.getElementById('monto_aprobado_formatted').value = formatCurrency(rawValue);
  }
}
  



/**
 * Muestra una notificación temporal
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo de notificación (success, error, info)
 */
function showNotification(message, type = 'info') {
  // Crear elemento de notificación si no existe
  let notification = document.getElementById('notification');
  if (!notification) {
    notification = document.createElement('div');
    notification.id = 'notification';
    notification.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300 translate-y-20 opacity-0`;
    document.body.appendChild(notification);
  }
  
  // Establecer estilos según tipo
  if (type === 'success') {
    notification.className = notification.className.replace(/bg-\w+-\d+/g, '');
    notification.classList.add('bg-green-100', 'text-green-800', 'border-l-4', 'border-green-500');
  } else if (type === 'error') {
    notification.className = notification.className.replace(/bg-\w+-\d+/g, '');
    notification.classList.add('bg-red-100', 'text-red-800', 'border-l-4', 'border-red-500');
  } else {
    notification.className = notification.className.replace(/bg-\w+-\d+/g, '');
    notification.classList.add('bg-blue-100', 'text-blue-800', 'border-l-4', 'border-blue-500');
  }
  
  // Establecer mensaje
  notification.innerHTML = message;
  
  // Mostrar notificación
  setTimeout(() => {
    notification.classList.remove('translate-y-20', 'opacity-0');
  }, 10);
  
  // Ocultar después de 3 segundos
  setTimeout(() => {
    notification.classList.add('translate-y-20', 'opacity-0');
  }, 3000);
}