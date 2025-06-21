// Script de emergencia para forzar visibilidad de submenús móviles
// Copia y pega en la consola del navegador

function forceShowMobileSubmenu(type) {
  const menuId = `mobile-${type}-menu`;
  const menu = document.getElementById(menuId);
  
  if (menu) {
    console.log(`🔧 Forcing ${menuId} to be visible`);
    
    // Eliminar todas las clases
    menu.className = '';
    
    // Aplicar estilos directos
    menu.style.cssText = `
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
      max-height: 500px !important;
      background: red !important;
      border: 5px solid yellow !important;
      padding: 20px !important;
      margin: 10px !important;
      z-index: 999999 !important;
      position: relative !important;
      color: white !important;
      font-size: 16px !important;
      font-weight: bold !important;
    `;
    
    console.log(`✅ ${menuId} should now be visible with red background`);
    
    // Verificar
    setTimeout(() => {
      const rect = menu.getBoundingClientRect();
      console.log(`📐 ${menuId} dimensions:`, rect);
    }, 100);
    
  } else {
    console.log(`❌ ${menuId} not found`);
  }
}

// Función para probar todos los submenús
function forceShowAllMobileSubmenus() {
  const types = ['controller', 'manager', 'project-manager', 'edp', 'admin'];
  
  types.forEach(type => {
    forceShowMobileSubmenu(type);
  });
}

// Auto-ejecutar si estamos en móvil
if (window.innerWidth < 768) {
  console.log(`
🚨 EMERGENCY MOBILE SUBMENU TESTER
   
Ejecuta estas funciones:
- forceShowMobileSubmenu('controller')
- forceShowMobileSubmenu('edp') 
- forceShowAllMobileSubmenus()
  `);
} else {
  console.log("📱 Redimensiona a móvil para usar este script");
} 