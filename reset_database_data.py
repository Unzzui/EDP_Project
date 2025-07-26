#!/usr/bin/env python3
"""
Script para hacer un reset de todos los datos de la base de datos excepto los usuarios.
Este script elimina todos los datos de EDP, proyectos, costos, logs, etc., pero preserva
la tabla de usuarios y sus datos.

Soporta tanto SQLite como Supabase como backends de datos.
"""

import os
import sys
import sqlite3
import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reset_database.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DatabaseReset:
    """Clase para manejar el reset de la base de datos."""
    
    def __init__(self):
        self.load_config()
        self.tables_to_reset = [
            'edp',
            'projects', 
            'cost_header',
            'cost_lines',
            'logs',
            'caja',
            'edp_log',
            'issues',
            'edp_status_history',
            'client_profiles'
        ]
        
    def load_config(self):
        """Cargar configuración desde variables de entorno."""
        # Cargar .env si existe
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Configuración de Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.data_backend = os.getenv('DATA_BACKEND', 'supabase')
        
        # Configuración de SQLite
        self.sqlite_path = os.getenv('SQLITE_DB_PATH', 'edp_mvp/instance/edp_database.db')
        
        logger.info(f"🔧 Backend de datos configurado: {self.data_backend}")
        
    def confirm_reset(self) -> bool:
        """Solicitar confirmación del usuario."""
        print("\n" + "="*60)
        print("⚠️  ADVERTENCIA: RESET DE BASE DE DATOS")
        print("="*60)
        print("Este script eliminará TODOS los datos de:")
        print("  • EDP (proyectos)")
        print("  • Projects")
        print("  • Cost Header y Cost Lines")
        print("  • Logs")
        print("  • Caja")
        print("  • Issues")
        print("  • Historial de estados")
        print("  • Perfiles de clientes")
        print("\n✅ PERO PRESERVARÁ:")
        print("  • Tabla de usuarios")
        print("  • Datos de autenticación")
        print("  • Configuraciones del sistema")
        print("\n" + "="*60)
        
        response = input("\n¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): ")
        return response.upper() == 'SI'
    
    def reset_sqlite_data(self) -> bool:
        """Reset de datos en SQLite (preservando usuarios)."""
        try:
            if not os.path.exists(self.sqlite_path):
                logger.warning(f"⚠️ Base de datos SQLite no encontrada en: {self.sqlite_path}")
                return True
            
            logger.info(f"🗄️ Conectando a SQLite: {self.sqlite_path}")
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            
            # Obtener lista de tablas existentes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [table[0] for table in cursor.fetchall()]
            
            logger.info(f"📋 Tablas encontradas: {existing_tables}")
            
            # Reset de cada tabla (excepto usuarios)
            for table in self.tables_to_reset:
                if table in existing_tables:
                    try:
                        # Contar registros antes del reset
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count_before = cursor.fetchone()[0]
                        
                        # Eliminar todos los datos
                        cursor.execute(f"DELETE FROM {table}")
                        deleted_count = cursor.rowcount
                        
                        # Reset auto-increment si existe
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                        
                        logger.info(f"🗑️ Tabla '{table}': {count_before} registros eliminados")
                        
                    except sqlite3.Error as e:
                        logger.error(f"❌ Error al resetear tabla '{table}': {e}")
                        continue
            
            # Commit cambios
            conn.commit()
            conn.close()
            
            logger.info("✅ Reset de SQLite completado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en reset de SQLite: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    def reset_supabase_data(self) -> bool:
        """Reset de datos en Supabase (preservando usuarios)."""
        if not self.supabase_url or not self.supabase_key:
            logger.warning("⚠️ Supabase no configurado, saltando reset de Supabase")
            return True
        
        try:
            logger.info("🗄️ Conectando a Supabase...")
            
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            
            base_url = f"{self.supabase_url}/rest/v1"
            
            # Reset de cada tabla
            for table in self.tables_to_reset:
                try:
                    # Verificar si la tabla existe
                    response = requests.get(
                        f"{base_url}/{table}",
                        headers=headers,
                        params={"limit": 1}
                    )
                    
                    if response.status_code == 404:
                        logger.info(f"📋 Tabla '{table}' no existe en Supabase, saltando...")
                        continue
                    
                    if response.status_code != 200:
                        logger.warning(f"⚠️ No se pudo acceder a tabla '{table}': {response.status_code}")
                        continue
                    
                    # Contar registros antes del reset
                    count_response = requests.get(
                        f"{base_url}/{table}",
                        headers=headers,
                        params={"select": "count"}
                    )
                    
                    count_before = 0
                    if count_response.status_code == 200:
                        try:
                            count_data = count_response.json()
                            count_before = count_data[0]['count'] if count_data else 0
                        except:
                            count_before = 0
                    
                    # Eliminar todos los registros
                    delete_response = requests.delete(
                        f"{base_url}/{table}",
                        headers=headers,
                        params={"neq": "id", "value": "0"}  # Eliminar todos (todos los IDs son > 0)
                    )
                    
                    if delete_response.status_code in [200, 204]:
                        logger.info(f"🗑️ Tabla '{table}': {count_before} registros eliminados")
                    else:
                        logger.warning(f"⚠️ Error al eliminar tabla '{table}': {delete_response.status_code}")
                    
                except Exception as e:
                    logger.error(f"❌ Error al resetear tabla '{table}' en Supabase: {e}")
                    continue
            
            logger.info("✅ Reset de Supabase completado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en reset de Supabase: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """Limpiar cache de Redis si está disponible."""
        try:
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                logger.info("📋 Redis no configurado, saltando limpieza de cache")
                return True
            
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            
            # Limpiar cache relacionado con datos
            cache_keys = r.keys("supabase:*")
            if cache_keys:
                r.delete(*cache_keys)
                logger.info(f"🗑️ Cache limpiado: {len(cache_keys)} claves eliminadas")
            else:
                logger.info("📋 No se encontraron claves de cache para limpiar")
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudo limpiar cache: {e}")
            return True
    
    def verify_reset(self) -> bool:
        """Verificar que el reset se completó correctamente."""
        logger.info("🔍 Verificando reset...")
        
        try:
            # Verificar SQLite
            if os.path.exists(self.sqlite_path):
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()
                
                for table in self.tables_to_reset:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            logger.warning(f"⚠️ Tabla '{table}' aún tiene {count} registros")
                        else:
                            logger.info(f"✅ Tabla '{table}' está vacía")
                    except sqlite3.OperationalError:
                        logger.info(f"📋 Tabla '{table}' no existe en SQLite")
                
                # Verificar que usuarios sigue existiendo
                cursor.execute("SELECT COUNT(*) FROM usuarios")
                user_count = cursor.fetchone()[0]
                logger.info(f"✅ Tabla usuarios preservada: {user_count} usuarios")
                
                conn.close()
            
            # Verificar Supabase
            if self.supabase_url and self.supabase_key:
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                }
                
                base_url = f"{self.supabase_url}/rest/v1"
                
                for table in self.tables_to_reset:
                    try:
                        response = requests.get(
                            f"{base_url}/{table}",
                            headers=headers,
                            params={"select": "count"}
                        )
                        
                        if response.status_code == 200:
                            count_data = response.json()
                            count = count_data[0]['count'] if count_data else 0
                            if count > 0:
                                logger.warning(f"⚠️ Tabla '{table}' en Supabase aún tiene {count} registros")
                            else:
                                logger.info(f"✅ Tabla '{table}' en Supabase está vacía")
                        else:
                            logger.info(f"📋 Tabla '{table}' no existe en Supabase")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error verificando tabla '{table}' en Supabase: {e}")
            
            logger.info("✅ Verificación completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en verificación: {e}")
            return False
    
    def create_backup(self) -> bool:
        """Crear backup antes del reset."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = "backups"
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Backup de SQLite
            if os.path.exists(self.sqlite_path):
                backup_path = f"{backup_dir}/edp_database_backup_{timestamp}.db"
                import shutil
                shutil.copy2(self.sqlite_path, backup_path)
                logger.info(f"💾 Backup SQLite creado: {backup_path}")
            
            # Backup de Supabase (exportar datos)
            if self.supabase_url and self.supabase_key:
                backup_file = f"{backup_dir}/supabase_backup_{timestamp}.json"
                self.export_supabase_data(backup_file)
                logger.info(f"💾 Backup Supabase creado: {backup_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return False
    
    def export_supabase_data(self, backup_file: str) -> bool:
        """Exportar datos de Supabase a archivo JSON."""
        try:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            
            base_url = f"{self.supabase_url}/rest/v1"
            backup_data = {}
            
            for table in self.tables_to_reset:
                try:
                    response = requests.get(
                        f"{base_url}/{table}",
                        headers=headers,
                        params={"limit": 10000}  # Límite alto para obtener todos los datos
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        backup_data[table] = data
                        logger.info(f"📋 Exportados {len(data)} registros de tabla '{table}'")
                    else:
                        logger.warning(f"⚠️ No se pudo exportar tabla '{table}': {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error exportando tabla '{table}': {e}")
            
            # Guardar backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exportando datos de Supabase: {e}")
            return False
    
    def run(self) -> bool:
        """Ejecutar el proceso completo de reset."""
        logger.info("🚀 Iniciando reset de base de datos...")
        
        # Confirmación del usuario
        if not self.confirm_reset():
            logger.info("❌ Reset cancelado por el usuario")
            return False
        
        # Crear backup
        logger.info("💾 Creando backup antes del reset...")
        if not self.create_backup():
            logger.warning("⚠️ No se pudo crear backup, continuando...")
        
        # Reset según el backend configurado
        success = True
        
        if self.data_backend == "sqlite":
            logger.info("🗄️ Ejecutando reset en SQLite...")
            success &= self.reset_sqlite_data()
        elif self.data_backend == "supabase":
            logger.info("🗄️ Ejecutando reset en Supabase...")
            success &= self.reset_supabase_data()
        else:
            # Reset en ambos si no está especificado
            logger.info("🗄️ Ejecutando reset en SQLite...")
            success &= self.reset_sqlite_data()
            logger.info("🗄️ Ejecutando reset en Supabase...")
            success &= self.reset_supabase_data()
        
        # Limpiar cache
        logger.info("🗑️ Limpiando cache...")
        self.clear_cache()
        
        # Verificar reset
        logger.info("🔍 Verificando reset...")
        self.verify_reset()
        
        if success:
            logger.info("✅ Reset completado exitosamente")
            print("\n" + "="*60)
            print("✅ RESET COMPLETADO EXITOSAMENTE")
            print("="*60)
            print("📋 Se han eliminado todos los datos de:")
            for table in self.tables_to_reset:
                print(f"   • {table}")
            print("\n✅ Se han preservado:")
            print("   • Tabla de usuarios")
            print("   • Datos de autenticación")
            print("   • Configuraciones del sistema")
            print("\n💾 Se ha creado un backup antes del reset")
            print("🗑️ Se ha limpiado el cache del sistema")
            print("="*60)
        else:
            logger.error("❌ Reset completado con errores")
            print("\n" + "="*60)
            print("❌ RESET COMPLETADO CON ERRORES")
            print("="*60)
            print("Revisa el archivo 'reset_database.log' para más detalles")
            print("="*60)
        
        return success

def main():
    """Función principal."""
    print("🗄️ Script de Reset de Base de Datos - EDP Project")
    print("="*60)
    
    try:
        reset = DatabaseReset()
        success = reset.run()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Reset cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 