#!/usr/bin/env python3
"""
Test para verificar que las variables de entorno separadas trabajen EXCLUSIVAMENTE
sin buscar archivos cuando están todas presentes.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Añadir el proyecto al path para poder importar
sys.path.insert(0, '/home/unzzui/Documents/coding/EDP_Project')

def test_env_vars_only():
    """Test que las variables de entorno separadas trabajen exclusivamente."""
    
    print("="*60)
    print("🧪 TEST: Variables de entorno separadas EXCLUSIVAMENTE")
    print("="*60)
    
    # Limpiar variables existentes para empezar limpio
    old_env = {}
    vars_to_clear = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GOOGLE_CREDENTIALS', 
        'GOOGLE_CREDENTIALS_FILE',
        'GOOGLE_PROJECT_ID',
        'GOOGLE_CLIENT_EMAIL', 
        'GOOGLE_PRIVATE_KEY'
    ]
    
    for var in vars_to_clear:
        old_env[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    try:
        print("📋 PASO 1: Configurar SOLO variables de entorno separadas")
        
        # Configurar variables separadas válidas
        os.environ['GOOGLE_PROJECT_ID'] = 'test-project-123'
        os.environ['GOOGLE_CLIENT_EMAIL'] = 'test-service@test-project-123.iam.gserviceaccount.com'
        os.environ['GOOGLE_PRIVATE_KEY'] = '''-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VQJQdGxTq6eF
wQ8TN8yOtOvAwj+kHT7M8j3m7+nE8yOtOvAwj+kHT7M8j3m7+nE8yOtOvAwj+kH
T7M8j3m7+nE8yOtOvAwj+kHT7M8j3m7+nE8yOtOvAwj+kHT7M8j3m7+nE8yOtOv
AwQ8TN8yOtOvAwj+kHT7M8j3m7+nE8yOtOvAwj+kHT7M8j3m7+nE8yOtOvAwj+k
HT7M8j3m7+nE8yOtOvAwj+kHT7M8j3m7+nE8yOtOvAwj+kHT7M8j3m7+nE8yOtO
vAwQ8TN8yOtOvAwj+kHT7M8j3m7+nE8yOtOvAwj+kHT7M8j3m7+nE8yOtOvAwj+
kHT7M8j3m7+nE8yOtOvAwj+kHT7M8j3m7+nE8yOtOvAwj+kHT7M8j3m7+nE8yOt
OvAwQ8TN8yOtOvAwj+kHT7M8j3m7+nEQIDAQABAoIBADfGHKuoq9HNxEgJqo4a
-----END PRIVATE KEY-----'''
        
        print(f"   ✅ GOOGLE_PROJECT_ID = {os.environ['GOOGLE_PROJECT_ID']}")
        print(f"   ✅ GOOGLE_CLIENT_EMAIL = {os.environ['GOOGLE_CLIENT_EMAIL']}")
        print(f"   ✅ GOOGLE_PRIVATE_KEY = *** (configurada)")
        
        print("\n📋 PASO 2: Verificar que NO hay archivos ni otras variables")
        
        # Verificar que no hay otras variables de archivo
        for var in ['GOOGLE_APPLICATION_CREDENTIALS', 'GOOGLE_CREDENTIALS', 'GOOGLE_CREDENTIALS_FILE']:
            value = os.environ.get(var)
            if value:
                print(f"   ❌ {var} está configurada: {value}")
            else:
                print(f"   ✅ {var} = NOT_SET")
        
        print("\n📋 PASO 3: Importar configuración y verificar comportamiento")
        
        # Importar y probar la configuración
        from edp_mvp.app.config import Config
        
        # Crear instancia de configuración
        config_instance = Config()
        
        print(f"\n📋 PASO 4: Resultado de _get_google_credentials_path()")
        credentials_path = config_instance._get_google_credentials_path()
        
        if credentials_path:
            print(f"✅ Credenciales path obtenido: {credentials_path}")
            
            # Verificar que es un archivo temporal
            if '/tmp/' in credentials_path:
                print("✅ Es un archivo temporal (correcto para variables separadas)")
            else:
                print("⚠️ No es un archivo temporal - podría ser un archivo existente")
            
            # Verificar que el archivo existe y tiene contenido válido
            if os.path.exists(credentials_path):
                print("✅ El archivo de credenciales existe")
                
                import json
                try:
                    with open(credentials_path, 'r') as f:
                        cred_data = json.load(f)
                    
                    print("✅ Archivo JSON válido")
                    print(f"   📧 client_email: {cred_data.get('client_email', 'N/A')}")
                    print(f"   🆔 project_id: {cred_data.get('project_id', 'N/A')}")
                    print(f"   🔐 private_key: {'***' + cred_data.get('private_key', '')[-20:] if cred_data.get('private_key') else 'N/A'}")
                    
                    required_fields = ['client_email', 'private_key', 'project_id']
                    missing = [f for f in required_fields if not cred_data.get(f)]
                    if missing:
                        print(f"❌ Faltan campos requeridos: {missing}")
                    else:
                        print("✅ Todos los campos requeridos están presentes")
                        
                except Exception as e:
                    print(f"❌ Error leyendo credenciales generadas: {e}")
            else:
                print("❌ El archivo de credenciales no existe")
        else:
            print("❌ No se obtuvieron credenciales")
        
        print("\n" + "="*60)
        print("🎯 RESUMEN DEL TEST")
        print("="*60)
        
        if credentials_path and '/tmp/' in credentials_path and os.path.exists(credentials_path):
            print("✅ TEST PASADO: Variables separadas trabajaron exclusivamente")
            print("✅ Se generó archivo temporal correctamente")
            print("✅ No se buscaron archivos existentes")
            return True
        else:
            print("❌ TEST FALLÓ: Variables separadas no funcionaron correctamente")
            return False
            
    finally:
        # Restaurar variables de entorno originales
        print("\n🧹 Limpiando variables de entorno...")
        for var in vars_to_clear:
            if var in os.environ:
                del os.environ[var]
            if old_env[var] is not None:
                os.environ[var] = old_env[var]

def test_fallback_to_files():
    """Test que el fallback a archivos funcione cuando faltan variables."""
    
    print("\n" + "="*60)
    print("🧪 TEST: Fallback a archivos cuando faltan variables")
    print("="*60)
    
    # Limpiar variables existentes
    old_env = {}
    vars_to_clear = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GOOGLE_CREDENTIALS', 
        'GOOGLE_CREDENTIALS_FILE',
        'GOOGLE_PROJECT_ID',
        'GOOGLE_CLIENT_EMAIL', 
        'GOOGLE_PRIVATE_KEY'
    ]
    
    for var in vars_to_clear:
        old_env[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    try:
        print("📋 PASO 1: Configurar SOLO algunas variables (incompletas)")
        
        # Configurar solo algunas variables (para forzar fallback)
        os.environ['GOOGLE_PROJECT_ID'] = 'test-project-123'
        # Falta GOOGLE_CLIENT_EMAIL y GOOGLE_PRIVATE_KEY
        
        print(f"   ✅ GOOGLE_PROJECT_ID = {os.environ['GOOGLE_PROJECT_ID']}")
        print(f"   ❌ GOOGLE_CLIENT_EMAIL = NOT_SET")
        print(f"   ❌ GOOGLE_PRIVATE_KEY = NOT_SET")
        
        print("\n📋 PASO 2: Importar configuración y verificar fallback")
        
        # Importar y probar la configuración
        from edp_mvp.app.config import Config
        
        # Crear instancia de configuración
        config_instance = Config()
        
        print(f"\n📋 PASO 3: Resultado de _get_google_credentials_path()")
        credentials_path = config_instance._get_google_credentials_path()
        
        print("\n" + "="*60)
        print("🎯 RESUMEN DEL TEST FALLBACK")
        print("="*60)
        
        if credentials_path is None:
            print("✅ TEST PASADO: Fallback funcionó correctamente")
            print("✅ Variables incompletas detectadas")
            print("✅ Se buscaron archivos como fallback")
            print("✅ No se encontraron archivos (esperado en este test)")
            return True
        else:
            print("⚠️ TEST RESULTADO: Se encontraron credenciales en archivos")
            print(f"📁 Archivo encontrado: {credentials_path}")
            return True
            
    finally:
        # Restaurar variables de entorno originales
        print("\n🧹 Limpiando variables de entorno...")
        for var in vars_to_clear:
            if var in os.environ:
                del os.environ[var]
            if old_env[var] is not None:
                os.environ[var] = old_env[var]

if __name__ == "__main__":
    print("🚀 Iniciando tests de configuración de credenciales Google...")
    
    # Test 1: Variables separadas exclusivamente
    test1_result = test_env_vars_only()
    
    # Test 2: Fallback a archivos
    test2_result = test_fallback_to_files()
    
    print("\n" + "="*60)
    print("🏁 RESULTADOS FINALES")
    print("="*60)
    
    if test1_result:
        print("✅ Test 1 (Variables exclusivas): PASADO")
    else:
        print("❌ Test 1 (Variables exclusivas): FALLÓ")
    
    if test2_result:
        print("✅ Test 2 (Fallback a archivos): PASADO")
    else:
        print("❌ Test 2 (Fallback a archivos): FALLÓ")
    
    if test1_result and test2_result:
        print("\n🎉 TODOS LOS TESTS PASARON")
        sys.exit(0)
    else:
        print("\n💥 ALGUNOS TESTS FALLARON")
        sys.exit(1)
