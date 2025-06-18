
#!/usr/bin/env python3
"""
Script para extraer valores individuales de tu archivo JSON de Google
para configurar variables de entorno en Render.
"""

import json
import sys
import os

def extract_credentials(json_file_path):
    """Extrae valores individuales del archivo JSON de credenciales"""
    
    try:
        with open(json_file_path, 'r') as f:
            creds = json.load(f)
        
        print("🔑 VALORES PARA VARIABLES DE ENTORNO EN RENDER")
        print("=" * 60)
        print()
        
        # Extraer valores principales
        project_id = creds.get('project_id', '')
        client_email = creds.get('client_email', '')
        private_key = creds.get('private_key', '')
        
        print("📋 COPIA ESTAS VARIABLES EN RENDER:")
        print("-" * 40)
        print(f"GOOGLE_PROJECT_ID={project_id}")
        print(f"GOOGLE_CLIENT_EMAIL={client_email}")
        print(f"GOOGLE_PRIVATE_KEY={private_key}")
        print()
        
        print("⚠️  IMPORTANTE:")
        print("- Copia cada línea exactamente como aparece")
        print("- El PRIVATE_KEY incluye \\n que son necesarios")
        print("- NO agregues comillas adicionales")
        print()
        
        # Validaciones
        print("✅ VALIDACIONES:")
        if project_id:
            print(f"✅ Project ID encontrado: {project_id}")
        else:
            print("❌ Project ID no encontrado")
            
        if client_email and '@' in client_email:
            print(f"✅ Client Email válido: {client_email}")
        else:
            print("❌ Client Email inválido")
            
        if private_key and 'BEGIN PRIVATE KEY' in private_key:
            print(f"✅ Private Key encontrada ({len(private_key)} caracteres)")
        else:
            print("❌ Private Key no encontrada o inválida")
            
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: Archivo no encontrado: {json_file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Archivo JSON inválido: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Uso: python extract_google_credentials.py <ruta-al-archivo-json>")
        print()
        print("Ejemplo:")
        print("  python extract_google_credentials.py ./edp_mvp/app/keys/edp-control-system-f3cfafc0093a.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"❌ Archivo no existe: {json_file}")
        sys.exit(1)
    
    success = extract_credentials(json_file)
    
    if success:
        print("🎉 ¡Extracción completada exitosamente!")
    else:
        print("💥 Error en la extracción")
        sys.exit(1)

if __name__ == "__main__":
    main()