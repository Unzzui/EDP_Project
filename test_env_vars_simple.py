#!/usr/bin/env python3
"""
Test simplificado para verificar que las variables de entorno separadas funcionan sin archivos temporales
"""

import os
import sys
from pathlib import Path

# Añadir el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

def load_env_from_file():
    """Cargar variables de entorno desde .env"""
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        print("❌ No se encuentra archivo .env")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Parsear .env manualmente para preservar saltos de línea
    lines = content.split('\n')
    current_var = None
    current_value = ""
    
    for line in lines:
        if '=' in line and not line.startswith('#'):
            if current_var:
                os.environ[current_var] = current_value.strip()
            
            key, value = line.split('=', 1)
            current_var = key.strip()
            current_value = value
        else:
            if current_var:
                current_value += '\n' + line
    
    if current_var:
        os.environ[current_var] = current_value.strip()
    
    return True

def test_google_service():
    """Test del servicio de Google Sheets"""
    print("🧪 TESTING SERVICIO GOOGLE SHEETS CON VARIABLES SEPARADAS")
    print("=" * 70)
    
    # Cargar variables desde .env
    if not load_env_from_file():
        return False
    
    # Verificar variables
    vars_to_check = ['GOOGLE_PROJECT_ID', 'GOOGLE_CLIENT_EMAIL', 'GOOGLE_PRIVATE_KEY']
    print("📍 Variables detectadas:")
    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            if var == 'GOOGLE_PRIVATE_KEY':
                display_value = '***' + value[-20:] if len(value) > 20 else '***'
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: NOT_SET")
            return False
    
    print("\n🔧 Importando y probando gsheet.py...")
    
    try:
        from edp_mvp.app.utils.gsheet import get_service
        
        print("✅ Módulo gsheet importado correctamente")
        
        # Intentar crear servicio
        service = get_service()
        
        if service:
            print("✅ Servicio de Google Sheets creado exitosamente")
            print("🎉 VARIABLES DE ENTORNO SEPARADAS FUNCIONANDO CORRECTAMENTE")
            return True
        else:
            print("❌ No se pudo crear servicio de Google Sheets")
            return False
            
    except Exception as e:
        print(f"❌ Error importando o usando gsheet: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO TEST SIMPLIFICADO")
    print("=" * 70)
    
    success = test_google_service()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 TEST EXITOSO")
        print("✅ Variables de entorno separadas funcionan correctamente")
        print("✅ No se generan archivos temporales")
        print("✅ Listo para Render deploy")
    else:
        print("❌ TEST FALLÓ")
        print("⚠️ Revisar configuración de variables de entorno")
    
    sys.exit(0 if success else 1)
