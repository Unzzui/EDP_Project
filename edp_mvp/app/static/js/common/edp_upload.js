// === EDP UPLOAD FUNCTIONALITY ===

// Variables globales
let currentFile = null;
let formOptions = null;
let projectsInfo = null; // Información completa de proyectos para autocompletado
let uploadStats = {
    total: 0,
    successful: 0,
    failed: 0,
    successRate: 0
};

// === INICIALIZACIÓN ===
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando EDP Upload...');
    
    initializeUploadFunctionality();
    loadUploadStats();
    setupAutoDateFields(); // Configurar fechas automáticas
    
    console.log('✅ EDP Upload inicializado correctamente');
});

// === FUNCIONES PRINCIPALES ===

function initializeUploadFunctionality() {
    // Configurar drag & drop para carga masiva
    setupDragAndDrop();
    
    // Configurar formulario manual
    setupManualForm();
    
    // Configurar validación en tiempo real
    setupRealTimeValidation();
    
    // Cargar opciones del formulario
    loadFormOptions();
}

// === CONFIGURACIÓN DE FECHAS AUTOMÁTICAS ===

function setupAutoDateFields() {
    // Configurar fecha de emisión con fecha de hoy por defecto
    const fechaEmisionInput = document.querySelector('input[name="fecha_emision"]');
    if (fechaEmisionInput) {
        const today = new Date().toISOString().split('T')[0];
        fechaEmisionInput.value = today;
        
        // Escuchar cambios para actualizar fecha estimada de pago
        fechaEmisionInput.addEventListener('change', updateFechaEstimadaPago);
        
        // Actualizar fecha estimada de pago inicialmente
        updateFechaEstimadaPago();
    }
}

function updateFechaEstimadaPago() {
    const fechaEmisionInput = document.querySelector('input[name="fecha_emision"]');
    const fechaEstimadaInput = document.querySelector('input[name="fecha_estimada_pago"]');
    
    if (fechaEmisionInput && fechaEstimadaInput && fechaEmisionInput.value) {
        const fechaEmision = new Date(fechaEmisionInput.value);
        fechaEmision.setDate(fechaEmision.getDate() + 30); // Agregar 30 días
        
        const fechaEstimada = fechaEmision.toISOString().split('T')[0];
        fechaEstimadaInput.value = fechaEstimada;
        
        // Generar el mes automáticamente
        updateMesField();
    }
}

function updateMesField() {
    const fechaEmisionInput = document.querySelector('input[name="fecha_emision"]');
    const mesInput = document.getElementById('mes-display');
    
    if (fechaEmisionInput && mesInput && fechaEmisionInput.value) {
        const fecha = new Date(fechaEmisionInput.value);
        const mes = fecha.toLocaleDateString('es-ES', { 
            year: 'numeric', 
            month: 'long' 
        });
        mesInput.textContent = mes;
    }
}

// === FORMATEO DE MONTOS ===

function formatMonto(input) {
    let value = input.value.replace(/[^\d]/g, ''); // Solo números
    if (value) {
        // Formatear con separadores de miles
        value = parseInt(value).toLocaleString('es-CL');
        input.value = value;
    }
}

function setupMontoFormatting() {
    const montoInputs = document.querySelectorAll('input[name="monto_propuesto"], input[name="monto_aprobado"]');
    montoInputs.forEach(input => {
        input.addEventListener('input', function() {
            formatMonto(this);
        });
        
        input.addEventListener('blur', function() {
            formatMonto(this);
        });
    });
}

// === CARGA DE OPCIONES ===

async function loadFormOptions() {
    try {
        console.log('📡 Solicitando opciones del formulario...');
        const response = await fetch('/edp/upload/options');
        const data = await response.json();
        
        if (data.success) {
            formOptions = data.options;
            projectsInfo = data.projects_info; // Guardar información de proyectos
            console.log('✅ Opciones del formulario cargadas:', formOptions);
            console.log('✅ Información de proyectos cargada:', projectsInfo);
            
            // Poblar opciones después de cargar
            populateSelectOptions();
        } else {
            console.error('❌ Error cargando opciones:', data.message);
            // Mostrar toast de error
            if (typeof showToast === 'function') {
                showToast('Error cargando opciones del formulario', 'error');
            }
        }
    } catch (error) {
        console.error('❌ Error de conexión cargando opciones:', error);
        // Mostrar toast de error
        if (typeof showToast === 'function') {
            showToast('Error de conexión al cargar opciones', 'error');
        }
    }
}

function populateSelectOptions() {
    if (!formOptions) return;
    
    // Poblar proyectos
    const proyectoSelect = document.querySelector('select[name="proyecto"]');
    if (proyectoSelect) {
        proyectoSelect.innerHTML = '<option value="">Seleccionar proyecto...</option>';
        formOptions.proyectos.forEach(proyecto => {
            const option = document.createElement('option');
            option.value = proyecto;
            option.textContent = proyecto;
            proyectoSelect.appendChild(option);
        });
        
        // Configurar autocompletado cuando cambie el proyecto
        proyectoSelect.addEventListener('change', handleProjectChange);
    }
    
    // Poblar clientes
    const clienteSelect = document.querySelector('select[name="cliente"]');
    if (clienteSelect) {
        clienteSelect.innerHTML = '<option value="">Seleccionar cliente...</option>';
        formOptions.clientes.forEach(cliente => {
            const option = document.createElement('option');
            option.value = cliente;
            option.textContent = cliente;
            clienteSelect.appendChild(option);
        });
    }
    
    // Poblar jefes de proyecto
    const jefeSelect = document.querySelector('select[name="jefe_proyecto"]');
    if (jefeSelect) {
        jefeSelect.innerHTML = '<option value="">Seleccionar jefe de proyecto...</option>';
        formOptions.jefes_proyecto.forEach(jefe => {
            const option = document.createElement('option');
            option.value = jefe;
            option.textContent = jefe;
            jefeSelect.appendChild(option);
        });
    }
    
    // Para gestores, crear datalist si no existe (para autocompletado)
    setupGestorAutocomplete();
}

function setupGestorAutocomplete() {
    const gestorInput = document.querySelector('input[name="gestor"]');
    if (gestorInput && formOptions && formOptions.gestores) {
        // Crear datalist para autocompletado
        let datalist = document.getElementById('gestores-datalist');
        if (!datalist) {
            datalist = document.createElement('datalist');
            datalist.id = 'gestores-datalist';
            document.body.appendChild(datalist);
        }
        
        // Limpiar y poblar datalist
        datalist.innerHTML = '';
        formOptions.gestores.forEach(gestor => {
            const option = document.createElement('option');
            option.value = gestor;
            datalist.appendChild(option);
        });
        
        // Asociar datalist con input
        gestorInput.setAttribute('list', 'gestores-datalist');
        gestorInput.setAttribute('placeholder', 'Escribir o seleccionar gestor...');
    }
}

