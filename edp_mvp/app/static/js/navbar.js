/**
 * Navbar Unificado - Script de funcionalidad
 * Maneja la navegación completa incluyendo menús móviles y dropdowns
 */

document.addEventListener('DOMContentLoaded', function() {
  console.log('🚀 Navbar script loaded and DOM ready');
  
  // ===== NAVEGACIÓN MÓVIL PRINCIPAL =====
  initializeMobileNavigation();
  
  // ===== DROPDOWNS DE ESCRITORIO =====
  initializeDesktopDropdowns();
  
  // ===== FUNCIONALIDADES ADICIONALES =====
  initializeAccessibility();
  initializeSmartNavigation();
});

/**
 * Inicializa la navegación móvil principal
 */
function initializeMobileNavigation() {
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  const mobileMenu = document.getElementById('mobile-menu');
  
  console.log('📱 Mobile menu button:', mobileMenuButton);
  console.log('📋 Mobile menu:', mobileMenu);
  
  // Lista de submenús móviles
  const mobileSubmenus = [
    { toggle: 'mobile-controller-toggle', menu: 'mobile-controller-menu', arrow: 'mobile-controller-arrow' },
    { toggle: 'mobile-manager-toggle', menu: 'mobile-manager-menu', arrow: 'mobile-manager-arrow' },
    { toggle: 'mobile-edp-toggle', menu: 'mobile-edp-menu', arrow: 'mobile-edp-arrow' },
    { toggle: 'mobile-admin-toggle', menu: 'mobile-admin-menu', arrow: 'mobile-admin-arrow' }
  ];

  // Función para cerrar todos los submenús móviles
  function closeAllMobileSubmenus() {
    mobileSubmenus.forEach(submenu => {
      const menu = document.getElementById(submenu.menu);
      const arrow = document.getElementById(submenu.arrow);
      if (menu) menu.classList.add('hidden');
      if (arrow) arrow.classList.remove('rotate-180');
    });
  }

  // Configurar menú móvil principal
  if (mobileMenuButton && mobileMenu) {
    mobileMenuButton.addEventListener('click', function(e) {
      e.stopPropagation();
      console.log('🔥 Mobile menu button clicked!');
      
      const isHidden = mobileMenu.classList.contains('hidden');
      
      if (isHidden) {
        mobileMenu.classList.remove('hidden');
        console.log('👀 Mobile menu shown');
      } else {
        mobileMenu.classList.add('hidden');
        closeAllMobileSubmenus();
        console.log('🙈 Mobile menu hidden');
      }
    });
    
    console.log('✅ Mobile menu button configured');
  } else {
    console.error('❌ Mobile menu elements not found!');
  }

  // Configurar submenús móviles
  mobileSubmenus.forEach(submenu => {
    const toggle = document.getElementById(submenu.toggle);
    const menu = document.getElementById(submenu.menu);
    const arrow = document.getElementById(submenu.arrow);
    
    if (toggle && menu && arrow) {
      toggle.addEventListener('click', function(e) {
        e.stopPropagation();
        console.log(`🔄 Submenu ${submenu.toggle} clicked`);
        
        const isHidden = menu.classList.contains('hidden');
        
        // Cerrar otros submenús móviles
        mobileSubmenus.forEach(otherSubmenu => {
          if (otherSubmenu.menu !== submenu.menu) {
            const otherMenu = document.getElementById(otherSubmenu.menu);
            const otherArrow = document.getElementById(otherSubmenu.arrow);
            if (otherMenu) otherMenu.classList.add('hidden');
            if (otherArrow) otherArrow.classList.remove('rotate-180');
          }
        });
        
        // Toggle del submenú actual
        if (isHidden) {
          menu.classList.remove('hidden');
          arrow.classList.add('rotate-180');
          console.log(`📂 ${submenu.toggle} opened`);
        } else {
          menu.classList.add('hidden');
          arrow.classList.remove('rotate-180');
          console.log(`📁 ${submenu.toggle} closed`);
        }
      });
      
      console.log(`✅ Submenu ${submenu.toggle} configured`);
    }
  });

  // Cerrar menú móvil al hacer clic fuera
  document.addEventListener('click', function(e) {
    if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
      if (!mobileMenu.contains(e.target) && !mobileMenuButton.contains(e.target)) {
        mobileMenu.classList.add('hidden');
        closeAllMobileSubmenus();
        console.log('🚪 Mobile menu closed by outside click');
      }
    }
  });

  // Prevenir que los clics dentro del menú lo cierren
  if (mobileMenu) {
    mobileMenu.addEventListener('click', function(e) {
      e.stopPropagation();
    });
  }

  // Cerrar menú móvil al cambiar tamaño de pantalla
  window.addEventListener('resize', function() {
    if (window.innerWidth >= 768 && mobileMenu) { // md breakpoint
      mobileMenu.classList.add('hidden');
      closeAllMobileSubmenus();
      console.log('📱 Mobile menu closed due to screen resize');
    }
  });
}

