#!/usr/bin/env python3
"""
Script simple para verificar que las credenciales se cargan correctamente en Render
Este script se puede llamar desde cualquier vista para debug
"""
import os
import sys

def check_credentials_status():
    """Verificar estado de credenciales de manera simple"""
    print("🔍 VERIFICACIÓN RÁPIDA DE CREDENCIALES")
    print("=" * 45)
    
    # Verificar variables de entorno
    google_app_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    google_creds = os.getenv('GOOGLE_CREDENTIALS')
    sheet_id = os.getenv('SHEET_ID')
    
    print(f"📋 Variables de entorno:")
    print(f"   GOOGLE_APPLICATION_CREDENTIALS: {google_app_creds}")
    print(f"   GOOGLE_CREDENTIALS: {google_creds}")
    print(f"   SHEET_ID: {sheet_id}")
    
    # Verificar si los archivos existen
    credential_files = [google_app_creds, google_creds] if google_app_creds and google_creds else []
    
    for cred_file in credential_files:
        if cred_file and os.path.exists(cred_file):
            try:
                file_size = os.path.getsize(cred_file)
                print(f"   ✅ {cred_file} ({file_size} bytes)")
                
                # Intentar leer como JSON
                import json
                with open(cred_file, 'r') as f:
                    data = json.load(f)
                print(f"      📧 Client: {data.get('client_email', 'N/A')}")
                print(f"      🆔 Project: {data.get('project_id', 'N/A')}")
                return True
                
            except PermissionError:
                print(f"   ❌ {cred_file} (sin permisos)")
            except Exception as e:
                print(f"   ❌ {cred_file} (error: {e})")
        else:
            print(f"   ❌ {cred_file} (no existe)")
    
    # Verificar directorios alternativos
    alt_dirs = ['/app/secrets', '/etc/secrets']
    for dir_path in alt_dirs:
        if os.path.exists(dir_path):
            try:
                files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
                print(f"   📁 {dir_path}: {files}")
            except:
                print(f"   📁 {dir_path}: (sin acceso)")
    
    return False

def test_google_service():
    """Test rápido del servicio de Google"""
    try:
        # Añadir el path del proyecto
        import sys
        sys.path.insert(0, '/app')
        
        from edp_mvp.app.utils.gsheet import get_service
        service = get_service()
        
        if service:
            print("✅ Servicio de Google Sheets inicializado")
            return True
        else:
            print("❌ No se pudo inicializar servicio de Google Sheets")
            return False
    except Exception as e:
        print(f"❌ Error probando servicio: {e}")
        return False

def get_credentials_summary():
    """Obtener resumen simple del estado de credenciales"""
    has_creds = check_credentials_status()
    has_service = test_google_service()
    
    if has_creds and has_service:
        return "🟢 Google Sheets ACTIVO"
    elif has_creds:
        return "🟡 Credenciales OK, Servicio FALLA"
    else:
        return "🔴 Modo DEMO activo"

if __name__ == "__main__":
    status = get_credentials_summary()
    print(f"\n📊 ESTADO: {status}")
