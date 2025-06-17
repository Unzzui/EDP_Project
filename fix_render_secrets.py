#!/usr/bin/env python3
"""
Script para manejar Secret Files de Render y copiarlos a ubicaciones accesibles
Este script debe ejecutarse con permisos de root en el entrypoint
"""
import os
import shutil
import json
import stat
import subprocess
import sys
from pathlib import Path

def fix_render_secret_files():
    """
    Copia los Secret Files de Render a ubicaciones accesibles por el usuario de la app
    """
    print("🔧 PREPARANDO SECRET FILES DE RENDER")
    print("=" * 50)
    
    secrets_dir = Path("/etc/secrets")
    app_secrets_dir = Path("/app/secrets")
    
    # Crear directorio de secrets en la app si no existe
    app_secrets_dir.mkdir(exist_ok=True)
    
    if not secrets_dir.exists():
        print("📁 Directorio /etc/secrets no encontrado - funcionando en desarrollo")
        return True
    
    print(f"📁 Directorio Secret Files encontrado: {secrets_dir}")
    
    # Listar archivos en Secret Files
    try:
        secret_files = list(secrets_dir.iterdir())
        print(f"📄 Archivos en Secret Files: {len(secret_files)}")
        for file in secret_files:
            if file.is_file():
                file_size = file.stat().st_size
                file_perms = oct(file.stat().st_mode)[-3:]
                print(f"   📄 {file.name} ({file_size} bytes, perms: {file_perms})")
    except PermissionError as e:
        print(f"❌ Error listando Secret Files: {e}")
        return False
    
    # Buscar y copiar archivo de credenciales Google
    google_creds_patterns = [
        "edp-control-system-f3cfafc0093a.json",
        "edp-control-system-*.json", 
        "google-credentials.json",
        "*.json"
    ]
    
    copied_files = []
    
    for pattern in google_creds_patterns:
        matching_files = list(secrets_dir.glob(pattern))
        for source_file in matching_files:
            if source_file.is_file():
                try:
                    dest_file = app_secrets_dir / source_file.name
                    
                    # Copiar archivo
                    shutil.copy2(source_file, dest_file)
                    
                    # Cambiar permisos para que sea legible por appuser
                    dest_file.chmod(0o644)
                    
                    # Verificar que se puede leer como JSON
                    try:
                        with open(dest_file, 'r') as f:
                            json.load(f)
                        print(f"✅ Copiado y verificado: {source_file.name} → {dest_file}")
                        copied_files.append(str(dest_file))
                    except json.JSONDecodeError as e:
                        print(f"❌ Archivo {source_file.name} no es JSON válido: {e}")
                        dest_file.unlink()  # Eliminar archivo inválido
                    
                except Exception as e:
                    print(f"❌ Error copiando {source_file}: {e}")
    
    if copied_files:
        print(f"✅ Secret Files copiados exitosamente: {len(copied_files)}")
        
        # Cambiar propietario del directorio a appuser si es posible
        try:
            # Obtener UID y GID de appuser
            import pwd
            try:
                appuser = pwd.getpwnam('appuser')
                shutil.chown(app_secrets_dir, user=appuser.pw_uid, group=appuser.pw_gid)
                
                # Cambiar propietario de todos los archivos copiados
                for file_path in copied_files:
                    shutil.chown(file_path, user=appuser.pw_uid, group=appuser.pw_gid)
                    
                print("✅ Propietario cambiado a appuser")
            except KeyError:
                print("⚠️ Usuario appuser no encontrado, manteniendo permisos actuales")
        except Exception as e:
            print(f"⚠️ No se pudo cambiar propietario: {e}")
        
        return True
    else:
        print("⚠️ No se encontraron Secret Files válidos para copiar")
        return False

def verify_copied_secrets():
    """Verificar que los archivos copiados sean accesibles"""
    print("\n🔍 VERIFICANDO SECRET FILES COPIADOS")
    print("=" * 50)
    
    app_secrets_dir = Path("/app/secrets")
    
    if not app_secrets_dir.exists():
        print("❌ Directorio /app/secrets no existe")
        return False
    
    json_files = list(app_secrets_dir.glob("*.json"))
    
    if not json_files:
        print("❌ No se encontraron archivos JSON en /app/secrets")
        return False
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Verificar campos requeridos para Google Service Account
            required_fields = ['client_email', 'private_key', 'project_id']
            has_required = all(field in data for field in required_fields)
            
            if has_required:
                print(f"✅ {json_file.name}: Credenciales válidas")
                print(f"   📧 Client Email: {data.get('client_email')}")
                print(f"   🆔 Project ID: {data.get('project_id')}")
                return True
            else:
                missing = [f for f in required_fields if f not in data]
                print(f"❌ {json_file.name}: Faltan campos {missing}")
        
        except Exception as e:
            print(f"❌ Error verificando {json_file.name}: {e}")
    
    return False

if __name__ == "__main__":
    print("🔧 CONFIGURADOR DE SECRET FILES PARA RENDER")
    print("=" * 60)
    
    # Solo ejecutar si somos root (en el entrypoint)
    if os.geteuid() != 0:
        print("⚠️ Este script debe ejecutarse como root en el entrypoint")
        print("💡 Se ejecutará automáticamente durante el deploy en Render")
        sys.exit(0)
    
    # Realizar las correcciones
    copy_success = fix_render_secret_files()
    verify_success = verify_copied_secrets()
    
    print("\n" + "=" * 60)
    if copy_success and verify_success:
        print("🎉 SECRET FILES CONFIGURADOS CORRECTAMENTE")
        print("✅ Google Sheets debería funcionar en producción")
        sys.exit(0)
    else:
        print("⚠️ PROBLEMAS CON SECRET FILES")
        print("🎭 La aplicación funcionará en modo demo")
        sys.exit(0)  # No fallar el deploy, solo continuar en modo demo