function handleProjectChange(event) {
    const selectedProject = event.target.value;
    
    // Ocultar indicadores si no hay proyecto seleccionado
    if (!selectedProject) {
        hideAutocompleteIndicators();
        return;
    }
    
    if (!projectsInfo || !projectsInfo[selectedProject]) {
        console.warn(`⚠️ No se encontró información para el proyecto: ${selectedProject}`);
        hideAutocompleteIndicators();
        return;
    }
    
    const projectInfo = projectsInfo[selectedProject];
    let autocompletedFields = [];
    
    // Autocompletar cliente
    const clienteSelect = document.querySelector('select[name="cliente"]');
    const clienteIndicator = document.getElementById('cliente-autocomplete-indicator');
    
    if (clienteSelect && projectInfo.cliente) {
        clienteSelect.value = projectInfo.cliente;
        autocompletedFields.push('Cliente');
        
        // Mostrar indicador y feedback visual
        if (clienteIndicator) clienteIndicator.style.display = 'inline';
        animateFieldUpdate(clienteSelect);
    } else {
        if (clienteIndicator) clienteIndicator.style.display = 'none';
    }
    
    // Autocompletar jefe de proyecto
    const jefeSelect = document.querySelector('select[name="jefe_proyecto"]');
    const jefeIndicator = document.getElementById('jefe-autocomplete-indicator');
    
    if (jefeSelect && projectInfo.jefe_proyecto) {
        jefeSelect.value = projectInfo.jefe_proyecto;
        autocompletedFields.push('Jefe de Proyecto');
        
        // Mostrar indicador y feedback visual
        if (jefeIndicator) jefeIndicator.style.display = 'inline';
        animateFieldUpdate(jefeSelect);
    } else {
        if (jefeIndicator) jefeIndicator.style.display = 'none';
    }
    
    // Autocompletar gestor en el campo de texto
    const gestorInput = document.querySelector('input[name="gestor"]');
    const gestorIndicator = document.getElementById('gestor-autocomplete-indicator');
    
    if (gestorInput && projectInfo.gestor) {
        gestorInput.value = projectInfo.gestor;
        autocompletedFields.push('Gestor');
        
        // Mostrar indicador y feedback visual
        if (gestorIndicator) gestorIndicator.style.display = 'inline';
        animateFieldUpdate(gestorInput);
    } else {
        if (gestorIndicator) gestorIndicator.style.display = 'none';
    }
    
    // Mostrar toast informativo solo si se autocompletó algo
    if (autocompletedFields.length > 0) {
        showToast(
            `🚀 Autocompletado: ${autocompletedFields.join(', ')} para ${selectedProject}`, 
            'success'
        );
        
        console.log(`🔄 Autocompletado para ${selectedProject}:`, {
            cliente: projectInfo.cliente,
            jefe_proyecto: projectInfo.jefe_proyecto,
            gestor: projectInfo.gestor,
            fecha_inicio: projectInfo.fecha_inicio,
            fecha_fin_prevista: projectInfo.fecha_fin_prevista,
            monto_contrato: projectInfo.monto_contrato,
            moneda: projectInfo.moneda
        });
    }
}

function animateFieldUpdate(element) {
    // Agregar animación de feedback visual
    element.style.backgroundColor = '#dcfce7'; // Verde claro
    element.style.borderColor = '#10b981'; // Verde
    element.style.transform = 'scale(1.02)';
    
    setTimeout(() => {
        element.style.backgroundColor = '';
        element.style.borderColor = '';
        element.style.transform = '';
    }, 400);
}

function hideAutocompleteIndicators() {
    const indicators = [
        'cliente-autocomplete-indicator',
        'jefe-autocomplete-indicator', 
        'gestor-autocomplete-indicator'
    ];
    
    indicators.forEach(id => {
        const indicator = document.getElementById(id);
        if (indicator) indicator.style.display = 'none';
    });
}

function setupFechaEmisionListener() {
    const fechaEmisionInput = document.querySelector('input[name="fecha_emision"]');
    if (fechaEmisionInput) {
        fechaEmisionInput.addEventListener('change', function() {
            updateMesField();
            updateFechaEstimadaPago();
        });
        
        // Inicializar al cargar
        updateMesField();
        updateFechaEstimadaPago();
    }
}

// === MODAL MANUAL ===

function openManualUpload() {
    const modal = document.getElementById('manual-upload-modal');
    if (modal) {
        modal.style.display = 'flex';
        modal.style.opacity = '0';
        
        // Cargar opciones si no están cargadas, o poblar si ya están cargadas
        if (!formOptions) {
            console.log('🔄 Cargando opciones del formulario...');
            loadFormOptions();
        } else {
            console.log('🔄 Poblando opciones existentes...');
            populateSelectOptions();
        }
        
        // Configurar formateo de montos
        setupMontoFormatting();
        
        // Configurar fechas automáticas
        setupAutoDateFields();
        
        // Configurar listener de fecha emisión
        setupFechaEmisionListener();
        
        // Animación de entrada
        setTimeout(() => {
            modal.style.opacity = '1';
        }, 10);
        
        // Focus en primer campo
        const firstInput = modal.querySelector('input, select');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
}

function closeManualUpload() {
    const modal = document.getElementById('manual-upload-modal');
    if (modal) {
        modal.style.opacity = '0';
        setTimeout(() => {
            modal.style.display = 'none';
            // Limpiar formulario
            const form = modal.querySelector('form');
            if (form) {
                form.reset();
                // Ocultar indicadores de autocompletado
                hideAutocompleteIndicators();
                // Restablecer fechas automáticas
                setupAutoDateFields();
            }
        }, 300);
    }
}

// === CONFIGURACIÓN DEL FORMULARIO MANUAL ===

function setupManualForm() {
    const form = document.getElementById('manual-edp-form');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Feedback inmediato al hacer clic
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.classList.add('animate-pulse');
            setTimeout(() => submitButton.classList.remove('animate-pulse'), 200);
        }
        
        // Recopilar datos del formulario
        const formData = new FormData(form);
        const data = {};
        
        // Convertir FormData a objeto, limpiando montos
        for (let [key, value] of formData.entries()) {
            if (key === 'monto_propuesto' || key === 'monto_aprobado') {
                // Limpiar formato de montos (quitar puntos, comas)
                const cleanValue = value.replace(/[^\d]/g, '');
                data[key] = cleanValue ? parseInt(cleanValue) : (key === 'monto_propuesto' ? 0 : '');
            } else {
                data[key] = value.trim();
            }
        }
        
        console.log('📤 Enviando datos del formulario:', data);
        
        // Validar datos
        const validation = validateManualData(data);
        if (!validation.valid) {
            showValidationErrors(validation.errors);
            showToast('❌ Por favor corrija los errores antes de continuar', 'error');
            return;
        }
        
        try {
            // Mostrar indicadores de carga
            showFormLoading(true);
            showProgress(true);
            updateProgress(10, 'Validando datos...');
            
            // Pequeño delay para mostrar el feedback visual
            await new Promise(resolve => setTimeout(resolve, 200));
            
            updateProgress(30, 'Enviando EDP...');
            
            const response = await fetch('/edp/upload/manual', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            updateProgress(70, 'Procesando respuesta...');
            const result = await response.json();
            
            updateProgress(100, 'Completado');
            
            // Pequeño delay para mostrar completado
            await new Promise(resolve => setTimeout(resolve, 500));
            
            if (result.success) {
                showToast(result.message, 'success');
                closeManualUpload();
                loadUploadStats(); // Actualizar estadísticas
            } else {
                showToast(result.message || 'Error creando EDP', 'error');
                if (result.errors) {
                    showValidationErrors(result.errors);
                }
            }
            
        } catch (error) {
            console.error('❌ Error enviando formulario:', error);
            showToast('Error de conexión. Intente nuevamente.', 'error');
        } finally {
            showFormLoading(false);
            showProgress(false);
        }
    });
}