/**
 * Inicializa los dropdowns de escritorio
 */
function initializeDesktopDropdowns() {
  const desktopDropdowns = [
    { button: 'user-menu-button', menu: 'user-menu' },
    { button: 'controller-menu-button', menu: 'controller-menu' },
    { button: 'manager-menu-button', menu: 'manager-menu' },
    { button: 'edp-menu-button', menu: 'edp-menu' },
    { button: 'admin-menu-button', menu: 'admin-menu' }
  ];

  // Función para cerrar todos los dropdowns de escritorio
  function closeAllDesktopDropdowns() {
    desktopDropdowns.forEach(dropdown => {
      const menu = document.getElementById(dropdown.menu);
      if (menu) menu.classList.add('hidden');
    });
  }

  // Configurar cada dropdown de escritorio
  desktopDropdowns.forEach(dropdown => {
    const button = document.getElementById(dropdown.button);
    const menu = document.getElementById(dropdown.menu);
    
    if (button && menu) {
      button.addEventListener('click', function(e) {
        e.stopPropagation();
        
        // Cerrar otros dropdowns
        desktopDropdowns.forEach(otherDropdown => {
          if (otherDropdown.menu !== dropdown.menu) {
            const otherMenu = document.getElementById(otherDropdown.menu);
            if (otherMenu) otherMenu.classList.add('hidden');
          }
        });
        
        // Toggle del dropdown actual
        menu.classList.toggle('hidden');
        console.log(`🖥️ Desktop dropdown ${dropdown.button} toggled`);
      });

      menu.addEventListener('click', function(e) {
        e.stopPropagation();
      });
      
      console.log(`✅ Desktop dropdown ${dropdown.button} configured`);
    }
  });

  // Cerrar dropdowns al hacer clic fuera
  document.addEventListener('click', function() {
    closeAllDesktopDropdowns();
  });
}

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
        console.log('⌨️ Mobile menu closed with ESC key');
      }
      
      // Cerrar dropdowns de escritorio también
      const desktopDropdowns = [
        'user-menu', 'controller-menu', 'manager-menu', 'edp-menu', 'admin-menu'
      ];
      
      desktopDropdowns.forEach(menuId => {
        const menu = document.getElementById(menuId);
        if (menu && !menu.classList.contains('hidden')) {
          menu.classList.add('hidden');
        }
      });
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
   * Fuerza el cierre de todos los dropdowns
   */
  closeAllDropdowns: function() {
    const dropdowns = [
      'user-menu', 'controller-menu', 'manager-menu', 'edp-menu', 'admin-menu'
    ];
    
    dropdowns.forEach(menuId => {
      const menu = document.getElementById(menuId);
      if (menu) {
        menu.classList.add('hidden');
      }
    });
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
  highlightNavLink: function(selector) {
    const link = document.querySelector(selector);
    if (link) {
      link.classList.add('bg-blue-100', 'text-blue-600');
      setTimeout(() => {
        link.classList.remove('bg-blue-100', 'text-blue-600');
      }, 2000);
    }
  }
};

// Exponer utilidades globalmente para uso en otros scripts
window.NavbarUnified = window.NavbarUtils;
