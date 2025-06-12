/**
 * Navbar Unificado - Script de funcionalidad
 * Maneja la interacción del navbar que se adapta según el rol del usuario
 */

document.addEventListener('DOMContentLoaded', function() {
  // Variables principales
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  const mobileMenu = document.getElementById('mobile-menu');
  
  // Funcionalidad del menú móvil
  if (mobileMenuButton && mobileMenu) {
    // Toggle del menú móvil
    mobileMenuButton.addEventListener('click', function(e) {
      e.stopPropagation();
      mobileMenu.classList.toggle('hidden');
      
      // Animación del icono hamburguesa
      const icon = mobileMenuButton.querySelector('svg');
      if (icon) {
        icon.classList.toggle('transform');
        icon.classList.toggle('rotate-90');
      }
    });

    // Cerrar menú móvil al hacer click fuera
    document.addEventListener('click', function(e) {
      if (!mobileMenu.contains(e.target) && !mobileMenuButton.contains(e.target)) {
        mobileMenu.classList.add('hidden');
        
        // Restaurar icono hamburguesa
        const icon = mobileMenuButton.querySelector('svg');
        if (icon) {
          icon.classList.remove('transform', 'rotate-90');
        }
      }
    });

    // Cerrar menú móvil al cambiar tamaño de pantalla
    window.addEventListener('resize', function() {
      if (window.innerWidth >= 768) { // md breakpoint
        mobileMenu.classList.add('hidden');
        
        // Restaurar icono hamburguesa
        const icon = mobileMenuButton.querySelector('svg');
        if (icon) {
          icon.classList.remove('transform', 'rotate-90');
        }
      }
    });
  }

  // Funcionalidad de notificaciones (placeholder)
  const notificationButton = document.querySelector('[data-notifications]');
  if (notificationButton) {
    notificationButton.addEventListener('click', function() {
      // Aquí se podría implementar la funcionalidad de notificaciones
      console.log('Notificaciones clicked');
    });
  }

  // Mejoras de accesibilidad
  initializeAccessibility();
  
  // Sistema de navegación inteligente
  initializeSmartNavigation();
});

/**
 * Inicializa mejoras de accesibilidad para el navbar
 */
function initializeAccessibility() {
  // Añadir indicadores visuales para navegación por teclado
  const navLinks = document.querySelectorAll('nav a, nav button');
  
  navLinks.forEach(link => {
    link.addEventListener('focus', function() {
      this.classList.add('ring-2', 'ring-blue-500', 'ring-opacity-50');
    });
    
    link.addEventListener('blur', function() {
      this.classList.remove('ring-2', 'ring-blue-500', 'ring-opacity-50');
    });
  });

  // Soporte para navegación con teclas
  document.addEventListener('keydown', function(e) {
    // ESC para cerrar menús
    if (e.key === 'Escape') {
      const mobileMenu = document.getElementById('mobile-menu');
      if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
        mobileMenu.classList.add('hidden');
      }
    }
  });
}

/**
 * Sistema de navegación inteligente que recuerda preferencias
 */
function initializeSmartNavigation() {
  // Guardar última página visitada por rol
  const currentPath = window.location.pathname;
  const userRole = getCurrentUserRole();
  
  if (userRole) {
    localStorage.setItem(`lastVisited_${userRole}`, currentPath);
  }

  // Añadir indicadores de carga para transiciones
  const navLinks = document.querySelectorAll('nav a:not([href="#"])');
  
  navLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      // Solo para navegación interna
      if (this.hostname === window.location.hostname) {
        // Mostrar indicador de carga
        showNavigationLoader();
      }
    });
  });
}

/**
 * Obtiene el rol del usuario actual desde el DOM
 */
function getCurrentUserRole() {
  const roleElement = document.querySelector('[data-user-role]');
  if (roleElement) {
    return roleElement.dataset.userRole;
  }
  
  // Fallback: detectar desde la URL o navbar
  const navbar = document.querySelector('nav');
  if (navbar && navbar.textContent.includes('Manager')) {
    return 'manager';
  }
  
  return 'controller'; // default
}

/**
 * Muestra un indicador sutil de carga durante la navegación
 */
function showNavigationLoader() {
  // Crear indicador de carga si no existe
  let loader = document.getElementById('nav-loader');
  if (!loader) {
    loader = document.createElement('div');
    loader.id = 'nav-loader';
    loader.className = 'fixed top-0 left-0 w-full h-1 bg-blue-500 z-50 opacity-0 transition-opacity';
    loader.innerHTML = '<div class="h-full bg-gradient-to-r from-blue-400 to-blue-600 animate-pulse"></div>';
    document.body.appendChild(loader);
  }
  
  // Mostrar loader
  loader.classList.remove('opacity-0');
  loader.classList.add('opacity-100');
  
  // Ocultar después de un breve momento
  setTimeout(() => {
    if (loader) {
      loader.classList.remove('opacity-100');
      loader.classList.add('opacity-0');
    }
  }, 500);
}

/**
 * Funciones de utilidad para el navbar
 */
window.NavbarUtils = {
  /**
   * Fuerza el cierre del menú móvil
   */
  closeMobileMenu: function() {
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu) {
      mobileMenu.classList.add('hidden');
    }
  },
  
  /**
   * Actualiza el indicador de notificaciones
   */
  updateNotificationBadge: function(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
      if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.classList.remove('hidden');
      } else {
        badge.classList.add('hidden');
      }
    }
  },
  
  /**
   * Resalta temporalmente un enlace del navbar
   */
  highlightNavLink: function(linkSelector, duration = 2000) {
    const link = document.querySelector(linkSelector);
    if (link) {
      link.classList.add('bg-yellow-100', 'dark:bg-yellow-900');
      setTimeout(() => {
        link.classList.remove('bg-yellow-100', 'dark:bg-yellow-900');
      }, duration);
    }
  }
};

// Exponer utilidades globalmente para uso en otros scripts
window.NavbarUnified = window.NavbarUtils;
