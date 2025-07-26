#!/usr/bin/env python3
"""
Script rápido para reset de base de datos sin confirmaciones.
ÚSALO CON PRECAUCIÓN - ELIMINA TODOS LOS DATOS EXCEPTO USUARIOS.
"""

import os
import sys
import sqlite3
import requests
from dotenv import load_dotenv

def quick_reset():
    """Reset rápido sin confirmaciones."""
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Configuración
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    sqlite_path = os.getenv('SQLITE_DB_PATH', 'edp_mvp/instance/edp_database.db')
    data_backend = os.getenv('DATA_BACKEND', 'supabase')
    
    tables_to_reset = [
        'edp', 'projects', 'cost_header', 'cost_lines', 
        'logs', 'caja', 'edp_log', 'issues', 
        'edp_status_history', 'client_profiles'
    ]
    
    print("🗄️ Reset rápido de base de datos...")
    
    # Reset SQLite
    if os.path.exists(sqlite_path):
        print(f"🗄️ Reseteando SQLite: {sqlite_path}")
        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            
            for table in tables_to_reset:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                    print(f"   ✅ {table} reseteada")
                except sqlite3.OperationalError:
                    print(f"   📋 {table} no existe")
            
            conn.commit()
            conn.close()
            print("✅ SQLite reseteado")
        except Exception as e:
            print(f"❌ Error SQLite: {e}")
    
    # Reset Supabase
    if supabase_url and supabase_key:
        print("🗄️ Reseteando Supabase...")
        try:
            headers = {
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json"
            }
            
            base_url = f"{supabase_url}/rest/v1"
            
            for table in tables_to_reset:
                try:
                    # Eliminar todos los registros
                    response = requests.delete(
                        f"{base_url}/{table}",
                        headers=headers,
                        params={"neq": "id", "value": "0"}
                    )
                    
                    if response.status_code in [200, 204]:
                        print(f"   ✅ {table} reseteada")
                    else:
                        print(f"   📋 {table} no existe o error")
                        
                except Exception as e:
                    print(f"   ❌ Error en {table}: {e}")
            
            print("✅ Supabase reseteado")
        except Exception as e:
            print(f"❌ Error Supabase: {e}")
    
    # Limpiar cache Redis
    try:
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            import redis
            r = redis.from_url(redis_url)
            cache_keys = r.keys("supabase:*")
            if cache_keys:
                r.delete(*cache_keys)
                print(f"🗑️ Cache limpiado: {len(cache_keys)} claves")
    except:
        pass
    
    print("✅ Reset completado")

if __name__ == "__main__":
    quick_reset() 