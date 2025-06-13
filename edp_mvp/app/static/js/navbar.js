/**
 * Navbar Unificado - Script de funcionalidad
 * Maneja la navegación completa incluyendo menús móviles y dropdowns
 */

// 🚀 SCRIPT DE NAVEGACIÓN SIMPLIFICADO Y ROBUSTO
console.log("🚀 Iniciando script de navegación...");

document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 DOM cargado, inicializando navegación...");

  // Función simple para manejar dropdowns
  function setupSimpleDropdown(buttonId, menuId) {
    const button = document.getElementById(buttonId);
    const menu = document.getElementById(menuId);

    // Ya verificamos la existencia antes de llamar esta función
    if (!button || !menu) {
      return;
    }

    // Variable para evitar clicks múltiples
    let isProcessing = false;

    // Remover cualquier listener existente clonando el elemento
    const newButton = button.cloneNode(true);
    button.parentNode.replaceChild(newButton, button);
    
    newButton.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation(); // Evitar múltiples listeners

      // Evitar procesamiento múltiple
      if (isProcessing) {
        return;
      }
      
      isProcessing = true;

      // Cerrar otros menús
      document
        .querySelectorAll('[id$="-menu"]:not([id*="mobile"])')
        .forEach((otherMenu) => {
          if (otherMenu !== menu) {
            otherMenu.classList.add("hidden");
            otherMenu.style.cssText = ""; // Limpiar estilos inline
          }
        });

      // Toggle del menú actual
      const isHidden = menu.classList.contains("hidden");
      menu.classList.toggle("hidden");

      // Si se está abriendo, forzar estilos inline para asegurar visibilidad
      if (isHidden) {
        // Obtener colores del tema actual
        const themeColors = getCurrentThemeColors();
        
        menu.style.cssText = `
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
          z-index: 999999 !important;
          position: absolute !important;
          background: ${themeColors.bgCard} !important;
          border: 1px solid ${themeColors.borderColor} !important;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, ${themeColors.isDarkMode ? '0.6' : '0.1'}), 0 4px 6px -2px rgba(0, 0, 0, ${themeColors.isDarkMode ? '0.4' : '0.05'}) !important;
          min-width: 200px !important;
          top: 100% !important;
          left: 0 !important;
          padding: 0.5rem 0 !important;
          margin-top: 0.5rem !important;
          border-radius: 0.375rem !important;
          transform: none !important;
          pointer-events: auto !important;
          color: ${themeColors.textPrimary} !important;
        `;
      } else {
        // Si se está cerrando, limpiar estilos inline
        menu.style.cssText = "";
      }

      // Rotar flecha
      const arrow = newButton.querySelector("svg:last-child");
      if (arrow) {
        if (isHidden) {
          arrow.classList.add("rotate-180");
        } else {
          arrow.classList.remove("rotate-180");
        }
      }
      
      // Liberar el lock después de un breve delay
      setTimeout(() => {
        isProcessing = false;
      }, 300);
    });
  }

  // Configurar dropdowns con delay - solo los que existen
  setTimeout(() => {
    console.log("🔧 Configurando dropdowns...");
    
    // Lista de todos los posibles dropdowns
    const dropdowns = [
      { button: "controller-menu-button", menu: "controller-menu" },
      { button: "project-manager-menu-button", menu: "project-manager-menu" },
      { button: "manager-menu-button", menu: "manager-menu" },
      { button: "edp-menu-button", menu: "edp-menu" },
      { button: "admin-menu-button", menu: "admin-menu" },
      { button: "user-menu-button", menu: "user-menu" }
    ];
    
    // Configurar solo los dropdowns que existen en el DOM
    dropdowns.forEach(dropdown => {
      const button = document.getElementById(dropdown.button);
      const menu = document.getElementById(dropdown.menu);
      
      if (button && menu) {
        console.log(`✅ Configurando ${dropdown.button}`);
        setupSimpleDropdown(dropdown.button, dropdown.menu);
      } else {
        console.log(`⏭️ Saltando ${dropdown.button} (no existe para este rol)`);
      }
    });
  }, 200);

  // Cerrar menús al hacer clic fuera
  document.addEventListener("click", function (e) {
    if (
      !e.target.closest('[id$="-menu-button"]') &&
      !e.target.closest('[id$="-menu"]')
    ) {
      document
        .querySelectorAll('[id$="-menu"]:not([id*="mobile"])')
        .forEach((menu) => {
          menu.classList.add("hidden");
          menu.style.cssText = ""; // Limpiar estilos inline

          // Resetear flecha
          const buttonId = menu.id.replace("-menu", "-menu-button");
          const button = document.getElementById(buttonId);
          const arrow = button?.querySelector("svg:last-child");
          if (arrow) {
            arrow.classList.remove("rotate-180");
          }
        });
    }
  });

  // Menú móvil
  const mobileMenuButton = document.getElementById("mobile-menu-button");
  const mobileMenu = document.getElementById("mobile-menu");

  if (mobileMenuButton && mobileMenu) {
    mobileMenuButton.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      mobileMenu.classList.toggle("hidden");
    });
  }

  // Configurar menús móviles desplegables
  function setupMobileDropdown(toggleId, menuId, arrowId) {
    const toggle = document.getElementById(toggleId);
    const menu = document.getElementById(menuId);
    const arrow = document.getElementById(arrowId);

    if (toggle && menu) {
      toggle.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        
        menu.classList.toggle("hidden");
        
        if (arrow) {
          arrow.classList.toggle("rotate-180");
        }
      });
    }
  }

  // Configurar menús móviles - solo los que existen
  const mobileDropdowns = [
    { toggle: "mobile-controller-toggle", menu: "mobile-controller-menu", arrow: "mobile-controller-arrow" },
    { toggle: "mobile-manager-toggle", menu: "mobile-manager-menu", arrow: "mobile-manager-arrow" },
    { toggle: "mobile-project-manager-toggle", menu: "mobile-project-manager-menu", arrow: "mobile-project-manager-arrow" },
    { toggle: "mobile-edp-toggle", menu: "mobile-edp-menu", arrow: "mobile-edp-arrow" },
    { toggle: "mobile-admin-toggle", menu: "mobile-admin-menu", arrow: "mobile-admin-arrow" }
  ];
  
  mobileDropdowns.forEach(dropdown => {
    const toggle = document.getElementById(dropdown.toggle);
    const menu = document.getElementById(dropdown.menu);
    
    if (toggle && menu) {
      console.log(`📱 Configurando menú móvil: ${dropdown.toggle}`);
      setupMobileDropdown(dropdown.toggle, dropdown.menu, dropdown.arrow);
    } else {
      console.log(`⏭️ Saltando menú móvil ${dropdown.toggle} (no existe para este rol)`);
    }
  });

  console.log("✅ Navegación inicializada correctamente");

  // Observer para cambios de tema
  const themeObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'attributes' && 
          (mutation.attributeName === 'data-theme' || mutation.attributeName === 'class')) {
        // Actualizar dropdowns abiertos cuando cambie el tema
        const openDropdowns = document.querySelectorAll('[id$="-menu"]:not(.hidden):not([id*="mobile"])');
        openDropdowns.forEach(dropdown => {
          const themeColors = getCurrentThemeColors();
          dropdown.style.background = themeColors.bgCard;
          dropdown.style.borderColor = themeColors.borderColor;
          dropdown.style.color = themeColors.textPrimary;
        });
      }
    });
  });

  // Observar cambios en el elemento html
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme', 'class']
  });
});

console.log("📝 Script de navegación cargado");

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
      if (mobileMenu && mobileMenu.classList.contains('hidden')) {
        mobileMenu.classList.remove('hidden');
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

/**
 * Obtiene los colores del tema actual
 */
function getCurrentThemeColors() {
  const computedStyle = getComputedStyle(document.documentElement);
  const isDarkMode = document.documentElement.hasAttribute('data-theme') && 
                    document.documentElement.getAttribute('data-theme') === 'dark' ||
                    document.documentElement.classList.contains('dark');
  
  return {
    bgCard: computedStyle.getPropertyValue('--bg-card').trim() || (isDarkMode ? '#1c1c1e' : '#ffffff'),
    borderColor: computedStyle.getPropertyValue('--border-color').trim() || (isDarkMode ? '#3a3a3c' : '#d1d5db'),
    textPrimary: computedStyle.getPropertyValue('--text-primary').trim() || (isDarkMode ? '#f5f5f7' : '#1e293b'),
    bgHover: computedStyle.getPropertyValue('--bg-hover').trim() || (isDarkMode ? '#2e2e30' : '#e2e8f0'),
    isDarkMode
  };
}
