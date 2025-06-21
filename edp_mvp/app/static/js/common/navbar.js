/**
 * Navbar Unificado - Script de funcionalidad FINAL
 * Solución integrada para navegación móvil y desktop sin archivos externos
 */

console.log("🚀 Iniciando sistema de navegación v3.0 - Solución Final");

document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 DOM listo - Inicializando navegación integrada");

  // ==========================================================================
  // VARIABLES GLOBALES DE ESTADO
  // ==========================================================================
  
  let isDesktop = window.innerWidth >= 768;
  let mobileMenuState = {
    isOpen: false,
    activeSubmenu: null
  };

  // ==========================================================================
  // UTILIDADES
  // ==========================================================================
  
  function getCurrentThemeColors() {
    // En lugar de detectar manualmente, obtener los valores directamente de las variables CSS
    const computedStyle = getComputedStyle(document.documentElement);
    
    const bgCard = computedStyle.getPropertyValue('--bg-card').trim();
    const borderColor = computedStyle.getPropertyValue('--border-color').trim();
    const textPrimary = computedStyle.getPropertyValue('--text-primary').trim();
    const textSecondary = computedStyle.getPropertyValue('--text-secondary').trim();
    const shadowElevated = computedStyle.getPropertyValue('--shadow-elevated').trim();
    
    // Detectar si es modo oscuro basado en el color del texto
    const isDarkMode = textPrimary === '#ffffff' || textPrimary === 'rgb(255, 255, 255)';
    
    console.log('🎨 Variables CSS obtenidas:', {
      bgCard,
      borderColor,
      textPrimary,
      textSecondary,
      shadowElevated,
      isDarkMode
    });
    
    return {
      bgCard: bgCard || (isDarkMode ? '#0a0a0a' : '#ffffff'),
      borderColor: borderColor || (isDarkMode ? '#1a1a1a' : '#e5e7eb'),
      textPrimary: textPrimary || (isDarkMode ? '#ffffff' : '#1a1a1a'),
      textSecondary: textSecondary || (isDarkMode ? '#888888' : '#6b7280'),
      shadowElevated: shadowElevated || (isDarkMode ? '0 0 30px rgba(0, 255, 136, 0.05)' : '0 4px 12px rgba(0, 0, 0, 0.05)'),
      isDarkMode: isDarkMode
    };
  }

  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // ==========================================================================
  // SISTEMA DE NAVEGACIÓN DESKTOP
  // ==========================================================================
  
  function initializeDesktopNavigation() {
    console.log("🖥️ Inicializando navegación desktop");
    
    // Asegurar que todos los dropdowns estén cerrados al inicio
    document.querySelectorAll('[id$="-menu"]:not([id*="mobile"])').forEach(menu => {
      menu.classList.add("hidden");
      menu.classList.remove("show");
      menu.style.cssText = `
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
      `;
      console.log(`🔒 Forzando cierre inicial del dropdown ${menu.id}`);
    });
    
    const dropdowns = [
      { button: "controller-menu-button", menu: "controller-menu" },
      { button: "project-manager-menu-button", menu: "project-manager-menu" },
      { button: "manager-menu-button", menu: "manager-menu" },
      { button: "edp-menu-button", menu: "edp-menu" },
      { button: "admin-menu-button", menu: "admin-menu" },
      { button: "user-menu-button", menu: "user-menu" }
    ];
    
    function closeAllDesktopDropdowns() {
      document.querySelectorAll('[id$="-menu"]:not([id*="mobile"])').forEach(menu => {
        menu.classList.add("hidden");
        menu.classList.remove("show");
        menu.style.cssText = "";
        
        // Resetear flecha
        const buttonId = menu.id.replace("-menu", "-menu-button");
        const button = document.getElementById(buttonId);
        const arrow = button?.querySelector("svg:last-child");
        if (arrow) {
          arrow.classList.remove("rotate-180");
        }
      });
    }
    
    dropdowns.forEach(dropdown => {
      const button = document.getElementById(dropdown.button);
      const menu = document.getElementById(dropdown.menu);
      
      console.log(`🔍 Verificando dropdown ${dropdown.button}:`, {
        button: button ? '✅ Found' : '❌ Missing',
        menu: menu ? '✅ Found' : '❌ Missing',
        buttonId: dropdown.button,
        menuId: dropdown.menu,
        initialHiddenState: menu ? menu.classList.contains('hidden') : 'N/A',
        initialClasses: menu ? menu.className : 'N/A'
      });
      
      if (button && menu) {
        button.addEventListener("click", function (e) {
          // Verificar si es desktop en tiempo real
          const currentIsDesktop = window.innerWidth >= 768;
          console.log(`🖥️ Click en dropdown button ${dropdown.button}: isDesktop=${currentIsDesktop}, width=${window.innerWidth}`);
          
          if (!currentIsDesktop) return;
          
          e.preventDefault();
          e.stopPropagation();
          
          // Cerrar todos los dropdowns primero
          document.querySelectorAll('[id$="-menu"]:not([id*="mobile"])').forEach(otherMenu => {
            otherMenu.classList.add("hidden");
            otherMenu.classList.remove("show");
            otherMenu.style.cssText = `
              display: none !important;
              visibility: hidden !important;
              opacity: 0 !important;
            `;
            
            // Resetear flecha del otro menú
            const otherButtonId = otherMenu.id.replace("-menu", "-menu-button");
            const otherButton = document.getElementById(otherButtonId);
            const otherArrow = otherButton?.querySelector("svg:last-child");
            if (otherArrow) {
              otherArrow.classList.remove("rotate-180");
            }
          });
          
          // Siempre abrir el dropdown clickeado
          console.log(`🎨 Abriendo dropdown ${dropdown.menu}`);
          const themeColors = getCurrentThemeColors();
          
          menu.classList.remove("hidden");
          menu.classList.add("show");
          menu.style.cssText = `
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 999999 !important;
            position: absolute !important;
            background: ${themeColors.bgCard} !important;
            border: 1px solid ${themeColors.borderColor} !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
            min-width: 200px !important;
            top: 100% !important;
            left: 0 !important;
            padding: 8px !important;
            margin-top: 4px !important;
            border-radius: 8px !important;
            transform: translateY(0) !important;
            pointer-events: auto !important;
            color: ${themeColors.textPrimary} !important;
            max-height: 400px !important;
            overflow-y: auto !important;
          `;
          
          // Aplicar estilos a los elementos internos del dropdown
          const dropdownItems = menu.querySelectorAll('.dropdown-item, a');
          dropdownItems.forEach(item => {
            item.style.setProperty('color', themeColors.textPrimary, 'important');
            item.style.setProperty('background-color', 'transparent', 'important');
            item.style.setProperty('display', 'flex', 'important');
            item.style.setProperty('align-items', 'center', 'important');
            item.style.setProperty('padding', '8px 12px', 'important');
            item.style.setProperty('text-decoration', 'none', 'important');
            item.style.setProperty('border-radius', '4px', 'important');
            item.style.setProperty('transition', 'all 0.2s ease', 'important');
          });
          
          console.log('🎨 Dropdown abierto usando variables CSS:', {
            menuId: menu.id,
            usandoVariablesCSS: true,
            bgCard: themeColors.bgCard,
            textColor: themeColors.textPrimary
          });
          
          // Debug: Verificar el estado del elemento después de aplicar estilos
          setTimeout(() => {
            const computedStyle = window.getComputedStyle(menu);
            console.log(`🔍 Estado del dropdown ${menu.id} después de aplicar estilos:`, {
              display: computedStyle.display,
              visibility: computedStyle.visibility,
              opacity: computedStyle.opacity,
              zIndex: computedStyle.zIndex,
              position: computedStyle.position,
              top: computedStyle.top,
              left: computedStyle.left,
              hasHiddenClass: menu.classList.contains('hidden'),
              hasShowClass: menu.classList.contains('show'),
              inlineStyles: menu.style.cssText
            });
          }, 100);
          
          // Rotar flecha
          const arrow = button.querySelector("svg:last-child");
          if (arrow) {
            arrow.classList.add("rotate-180");
          }
        });
      }
    });
    
    // Click fuera para cerrar dropdowns desktop
    document.addEventListener("click", function (e) {
      // Verificar si es desktop en tiempo real
      const currentIsDesktop = window.innerWidth >= 768;
      if (!currentIsDesktop) return;
      
      const isDropdownClick = e.target.closest('[id$="-menu-button"]') || 
                             e.target.closest('[id$="-menu"]:not([id*="mobile"])');
      
      if (!isDropdownClick) {
        closeAllDesktopDropdowns();
      }
    });
  }

  // ==========================================================================
  // SISTEMA DE NAVEGACIÓN MÓVIL - SOLUCIÓN FINAL
  // ==========================================================================
  
  function initializeMobileNavigation() {
    console.log("📱 Inicializando navegación móvil - Solución Final");
    
    const mobileMenuButton = document.getElementById("mobile-menu-button");
    const mobileMenu = document.getElementById("mobile-menu");

    if (!mobileMenuButton || !mobileMenu) {
      console.log("⚠️ Elementos de menú móvil no encontrados");
      return;
    }

    // ==========================================================================
    // FUNCIONES DEL MENÚ PRINCIPAL MÓVIL
    // ==========================================================================
    
    function openMobileMenu() {
      console.log("🔓 Abriendo menú móvil");
      mobileMenuState.isOpen = true;
      
      // Prevenir scroll del body
      document.body.style.overflow = 'hidden';
      
      // Mostrar menú
      mobileMenu.classList.remove("hidden");
      mobileMenu.style.cssText = `
        display: block !important;
        opacity: 1 !important;
        visibility: visible !important;
        z-index: 9999 !important;
      `;
      
      // Cambiar icono a X
      updateMobileMenuIcon(true);
    }

    function closeMobileMenu() {
      console.log("🔒 Cerrando menú móvil");
      mobileMenuState.isOpen = false;
      mobileMenuState.activeSubmenu = null;
      
      // Restaurar scroll del body
      document.body.style.overflow = '';
      
      // Cerrar todos los submenús
      closeAllMobileSubmenus();
      
      // Ocultar menú principal
      mobileMenu.classList.add("hidden");
      mobileMenu.style.cssText = "";
      
      // Restaurar icono hamburguesa
      updateMobileMenuIcon(false);
    }

    function updateMobileMenuIcon(isOpen) {
      const icon = mobileMenuButton.querySelector('svg');
      if (icon) {
        if (isOpen) {
          icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />`;
        } else {
          icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />`;
        }
      }
    }

    function closeAllMobileSubmenus() {
      document.querySelectorAll('[id^="mobile-"][id$="-menu"]').forEach(submenu => {
        submenu.classList.add("hidden");
        submenu.style.cssText = "";
      });
      
      document.querySelectorAll('[id^="mobile-"][id$="-arrow"]').forEach(arrow => {
        arrow.classList.remove("rotate-180");
      });
      
      mobileMenuState.activeSubmenu = null;
    }

    // ==========================================================================
    // EVENT LISTENERS PRINCIPALES
    // ==========================================================================
    
    // Toggle del menú móvil principal
    mobileMenuButton.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      
      console.log(`📱 Toggle menú móvil - Estado: ${mobileMenuState.isOpen ? 'abierto' : 'cerrado'}`);
      
      if (mobileMenuState.isOpen) {
        closeMobileMenu();
      } else {
        openMobileMenu();
      }
    });

    // ==========================================================================
    // MANEJO DE SUBMENÚS MÓVILES - LA CLAVE DE LA SOLUCIÓN
    // ==========================================================================
    
    // Event delegation para TODOS los clicks dentro del menú móvil
    mobileMenu.addEventListener("click", function (e) {
      console.log("📱 Click en menú móvil:", e.target.tagName, e.target.className);
      
      // Buscar si el click fue en un botón de toggle de submenú
      const toggleButton = e.target.closest('[id^="mobile-"][id$="-toggle"]');
      
      if (toggleButton) {
        // *** ESTA ES LA CLAVE: Prevenir completamente la propagación ***
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        
        const toggleId = toggleButton.id;
        const menuId = toggleId.replace("-toggle", "-menu");
        const arrowId = toggleId.replace("-toggle", "-arrow");
        
        console.log(`📱 Toggle detectado: ${toggleId} -> ${menuId}`);
        
        handleMobileSubmenuToggle(menuId, arrowId);
        
        // *** IMPORTANTE: Return para no procesar más eventos ***
        return;
      }
      
      // Si es un link directo (no en toggle), permitir navegación
      const link = e.target.closest('a[href]');
      if (link && !link.closest('[id^="mobile-"][id$="-toggle"]')) {
        console.log("📱 Navegación a:", link.href);
        // Cerrar menú al navegar (opcional)
        setTimeout(() => closeMobileMenu(), 100);
      }
    });

    function handleMobileSubmenuToggle(menuId, arrowId) {
      console.log(`🔄 Manejando toggle de submenú: ${menuId}`);
      
      const submenu = document.getElementById(menuId);
      const arrow = document.getElementById(arrowId);
      
      if (!submenu) {
        console.log(`❌ Submenú no encontrado: ${menuId}`);
        return;
      }
      
      const isCurrentlyHidden = submenu.classList.contains("hidden");
      console.log(`📱 Submenú ${menuId} está ${isCurrentlyHidden ? 'cerrado' : 'abierto'}`);
      
      // Cerrar otros submenús si están abiertos
      if (mobileMenuState.activeSubmenu && mobileMenuState.activeSubmenu !== menuId) {
        const otherSubmenu = document.getElementById(mobileMenuState.activeSubmenu);
        const otherArrowId = mobileMenuState.activeSubmenu.replace("-menu", "-arrow");
        const otherArrow = document.getElementById(otherArrowId);
        
        if (otherSubmenu) {
          otherSubmenu.classList.add("hidden");
          otherSubmenu.style.cssText = "";
        }
        if (otherArrow) {
          otherArrow.classList.remove("rotate-180");
        }
      }
      
      // Toggle del submenú actual
      if (isCurrentlyHidden) {
        // Abrir submenú
        submenu.classList.remove("hidden");
        submenu.style.cssText = `
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
          max-height: none !important;
          overflow: visible !important;
        `;
        
        if (arrow) {
          arrow.classList.add("rotate-180");
        }
        
        mobileMenuState.activeSubmenu = menuId;
        console.log(`✅ Submenú ${menuId} abierto`);
      } else {
        // Cerrar submenú
        submenu.classList.add("hidden");
        submenu.style.cssText = "";
        
        if (arrow) {
          arrow.classList.remove("rotate-180");
        }
        
        mobileMenuState.activeSubmenu = null;
        console.log(`✅ Submenú ${menuId} cerrado`);
      }
    }

    // ==========================================================================
    // EVENTOS GLOBALES
    // ==========================================================================
    
    // Click fuera del menú móvil
    document.addEventListener("click", function (e) {
      if (!mobileMenuState.isOpen || isDesktop) return;
      
      // Solo cerrar si el click es completamente fuera del menú móvil
      const isInsideMobileMenu = mobileMenu.contains(e.target);
      const isMobileMenuButton = mobileMenuButton.contains(e.target);
      
      if (!isInsideMobileMenu && !isMobileMenuButton) {
        console.log("📱 Click fuera del menú móvil - cerrando");
        closeMobileMenu();
      }
    });
    
    // Cerrar con tecla Escape
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && mobileMenuState.isOpen) {
        closeMobileMenu();
      }
    });
    
    // Cerrar al cambiar a desktop
    window.addEventListener("resize", debounce(function () {
      const wasDesktop = isDesktop;
      isDesktop = window.innerWidth >= 768;
      
      if (!wasDesktop && isDesktop && mobileMenuState.isOpen) {
        closeMobileMenu();
      }
    }, 250));

    console.log("✅ Navegación móvil inicializada - Solución integrada activa");
  }

  // ==========================================================================
  // INICIALIZACIÓN PRINCIPAL
  // ==========================================================================
  
  function initialize() {
    console.log("🚀 Inicializando sistema completo de navegación");
    
    // Detectar tipo de dispositivo
    isDesktop = window.innerWidth >= 768;
    console.log(`📱 Dispositivo: ${isDesktop ? 'Desktop' : 'Móvil'}`);
    
    // Inicializar sistemas
    initializeDesktopNavigation();
    initializeMobileNavigation();
    
    console.log("✅ Sistema de navegación inicializado - Solución final activa");
  }

  // Pequeño delay para asegurar DOM completamente listo
  setTimeout(initialize, 100);
});

