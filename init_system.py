#!/usr/bin/env python3
"""
Script de inicialización del sistema EDP
Este script configura la hoja de usuarios en Google Sheets si no existe
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from edp_mvp.app.utils.init_users_db import init_users_db

def main():
    """Initialize the EDP system."""
    print("🚀 Inicializando sistema EDP...")
    print("=" * 50)
    
    try:
        # Initialize users database
        print("\n1. Configurando base de datos de usuarios...")
        success = init_users_db()
        
        if success:
            print("\n✅ Sistema inicializado correctamente!")
            print("\n📋 Información importante:")
            print("   - Se ha creado la base de datos SQLite 'edp_database.db'")
            print("   - Tabla 'usuarios' configurada correctamente")
            print("   - Usuario administrador por defecto creado:")
            print("     👤 Username: admin")
            print("     🔒 Password: admin123")
            print("   - ⚠️  Cambie esta contraseña después del primer login")
            print("\n🔗 Acceda al sistema en: http://localhost:5000/login")
            print("\n📊 Para gestionar usuarios vaya a: http://localhost:5000/admin/usuarios")
        else:
            print("\n❌ Error durante la inicialización")
            print("   Verifique los permisos de escritura en el directorio")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        return 1
    
    print("\n" + "=" * 50)
    print("🎉 ¡Listo para usar!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 