// === VALIDACIÓN EN TIEMPO REAL ===

function setupRealTimeValidation() {
    // Validar campo número EDP
    const nEdpInput = document.querySelector('input[name="n_edp"]');
    const proyectoSelect = document.querySelector('select[name="proyecto"]');
    
    if (nEdpInput) {
        nEdpInput.addEventListener('input', function() {
            // Solo permitir números
            this.value = this.value.replace(/[^\d]/g, '');
            
            // Validación de duplicados con debounce
            if (this.value && this.value.length > 0) {
                clearTimeout(this.validationTimeout);
                this.validationTimeout = setTimeout(() => {
                    validateEdpUnique(this.value);
                }, 500); // Esperar 500ms después de que el usuario deje de escribir
            }
        });
    }
    
    // Validar cuando cambie el proyecto
    if (proyectoSelect) {
        proyectoSelect.addEventListener('change', function() {
            // Re-validar EDP si ya hay un número ingresado
            if (nEdpInput && nEdpInput.value) {
                setTimeout(() => {
                    validateEdpUnique(nEdpInput.value);
                }, 100); // Pequeño delay para que se complete el cambio de proyecto
            }
        });
    }
    
    // Validar campos de montos
    const montoInputs = document.querySelectorAll('input[name="monto_propuesto"], input[name="monto_aprobado"]');
    montoInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Validar que solo sean números
            let value = this.value.replace(/[^\d]/g, '');
            if (value && parseInt(value) > 0) {
                this.classList.remove('invalid');
                this.classList.add('valid');
            } else if (this.name === 'monto_propuesto') {
                this.classList.add('invalid');
                this.classList.remove('valid');
            }
        });
    });
    
    // Validar fechas
    const fechaInputs = document.querySelectorAll('input[type="date"]');
    fechaInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.value) {
                this.classList.remove('invalid');
                this.classList.add('valid');
                
                // Actualizar campos dependientes
                if (this.name === 'fecha_emision') {
                    updateMesField();
                    updateFechaEstimadaPago();
                }
            } else if (this.name === 'fecha_emision') {
                this.classList.add('invalid');
                this.classList.remove('valid');
            }
        });
    });
}

async function validateEdpUnique(nedp) {
    const input = document.querySelector('input[name="n_edp"]');
    const proyectoInput = document.querySelector('select[name="proyecto"]');
    
    // Limpiar estados previos
    input.classList.remove('valid', 'invalid');
    
    // Validar formato básico
    if (!nedp || parseInt(nedp) <= 0) {
        input.classList.add('invalid');
        return;
    }
    
    // Validar si hay proyecto seleccionado
    if (!proyectoInput?.value) {
        return; // No validar duplicados sin proyecto
    }
    
    try {
        // Mostrar indicador de validación
        const validationIndicator = document.getElementById('edp-validation-indicator');
        if (validationIndicator) {
            validationIndicator.style.display = 'inline-block';
            validationIndicator.innerHTML = '🔍 Validando...';
        }
        
        const response = await fetch('/edp/upload/validate-duplicate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                n_edp: nedp,
                proyecto: proyectoInput.value
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (result.is_duplicate) {
                input.classList.add('invalid');
                input.classList.remove('valid');
                input.classList.add('validation-pulse');
                
                if (validationIndicator) {
                    validationIndicator.innerHTML = '❌ EDP duplicado';
                    validationIndicator.style.color = '#ef4444';
                }
                
                showToast(`❌ Ya existe un EDP #${nedp} para el proyecto ${proyectoInput.value}`, 'error');
            } else {
                input.classList.add('valid');
                input.classList.remove('invalid');
                input.classList.add('validation-pulse');
                
                if (validationIndicator) {
                    validationIndicator.innerHTML = '✅ EDP único';
                    validationIndicator.style.color = '#10b981';
                }
            }
            
            // Remover el efecto de pulso después de la animación
            setTimeout(() => {
                input.classList.remove('validation-pulse');
            }, 600);
        }
        
        // Ocultar indicador después de 3 segundos
        if (validationIndicator) {
            setTimeout(() => {
                validationIndicator.style.display = 'none';
            }, 3000);
        }
        
    } catch (error) {
        console.error('Error validando EDP único:', error);
        
        const validationIndicator = document.getElementById('edp-validation-indicator');
        if (validationIndicator) {
            validationIndicator.innerHTML = '⚠️ Error validando';
            validationIndicator.style.color = '#f59e0b';
            setTimeout(() => {
                validationIndicator.style.display = 'none';
            }, 3000);
        }
    }
}

// === CARGA MASIVA ===

function openBulkUpload() {
    const modal = document.getElementById('bulk-upload-modal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    resetBulkUpload();
}

function closeBulkUpload() {
    const modal = document.getElementById('bulk-upload-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    
    resetBulkUpload();
}

function setupDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('bulk-file-input');
    
    if (!dropZone || !fileInput) return;
    
    // Click para seleccionar archivo
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });
    
    // Drag & Drop con nueva UI
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
        // Mostrar estado de dragover
        const normalState = document.getElementById('drop-zone-normal');
        const dragoverState = document.getElementById('drop-zone-dragover');
        if (normalState && dragoverState) {
            normalState.classList.add('hidden');
            dragoverState.classList.remove('hidden');
        }
    });
    
    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        // Solo remover si realmente salimos del dropzone
        if (!dropZone.contains(e.relatedTarget)) {
            dropZone.classList.remove('dragover');
            // Restaurar estado normal
            const normalState = document.getElementById('drop-zone-normal');
            const dragoverState = document.getElementById('drop-zone-dragover');
            if (normalState && dragoverState) {
                normalState.classList.remove('hidden');
                dragoverState.classList.add('hidden');
            }
        }
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        // Restaurar estado normal
        const normalState = document.getElementById('drop-zone-normal');
        const dragoverState = document.getElementById('drop-zone-dragover');
        if (normalState && dragoverState) {
            normalState.classList.remove('hidden');
            dragoverState.classList.add('hidden');
        }
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });
    
    // Input file change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
}