// ==========================================================================
// FUNCIONES GLOBALES DE UTILIDAD
// ==========================================================================

// Función para forzar apertura de dropdown
window.forceOpenDropdown = function(menuId = 'manager-menu') {
  const menu = document.getElementById(menuId);
  const button = document.getElementById(menuId.replace('-menu', '-menu-button'));
  
  if (!menu || !button) {
    console.log(`❌ Elementos no encontrados: menu=${!!menu}, button=${!!button}`);
    return;
  }
  
  console.log(`🔧 Forzando apertura del dropdown ${menuId}...`);
  
  // Cerrar todos los otros dropdowns
  document.querySelectorAll('[id$="-menu"]:not([id*="mobile"])').forEach(otherMenu => {
    if (otherMenu.id !== menu.id) {
      otherMenu.classList.add("hidden");
      otherMenu.classList.remove("show");
      otherMenu.style.cssText = "";
    }
  });
  
  // Abrir el dropdown actual
  menu.classList.remove("hidden");
  menu.classList.add("show");
  menu.style.cssText = `
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
    position: absolute !important;
    background: #0a0a0a !important;
    border: 1px solid #1a1a1a !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
    min-width: 200px !important;
    top: 100% !important;
    left: 0 !important;
    padding: 8px !important;
    margin-top: 4px !important;
    border-radius: 8px !important;
    transform: translateY(0) !important;
    pointer-events: auto !important;
    color: #ffffff !important;
  `;
  
  // Aplicar estilos a los elementos internos
  const dropdownItems = menu.querySelectorAll('.dropdown-item, a');
  dropdownItems.forEach(item => {
    item.style.setProperty('color', '#ffffff', 'important');
    item.style.setProperty('background-color', 'transparent', 'important');
    item.style.setProperty('display', 'flex', 'important');
    item.style.setProperty('align-items', 'center', 'important');
    item.style.setProperty('padding', '8px 12px', 'important');
    item.style.setProperty('text-decoration', 'none', 'important');
    item.style.setProperty('border-radius', '4px', 'important');
  });
  
  // Rotar flecha
  const arrow = button.querySelector("svg:last-child");
  if (arrow) {
    arrow.classList.add("rotate-180");
  }
  
  console.log(`✅ Dropdown ${menuId} forzado a abrir`);
};

