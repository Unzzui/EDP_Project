#!/usr/bin/env python3
"""
Test para simular el entorno de Render localmente
"""
import os
import sys
import tempfile
import json
from pathlib import Path

# Simular las variables de entorno de Render
def setup_render_simulation():
    """Configurar variables de entorno como en Render"""
    print("🎭 SIMULANDO ENTORNO DE RENDER")
    print("=" * 40)
    
    # Crear directorio temporal que simule /etc/secrets
    secrets_dir = Path("/tmp/test_etc_secrets")
    secrets_dir.mkdir(exist_ok=True)
    
    # Crear archivo de credenciales de prueba
    test_creds = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest-private-key\n-----END PRIVATE KEY-----",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    
    creds_file = secrets_dir / "edp-control-system-f3cfafc0093a.json"
    with open(creds_file, 'w') as f:
        json.dump(test_creds, f, indent=2)
    
    # Configurar variables de entorno como en Render
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(creds_file)
    os.environ['GOOGLE_CREDENTIALS'] = str(creds_file)
    os.environ['SHEET_ID'] = 'test-sheet-id-123'
    os.environ['FLASK_ENV'] = 'production'
    os.environ['DEBUG'] = 'False'
    
    print(f"✅ Credenciales de prueba creadas en: {creds_file}")
    print(f"✅ Variables de entorno configuradas:")
    print(f"   GOOGLE_APPLICATION_CREDENTIALS={os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
    print(f"   GOOGLE_CREDENTIALS={os.getenv('GOOGLE_CREDENTIALS')}")
    print(f"   SHEET_ID={os.getenv('SHEET_ID')}")
    
    return secrets_dir, creds_file

def test_config_loading():
    """Test de carga de configuración"""
    print("\n🔧 TESTING CARGA DE CONFIGURACIÓN")
    print("=" * 40)
    
    try:
        # Añadir el proyecto al path
        project_path = '/home/unzzui/Documents/coding/EDP_Project'
        if project_path not in sys.path:
            sys.path.insert(0, project_path)
            
        from edp_mvp.app.config import get_config
        
        config = get_config()
        
        print(f"✅ Config cargado correctamente")
        print(f"📍 GOOGLE_CREDENTIALS: {config.GOOGLE_CREDENTIALS}")
        print(f"📊 SHEET_ID: {config.SHEET_ID}")
        print(f"🌍 Environment: {config.FLASK_ENV}")
        
        if config.GOOGLE_CREDENTIALS:
            print("✅ Credenciales encontradas en configuración")
            
            # Verificar que el archivo es legible
            if os.path.exists(config.GOOGLE_CREDENTIALS):
                print("✅ Archivo de credenciales existe y es accesible")
                
                try:
                    with open(config.GOOGLE_CREDENTIALS, 'r') as f:
                        data = json.load(f)
                    print("✅ Archivo de credenciales es JSON válido")
                    print(f"   📧 Client Email: {data.get('client_email', 'N/A')}")
                    return True
                except Exception as e:
                    print(f"❌ Error leyendo credenciales: {e}")
                    return False
            else:
                print("❌ Archivo de credenciales no existe")
                return False
        else:
            print("❌ No se encontraron credenciales en configuración")
            return False
            
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gsheet_service():
    """Test del servicio de Google Sheets"""
    print("\n📊 TESTING SERVICIO GOOGLE SHEETS")
    print("=" * 40)
    
    try:
        from edp_mvp.app.utils.gsheet import get_service
        
        service = get_service()
        
        if service:
            print("✅ Servicio de Google Sheets inicializado")
            print("✅ Las credenciales son válidas")
            return True
        else:
            print("❌ No se pudo inicializar servicio de Google Sheets")
            print("⚠️ Esto puede ser normal si las credenciales son de prueba")
            return False
            
    except Exception as e:
        print(f"❌ Error con servicio Google Sheets: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_simulation(secrets_dir):
    """Limpiar archivos de simulación"""
    print("\n🧹 LIMPIANDO SIMULACIÓN")
    print("=" * 40)
    
    try:
        import shutil
        shutil.rmtree(secrets_dir)
        print("✅ Archivos de simulación eliminados")
        
        # Limpiar variables de entorno
        for var in ['GOOGLE_APPLICATION_CREDENTIALS', 'GOOGLE_CREDENTIALS']:
            if var in os.environ:
                del os.environ[var]
        print("✅ Variables de entorno limpiadas")
        
    except Exception as e:
        print(f"⚠️ Error en limpieza: {e}")

if __name__ == "__main__":
    print("🧪 TEST DE SIMULACIÓN DE RENDER")
    print("=" * 60)
    
    # Setup
    secrets_dir, creds_file = setup_render_simulation()
    
    # Tests
    tests = [
        ("Carga de configuración", test_config_loading),
        ("Servicio Google Sheets", test_gsheet_service)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 Ejecutando: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASS")
                passed += 1
            else:
                print(f"❌ {test_name}: FAIL")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    # Cleanup
    cleanup_simulation(secrets_dir)
    
    # Resultados
    print("\n" + "=" * 60)
    print(f"📊 RESULTADOS: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡SIMULACIÓN EXITOSA!")
        print("✅ La configuración debería funcionar en Render")
        sys.exit(0)
    else:
        print("⚠️ Algunos tests fallaron")
        print("💡 Revisar configuración antes del deploy")
        sys.exit(1)
