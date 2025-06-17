#!/usr/bin/env python3
"""
Script de debug para verificar variables de entorno en Render
"""
import os

def debug_env():
    """Debug environment variables"""
    print("🔍 DEBUGGER DE VARIABLES DE ENTORNO")
    print("=" * 50)
    
    # Variables críticas
    critical_vars = [
        'DATABASE_URL',
        'REDIS_URL', 
        'FLASK_ENV',
        'SECRET_KEY',
        'PORT'
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            # Ocultar información sensible
            if var in ['SECRET_KEY', 'DATABASE_URL', 'REDIS_URL']:
                display_value = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***HIDDEN***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    print("\n🔍 ANÁLISIS DATABASE_URL:")
    database_url = os.getenv('DATABASE_URL', '')
    if database_url:
        print(f"📄 URL completa (primeros 50 chars): {database_url[:50]}...")
        
        # Detectar placeholders
        placeholders = ['username', 'password', 'hostname', 'port', 'database', 'host']
        found_placeholders = [p for p in placeholders if p in database_url.lower()]
        
        if found_placeholders:
            print(f"⚠️  PLACEHOLDERS DETECTADOS: {found_placeholders}")
            print("💡 Esto significa que Render aún no ha sustituido los valores reales")
        else:
            print("✅ No se detectaron placeholders - URL parece válida")
            
        # Análisis de esquema
        if database_url.startswith('postgres://'):
            print("🔧 URL usa esquema 'postgres://' - se convertirá a 'postgresql://'")
        elif database_url.startswith('postgresql://'):
            print("✅ URL usa esquema correcto 'postgresql://'")
        else:
            print(f"⚠️  Esquema desconocido: {database_url.split('://')[0] if '://' in database_url else 'N/A'}")
    else:
        print("❌ DATABASE_URL no configurado")
    
    print("\n🔍 ANÁLISIS GOOGLE SHEETS:")
    
    # Verificar SHEET_ID
    sheet_id = os.getenv('SHEET_ID', '')
    if sheet_id:
        print(f"✅ SHEET_ID configurado: {sheet_id[:20]}...")
    else:
        print("❌ SHEET_ID no configurado")
    
    # Verificar credenciales en múltiples ubicaciones
    print("\n🔍 BÚSQUEDA DE CREDENCIALES GOOGLE:")
    credential_paths = [
        '/etc/secrets/edp-control-system-f3cfafc0093a.json',  # Render Secret Files
        '/etc/secrets/google-credentials.json',
        '/app/edp_mvp/app/keys/edp-control-system-f3cfafc0093a.json',  # Ubicación en contenedor
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS')  # Variable de entorno
    ]
    
    found_credentials = False
    for path in credential_paths:
        if path and os.path.exists(path):
            print(f"✅ ENCONTRADO: {path}")
            found_credentials = True
            # Verificar permisos de lectura
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    if 'client_email' in content:
                        print("   📧 Archivo contiene client_email - formato correcto")
                    else:
                        print("   ⚠️ Archivo no parece ser credenciales válidas")
            except Exception as e:
                print(f"   ❌ Error leyendo archivo: {e}")
        elif path:
            print(f"❌ No encontrado: {path}")
    
    if not found_credentials:
        print("⚠️ No se encontraron credenciales - se usará modo demo")
    
    # Verificar Secret Files directory
    print(f"\n🔍 CONTENIDO DE /etc/secrets/:")
    try:
        import glob
        secret_files = glob.glob('/etc/secrets/*')
        if secret_files:
            for file in secret_files:
                print(f"   📄 {file}")
        else:
            print("   📂 Directorio vacío o no existe")
    except Exception as e:
        print(f"   ❌ Error listando /etc/secrets/: {e}")

if __name__ == "__main__":
    debug_env()
