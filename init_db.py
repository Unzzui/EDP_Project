#!/usr/bin/env python3
"""
Script para inicializar la base de datos en producción
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edp_mvp.app import create_app
from edp_mvp.app.extensions import db

def init_db():
    """Initialize database tables"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Creando tablas de base de datos...")
        try:
            db.create_all()
            print("✅ Base de datos inicializada correctamente")
        except Exception as e:
            print(f"❌ Error al inicializar base de datos: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