// Función para debug específico del dropdown
window.debugDropdown = function(menuId = 'manager-menu') {
  const menu = document.getElementById(menuId);
  const button = document.getElementById(menuId.replace('-menu', '-menu-button'));
  
  if (!menu || !button) {
    console.log(`❌ Elementos no encontrados: menu=${!!menu}, button=${!!button}`);
    return;
  }
  
  console.log(`🔍 Debug del dropdown ${menuId}:`);
  
  // Estado actual
  const computedStyle = window.getComputedStyle(menu);
  console.log('📊 Estado actual:', {
    display: computedStyle.display,
    visibility: computedStyle.visibility,
    opacity: computedStyle.opacity,
    zIndex: computedStyle.zIndex,
    position: computedStyle.position,
    top: computedStyle.top,
    left: computedStyle.left,
    transform: computedStyle.transform,
    hasHiddenClass: menu.classList.contains('hidden'),
    hasShowClass: menu.classList.contains('show'),
    inlineStyles: menu.style.cssText
  });
  
  // Forzar apertura del dropdown
  console.log('🔧 Forzando apertura del dropdown...');
  menu.classList.remove('hidden');
  menu.classList.add('show');
  menu.style.cssText = `
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
    position: absolute !important;
    background: #0a0a0a !important;
    border: 1px solid #1a1a1a !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
    min-width: 200px !important;
    top: 100% !important;
    left: 0 !important;
    padding: 8px !important;
    margin-top: 4px !important;
    border-radius: 8px !important;
    transform: translateY(0) !important;
    pointer-events: auto !important;
    color: #ffffff !important;
  `;
  
  setTimeout(() => {
    const newComputedStyle = window.getComputedStyle(menu);
    console.log('📊 Estado después de forzar:', {
      display: newComputedStyle.display,
      visibility: newComputedStyle.visibility,
      opacity: newComputedStyle.opacity,
      zIndex: newComputedStyle.zIndex,
      position: newComputedStyle.position,
      top: newComputedStyle.top,
      left: newComputedStyle.left,
      transform: newComputedStyle.transform
    });
  }, 100);
};

