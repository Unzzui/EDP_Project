"""
Servicio de Supabase que reemplaza completamente Google Sheets
Incluye todas las operaciones CRUD, cache y manejo de datos
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import logging

# Redis para cache
try:
    import redis
    redis_url = os.getenv("REDIS_URL")
    redis_client = redis.from_url(redis_url) if redis_url else None
    if redis_client:
        redis_client.ping()
        print("✅ Redis disponible para cache de Supabase")
except (ImportError, Exception) as e:
    redis_client = None
    print(f"⚠️ Redis no disponible para cache: {e}")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseService:
    """Servicio principal de Supabase que reemplaza Google Sheets"""
    
    def __init__(self):
        self.load_config()
        self.setup_client()
        self.cache_timeout = 120  # 2 minutos de cache por defecto
        self._cache = {}  # Cache en memoria como fallback
        
    def load_config(self):
        """Cargar configuración de Supabase"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("❌ Variables SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY no definidas")
        
        logger.info("✅ Configuración de Supabase cargada")
    
    def setup_client(self):
        """Configurar cliente HTTP para Supabase"""
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        self.base_url = f"{self.supabase_url}/rest/v1"
        logger.info("✅ Cliente de Supabase configurado")
    
    def _get_cache_key(self, table: str, filters: Dict = None, operation: str = "select") -> str:
        """Generar clave de cache única"""
        cache_key = f"supabase:{table}:{operation}"
        if filters:
            filter_str = json.dumps(filters, sort_keys=True)
            cache_key += f":{hash(filter_str)}"
        return cache_key
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Obtener datos desde cache (Redis primero, memoria como fallback)"""
        # Intentar Redis primero
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Error leyendo cache Redis: {e}")
        
        # Fallback a cache en memoria
        if cache_key in self._cache:
            timestamp, data = self._cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.cache_timeout:
                return data
            else:
                del self._cache[cache_key]
        
        return None
    
    def _set_cache(self, cache_key: str, data: Any, ttl: int = None) -> None:
        """Guardar datos en cache"""
        ttl = ttl or self.cache_timeout
        
        # Guardar en Redis
        if redis_client:
            try:
                redis_client.setex(
                    cache_key, 
                    ttl, 
                    json.dumps(data, default=str)
                )
            except Exception as e:
                logger.warning(f"Error guardando cache Redis: {e}")
        
        # Guardar en memoria como fallback
        self._cache[cache_key] = (datetime.now().timestamp(), data)
    
    def _clear_cache(self, pattern: str = None) -> None:
        """Limpiar cache"""
        # Limpiar Redis
        if redis_client:
            try:
                if pattern:
                    keys = redis_client.keys(f"supabase:*{pattern}*")
                else:
                    keys = redis_client.keys("supabase:*")
                
                if keys:
                    redis_client.delete(*keys)
                    logger.info(f"🧹 Cache Redis limpiado: {len(keys)} keys")
            except Exception as e:
                logger.warning(f"Error limpiando cache Redis: {e}")
        
        # Limpiar memoria
        if pattern:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
        else:
            self._cache.clear()
        
        logger.info("🧹 Cache en memoria limpiado")

    def _convert_updates_for_json(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convierte updates para que sean compatibles con JSON y con la base de datos.
        IMPORTANTE: Los montos se convierten específicamente a float para coincidir 
        con el tipo 'numeric' de PostgreSQL.
        """
        # Usar la función centralizada de conversión
        from ..utils.type_conversion import convert_edp_updates_for_db
        return convert_edp_updates_for_db(updates)
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> requests.Response:
        """Realizar petición HTTP a Supabase"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición Supabase: {e}")
            raise
    
    # === OPERACIONES GENERALES ===
    
    def select(self, table: str, filters: Dict = None, columns: str = "*", 
               order_by: str = None, limit: int = None, use_cache: bool = True) -> List[Dict]:
        """Seleccionar registros de una tabla"""
        cache_key = self._get_cache_key(table, filters, "select") if use_cache else None
        
        # Verificar cache
        if use_cache and cache_key:
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                logger.info(f"🚀 Cache hit para {table}")
                return cached_data
        
        # Construir parámetros de consulta
        params = {"select": columns}
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    params[f"{key}"] = f"in.({','.join(map(str, value))})"
                elif isinstance(value, dict):
                    # Operadores especiales como gt, lt, eq, etc.
                    for op, val in value.items():
                        params[f"{key}"] = f"{op}.{val}"
                else:
                    params[f"{key}"] = f"eq.{value}"
        
        if order_by:
            params["order"] = order_by
        
        if limit:
            params["limit"] = limit
        
        # Hacer petición
        response = self._make_request("GET", table, params=params)
        data = response.json()
        
        # Guardar en cache
        if use_cache and cache_key:
            self._set_cache(cache_key, data)
        
        logger.info(f"📥 Obtenidos {len(data)} registros de {table}")
        return data
    
    def insert(self, table: str, data: Union[Dict, List[Dict]], upsert: bool = False) -> List[Dict]:
        """Insertar uno o más registros"""
        # Preparar headers
        headers = self.headers.copy()
        if upsert:
            headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        
        # Convertir tipos para serialización JSON
        if isinstance(data, list):
            data_converted = [self._convert_updates_for_json(item) for item in data]
        else:
            data_converted = self._convert_updates_for_json(data)
        
        # Hacer petición
        response = requests.post(
            f"{self.base_url}/{table}",
            headers=headers,
            json=data_converted,
            timeout=30
        )
        response.raise_for_status()
        
        # Limpiar cache relacionado
        self._clear_cache(table)
        
        result = response.json()
        count = len(result) if isinstance(result, list) else 1
        logger.info(f"✅ Insertados {count} registros en {table}")
        
        return result
    
    def update(self, table: str, filters: Dict, updates: Dict) -> List[Dict]:
        """Actualizar registros"""
        # Construir parámetros de filtro
        params = {}
        for key, value in filters.items():
            params[f"{key}"] = f"eq.{value}"
        
        # Convertir tipos para serialización JSON
        updates_converted = self._convert_updates_for_json(updates)
        
        print(f"🔍 Supabase update request:")
        print(f"   - URL: {self.base_url}/{table}")
        print(f"   - Filters: {filters}")
        print(f"   - Params: {params}")
        print(f"   - Updates: {updates_converted}")
        
        # Hacer petición
        response = requests.patch(
            f"{self.base_url}/{table}",
            headers=self.headers,
            json=updates_converted,
            params=params,
            timeout=30
        )
        
        if not response.ok:
            print(f"❌ Error response status: {response.status_code}")
            print(f"❌ Error response body: {response.text}")
        
        response.raise_for_status()
        
        # Limpiar cache relacionado
        self._clear_cache(table)
        
        result = response.json()
        count = len(result) if isinstance(result, list) else 1
        logger.info(f"🔄 Actualizados {count} registros en {table}")
        
        return result
    
    def delete(self, table: str, filters: Dict) -> bool:
        """Eliminar registros"""
        try:
            # Construir parámetros de filtro
            params = {}
            for key, value in filters.items():
                params[f"{key}"] = f"eq.{value}"
            
            # Hacer petición
            response = requests.delete(
                f"{self.base_url}/{table}",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Limpiar cache relacionado
            self._clear_cache(table)
            
            # Supabase puede devolver 200 o 204 para eliminaciones exitosas
            success = response.status_code in [200, 204]
            
            logger.info(f"🗑️ Registros eliminados de {table}")
            return success
            
        except Exception as e:
            print(f"💥 Error in delete method: {e}")
            logger.error(f"Error deleting from {table}: {e}")
            raise
    
    # === OPERACIONES ESPECÍFICAS EDP ===
    
    def get_edp_data(self, filters: Dict = None, columns: str = "*") -> List[Dict]:
        """Obtener datos EDP"""
        return self.select("edp", filters, columns, order_by="id")
    
    def get_edp_by_id(self, edp_id: int) -> Optional[Dict]:
        """Obtener EDP por ID"""
        results = self.select("edp", {"id": edp_id})
        return results[0] if results else None
    
    def create_edp(self, edp_data: Dict) -> Dict:
        """Crear nuevo EDP"""
        # Filtrar campos válidos antes de crear
        filtered_data = self._filter_valid_edp_fields(edp_data)
        
        # Agregar timestamp
        filtered_data["created_at"] = datetime.now().isoformat()
        filtered_data["updated_at"] = datetime.now().isoformat()
        
        result = self.insert("edp", filtered_data)
        return result[0] if isinstance(result, list) else result
    
    def _filter_valid_edp_fields(self, updates: Dict) -> Dict:
        """Filtrar campos válidos para la tabla EDP basándose en el esquema real de la BD"""
        # Campos válidos según el esquema de Supabase proporcionado por el usuario
        valid_fields = {
            'id', 'n_edp', 'proyecto', 'cliente', 'gestor', 'jefe_proyecto', 'mes',
            'fecha_emision', 'fecha_envio_cliente', 'monto_propuesto', 'monto_aprobado',
            'fecha_estimada_pago', 'conformidad_enviada', 'n_conformidad', 'fecha_conformidad',
            'estado', 'observaciones', 'registrado_por', 'estado_detallado', 'fecha_registro',
            'motivo_no_aprobado', 'tipo_falla', 'created_at', 'updated_at', 'dias_en_cliente',
            'prioridad', 'fecha_ultimo_seguimiento', 'dso_actual', 'esta_vencido', 'categoria_aging'
            # 'last_modified_by' campo no existe en BD
        }
        
        # Filtrar solo campos válidos
        filtered_updates = {}
        invalid_fields = []
        
        for key, value in updates.items():
            if key in valid_fields:
                filtered_updates[key] = value
            else:
                invalid_fields.append(key)
        
        # Log de campos inválidos para debugging
        if invalid_fields:
            logger.warning(f"🔍 Campos ignorados (no existen en BD): {invalid_fields}")
        
        return filtered_updates

    def update_edp(self, edp_id: int, updates: Dict, usuario: str = None) -> Dict:
        """Actualizar EDP"""
        # Filtrar campos válidos antes de actualizar
        filtered_updates = self._filter_valid_edp_fields(updates)
        
        filtered_updates["updated_at"] = datetime.now().isoformat()
        # if usuario:
        #     filtered_updates["last_modified_by"] = usuario  # Campo no existe en BD
        
        result = self.update("edp", {"id": edp_id}, filtered_updates)
        
        # Registrar en log (opcional - no bloquear si falla)
        if result:
            try:
                self.create_log({
                    "edp_id": str(edp_id),
                    "log_type": "update",
                    "message": f"EDP actualizado por {usuario or 'sistema'}",
                    "user": usuario or "sistema",
                    "details": json.dumps(filtered_updates)
                })
            except Exception as log_error:
                logger.warning(f"No se pudo registrar log para EDP {edp_id}: {log_error}")
                # Continuar sin bloquear la actualización
        
        return result[0] if isinstance(result, list) else result
    
    # === OPERACIONES DE PROYECTOS ===
    
    def get_projects_data(self, filters: Dict = None) -> List[Dict]:
        """Obtener datos de proyectos"""
        return self.select("projects", filters, order_by="id")
    
    def create_project(self, project_data: Dict) -> Dict:
        """Crear nuevo proyecto"""
        project_data["created_at"] = datetime.now().isoformat()
        result = self.insert("projects", project_data)
        return result[0] if isinstance(result, list) else result
    
    # === OPERACIONES DE COSTOS ===
    
    def get_cost_header_data(self, filters: Dict = None) -> List[Dict]:
        """Obtener encabezados de costos"""
        return self.select("cost_header", filters, order_by="cost_id")
    
    def get_cost_lines_data(self, filters: Dict = None) -> List[Dict]:
        """Obtener líneas de costos"""
        return self.select("cost_lines", filters, order_by="line_id")
    
    def create_cost_header(self, cost_data: Dict) -> Dict:
        """Crear encabezado de costo"""
        cost_data["created_at"] = datetime.now().isoformat()
        result = self.insert("cost_header", cost_data)
        return result[0] if isinstance(result, list) else result
    
    def create_cost_line(self, line_data: Dict) -> Dict:
        """Crear línea de costo"""
        result = self.insert("cost_lines", line_data)
        return result[0] if isinstance(result, list) else result
    
    # === OPERACIONES DE LOGS ===
    
    def get_log_data(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Obtener datos de logs"""
        return self.select("logs", filters, order_by="timestamp.desc", limit=limit)
    
    def create_log(self, log_data: Dict) -> Dict:
        """Crear entrada de log"""
        log_data["timestamp"] = datetime.now().isoformat()
        if "id" not in log_data:
            # Generar ID único para el log
            log_data["id"] = f"log_{int(datetime.now().timestamp())}"
        
        result = self.insert("logs", log_data)
        return result[0] if isinstance(result, list) else result
    
    def delete_old_logs(self, days_old: int = 90) -> bool:
        """Eliminar logs antiguos"""
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
        
        try:
            self.delete("logs", {"timestamp": {"lt": cutoff_date}})
            logger.info(f"🧹 Logs eliminados antes de {cutoff_date}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando logs antiguos: {e}")
            return False
    
    # === OPERACIONES DE CACHE ===
    
    def clear_all_cache(self) -> None:
        """Limpiar todo el cache"""
        self._clear_cache()
        logger.info("🧹 Todo el cache de Supabase limpiado")
    
    def clear_table_cache(self, table: str) -> None:
        """Limpiar cache de una tabla específica"""
        self._clear_cache(table)
        logger.info(f"🧹 Cache de tabla {table} limpiado")
    
    # === CONVERSIÓN DE DATOS ===
    
    def to_dataframe(self, table: str, filters: Dict = None) -> pd.DataFrame:
        """Convertir datos de tabla a DataFrame de pandas"""
        data = self.select(table, filters)
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Aplicar transformaciones básicas
        for col in df.columns:
            if col.endswith('_at') or col in ['fecha_inicio', 'fecha_fin', 'fecha_factura']:
                # Convertir fechas
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif col in ['monto_contrato', 'importe_bruto', 'importe_neto', 'precio_unitario']:
                # Convertir números
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    # === OPERACIONES BATCH ===
    
    def bulk_insert(self, table: str, data_list: List[Dict], batch_size: int = 100) -> bool:
        """Insertar datos en lotes"""
        total_records = len(data_list)
        success_count = 0
        
        for i in range(0, total_records, batch_size):
            batch = data_list[i:i + batch_size]
            try:
                self.insert(table, batch)
                success_count += len(batch)
                logger.info(f"📦 Lote {i//batch_size + 1}: {len(batch)} registros insertados en {table}")
            except Exception as e:
                logger.error(f"❌ Error en lote {i//batch_size + 1}: {e}")
        
        logger.info(f"✅ Inserción masiva completada: {success_count}/{total_records} registros en {table}")
        return success_count == total_records
    
    # === HEALTH CHECK ===
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar estado de la conexión"""
        try:
            # Probar conexión básica
            response = self._make_request("GET", "edp", params={"limit": 1})
            
            # Verificar cache
            cache_status = "healthy"
            if redis_client:
                try:
                    redis_client.ping()
                    cache_status = "redis_available"
                except:
                    cache_status = "redis_unavailable"
            else:
                cache_status = "redis_not_configured"
            
            return {
                "status": "healthy",
                "database": "connected",
                "cache": cache_status,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# === SERVICIO ASÍNCRONO ===

class SupabaseServiceAsync:
    """Versión asíncrona del servicio Supabase"""
    
    def __init__(self):
        self.service = SupabaseService()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def get_edp_data(self, filters: Dict = None) -> pd.DataFrame:
        """Obtener datos EDP de forma asíncrona"""
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            self.executor, 
            lambda: self.service.get_edp_data(filters)
        )
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    async def get_projects_data(self, filters: Dict = None) -> pd.DataFrame:
        """Obtener datos de proyectos de forma asíncrona"""
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            self.executor, 
            lambda: self.service.get_projects_data(filters)
        )
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    async def get_cost_header_data(self, filters: Dict = None) -> pd.DataFrame:
        """Obtener encabezados de costos de forma asíncrona"""
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            self.executor, 
            lambda: self.service.get_cost_header_data(filters)
        )
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    async def get_cost_lines_data(self, filters: Dict = None) -> pd.DataFrame:
        """Obtener líneas de costos de forma asíncrona"""
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            self.executor, 
            lambda: self.service.get_cost_lines_data(filters)
        )
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    async def get_log_data(self, filters: Dict = None) -> pd.DataFrame:
        """Obtener datos de logs de forma asíncrona"""
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            self.executor, 
            lambda: self.service.get_log_data(filters)
        )
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    async def update_edp(self, edp_id: int, updates: Dict, usuario: str = None) -> Dict:
        """Actualizar EDP de forma asíncrona"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            lambda: self.service.update_edp(edp_id, updates, usuario)
        )
    
    async def create_edp(self, edp_data: Dict) -> Dict:
        """Crear EDP de forma asíncrona"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            lambda: self.service.create_edp(edp_data)
        )
    
    async def clear_cache(self) -> None:
        """Limpiar cache de forma asíncrona"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.service.clear_all_cache
        )


# === INSTANCIA GLOBAL ===
_supabase_service = None
_supabase_async_service = None

def get_supabase_service() -> SupabaseService:
    """Obtener instancia singleton del servicio Supabase"""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service

def get_supabase_async_service() -> SupabaseServiceAsync:
    """Obtener instancia singleton del servicio asíncrono"""
    global _supabase_async_service
    if _supabase_async_service is None:
        _supabase_async_service = SupabaseServiceAsync()
    return _supabase_async_service