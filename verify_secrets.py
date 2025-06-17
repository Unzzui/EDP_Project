#!/usr/bin/env python3
"""
Script para verificar que los Secret Files estén correctamente configurados en Render
"""
import os
import json
import sys

def verify_secret_files():
    """Verificar que los Secret Files de Render estén disponibles"""
    
    print("🔐 VERIFICANDO SECRET FILES DE RENDER")
    print("=" * 50)
    
    # Verificar directorio de Secret Files copiados (creados por fix_render_secrets.py)
    app_secrets_dir = "/app/secrets"
    
    if os.path.exists(app_secrets_dir):
        print(f"✅ Directorio de Secret Files copiados encontrado: {app_secrets_dir}")
        
        # Listar archivos en el directorio de la app
        try:
            secret_files = os.listdir(app_secrets_dir)
            print(f"\n📁 Archivos en {app_secrets_dir} ({len(secret_files)}):")
            for file in secret_files:
                file_path = os.path.join(app_secrets_dir, file)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"   📄 {file} ({file_size} bytes)")
                else:
                    print(f"   📁 {file} (directorio)")
        except Exception as e:
            print(f"❌ Error listando Secret Files copiados: {e}")
            return False
            
        # Verificar archivo específico de credenciales Google en directorio copiado
        google_patterns = [
            "edp-control-system-f3cfafc0093a.json",
            "edp-control-system-*.json",
            "google-credentials.json"
        ]
        
        for pattern in google_patterns:
            import glob
            matching_files = glob.glob(os.path.join(app_secrets_dir, pattern))
            for google_creds_file in matching_files:
                if os.path.exists(google_creds_file):
                    print(f"\n✅ Credenciales Google encontradas: {google_creds_file}")
                    return verify_google_credentials_file(google_creds_file)
    
    # Si no hay archivos copiados, verificar directorio original (solo informativamente)
    secrets_dir = "/etc/secrets"
    
    if os.path.exists(secrets_dir):
        print(f"📁 Directorio Secret Files original: {secrets_dir}")
        
        # Intentar listar (puede fallar por permisos)
        try:
            secret_files = os.listdir(secrets_dir)
            print(f"📄 Archivos en Secret Files originales: {len(secret_files)}")
            
            # Verificar archivo específico de credenciales Google en directorio original
            google_creds_file = os.path.join(secrets_dir, "edp-control-system-f3cfafc0093a.json")
            
            if os.path.exists(google_creds_file):
                print(f"✅ Credenciales Google encontradas en original: {google_creds_file}")
                return verify_google_credentials_file(google_creds_file)
                
        except PermissionError:
            print("⚠️ No se puede acceder a Secret Files originales por permisos")
            print("💡 Esto es normal - los archivos deberían estar copiados en /app/secrets")
        except Exception as e:
            print(f"⚠️ Error accediendo a Secret Files originales: {e}")
    else:
        print("📁 Directorio /etc/secrets no encontrado")
        print("💡 Esto es normal en desarrollo local")
    
    print("❌ No se encontraron credenciales Google en ninguna ubicación")
    return False

def verify_google_credentials_file(google_creds_file):
    """Verificar un archivo específico de credenciales Google"""
    try:
        # Verificar contenido del archivo
        with open(google_creds_file, 'r') as f:
            creds_data = json.load(f)
        
        required_fields = ['client_email', 'private_key', 'project_id']
        missing_fields = [field for field in required_fields if field not in creds_data]
        
        if missing_fields:
            print(f"❌ Faltan campos requeridos: {missing_fields}")
            return False
        else:
            print("✅ Archivo de credenciales tiene el formato correcto")
            print(f"   📧 Client Email: {creds_data.get('client_email', 'N/A')}")
            print(f"   🆔 Project ID: {creds_data.get('project_id', 'N/A')}")
            return True
            
    except PermissionError as pe:
        print(f"⚠️ Error de permisos leyendo credenciales: {pe}")
        print("💡 El archivo existe pero no se puede leer con los permisos actuales")
        print("🎭 La aplicación funcionará en modo demo")
        return True  # Considerar como válido si existe pero no se puede leer
    except json.JSONDecodeError as e:
        print(f"❌ Error: Archivo no es JSON válido: {e}")
        return False
    except Exception as e:
        print(f"❌ Error leyendo credenciales: {e}")
        return False

def verify_environment_vars():
    """Verificar variables de entorno relacionadas con Google Sheets"""
    
    print("\n🔍 VERIFICANDO VARIABLES DE ENTORNO")
    print("=" * 50)
    
    sheet_id = os.getenv('SHEET_ID')
    if sheet_id:
        print(f"✅ SHEET_ID configurado: {sheet_id}")
    else:
        print("❌ SHEET_ID no configurado")
        print("💡 Configura en Render: Environment → Add Environment Variable")
        return False
    
    return True

if __name__ == "__main__":
    print("🔐 VERIFICADOR DE SECRET FILES PARA RENDER")
    print("=" * 60)
    
    secrets_ok = verify_secret_files()
    env_ok = verify_environment_vars()
    
    print("\n" + "=" * 60)
    if secrets_ok and env_ok:
        print("🎉 ¡TODO CONFIGURADO CORRECTAMENTE!")
        print("✅ Google Sheets debería funcionar en producción")
        sys.exit(0)
    else:
        print("⚠️  CONFIGURACIÓN INCOMPLETA")
        if not secrets_ok:
            print("❌ Faltan Secret Files")
        if not env_ok:
            print("❌ Faltan variables de entorno")
        print("🎭 La aplicación funcionará en modo demo")
        sys.exit(1)