async function handleFileSelection(file) {
    // Validar archivo
    const validation = validateFile(file);
    if (!validation.valid) {
        showToast(validation.message, 'error');
        return;
    }
    
    currentFile = file;
    
    // Mostrar progreso
    showProgress(true);
    updateProgress(5, 'Iniciando validación...');
    
    try {
        // Validar archivo en el servidor
        const formData = new FormData();
        formData.append('file', file);
        
        updateProgress(15, 'Subiendo archivo...');
        
        // Simular progreso de carga con más detalle
        setTimeout(() => updateProgress(25, 'Cargando caché de EDPs...'), 100);
        setTimeout(() => updateProgress(45, 'Caché listo, analizando contenido...'), 300);
        setTimeout(() => updateProgress(65, 'Validando estructura...'), 500);
        setTimeout(() => updateProgress(85, 'Verificando duplicados...'), 700);
        
        const response = await fetch('/edp/upload/validate', {
            method: 'POST',
            body: formData
        });
        
        // Obtener el texto de la respuesta una sola vez
        const responseText = await response.text();
        console.log('Respuesta del servidor:', responseText);
        
        // Verificar si la respuesta es exitosa
        if (!response.ok) {
            console.error('Error del servidor:', responseText);
            throw new Error(`Error del servidor: ${response.status} - ${responseText}`);
        }
        
        // Intentar parsear JSON con mejor manejo de errores
        let result;
        try {
            result = JSON.parse(responseText);
        } catch (parseError) {
            console.error('Error parseando JSON:', parseError);
            console.error('Respuesta recibida:', responseText);
            throw new Error('La respuesta del servidor no es JSON válido');
        }
        
        updateProgress(100, 'Validación completada');
        
        setTimeout(() => {
            showProgress(false);
            
            // Debug: Mostrar la respuesta completa en consola
            console.log('🔍 Respuesta completa del servidor:', result);
            console.log('🔍 Tiene sugerencias?', result.suggestions);
            
            if (result.success) {
                showFilePreview(result);
            } else {
                showValidationResults(result);
            }
        }, 500);
        
    } catch (error) {
        console.error('Error validando archivo:', error);
        showProgress(false);
        showToast(`❌ ${error.message || 'Error validando archivo. Inténtelo de nuevo.'}`, 'error');
    }
}

