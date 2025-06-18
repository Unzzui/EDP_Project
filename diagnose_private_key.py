#!/usr/bin/env python3
"""
Diagnóstico específico para el formato de GOOGLE_PRIVATE_KEY
"""

import os
import json
import tempfile
from pathlib import Path

def load_env_file(env_file_path):
    """Cargar archivo .env manualmente para inspeccionar el contenido"""
    if not Path(env_file_path).exists():
        print(f"❌ Archivo .env no encontrado: {env_file_path}")
        return
    
    with open(env_file_path, 'r') as f:
        content = f.read()
    
    print(f"📄 Contenido del archivo {env_file_path}:")
    print("-" * 50)
    
    # Buscar la línea que contiene GOOGLE_PRIVATE_KEY
    lines = content.split('\n')
    in_private_key = False
    private_key_lines = []
    
    for i, line in enumerate(lines):
        if line.startswith('GOOGLE_PRIVATE_KEY='):
            in_private_key = True
            private_key_lines.append(line)
            print(f"Línea {i+1}: {line[:50]}...")
        elif in_private_key:
            if line.startswith('-----END PRIVATE KEY-----'):
                private_key_lines.append(line)
                in_private_key = False
                print(f"Línea {i+1}: {line}")
                break
            else:
                private_key_lines.append(line)
                print(f"Línea {i+1}: {line[:50]}...")
    
    print("-" * 50)
    
    # Reconstruir la clave privada completa
    if private_key_lines:
        # Remover el prefijo GOOGLE_PRIVATE_KEY= de la primera línea
        first_line = private_key_lines[0]
        if first_line.startswith('GOOGLE_PRIVATE_KEY='):
            private_key_lines[0] = first_line[len('GOOGLE_PRIVATE_KEY='):]
        
        full_private_key = '\n'.join(private_key_lines)
        
        print("🔍 Clave privada reconstruida:")
        print(f"   Empieza con: {full_private_key[:50]}...")
        print(f"   Termina con: ...{full_private_key[-50:]}")
        print(f"   Longitud total: {len(full_private_key)} caracteres")
        print(f"   Saltos de línea: {full_private_key.count(chr(10))} caracteres \\n")
        
        return full_private_key
    
    return None

def test_private_key_formats():
    """Probar diferentes formatos de clave privada"""
    
    print("🧪 DIAGNÓSTICO DE GOOGLE_PRIVATE_KEY")
    print("=" * 60)
    
    # 1. Leer desde .env local
    env_file = ".env"
    if Path(env_file).exists():
        print("📁 Leyendo desde .env local...")
        manual_key = load_env_file(env_file)
    else:
        print("⚠️ No se encontró .env local")
        manual_key = None
    
    # 2. Leer desde variables de entorno
    env_key = os.getenv('GOOGLE_PRIVATE_KEY')
    
    print(f"\n🔍 Comparación de fuentes:")
    if manual_key:
        print(f"   📁 Desde .env: {len(manual_key)} caracteres")
        print(f"   📁 Empieza: {manual_key[:30]}...")
        print(f"   📁 Termina: ...{manual_key[-30:]}")
    
    if env_key:
        print(f"   🌍 Desde ENV: {len(env_key)} caracteres")
        print(f"   🌍 Empieza: {env_key[:30]}...")
        print(f"   🌍 Termina: ...{env_key[-30:]}")
    else:
        print("   🌍 Variable de entorno no encontrada")
    
    # 3. Probar crear credenciales con diferentes formatos
    test_keys = []
    
    if env_key:
        test_keys.append(("Variable entorno original", env_key))
        
        # Procesar \\n literales
        if '\\n' in env_key:
            processed_key = env_key.replace('\\n', '\n')
            test_keys.append(("Variable entorno con \\n procesados", processed_key))
    
    if manual_key:
        test_keys.append(("Lectura manual de .env", manual_key))
    
    # Probar cada formato
    for name, key in test_keys:
        print(f"\n🧪 Probando: {name}")
        test_credentials_format(key, name)

def test_credentials_format(private_key, test_name):
    """Probar crear credenciales con una clave privada específica"""
    
    try:
        # Datos de prueba
        credentials_data = {
            "type": "service_account",
            "project_id": "edp-control-system",
            "private_key_id": "test-key-id",
            "private_key": private_key,
            "client_email": "edp-api-access@edp-control-system.iam.gserviceaccount.com",
            "client_id": "test-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test.com"
        }
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(credentials_data, f, indent=2)
            temp_path = f.name
        
        print(f"   📄 Archivo temporal: {temp_path}")
        
        # Probar crear credenciales
        from google.oauth2.service_account import Credentials
        
        try:
            creds = Credentials.from_service_account_file(temp_path, scopes=['https://www.googleapis.com/auth/spreadsheets'])
            print(f"   ✅ {test_name}: Credenciales creadas exitosamente")
            
            # Probar crear servicio
            from googleapiclient.discovery import build
            service = build('sheets', 'v4', credentials=creds)
            print(f"   ✅ {test_name}: Servicio Google Sheets creado exitosamente")
            
        except Exception as cred_error:
            print(f"   ❌ {test_name}: Error creando credenciales: {cred_error}")
        
        # Limpiar archivo temporal
        os.unlink(temp_path)
        
    except Exception as e:
        print(f"   ❌ {test_name}: Error general: {e}")

if __name__ == "__main__":
    # Cargar variables de entorno desde .env si está disponible
    if Path(".env").exists():
        print("📋 Cargando variables desde .env...")
        with open(".env", 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    test_private_key_formats()
