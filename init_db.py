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
    """Esperar a que la base de datos esté disponible"""
    print("🔍 Verificando disponibilidad de la base de datos...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url or database_url == "":
        print("⚠️ DATABASE_URL no configurado, usando SQLite")
        return True
    
    if 'port' in database_url and not database_url.count(':') >= 2:
        print(f"⚠️ DATABASE_URL mal formateado: {database_url}")
        print("⚠️ Usando SQLite como fallback")
        return True
    
    # Intentar conectar a PostgreSQL
    max_retries = 30
    for i in range(max_retries):
        try:
            import psycopg2
            # Extraer componentes de la URL para testing
            if database_url.startswith('postgres://'):
                test_url = database_url.replace('postgres://', 'postgresql://', 1)
            else:
                test_url = database_url
            
            conn = psycopg2.connect(test_url)
            conn.close()
            print("✅ Base de datos PostgreSQL disponible")
            return True
        except Exception as e:
            print(f"⏳ Esperando base de datos... intento {i+1}/{max_retries}")
            time.sleep(2)
    
    print("⚠️ No se pudo conectar a PostgreSQL, usando SQLite")
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
