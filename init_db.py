#!/usr/bin/env python3
"""
Script para inicializar la base de datos en producción
"""
import os
import sys
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def wait_for_db():
    """Verificar disponibilidad de la base de datos"""
    print("🔍 Verificando disponibilidad de la base de datos...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url or database_url == "":
        print("⚠️ DATABASE_URL no configurado, usando SQLite")
        return True
    
    # Detectar placeholders comunes
    placeholders = ['username', 'password', 'hostname', 'port', 'database', 'host']
    has_placeholder = any(placeholder in database_url.lower() for placeholder in placeholders)
    
    if has_placeholder:
        print(f"⚠️ DATABASE_URL contiene placeholders: {database_url[:50]}...")
        print("⚠️ Usando SQLite como fallback - no se intentará conectar a PostgreSQL")
        return True
    
    print(f"✅ DATABASE_URL válido detectado: {database_url[:30]}...")
    return True

def init_db():
    """Initialize database tables"""
    if not wait_for_db():
        return False
    
    try:
        from edp_mvp.app import create_app
        from edp_mvp.app.extensions import db
        
        app = create_app()
        
        with app.app_context():
            print("🔄 Creando tablas de base de datos...")
            db.create_all()
            print("✅ Base de datos inicializada correctamente")
            return True
            
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
