#!/usr/bin/env python3
"""
Script para agregar la columna email a la tabla usuarios.
Ejecutar este script para migrar la base de datos.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from edp_mvp.app import create_app
from edp_mvp.extensions import db
from edp_mvp.models.user import User

def migrate_add_email_column():
    """Agregar la columna email a la tabla usuarios."""
    try:
        app = create_app()
        
        with app.app_context():
            print("🔄 Iniciando migración para agregar columna email...")
            
            # Verificar si la columna ya existe
            try:
                # Intentar acceder a la columna email
                result = db.session.execute("SELECT email FROM usuarios LIMIT 1")
                print("✅ La columna email ya existe en la tabla usuarios.")
                return True
            except Exception as e:
                if "column" in str(e).lower() and "email" in str(e).lower():
                    print("📝 La columna email no existe. Agregándola...")
                else:
                    print(f"❌ Error verificando columna: {e}")
                    return False
            
            # Agregar la columna email
            try:
                db.session.execute("ALTER TABLE usuarios ADD COLUMN email VARCHAR(255)")
                db.session.execute("CREATE INDEX idx_usuarios_email ON usuarios(email)")
                db.session.commit()
                print("✅ Columna email agregada exitosamente.")
                
                # Verificar que se agregó correctamente
                result = db.session.execute("SELECT email FROM usuarios LIMIT 1")
                print("✅ Verificación exitosa - La columna email está disponible.")
                
                # Mostrar estadísticas
                total_users = User.query.count()
                users_with_email = User.query.filter(User.email.isnot(None)).count()
                print(f"📊 Estadísticas:")
                print(f"   - Total de usuarios: {total_users}")
                print(f"   - Usuarios con email: {users_with_email}")
                print(f"   - Usuarios sin email: {total_users - users_with_email}")
                
                return True
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error agregando columna email: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error en la migración: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando migración de base de datos...")
    success = migrate_add_email_column()
    
    if success:
        print("✅ Migración completada exitosamente!")
        print("\n📋 Próximos pasos:")
        print("1. Ejecutar el script SQL si usas PostgreSQL:")
        print("   psql -d tu_base_de_datos -f add_email_column.sql")
        print("2. Reiniciar la aplicación")
        print("3. Probar la creación de usuarios con email")
    else:
        print("❌ La migración falló. Revisa los errores arriba.")
        sys.exit(1) 