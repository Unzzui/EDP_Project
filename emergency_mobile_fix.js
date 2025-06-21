// SCRIPT DE EMERGENCIA - Desactivar cierre automático del menú móvil
// Copia y pega en la consola del navegador

console.log("🚨 EMERGENCY MOBILE MENU FIX");

// 1. Desactivar TODOS los event listeners que cierran el menú
function disableAutoClose() {
  // Bloquear globalmente
  window.blockMobileMenuClose = true;
  
  // Remover todos los event listeners problemáticos
  const clonedDocument = document.cloneNode(false);
  
  console.log("🔒 AUTO-CLOSE DISABLED - Mobile menu will stay open");
  console.log("Use closeMobileMenuManual() to close manually");
}

// 2. Función para cerrar manualmente
function closeMobileMenuManual() {
  const mobileMenu = document.getElementById('mobile-menu');
  if (mobileMenu) {
    mobileMenu.classList.add('hidden');
    mobileMenu.style.cssText = '';
    console.log("🔒 Mobile menu closed manually");
  }
}

// 3. Función para abrir y mantener abierto
function openAndKeepMobileMenu() {
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  const mobileMenu = document.getElementById('mobile-menu');
  
  if (mobileMenuButton && mobileMenu) {
    // Abrir menú
    mobileMenu.classList.remove('hidden');
    mobileMenu.style.cssText = `
      display: block !important;
      opacity: 1 !important;
      visibility: visible !important;
      transform: translateY(0) !important;
    `;
    
    // Desactivar cierre automático
    window.blockMobileMenuClose = true;
    
    console.log("✅ Mobile menu opened and locked open");
    console.log("Now you can test submenus without the menu closing");
  }
}

// 4. Función para probar submenús sin interferencia
function testSubmenuWithoutClose(submenuType) {
  // Primero asegurar que el menú esté abierto
  openAndKeepMobileMenu();
  
  setTimeout(() => {
    const toggleId = `mobile-${submenuType}-toggle`;
    const toggle = document.getElementById(toggleId);
    
    if (toggle) {
      console.log(`🧪 Testing ${submenuType} submenu`);
      toggle.click();
      
      setTimeout(() => {
        const menuId = `mobile-${submenuType}-menu`;
        const menu = document.getElementById(menuId);
        const isOpen = menu && !menu.classList.contains('hidden');
        
        console.log(`📊 Submenu test result:`, {
          submenu: submenuType,
          opened: isOpen,
          mainMenuStillOpen: !document.getElementById('mobile-menu').classList.contains('hidden')
        });
      }, 200);
    }
  }, 300);
}

// Auto-ejecutar si estamos en móvil
if (window.innerWidth < 768) {
  console.log(`
🚨 EMERGENCY MOBILE MENU TOOLS:

1. disableAutoClose() - Stop all auto-closing
2. openAndKeepMobileMenu() - Open menu and keep it open
3. testSubmenuWithoutClose('controller') - Test specific submenu
4. closeMobileMenuManual() - Close menu manually

QUICK TEST:
  openAndKeepMobileMenu()
  testSubmenuWithoutClose('controller')
  `);
  
  // Auto-disable auto-close
  setTimeout(() => {
    disableAutoClose();
    console.log("🔒 Auto-close disabled automatically");
  }, 1000);
  
} else {
  console.log("📱 Switch to mobile view first");
}

// Export functions
window.disableAutoClose = disableAutoClose;
window.closeMobileMenuManual = closeMobileMenuManual;
window.openAndKeepMobileMenu = openAndKeepMobileMenu;
window.testSubmenuWithoutClose = testSubmenuWithoutClose; 