// Función para debug desde consola del navegador
window.debugNavbar = function() {
  console.log("🔍 Estado del sistema de navegación:", {
    windowWidth: window.innerWidth,
    isDesktop: window.innerWidth >= 768,
    mobileMenuButton: document.getElementById("mobile-menu-button") ? "✅ Encontrado" : "❌ No encontrado",
    mobileMenu: document.getElementById("mobile-menu") ? "✅ Encontrado" : "❌ No encontrado",
    mobileSubmenus: document.querySelectorAll('[id^="mobile-"][id$="-menu"]').length + " encontrados",
    mobileToggles: document.querySelectorAll('[id^="mobile-"][id$="-toggle"]').length + " encontrados"
  });
  
  // Listar todos los elementos móviles
  console.log("📱 Elementos móviles encontrados:");
  document.querySelectorAll('[id^="mobile-"]').forEach(el => {
    console.log(`  - ${el.id}: ${el.tagName.toLowerCase()} (${el.className || 'sin clases'})`);
  });
};

// Función para debug de temas
window.debugTheme = function() {
  const htmlElement = document.documentElement;
  const bodyElement = document.body;
  const computedStyle = getComputedStyle(htmlElement);
  
  console.log("🎨 Debug de tema completo:", {
    htmlClasses: htmlElement.className,
    bodyClasses: bodyElement.className,
    htmlDataTheme: htmlElement.getAttribute('data-theme'),
    bodyDataTheme: bodyElement.getAttribute('data-theme'),
    computedBackgroundColor: window.getComputedStyle(bodyElement).backgroundColor,
    computedColor: window.getComputedStyle(bodyElement).color,
    systemPreference: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  });
  
  // Mostrar las variables CSS actuales
  console.log("🎨 Variables CSS actuales:", {
    '--bg-card': computedStyle.getPropertyValue('--bg-card').trim(),
    '--border-color': computedStyle.getPropertyValue('--border-color').trim(),
    '--text-primary': computedStyle.getPropertyValue('--text-primary').trim(),
    '--text-secondary': computedStyle.getPropertyValue('--text-secondary').trim(),
    '--shadow-elevated': computedStyle.getPropertyValue('--shadow-elevated').trim(),
    '--bg-primary': computedStyle.getPropertyValue('--bg-primary').trim(),
    '--bg-secondary': computedStyle.getPropertyValue('--bg-secondary').trim(),
    '--radius-md': computedStyle.getPropertyValue('--radius-md').trim()
  });
  
  // Probar la función getCurrentThemeColors
  const themeColors = getCurrentThemeColors();
  console.log("🎨 Colores procesados:", themeColors);
  
  // Mostrar todos los dropdowns desktop
  const desktopDropdowns = document.querySelectorAll('[id$="-menu"]:not([id*="mobile"])');
  console.log("🖥️ Dropdowns desktop encontrados:", desktopDropdowns.length);
  desktopDropdowns.forEach(dropdown => {
    console.log(`  - ${dropdown.id}: ${dropdown.classList.contains('hidden') ? 'cerrado' : 'abierto'}`);
  });
};

console.log("🎉 Sistema de navegación cargado completamente - Versión Final Integrada");
console.log("💡 Usa window.debugNavbar() en la consola para información de debug");
