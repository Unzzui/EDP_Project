#!/usr/bin/env python3
"""
Script para corregir las clases CSS del navbar y estandarizar todos los dropdowns
"""

import re
import os

def fix_navbar_classes():
    """Corrige las clases CSS inconsistentes en el navbar"""
    
    navbar_file = '/home/unzzui/Documents/coding/EDP_Project/edp_mvp/app/templates/base/navbar.html'
    
    if not os.path.exists(navbar_file):
        print(f"❌ Archivo no encontrado: {navbar_file}")
        return
    
    # Leer el archivo
    with open(navbar_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 Corrigiendo clases CSS del navbar...")
    
    # Patrón para encontrar elementos con clases inconsistentes en dropdowns
    # Reemplazar clases de Tailwind por clases CSS estándar
    
    # 1. Cambiar contenedores de dropdown
    content = re.sub(
        r'class="hidden absolute left-0 mt-2 w-\d+ bg-\[color:var\(--bg-card\)\] border border-\[color:var\(--border-color\)\] rounded-md shadow-lg z-50"',
        'class="dropdown-menu hidden"',
        content
    )
    
    # 2. Cambiar contenido de dropdown
    content = re.sub(
        r'class="py-2"',
        'class="dropdown-content"',
        content
    )
    
    # 3. Cambiar items de dropdown - más específico
    content = re.sub(
        r'class="block px-4 py-2 text-sm hover:bg-\[color:var\(--bg-highlight\)\] transition-colors"',
        'class="dropdown-item"',
        content
    )
    
    # 4. Cambiar iconos en dropdown items
    content = re.sub(
        r'class="w-4 h-4 inline mr-2"',
        'class="dropdown-icon"',
        content
    )
    
    # 5. Casos especiales con colores adicionales
    content = re.sub(
        r'class="block px-4 py-2 text-sm hover:bg-\[color:var\(--bg-highlight\)\] transition-colors text-\[color:var\(--text-secondary\)\]"',
        'class="dropdown-item"',
        content
    )
    
    # 6. Casos especiales para logout (color rojo)
    content = re.sub(
        r'class="block px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"',
        'class="dropdown-item text-red-600 hover:bg-red-50"',
        content
    )
    
    print("✅ Clases corregidas:")
    print("   - Contenedores de dropdown estandarizados")
    print("   - Elementos de dropdown uniformados")
    print("   - Iconos actualizados")
    
    # Escribir archivo corregido
    with open(navbar_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"💾 Archivo actualizado: {navbar_file}")

if __name__ == "__main__":
    fix_navbar_classes()
    print("🎉 Corrección completada!")
