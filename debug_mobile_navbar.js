/**
 * Script de debugging para probar submenús móviles
 * Ejecuta este script en la consola del navegador para probar
 */

// Función para probar todos los submenús móviles
function testMobileSubmenus() {
  console.log("🧪 TESTING MOBILE SUBMENUS");
  
  const mobileSubmenus = [
    'mobile-controller-menu',
    'mobile-manager-menu', 
    'mobile-project-manager-menu',
    'mobile-edp-menu',
    'mobile-admin-menu'
  ];
  
  mobileSubmenus.forEach(menuId => {
    const menu = document.getElementById(menuId);
    const toggleId = menuId.replace('-menu', '-toggle');
    const toggle = document.getElementById(toggleId);
    
    console.log(`📱 Testing ${menuId}:`, {
      menu: menu ? 'EXISTS' : 'NOT FOUND',
      toggle: toggle ? 'EXISTS' : 'NOT FOUND',
      hidden: menu ? menu.classList.contains('hidden') : 'N/A',
      style: menu ? menu.style.cssText : 'N/A'
    });
    
    if (menu && toggle) {
      // Agregar botón de debug
      if (!document.getElementById(`debug-${menuId}`)) {
        const debugBtn = document.createElement('button');
        debugBtn.id = `debug-${menuId}`;
        debugBtn.textContent = `Debug ${menuId}`;
        debugBtn.style.cssText = `
          position: fixed;
          top: ${10 + (mobileSubmenus.indexOf(menuId) * 40)}px;
          right: 10px;
          z-index: 99999;
          background: red;
          color: white;
          padding: 5px 10px;
          border: none;
          border-radius: 4px;
          font-size: 12px;
        `;
        
        debugBtn.onclick = function() {
          console.log(`🔧 Manual toggle for ${menuId}`);
          
          if (menu.classList.contains('hidden')) {
            menu.classList.remove('hidden');
            menu.classList.add('debug-mobile-submenu');
            menu.style.cssText = `
              display: block !important;
              opacity: 1 !important;
              max-height: 300px !important;
              visibility: visible !important;
              background: rgba(0, 255, 0, 0.1) !important;
              border: 2px solid lime !important;
              padding-top: 0.5rem !important;
            `;
            debugBtn.textContent = `Hide ${menuId}`;
            debugBtn.style.background = 'green';
          } else {
            menu.classList.add('hidden');
            menu.classList.remove('debug-mobile-submenu');
            menu.style.cssText = '';
            debugBtn.textContent = `Show ${menuId}`;
            debugBtn.style.background = 'red';
          }
        };
        
        document.body.appendChild(debugBtn);
      }
    }
  });
}

// Función para limpiar botones de debug
function cleanupDebugButtons() {
  const buttons = document.querySelectorAll('[id^="debug-mobile-"]');
  buttons.forEach(btn => btn.remove());
}

// Función para mostrar el estado actual del menú móvil
function showMobileMenuState() {
  const mobileMenu = document.getElementById('mobile-menu');
  const button = document.getElementById('mobile-menu-button');
  
  console.log("📱 MOBILE MENU STATE:", {
    menu: {
      exists: !!mobileMenu,
      hidden: mobileMenu ? mobileMenu.classList.contains('hidden') : 'N/A',
      style: mobileMenu ? mobileMenu.style.cssText : 'N/A',
      classes: mobileMenu ? mobileMenu.className : 'N/A'
    },
    button: {
      exists: !!button,
      classes: button ? button.className : 'N/A'
    },
    viewport: {
      width: window.innerWidth,
      isMobile: window.innerWidth < 768
    }
  });
}

// Función para simular click en menú móvil
function toggleMobileMenu() {
  const button = document.getElementById('mobile-menu-button');
  if (button) {
    console.log("🔴 Simulating mobile menu button click");
    button.click();
  } else {
    console.log("❌ Mobile menu button not found");
  }
}

// Función para simular click en submenú específico
function toggleMobileSubmenu(submenuName) {
  const toggleId = `mobile-${submenuName}-toggle`;
  const toggle = document.getElementById(toggleId);
  
  if (toggle) {
    console.log(`🔴 Simulating click on ${toggleId}`);
    toggle.click();
  } else {
    console.log(`❌ Toggle ${toggleId} not found`);
  }
}

// Función para aplicar estilos de debug a todos los submenús
function debugAllSubmenus() {
  const submenus = document.querySelectorAll('[id^="mobile-"][id$="-menu"]');
  
  submenus.forEach(submenu => {
    submenu.classList.remove('hidden');
    submenu.style.cssText = `
      display: block !important;
      opacity: 1 !important;
      max-height: 300px !important;
      visibility: visible !important;
      background: rgba(255, 255, 0, 0.2) !important;
      border: 2px dashed orange !important;
      padding: 0.5rem !important;
    `;
  });
  
  console.log("🟡 All mobile submenus forced visible for debugging");
}

// Agregar mensaje de ayuda
console.log(`
🧪 MOBILE NAVBAR DEBUG TOOLS:
   
📱 Basic Tests:
   showMobileMenuState() - Show current state
   toggleMobileMenu() - Toggle main mobile menu
   
🔧 Submenu Tests:
   testMobileSubmenus() - Add debug buttons for each submenu
   cleanupDebugButtons() - Remove debug buttons
   debugAllSubmenus() - Force show all submenus
   
📋 Individual Submenu Tests:
   toggleMobileSubmenu('controller') - Toggle controller submenu
   toggleMobileSubmenu('manager') - Toggle manager submenu
   toggleMobileSubmenu('edp') - Toggle EDP submenu
   toggleMobileSubmenu('admin') - Toggle admin submenu
   
💡 Usage: Copy and paste these function calls in browser console
`);

// Auto-execute basic test
if (window.innerWidth < 768) {
  console.log("📱 Mobile viewport detected, running basic tests...");
  showMobileMenuState();
} else {
  console.log("🖥️ Desktop viewport. Resize to < 768px for mobile testing.");
} 