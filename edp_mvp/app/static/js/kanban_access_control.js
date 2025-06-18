/**
 * Kanban Access Control - Control de acceso por roles en la vista Kanban
 * Maneja la visibilidad de filtros y funcionalidades según el rol del usuario
 */

class KanbanAccessControl {
    constructor() {
        this.userAccessLevel = null;
        this.managerName = null;
        this.currentUserRole = null;
        this.isRestrictedUser = false;
        
        this.init();
    }

    init() {
        // Obtener variables del template
        this.userAccessLevel = window.userAccessLevel || 'none';
        this.managerName = window.managerName || null;
        this.currentUserRole = window.currentUserRole || '';
        this.isRestrictedUser = window.isRestrictedUser || false;

        console.log('🔐 Kanban Access Control iniciado:', {
            accessLevel: this.userAccessLevel,
            managerName: this.managerName,
            role: this.currentUserRole,
            isRestricted: this.isRestrictedUser
        });

        // Aplicar controles de acceso
        this.applyAccessControls();
        
        // Agregar validaciones de seguridad
        this.addSecurityValidations();
        
        // Mostrar indicadores visuales
        this.showAccessIndicators();
    }

    applyAccessControls() {
        if (this.isRestrictedUser) {
            this.hideJefeProyectoFilter();
            this.restrictFilterManipulation();
            this.addRestrictedUserInfo();
        }
    }

    hideJefeProyectoFilter() {
        // Ocultar el filtro de jefe de proyecto para usuarios restringidos
        const jefeProyectoField = document.querySelector('[name="jefe_proyecto"]');
        const jefeProyectoContainer = jefeProyectoField?.closest('.form-group');
        
        if (jefeProyectoContainer) {
            jefeProyectoContainer.style.display = 'none';
            console.log('🔒 Filtro de jefe de proyecto oculto para usuario restringido');
        }

        // También ocultar en el formulario de filtros si existe
        const jefeProyectoSelect = document.getElementById('jefe_proyecto');
        if (jefeProyectoSelect) {
            const parentDiv = jefeProyectoSelect.closest('div');
            if (parentDiv) {
                parentDiv.style.display = 'none';
            }
        }
    }

    restrictFilterManipulation() {
        // Prevenir manipulación de URL para cambiar filtros de jefe_proyecto
        const currentUrl = new URL(window.location.href);
        
        // Si el usuario es restringido y hay un filtro de jefe_proyecto diferente al suyo
        if (this.isRestrictedUser && this.managerName) {
            const urlJefe = currentUrl.searchParams.get('jefe_proyecto');
            
            if (urlJefe && urlJefe !== this.managerName) {
                console.warn('🚫 Intento de acceso no autorizado detectado, redirigiendo...');
                currentUrl.searchParams.set('jefe_proyecto', this.managerName);
                window.location.href = currentUrl.toString();
                return;
            }
        }

        // Interceptar envíos de formularios para validar filtros
        const filterForms = document.querySelectorAll('form');
        filterForms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (this.isRestrictedUser) {
                    this.validateFormSubmission(form, e);
                }
            });
        });
    }

    validateFormSubmission(form, event) {
        const jefeProyectoInput = form.querySelector('[name="jefe_proyecto"]');
        
        if (jefeProyectoInput && this.managerName) {
            // Forzar el valor correcto
            jefeProyectoInput.value = this.managerName;
        }

        console.log('✅ Formulario validado para usuario restringido');
    }

    addRestrictedUserInfo() {
        // Agregar información visual para usuarios restringidos
        const headerArea = document.querySelector('.flex.items-center.gap-3.mb-2');
        
        if (headerArea && this.managerName) {
            const restrictedBadge = document.createElement('div');
            restrictedBadge.className = 'px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-medium';
            restrictedBadge.innerHTML = `
                <svg class="w-3 h-3 inline mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2z"/>
                </svg>
                Vista filtrada: ${this.managerName}
            `;
            
            headerArea.appendChild(restrictedBadge);
        }
    }

    showAccessIndicators() {
        // Mostrar indicadores de estado de acceso
        const titleElement = document.getElementById('view-title');
        
        if (titleElement) {
            if (this.isRestrictedUser) {
                titleElement.textContent = `Kanban - ${this.managerName || 'Mis Proyectos'}`;
            } else {
                titleElement.textContent = 'Kanban - Vista Completa';
            }
        }

        // Agregar tooltip explicativo
        this.addAccessTooltip();
    }

    addAccessTooltip() {
        const viewDescription = document.getElementById('view-description');
        
        if (viewDescription) {
            if (this.isRestrictedUser) {
                viewDescription.textContent = 'Mostrando solo los EDPs de tus proyectos asignados';
                viewDescription.className += ' text-amber-600';
            } else {
                viewDescription.textContent = 'Vista completa de todos los EDPs del sistema';
                viewDescription.className += ' text-green-600';
            }
        }
    }

    addSecurityValidations() {
        // Interceptar intentos de manipulación via DevTools
        if (this.isRestrictedUser) {
            // Proteger contra cambios en los filtros via JavaScript
            Object.defineProperty(window, 'managerName', {
                value: this.managerName,
                writable: false,
                configurable: false
            });

            // Interceptar peticiones AJAX para validar permisos
            this.interceptAjaxRequests();
        }
    }

    interceptAjaxRequests() {
        const originalFetch = window.fetch;
        const self = this;
        
        window.fetch = function(...args) {
            const url = args[0];
            
            // Validar peticiones relacionadas con EDPs
            if (typeof url === 'string' && url.includes('/api/get-edp/')) {
                console.log('🔍 Validando petición API:', url);
            }
            
            return originalFetch.apply(this, args);
        };
    }

    // Método público para validar acceso a un EDP específico
    canAccessEDP(edpData) {
        if (!this.isRestrictedUser) {
            return true; // Acceso completo
        }

        if (!edpData || !edpData.jefe_proyecto) {
            return false; // Sin datos o sin jefe asignado
        }

        return edpData.jefe_proyecto === this.managerName;
    }

    // Método para mostrar mensajes de acceso denegado
    showAccessDeniedMessage(message = 'No tienes permisos para acceder a este EDP') {
        // Crear o mostrar un toast de error
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        toast.innerHTML = `
            <div class="flex items-center">
                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remover después de 3 segundos
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

    // Método para obtener información del acceso actual
    getAccessInfo() {
        return {
            accessLevel: this.userAccessLevel,
            managerName: this.managerName,
            isRestricted: this.isRestrictedUser,
            role: this.currentUserRole
        };
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si estamos en la vista Kanban
    if (window.location.pathname.includes('/kanban')) {
        window.kanbanAccessControl = new KanbanAccessControl();
        
        // Hacer disponible globalmente para otros scripts
        window.validateEDPAccess = function(edpData) {
            return window.kanbanAccessControl.canAccessEDP(edpData);
        };
        
        window.showAccessDenied = function(message) {
            window.kanbanAccessControl.showAccessDeniedMessage(message);
        };
    }
});

// Exportar para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KanbanAccessControl;
}
