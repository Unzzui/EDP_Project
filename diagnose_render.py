#!/usr/bin/env python3
"""
Script de diagnóstico específico para problemas en Render
"""
import os
import sys
import json
from pathlib import Path

def diagnose_render_environment():
    """Diagnóstico completo del entorno de Render"""
    print("🔍 DIAGNÓSTICO DE ENTORNO RENDER")
    print("=" * 50)
    
    # 1. Variables de entorno importantes
    print("📋 VARIABLES DE ENTORNO:")
    important_vars = [
        'FLASK_ENV', 'SECRET_KEY', 'DEBUG', 'SHEET_ID',
        'DATABASE_URL', 'REDIS_URL', 'PORT', 'RENDER'
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        if value:
            # Ocultar valores sensibles
            if var in ['SECRET_KEY', 'DATABASE_URL']:
                display_value = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"   ✅ {var}={display_value}")
        else:
            print(f"   ❌ {var}=NOT_SET")
    
    # 2. Verificar directorios importantes
    print("\n📁 DIRECTORIOS:")
    important_dirs = [
        '/etc/secrets',
        '/app/secrets',
        'edp_mvp/app',
        'edp_mvp/app/',
        'edp_mvp/app/keys',
        'edp_mvp/app/app',
        'edp_mvp/app/utils'
    ]
    
    for dir_path in important_dirs:
        if os.path.exists(dir_path):
            try:
                files = os.listdir(dir_path)
                print(f"   ✅ {dir_path} ({len(files)} archivos)")
                
                # Mostrar archivos importantes
                for file in files:
                    if file.endswith('.json') or file in ['demo_data.py', 'gsheet.py']:
                        file_path = os.path.join(dir_path, file)
                        file_size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                        print(f"      📄 {file} ({file_size} bytes)")
            except PermissionError:
                print(f"   ⚠️ {dir_path} (sin permisos de lectura)")
        else:
            print(f"   ❌ {dir_path} (no existe)")
    
    # 3. Verificar credenciales específicamente
    print("\n🔑 BÚSQUEDA DE CREDENCIALES:")
    credential_paths = [
        '/etc/secrets/edp-control-system-f3cfafc0093a.json',
        '/app/secrets/edp-control-system-f3cfafc0093a.json',
        '/etc/secrets/google-credentials.json',
        '/app/secrets/google-credentials.json'
        '/edp_mvp/app/keys/edp-control-system-f3cfafc0093a.json',
        '/edp_mvp/app/keys/google-credentials.json',
        '/edp_mvp/app/keys/edp-control-system-f3cfafc0093a.json',
    ]
    
    found_credentials = False
    for cred_path in credential_paths:
        if os.path.exists(cred_path):
            try:
                file_size = os.path.getsize(cred_path)
                print(f"   ✅ {cred_path} ({file_size} bytes)")
                
                # Intentar leer como JSON
                try:
                    with open(cred_path, 'r') as f:
                        data = json.load(f)
                    
                    required_fields = ['client_email', 'private_key', 'project_id']
                    has_all = all(field in data for field in required_fields)
                    
                    if has_all:
                        print(f"      ✅ JSON válido con campos requeridos")
                        print(f"      📧 Client: {data.get('client_email', 'N/A')}")
                        found_credentials = True
                    else:
                        missing = [f for f in required_fields if f not in data]
                        print(f"      ❌ Faltan campos: {missing}")
                        
                except PermissionError:
                    print(f"      ⚠️ Archivo existe pero sin permisos de lectura")
                except json.JSONDecodeError:
                    print(f"      ❌ Archivo no es JSON válido")
                except Exception as e:
                    print(f"      ❌ Error leyendo: {e}")
                    
            except Exception as e:
                print(f"   ❌ Error accediendo a {cred_path}: {e}")
        else:
            print(f"   ❌ {cred_path} (no existe)")
    
    # 4. Test de configuración de la app
    print("\n⚙️ CONFIGURACIÓN DE LA APP:")
    try:
        sys.path.insert(0, '/app')
        from edp_mvp.app.config import get_config
        
        config = get_config()
        print(f"   ✅ Config cargado correctamente")
        print(f"   🔑 GOOGLE_CREDENTIALS: {config.GOOGLE_CREDENTIALS}")
        print(f"   📊 SHEET_ID: {config.SHEET_ID}")
        print(f"   🌍 Environment: {config.FLASK_ENV}")
        print(f"   🐛 Debug: {config.DEBUG}")
        
        # Test del método de búsqueda de credenciales
        creds_path = config._get_google_credentials_path()
        print(f"   🔍 Resultado búsqueda credenciales: {creds_path}")
        
    except Exception as e:
        print(f"   ❌ Error cargando config: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. Test de datos demo
    print("\n🎭 TEST DE DATOS DEMO:")
    try:
        from edp_mvp.app.utils.demo_data import get_demo_edp_data, get_demo_logs_data
        
        edp_demo = get_demo_edp_data()
        print(f"   ✅ Datos demo EDP: {len(edp_demo)} registros")
        
        logs_demo = get_demo_logs_data()
        print(f"   ✅ Datos demo logs: {len(logs_demo)} registros")
        
    except Exception as e:
        print(f"   ❌ Error con datos demo: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Test de función read_sheet
    print("\n📊 TEST DE READ_SHEET:")
    try:
        from edp_mvp.app.utils.gsheet import read_sheet
        
        # Test con EDP
        edp_data = read_sheet("edp!A:V")
        print(f"   📈 EDP data: {len(edp_data)} registros")
        if not edp_data.empty:
            print(f"      Columnas: {list(edp_data.columns)[:5]}...")
        
        # Test con logs
        log_data = read_sheet("log!A:G")
        print(f"   📝 Log data: {len(log_data)} registros")
        if not log_data.empty:
            print(f"      Columnas: {list(log_data.columns)}")
            
    except Exception as e:
        print(f"   ❌ Error con read_sheet: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    if found_credentials:
        print("🎉 CREDENCIALES ENCONTRADAS - Google Sheets debería funcionar")
        return True
    else:
        print("⚠️ NO SE ENCONTRARON CREDENCIALES VÁLIDAS")
        print("🎭 La app debería funcionar en modo demo")
        return False

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO COMPLETO PARA RENDER")
    print("=" * 60)
    
    result = diagnose_render_environment()
    
    print(f"\n📋 RESULTADO: {'CREDENCIALES OK' if result else 'MODO DEMO'}")
    sys.exit(0 if result else 1)