function showFilePreview(result) {
    const previewDiv = document.getElementById('file-preview');
    const previewTable = document.getElementById('preview-table');
    const fileInfo = document.getElementById('file-info');
    const fileCount = document.getElementById('file-count');
    const previewWarnings = document.getElementById('preview-warnings');
    
    if (!result.preview || result.preview.length === 0) {
        showToast('El archivo está vacío o no tiene datos válidos', 'error');
        return;
    }
    
    // Actualizar información del archivo
    if (fileInfo) {
        fileInfo.innerHTML = `
            <div class="text-center">
                <div class="text-2xl font-bold" style="color: var(--success)">${result.total_rows}</div>
                <div class="text-xs" style="color: var(--text-tertiary)">Total EDPs</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold" style="color: var(--accent-blue)">${result.columns.length}</div>
                <div class="text-xs" style="color: var(--text-tertiary)">Columnas</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold" style="color: var(--accent-purple)">${currentFile.name.split('.').pop().toUpperCase()}</div>
                <div class="text-xs" style="color: var(--text-tertiary)">Formato</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold" style="color: var(--text-secondary)">${(currentFile.size / 1024 / 1024).toFixed(1)}MB</div>
                <div class="text-xs" style="color: var(--text-tertiary)">Tamaño</div>
            </div>
        `;
    }
    
    // Actualizar contador en el botón
    if (fileCount) {
        fileCount.textContent = result.total_rows;
    }
    
    // Crear tabla de preview con estilos mejorados
    const headers = Object.keys(result.preview[0]);
    let tableHTML = '<thead style="background-color: var(--bg-subtle)"><tr>';
    headers.forEach(header => {
        tableHTML += `<th class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider border-b" style="color: var(--text-secondary); border-color: var(--border-color)">${header}</th>`;
    });
    tableHTML += '</tr></thead><tbody style="background-color: var(--bg-card)" class="divide-y" style="border-color: var(--border-color-subtle)">';
    
    result.preview.forEach((row, index) => {
        tableHTML += `<tr class="transition-colors" style="hover: background-color: var(--bg-hover)">`;
        headers.forEach(header => {
            const value = row[header] || '';
            const displayValue = value.toString().length > 30 ? value.toString().substring(0, 30) + '...' : value;
            tableHTML += `<td class="px-4 py-3 text-sm whitespace-nowrap" style="color: var(--text-primary)" title="${value}">${displayValue}</td>`;
        });
        tableHTML += '</tr>';
    });
    tableHTML += '</tbody>';
    
    previewTable.innerHTML = tableHTML;
    
    // Mostrar warnings si los hay
    if (result.validation.warnings && result.validation.warnings.length > 0 && previewWarnings) {
        previewWarnings.innerHTML = `
            <div style="background-color: var(--warning-bg); border-color: var(--border-color)" class="border rounded-xl p-4">
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" style="color: var(--warning)" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                    </div>
                    <div>
                        <h4 class="font-medium mb-2" style="color: var(--text-primary)">⚠️ Advertencias:</h4>
                        <ul class="text-sm space-y-1" style="color: var(--text-secondary)">
                            ${result.validation.warnings.map(warning => `<li>• ${warning}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
        previewWarnings.classList.remove('hidden');
    }
    
    // Mostrar el preview
    previewDiv.classList.remove('hidden');
    
    // Scroll suave hacia el preview
    previewDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showValidationResults(result) {
    const previewDiv = document.getElementById('file-preview');
    
    // Debug: Log de la función
    console.log('🔍 showValidationResults llamada con:', result);
    console.log('🔍 result.suggestions:', result.suggestions);
    console.log('🔍 result.errors:', result.errors);
    
    // Verificar si hay sugerencias de duplicados
    const hasSuggestions = result.suggestions && result.suggestions.has_duplicates;
    
    let html = `
        <div class="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-2xl p-6">
            <div class="flex items-center space-x-3 mb-4">
                <div class="flex-shrink-0">
                    <div class="w-10 h-10 bg-red-500 rounded-lg flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                    </div>
                </div>
                <div>
                    <h3 class="text-lg font-semibold text-red-800">
                        ❌ ${hasSuggestions ? 'EDPs Duplicados Encontrados' : 'Errores de Validación'}
                    </h3>
                    <p class="text-sm text-red-600">
                        ${hasSuggestions ? 'Tenemos sugerencias para corregir automáticamente' : 'Corrija los errores para continuar'}
                    </p>
                </div>
            </div>
    `;
    
    if (hasSuggestions) {
        // Mostrar sugerencias para duplicados
        html += `
            <div class="bg-white rounded-xl border border-red-200 p-4 mb-4">
                <h4 class="font-medium text-red-800 mb-3">🔍 EDPs Duplicados y Sugerencias:</h4>
                <div class="space-y-3 max-h-60 overflow-y-auto">
        `;
        
        result.suggestions.duplicates.forEach(duplicate => {
            html += `
                <div class="bg-red-50 border border-red-200 rounded-lg p-3">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <p class="text-sm font-medium text-red-800">
                                Fila ${duplicate.row}: EDP #${duplicate.current_edp} ya existe
                            </p>
                            <p class="text-xs text-red-600 mt-1">
                                Proyecto: ${duplicate.proyecto} | Cliente: ${duplicate.cliente}
                            </p>
                        </div>
                        <div class="ml-4">
                            <span class="text-xs text-red-500 font-medium">
                                $${(duplicate.monto || 0).toLocaleString()}
                            </span>
                        </div>
                    </div>
                    
                    ${duplicate.suggested_numbers && duplicate.suggested_numbers.length > 0 ? `
                        <div class="mt-2 pt-2 border-t border-red-200">
                            <p class="text-xs text-green-700 font-medium mb-1">💡 Números disponibles:</p>
                            <div class="flex space-x-2">
                                ${duplicate.suggested_numbers.map(num => 
                                    `<span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-md font-medium">#${num}</span>`
                                ).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
            
            <!-- Botones de acción para sugerencias -->
            <div class="flex flex-col sm:flex-row gap-3 justify-end">
                <button onclick="resetBulkUpload()" 
                        class="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Seleccionar Otro Archivo
                </button>
                <button onclick="applySuggestions()" 
                        class="px-6 py-2 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-lg hover:shadow-lg transition-all duration-300 font-medium">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Aplicar Sugerencias y Descargar
                </button>
            </div>
        `;
    } else {
        // Mostrar errores generales
                 html += `
             <div class="bg-white rounded-xl border border-red-200 p-4 mb-4">
                 <h4 class="font-medium text-red-800 mb-3">Errores Encontrados:</h4>
                 <ul class="text-sm text-red-700 space-y-2 max-h-40 overflow-y-auto">
         `;
         
         // Manejar errores directamente en result.errors
         if (result.errors && Array.isArray(result.errors)) {
             result.errors.forEach(error => {
                 html += `<li class="flex items-start"><span class="text-red-500 mr-2">•</span><span>${error}</span></li>`;
             });
         }
         
         // Fallback para errores en result.validation
         if (result.validation && result.validation.errors) {
             result.validation.errors.forEach(error => {
                 html += `<li class="flex items-start"><span class="text-red-500 mr-2">•</span><span>${error}</span></li>`;
             });
         }
         
         if (result.validation && result.validation.row_errors) {
             result.validation.row_errors.forEach(rowError => {
                 html += `<li class="flex items-start"><span class="text-red-500 mr-2">•</span><span>Fila ${rowError.row}: ${Object.values(rowError.errors).join(', ')}</span></li>`;
             });
         }
        
        html += `
                </ul>
            </div>
            
            <div class="flex justify-end">
                <button onclick="resetBulkUpload()" 
                        class="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors">
                    Seleccionar Otro Archivo
                </button>
            </div>
        `;
    }
    
    html += `</div>`;
    
    previewDiv.innerHTML = html;
    previewDiv.classList.remove('hidden');
    
    // Guardar sugerencias para uso posterior
    if (hasSuggestions) {
        window.currentSuggestions = result.suggestions;
    }
}

async function processBulkUpload() {
    if (!currentFile) {
        showToast('No hay archivo seleccionado', 'error');
        setProcessButtonLoading(false);
        showGlobalLoading(false);
        return;
    }
    
    // Ocultar preview y mostrar progreso
    document.getElementById('file-preview').classList.add('hidden');
    showProgress(true);
    
    // Actualizar progreso global
    updateGlobalProgress(25, 'Preparando archivo para subida...', 2);
    
    try {
        const formData = new FormData();
        formData.append('file', currentFile);
        
        // Progreso: Subiendo archivo
        updateProgress(20, 'Subiendo archivo...');
        updateGlobalProgress(40, 'Subiendo archivo al servidor...', 2);
        
        const response = await fetch('/edp/upload/bulk', {
            method: 'POST',
            body: formData
        });
        
        // Progreso: Procesando datos
        updateProgress(60, 'Procesando datos...');
        updateGlobalProgress(70, 'Procesando y validando datos...', 3);
        
        const result = await response.json();
        
        // Progreso: Completado
        updateProgress(100, 'Procesamiento completado');
        updateGlobalProgress(100, 'Procesamiento completado exitosamente', 4);
        
        setTimeout(() => {
            showProgress(false);
            setProcessButtonLoading(false);
            
            // Mostrar overlay de éxito
            showSuccessOverlay(result.stats || {});
            
            // Mostrar resultados después del overlay
            setTimeout(() => {
                showUploadResults(result);
            }, 3500);
        }, 500);
        
    } catch (error) {
        console.error('Error procesando archivo:', error);
        showProgress(false);
        setProcessButtonLoading(false);
        showGlobalLoading(false);
        showToast('Error procesando archivo. Inténtelo de nuevo.', 'error');
    }
}

function showUploadResults(result) {
    const resultsDiv = document.getElementById('upload-results');
    const resultsContent = document.getElementById('results-content');
    
    const stats = result.stats || {};
    const isSuccess = result.success && stats.success_count > 0;
    
    let html = `
        <div class="space-y-4">
            <!-- Resumen -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-[color:var(--bg-secondary)] p-4 rounded-lg text-center">
                    <div class="text-2xl font-bold text-[color:var(--accent-blue)]">${stats.total_rows || 0}</div>
                    <div class="text-sm text-[color:var(--text-secondary)]">Total Procesados</div>
                </div>
                <div class="bg-[color:var(--bg-secondary)] p-4 rounded-lg text-center">
                    <div class="text-2xl font-bold text-[color:var(--accent-green)]">${stats.success_count || 0}</div>
                    <div class="text-sm text-[color:var(--text-secondary)]">Exitosos</div>
                </div>
                <div class="bg-[color:var(--bg-secondary)] p-4 rounded-lg text-center">
                    <div class="text-2xl font-bold text-[color:var(--accent-red)]">${stats.error_count || 0}</div>
                    <div class="text-sm text-[color:var(--text-secondary)]">Errores</div>
                </div>
                <div class="bg-[color:var(--bg-secondary)] p-4 rounded-lg text-center">
                    <div class="text-2xl font-bold text-[color:var(--accent-purple)]">${(stats.success_rate || 0).toFixed(1)}%</div>
                    <div class="text-sm text-[color:var(--text-secondary)]">Tasa de Éxito</div>
                </div>
            </div>
    `;
    
    // Mostrar información de correcciones si se aplicaron
    if (result.corrections_applied && result.corrections_applied > 0) {
        html += `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <div>
                        <h4 class="font-medium text-blue-800 mb-2">🔧 Correcciones Aplicadas Automáticamente</h4>
                        <p class="text-sm text-blue-700 mb-3">
                            Se aplicaron <strong>${result.corrections_applied}</strong> correcciones automáticamente para resolver duplicados:
                        </p>
        `;
        
        if (result.correction_details && result.correction_details.length > 0) {
            html += `<ul class="text-sm text-blue-600 space-y-1">`;
            result.correction_details.forEach(correction => {
                html += `
                    <li>• Fila ${correction.row}: EDP #${correction.old_edp} → #${correction.new_edp} (${correction.proyecto})</li>
                `;
            });
            html += `</ul>`;
        }
        
        html += `
                    </div>
                </div>
            </div>
        `;
    }
    
    html += `
            <!-- Mensaje principal -->
            <div class="p-4 rounded-lg ${isSuccess ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}">
                <div class="font-medium ${isSuccess ? 'text-green-800' : 'text-red-800'}">
                    ${isSuccess ? '✅' : '❌'} ${result.message}
                </div>
            </div>
    `;
    
    // Mostrar errores si los hay
    if (result.errors && result.errors.length > 0) {
        html += `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <h4 class="font-medium text-red-800 mb-2">Errores Encontrados:</h4>
                <div class="max-h-40 overflow-y-auto">
                    <ul class="text-sm text-red-700 space-y-1">
        `;
        
        result.errors.slice(0, 10).forEach(error => {
            if (error.row) {
                html += `<li>• Fila ${error.row}: ${JSON.stringify(error.errors || error.error)}</li>`;
            } else {
                html += `<li>• ${error.error || error}</li>`;
            }
        });
        
        if (result.errors.length > 10) {
            html += `<li class="font-medium">... y ${result.errors.length - 10} errores más</li>`;
        }
        
        html += `
                    </ul>
                </div>
            </div>
        `;
    }
    
    // Botones de acción
    html += `
            <div class="flex justify-between">
                <button onclick="resetBulkUpload()" 
                        class="px-4 py-2 border border-[color:var(--border-color)] text-[color:var(--text-secondary)] rounded-lg hover:bg-[color:var(--bg-card-hover)] transition-colors">
                    Subir Otro Archivo
                </button>
                <div class="space-x-2">
                    ${isSuccess ? `
                        <button onclick="goToKanban()" 
                                class="px-6 py-2 bg-[color:var(--accent-blue)] text-white rounded-lg hover:bg-blue-600 transition-colors">
                            Ver en Kanban
                        </button>
                    ` : ''}
                    <button onclick="closeBulkUpload()" 
                            class="px-6 py-2 bg-[color:var(--accent-green)] text-white rounded-lg hover:bg-green-600 transition-colors">
                            Finalizar
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultsContent.innerHTML = html;
    resultsDiv.classList.remove('hidden');
    
    // Actualizar estadísticas globales
    updateUploadStats(
        stats.total_rows || 0,
        stats.success_count || 0,
        stats.error_count || 0
    );
}

// === FUNCIONES DE UI ===

function showGlobalLoading(show = true) {
    const overlay = document.getElementById('global-loading-overlay');
    if (show) {
        overlay.classList.remove('hidden');
        // Resetear estado inicial
        updateGlobalProgress(0, 'Iniciando procesamiento...', 1);
    } else {
        overlay.classList.add('hidden');
    }
}

function updateGlobalProgress(percentage, message, step = 1) {
    // Actualizar barra de progreso
    const progressBar = document.getElementById('loading-progress-bar');
    const percentageSpan = document.getElementById('loading-percentage');
    const messageSpan = document.getElementById('loading-message');
    const stepSpan = document.getElementById('loading-step');
    
    if (progressBar) progressBar.style.width = percentage + '%';
    if (percentageSpan) percentageSpan.textContent = percentage + '%';
    if (messageSpan) messageSpan.textContent = message;
    if (stepSpan) stepSpan.textContent = `Paso ${step} de 4`;
    
    // Actualizar indicadores de etapas
    for (let i = 1; i <= 4; i++) {
        const stepElement = document.getElementById(`step-${i}`);
        const dot = stepElement?.querySelector('div');
        
        if (stepElement && dot) {
            if (i < step) {
                // Paso completado
                stepElement.classList.remove('opacity-50');
                stepElement.style.color = 'var(--success)';
                dot.style.backgroundColor = 'var(--success)';
            } else if (i === step) {
                // Paso actual
                stepElement.classList.remove('opacity-50');
                stepElement.style.color = 'var(--accent-blue)';
                dot.style.backgroundColor = 'var(--accent-blue)';
                dot.classList.add('animate-pulse');
            } else {
                // Paso pendiente
                stepElement.classList.add('opacity-50');
                stepElement.style.color = '';
                dot.style.backgroundColor = '';
                dot.classList.remove('animate-pulse');
            }
        }
    }
    
    // Cambiar icono según el progreso
    const icon = document.getElementById('loading-icon');
    if (icon && percentage >= 100) {
        // Cambiar a icono de éxito
        icon.classList.remove('animate-spin');
        icon.innerHTML = `
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        `;
        icon.style.color = 'var(--success)';
        icon.setAttribute('fill', 'none');
        icon.setAttribute('stroke', 'currentColor');
    }
}

function showSuccessOverlay(stats) {
    const overlay = document.getElementById('global-loading-overlay');
    const title = document.getElementById('loading-title');
    const message = document.getElementById('loading-message');
    const cancelBtn = document.getElementById('cancel-processing');
    
    // Cambiar a estado de éxito
    if (title) title.textContent = '✅ Procesamiento Completado';
    
    // Mensaje personalizado si se aplicaron correcciones
    let messageText = `Se procesaron ${stats.success_count || 0} EDPs exitosamente`;
    if (stats.corrections_applied && stats.corrections_applied > 0) {
        messageText += ` (${stats.corrections_applied} correcciones aplicadas automáticamente)`;
    }
    
    if (message) message.textContent = messageText;
    
    // Cambiar botón de cancelar por cerrar
    if (cancelBtn) {
        cancelBtn.textContent = 'Cerrar';
        cancelBtn.onclick = () => {
            showGlobalLoading(false);
            showUploadResults(stats);
        };
    }
    
    // Auto-cerrar después de 3 segundos
    setTimeout(() => {
        if (overlay && !overlay.classList.contains('hidden')) {
            showGlobalLoading(false);
            showUploadResults(stats);
        }
    }, 3000);
}

function cancelProcessing() {
    showGlobalLoading(false);
    setProcessButtonLoading(false);
    showToast('Procesamiento cancelado', 'warning');
}

async function applySuggestions() {
    if (!currentFile || !window.currentSuggestions) {
        showToast('No hay sugerencias disponibles', 'error');
        return;
    }
    
    try {
        // Mostrar loading global inmediatamente
        showGlobalLoading(true);
        updateGlobalProgress(10, 'Aplicando sugerencias automáticamente...', 1);
        
        showToast('Aplicando sugerencias y procesando automáticamente...', 'info');
        
        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('suggestions', JSON.stringify(window.currentSuggestions));
        
        // Progreso: Aplicando correcciones
        updateGlobalProgress(30, 'Corrigiendo números EDP duplicados...', 2);
        
        const response = await fetch('/edp/upload/apply-suggestions-and-process', {
            method: 'POST',
            body: formData
        });
        
        // Progreso: Procesando
        updateGlobalProgress(60, 'Procesando archivo corregido...', 3);
        
        const result = await response.json();
        
        if (result.success) {
            // Progreso: Completado
            updateGlobalProgress(100, 'Procesamiento completado exitosamente', 4);
            
            showToast('✅ Sugerencias aplicadas y archivo procesado exitosamente', 'success');
            
            // Ocultar preview de validación
            document.getElementById('file-preview').classList.add('hidden');
            
            setTimeout(() => {
                showGlobalLoading(false);
                
                // Mostrar overlay de éxito con información de correcciones
                const stats = result.stats || {};
                stats.corrections_applied = result.corrections_applied || 0;
                showSuccessOverlay(stats);
                
                // Mostrar resultados después del overlay
                setTimeout(() => {
                    showUploadResults(result);
                }, 3500);
            }, 500);
            
        } else {
            showGlobalLoading(false);
            showToast(`Error procesando archivo: ${result.message}`, 'error');
        }
        
    } catch (error) {
        console.error('Error aplicando sugerencias:', error);
        showGlobalLoading(false);
        showToast('Error aplicando sugerencias. Inténtelo de nuevo.', 'error');
    }
}

function showSuggestionSuccessMessage(filename) {
    const previewDiv = document.getElementById('file-preview');
    
    const html = `
        <div class="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-2xl p-6">
            <div class="flex items-center space-x-3 mb-4">
                <div class="flex-shrink-0">
                    <div class="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                </div>
                <div>
                    <h3 class="text-lg font-semibold text-green-800">
                        ✅ Sugerencias Aplicadas Exitosamente
                    </h3>
                    <p class="text-sm text-green-600">
                        Archivo corregido descargado: <strong>${filename}</strong>
                    </p>
                </div>
            </div>
            
            <div class="bg-white rounded-xl border border-green-200 p-4 mb-4">
                <h4 class="font-medium text-green-800 mb-3">📋 Próximos Pasos:</h4>
                <ol class="text-sm text-green-700 space-y-2">
                    <li class="flex items-start">
                        <span class="text-green-500 mr-2 font-bold">1.</span>
                        <span>Revisa el archivo descargado <strong>${filename}</strong></span>
                    </li>
                    <li class="flex items-start">
                        <span class="text-green-500 mr-2 font-bold">2.</span>
                        <span>Los números EDP duplicados han sido reemplazados automáticamente</span>
                    </li>
                    <li class="flex items-start">
                        <span class="text-green-500 mr-2 font-bold">3.</span>
                        <span>Sube el archivo corregido para procesarlo sin errores</span>
                    </li>
                </ol>
            </div>
            
            <div class="flex flex-col sm:flex-row gap-3 justify-end">
                <button onclick="resetBulkUpload()" 
                        class="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    Subir Archivo Corregido
                </button>
            </div>
        </div>
    `;
    
    previewDiv.innerHTML = html;
}

function handleProcessClick() {
    const processButton = document.getElementById('process-button');
    
    // Feedback visual inmediato al hacer clic
    if (processButton) {
        processButton.style.transform = 'scale(0.95)';
        setTimeout(() => {
            processButton.style.transform = '';
        }, 100);
    }
    
    // Mostrar overlay de carga global inmediatamente
    showGlobalLoading(true);
    
    // Activar inmediatamente el estado de carga del botón también
    setTimeout(() => {
        setProcessButtonLoading(true);
        
        // Simular progreso inicial
        setTimeout(() => {
            updateGlobalProgress(15, 'Validando archivos y verificando duplicados...', 1);
        }, 300);
        
        // Iniciar el procesamiento
        setTimeout(() => {
            processBulkUpload();
        }, 600);
    }, 50);
}

function setProcessButtonLoading(isLoading) {
    const processButton = document.getElementById('process-button') || document.querySelector('button[onclick*="processBulkUpload"]');
    const cancelButton = document.querySelector('button[onclick="resetBulkUpload()"]');
    
    if (!processButton) {
        console.warn('Process button not found');
        return;
    }
    
    if (isLoading) {
        // Deshabilitar ambos botones
        processButton.disabled = true;
        cancelButton.disabled = true;
        
        // Cambiar el contenido del botón
        processButton.innerHTML = `
            <svg class="animate-spin h-5 w-5 mr-2 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Procesando EDPs...
        `;
        
        // Agregar estilos de carga
        processButton.classList.add('opacity-75', 'cursor-not-allowed', 'btn-loading');
        cancelButton.classList.add('opacity-50', 'cursor-not-allowed');
        
    } else {
        // Habilitar botones
        processButton.disabled = false;
        cancelButton.disabled = false;
        
        // Restaurar contenido original
        const fileCount = document.getElementById('file-count')?.textContent || '';
        processButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Procesar&nbsp;<span id="file-count">${fileCount}</span>&nbsp;EDPs
        `;
        
        // Remover estilos de carga
        processButton.classList.remove('opacity-75', 'cursor-not-allowed', 'btn-loading');
        cancelButton.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

// === FUNCIONES AUXILIARES ===

function validateFile(file) {
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
        'application/vnd.ms-excel', // .xls
        'text/csv' // .csv
    ];
    
    if (file.size > maxSize) {
        return {
            valid: false,
            message: 'El archivo es demasiado grande. Máximo 16MB.'
        };
    }
    
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
        return {
            valid: false,
            message: 'Tipo de archivo no válido. Use .xlsx, .xls o .csv'
        };
    }
    
    return { valid: true };
}

function validateManualData(data) {
    const errors = [];
    
    // Campos requeridos actualizados
    const required = ['n_edp', 'proyecto', 'cliente', 'jefe_proyecto', 'fecha_emision', 'monto_propuesto'];
    
    required.forEach(field => {
        if (!data[field] || String(data[field]).trim() === '') {
            errors.push(`El campo ${field} es obligatorio`);
        }
    });
    
    // Validar N° EDP
    if (data.n_edp) {
        const nEdp = parseInt(data.n_edp);
        if (isNaN(nEdp) || nEdp <= 0) {
            errors.push('N° EDP debe ser un número entero positivo');
        }
        
        // Verificar si el campo tiene clase 'invalid' (duplicado detectado)
        const nEdpInput = document.querySelector('input[name="n_edp"]');
        if (nEdpInput && nEdpInput.classList.contains('invalid')) {
            errors.push(`❌ Ya existe un EDP #${nEdp} para el proyecto ${data.proyecto}. No se pueden crear EDPs duplicados.`);
        }
    }
    
    // Validar monto propuesto (obligatorio)
    if (data.monto_propuesto) {
        // Limpiar formato antes de validar
        const cleanMonto = String(data.monto_propuesto).replace(/[^\d]/g, '');
        const monto = parseInt(cleanMonto);
        if (isNaN(monto) || monto <= 0) {
            errors.push('Monto propuesto debe ser un número mayor a 0');
        }
    }
    
    // Validar monto aprobado (opcional, pero si existe debe ser válido)
    if (data.monto_aprobado && String(data.monto_aprobado).trim() !== '') {
        const cleanMonto = String(data.monto_aprobado).replace(/[^\d]/g, '');
        const monto = parseInt(cleanMonto);
        if (isNaN(monto) || monto < 0) {
            errors.push('Monto aprobado debe ser un número válido mayor o igual a 0');
        }
    }
    
    // Validar fecha de emisión
    if (data.fecha_emision) {
        try {
            const fecha = new Date(data.fecha_emision);
            if (isNaN(fecha.getTime())) {
                errors.push('Fecha de emisión no válida');
            }
        } catch (e) {
            errors.push('Formato de fecha de emisión incorrecto');
        }
    }
    
    // Validar fechas opcionales
    const optionalDateFields = ['fecha_envio_cliente', 'fecha_estimada_pago'];
    optionalDateFields.forEach(field => {
        if (data[field] && String(data[field]).trim() !== '') {
            try {
                const fecha = new Date(data[field]);
                if (isNaN(fecha.getTime())) {
                    errors.push(`${field} no válida`);
                }
            } catch (e) {
                errors.push(`Formato de ${field} incorrecto`);
            }
        }
    });
    
    return {
        valid: errors.length === 0,
        errors: errors
    };
}

function showValidationErrors(errors) {
    // Limpiar errores previos
    document.querySelectorAll('.field-error').forEach(el => el.remove());
    document.querySelectorAll('input, select').forEach(el => {
        el.classList.remove('border-red-500');
    });
    
    // Si errors es un array de strings
    if (Array.isArray(errors)) {
        // Mostrar errores generales en un toast
        const errorMessage = errors.join('\n');
        showToast(errorMessage, 'error');
        return;
    }
    
    // Si errors es un objeto con errores por campo
    Object.keys(errors).forEach(field => {
        const input = document.querySelector(`[name="${field}"]`);
        if (input) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error text-sm text-red-600 mt-1';
            
            // Manejar diferentes formatos de error
            const fieldErrors = Array.isArray(errors[field]) ? errors[field] : [errors[field]];
            errorDiv.textContent = fieldErrors.join(', ');
            
            input.parentNode.appendChild(errorDiv);
            
            // Resaltar campo con error
            input.classList.add('border-red-500');
            
            // Remover resaltado al corregir
            input.addEventListener('input', function() {
                this.classList.remove('border-red-500');
                const errorEl = this.parentNode.querySelector('.field-error');
                if (errorEl) errorEl.remove();
            }, { once: true });
        }
    });
}

function showProgress(show) {
    const progressDiv = document.getElementById('upload-progress');
    if (show) {
        progressDiv.classList.remove('hidden');
    } else {
        progressDiv.classList.add('hidden');
        // Reset progress when hiding
        updateProgress(0, 'Preparando...');
    }
}

function showFormLoading(show) {
    // Deshabilitar/habilitar el formulario
    const form = document.getElementById('manual-edp-form');
    const submitButton = form?.querySelector('button[type="submit"]');
    const inputs = form?.querySelectorAll('input, select, textarea');
    
    if (show) {
        // Deshabilitar todos los campos
        inputs?.forEach(input => {
            input.disabled = true;
            input.style.opacity = '0.6';
        });
        
        // Cambiar el botón de envío
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = `
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creando EDP...
            `;
            submitButton.classList.add('opacity-75', 'cursor-not-allowed');
        }
    } else {
        // Habilitar todos los campos
        inputs?.forEach(input => {
            input.disabled = false;
            input.style.opacity = '1';
        });
        
        // Restaurar el botón de envío
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Crear EDP
            `;
            submitButton.classList.remove('opacity-75', 'cursor-not-allowed');
        }
    }
}

function updateProgress(percentage, message) {
    const progressBar = document.getElementById('progress-bar');
    const progressPercentage = document.getElementById('progress-percentage');
    const progressMessage = document.getElementById('progress-message');
    const progressTitle = document.getElementById('progress-title');
    const progressIcon = document.getElementById('progress-icon');
    
    if (progressBar) {
        progressBar.style.width = percentage + '%';
    }
    
    if (progressPercentage) {
        progressPercentage.textContent = percentage + '%';
    }
    
    if (progressMessage && message) {
        progressMessage.textContent = message;
    }
    
    // Actualizar título según el progreso
    if (progressTitle) {
        if (percentage < 30) {
            progressTitle.textContent = 'Validando archivo...';
        } else if (percentage < 70) {
            progressTitle.textContent = 'Analizando contenido...';
        } else if (percentage < 100) {
            progressTitle.textContent = 'Finalizando validación...';
        } else {
            progressTitle.textContent = 'Validación completada';
        }
    }
    
    // Actualizar indicadores de etapas
    const stages = ['stage-1', 'stage-2', 'stage-3', 'stage-4'];
    stages.forEach((stageId, index) => {
        const stage = document.getElementById(stageId);
        if (stage) {
            const stageProgress = (index + 1) * 25;
            if (percentage >= stageProgress) {
                stage.classList.remove('opacity-50');
                stage.classList.add('font-medium');
                stage.style.color = 'var(--accent-blue)';
            } else {
                stage.classList.add('opacity-50');
                stage.classList.remove('font-medium');
                stage.style.color = '';
            }
        }
    });
    
    // Cambiar icono cuando se complete
    if (percentage >= 100 && progressIcon) {
        progressIcon.classList.remove('animate-spin');
        progressIcon.innerHTML = `
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        `;
    }
    
    console.log(`Progress: ${percentage}% - ${message}`);
}

function resetBulkUpload() {
    currentFile = null;
    
    // Resetear estado del botón de procesar
    setProcessButtonLoading(false);
    
    // Ocultar overlay global de carga
    showGlobalLoading(false);
    
    // Ocultar secciones
    document.getElementById('file-preview').classList.add('hidden');
    document.getElementById('upload-results').classList.add('hidden');
    document.getElementById('preview-warnings').classList.add('hidden');
    showProgress(false);
    
    // Limpiar contenido
    document.getElementById('preview-table').innerHTML = '';
    document.getElementById('file-info').innerHTML = '';
    document.getElementById('preview-warnings').innerHTML = '';
    document.getElementById('results-content').innerHTML = '';
    document.getElementById('bulk-file-input').value = '';
    
    // Resetear drop zone
    const dropZone = document.getElementById('drop-zone');
    const normalState = document.getElementById('drop-zone-normal');
    const dragoverState = document.getElementById('drop-zone-dragover');
    
    dropZone.classList.remove('dragover');
    
    if (normalState && dragoverState) {
        normalState.classList.remove('hidden');
        dragoverState.classList.add('hidden');
    }
    
    // Resetear progreso
    const progressIcon = document.getElementById('progress-icon');
    if (progressIcon) {
        progressIcon.classList.add('animate-spin');
        progressIcon.innerHTML = `
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        `;
    }
}

function updateUploadStats(total, successful, failed) {
    uploadStats.total += total;
    uploadStats.successful += successful;
    uploadStats.failed += failed;
    uploadStats.successRate = uploadStats.total > 0 ? (uploadStats.successful / uploadStats.total) * 100 : 0;
    
    // Actualizar UI
    document.getElementById('total-uploads').textContent = uploadStats.total;
    document.getElementById('successful-uploads').textContent = uploadStats.successful;
    document.getElementById('failed-uploads').textContent = uploadStats.failed;
    document.getElementById('success-rate').textContent = uploadStats.successRate.toFixed(1) + '%';
    
    // Guardar en localStorage
    localStorage.setItem('edp_upload_stats', JSON.stringify(uploadStats));
}

function loadUploadStats() {
    const saved = localStorage.getItem('edp_upload_stats');
    if (saved) {
        uploadStats = JSON.parse(saved);
        updateUploadStats(0, 0, 0); // Solo actualizar UI
    }
}

function goToKanban() {
    window.location.href = '/control/';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white z-50 animate__animated animate__fadeInUp`;
    
    switch (type) {
        case 'success':
            toast.classList.add('bg-green-600');
            message = `✅ ${message}`;
            break;
        case 'error':
            toast.classList.add('bg-red-600');
            message = `❌ ${message}`;
            break;
        case 'warning':
            toast.classList.add('bg-yellow-600');
            message = `⚠️ ${message}`;
            break;
        default:
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
    
    // Auto-remove después de 5 segundos
    setTimeout(() => {
        if (document.body.contains(toast)) {
            toast.classList.replace('animate__fadeInUp', 'animate__fadeOutDown');
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 500);
        }
    }, 5000);
}

// === FUNCIONES GLOBALES ===
window.openManualUpload = openManualUpload;
window.closeManualUpload = closeManualUpload;
window.openBulkUpload = openBulkUpload;
window.closeBulkUpload = closeBulkUpload;
window.processBulkUpload = processBulkUpload;
window.handleProcessClick = handleProcessClick;
window.resetBulkUpload = resetBulkUpload;
window.cancelProcessing = cancelProcessing;
window.applySuggestions = applySuggestions;
window.goToKanban = goToKanban;

console.log('📋 EDP Upload JS cargado correctamente'); 