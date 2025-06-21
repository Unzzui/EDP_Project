// Test para el comportamiento del navbar móvil
// El problema: cuando haces clic en submenú, se cierra todo el navbar

console.log("🧪 TESTING NAVBAR MOBILE BEHAVIOR");

// Función para probar el flujo completo
function testMobileNavbarFlow() {
  console.log("🚀 Starting mobile navbar flow test...");
  
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  const mobileMenu = document.getElementById('mobile-menu');
  const controllerToggle = document.getElementById('mobile-controller-toggle');
  
  if (!mobileMenuButton || !mobileMenu || !controllerToggle) {
    console.log("❌ Required elements not found:", {
      mobileMenuButton: !!mobileMenuButton,
      mobileMenu: !!mobileMenu,
      controllerToggle: !!controllerToggle
    });
    return;
  }
  
  // Paso 1: Abrir menú móvil
  console.log("🔵 Step 1: Opening mobile menu");
  mobileMenuButton.click();
  
  setTimeout(() => {
    const isMenuOpen = !mobileMenu.classList.contains('hidden');
    console.log(`📱 Mobile menu open: ${isMenuOpen}`);
    
    if (isMenuOpen) {
      // Paso 2: Hacer clic en submenú
      console.log("🔵 Step 2: Clicking on controller submenu");
      controllerToggle.click();
      
      setTimeout(() => {
        const isMenuStillOpen = !mobileMenu.classList.contains('hidden');
        const controllerMenu = document.getElementById('mobile-controller-menu');
        const isSubmenuOpen = controllerMenu && !controllerMenu.classList.contains('hidden');
        
        console.log("🎯 RESULTS:", {
          mainMenuStillOpen: isMenuStillOpen,
          submenuOpen: isSubmenuOpen,
          expected: "Both should be true"
        });
        
        if (!isMenuStillOpen) {
          console.log("❌ BUG CONFIRMED: Main menu closed when clicking submenu");
        } else {
          console.log("✅ SUCCESS: Main menu stayed open");
        }
        
        if (isSubmenuOpen) {
          console.log("✅ SUCCESS: Submenu opened");
        } else {
          console.log("❌ ISSUE: Submenu didn't open");
        }
        
      }, 200);
    }
  }, 200);
}

// Función para monitorear eventos
function monitorNavbarEvents() {
  console.log("👁️ Starting event monitoring...");
  
  const mobileMenu = document.getElementById('mobile-menu');
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  
  // Monitor cambios en el menú móvil
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
        const target = mutation.target;
        if (target.id === 'mobile-menu') {
          const isHidden = target.classList.contains('hidden');
          console.log(`📱 Mobile menu state changed: ${isHidden ? 'CLOSED' : 'OPEN'}`);
        }
      }
    });
  });
  
  if (mobileMenu) {
    observer.observe(mobileMenu, { attributes: true, attributeFilter: ['class'] });
  }
  
  // Monitor clicks en submenús
  document.querySelectorAll('[id^="mobile-"][id$="-toggle"]').forEach(toggle => {
    toggle.addEventListener('click', function(e) {
      console.log(`🔴 Submenu click detected: ${this.id}`, {
        preventDefault: e.defaultPrevented,
        propagationStopped: e.cancelBubble,
        timestamp: new Date().toISOString()
      });
    });
  });
}

// Auto-ejecutar si estamos en móvil
if (window.innerWidth < 768) {
  console.log(`
📱 MOBILE NAVBAR BEHAVIOR TESTER

Functions available:
- testMobileNavbarFlow() - Test the complete flow
- monitorNavbarEvents() - Monitor events in real-time

Expected behavior:
1. Click hamburger → menu opens
2. Click submenu → submenu opens, main menu STAYS open
3. Click outside → everything closes

Current issue: Step 2 closes the main menu
  `);
  
  // Auto-start monitoring
  setTimeout(monitorNavbarEvents, 500);
  
} else {
  console.log("📱 Switch to mobile view (< 768px) to test navbar behavior");
}

// Export functions globally
window.testMobileNavbarFlow = testMobileNavbarFlow;
window.monitorNavbarEvents = monitorNavbarEvents; 