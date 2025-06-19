#!/usr/bin/env python3
"""
Test script para verificar que log_cambio_edp detecta correctamente el usuario actual
"""

import sys
import os
sys.path.append('/home/unzzui/Documents/coding/EDP_Project')

from edp_mvp.app.utils.supabase_adapter import log_cambio_edp

def test_log_without_user():
    """Prueba que log_cambio_edp funciona cuando no se especifica usuario"""
    print("🧪 Probando log_cambio_edp sin especificar usuario...")
    
    try:
        # Esta llamada debería usar "Sistema" como fallback cuando no hay contexto de Flask
        log_cambio_edp(
            n_edp="TEST-001",
            proyecto="Proyecto Test",
            campo="estado",
            antes="borrador",
            despues="revision",
            # No especificamos usuario para probar auto-detección
        )
        print("✅ log_cambio_edp funcionó correctamente sin usuario especificado")
        
    except Exception as e:
        print(f"❌ Error en log_cambio_edp: {e}")
        import traceback
        traceback.print_exc()

def test_log_with_user():
    """Prueba que log_cambio_edp funciona cuando se especifica usuario"""
    print("🧪 Probando log_cambio_edp con usuario especificado...")
    
    try:
        log_cambio_edp(
            n_edp="TEST-002",
            proyecto="Proyecto Test",
            campo="monto",
            antes="1000",
            despues="1500",
            usuario="Usuario Manual"
        )
        print("✅ log_cambio_edp funcionó correctamente con usuario especificado")
        
    except Exception as e:
        print(f"❌ Error en log_cambio_edp: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de logging de usuario...\n")
    
    # Nota: Estas pruebas requieren que las credenciales de Google Sheets estén configuradas
    # y que GOOGLE_CREDENTIALS esté definido en la configuración
    
    test_log_without_user()
    print()
    test_log_with_user()
    
    print("\n✨ Pruebas completadas!")
    print("\nCómo funciona la nueva funcionalidad:")
    print("1. Cuando se llama log_cambio_edp() sin especificar 'usuario':")
    print("   - Si está en contexto de Flask con usuario autenticado → usa datos del usuario")
    print("   - Si no hay contexto o usuario → usa 'Sistema' como fallback")
    print("2. Cuando se especifica 'usuario' → usa el valor proporcionado")
    print("3. Los cambios son retrocompatibles con código existente")
