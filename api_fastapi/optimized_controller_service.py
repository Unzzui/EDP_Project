#!/usr/bin/env python3
"""
Versión optimizada del ControllerService para FastAPI
Aplicando cache multinivel, cálculos bajo demanda y background tasks
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import BackgroundTasks
import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Cache TTL configuration
CACHE_TTL = {
    "dashboard_quick": 300,      # 5 min - KPIs básicos
    "dashboard_detailed": 600,   # 10 min - Análisis completo
    "heavy_analysis": 1800,      # 30 min - Reportes pesados
    "filter_options": 900,       # 15 min - Opciones de filtro
    "raw_data": 180,            # 3 min - Datos base
}

class OptimizedControllerService:
    """Versión optimizada del ControllerService para FastAPI"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.redis_client = None
        self._memory_cache = {}
        self._cache_timestamps = {}
        
        # Importar servicios originales
        from edp_mvp.app.services.controller_service import ControllerService
        self.original_service = ControllerService()
        
    async def init_redis(self):
        """Inicializar Redis si está disponible"""
        try:
            self.redis_client = redis.from_url("redis://localhost:6379")
            await self.redis_client.ping()
            logger.info("✅ Redis conectado para cache optimizado")
        except Exception as e:
            logger.info(f"⚠️ Redis no disponible, usando solo cache en memoria: {e}")
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generar clave de cache única basada en parámetros"""
        # Filtrar valores None y normalizar
        clean_params = {k: v for k, v in kwargs.items() if v is not None}
        key_str = json.dumps(clean_params, sort_keys=True)
        hash_key = hashlib.md5(key_str.encode()).hexdigest()[:12]
        return f"{prefix}:{hash_key}"
    
    async def get_cache(self, key: str, ttl: int = 300) -> Optional[Any]:
        """Obtener del cache (Redis + memoria)"""
        # 1. Redis primero
        if self.redis_client:
            try:
                cached = await self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
        
        # 2. Memoria como fallback
        if key in self._memory_cache:
            timestamp = self._cache_timestamps.get(key, 0)
            if time.time() - timestamp < ttl:
                return self._memory_cache[key]
            else:
                # Limpiar cache expirado
                del self._memory_cache[key]
                del self._cache_timestamps[key]
        
        return None
    
    async def set_cache(self, key: str, data: Any, ttl: int = 300):
        """Guardar en cache (Redis + memoria)"""
        # Redis
        if self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, json.dumps(data, default=str))
            except Exception:
                pass
        
        # Memoria
        self._memory_cache[key] = data
        self._cache_timestamps[key] = time.time()

    async def get_dashboard_quick_kpis(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        🚀 RÁPIDO (< 500ms) - Solo KPIs esenciales
        Para widgets principales, actualizaciones frecuentes
        """
        cache_key = self._get_cache_key("dashboard_quick", **(filters or {}))
        
        # Intentar cache primero
        cached = await self.get_cache(cache_key, CACHE_TTL["dashboard_quick"])
        if cached:
            cached["from_cache"] = True
            return cached
        
        start_time = time.time()
        
        try:
            # Obtener solo datos mínimos necesarios
            df_edp, df_log = await self._get_minimal_data()
            
            if df_edp.empty:
                return self._get_empty_quick_kpis()
            
            # Aplicar filtros básicos
            df_filtered = await self._apply_basic_filters(df_edp, filters or {})
            
            # Calcular solo KPIs críticos
            quick_kpis = {
                "total_edps": len(df_filtered),
                "total_pagados": len(df_filtered[df_filtered["estado"] == "pagado"]),
                "total_pendientes": len(df_filtered[df_filtered["estado"].isin(["enviado", "revisión"])]),
                "monto_total": float(df_filtered["monto_aprobado"].sum()),
                "monto_pagado": float(df_filtered[df_filtered["estado"] == "pagado"]["monto_aprobado"].sum()),
                "dias_promedio": float(df_filtered["dias_espera"].mean()) if not df_filtered["dias_espera"].isna().all() else 0,
                "criticos": len(df_filtered[df_filtered.get("critico", False) == True]),
                "last_updated": datetime.now().isoformat(),
                "calculation_time": round(time.time() - start_time, 3),
                "from_cache": False
            }
            
            # Cache resultado
            await self.set_cache(cache_key, quick_kpis, CACHE_TTL["dashboard_quick"])
            
            return quick_kpis
            
        except Exception as e:
            logger.error(f"Error en dashboard quick KPIs: {e}")
            return self._get_empty_quick_kpis()

    async def get_dashboard_detailed_analysis(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        📊 MEDIO (1-3s) - Análisis detallado con gráficos
        Para dashboard completo, métricas avanzadas
        """
        cache_key = self._get_cache_key("dashboard_detailed", **(filters or {}))
        
        # Intentar cache
        cached = await self.get_cache(cache_key, CACHE_TTL["dashboard_detailed"])
        if cached:
            cached["from_cache"] = True
            return cached
        
        start_time = time.time()
        
        try:
            # Obtener datos completos
            df_edp, df_log = await self._get_full_data()
            
            if df_edp.empty:
                return self._get_empty_detailed_analysis()
            
            # Procesar en paralelo diferentes secciones
            tasks = [
                self._calculate_financial_metrics_async(df_edp, filters),
                self._calculate_performance_metrics_async(df_edp, filters), 
                self._generate_chart_data_async(df_edp, filters),
                self._calculate_dso_metrics_async(df_edp, filters),
            ]
            
            financial, performance, charts, dso = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Manejar excepciones
            if isinstance(financial, Exception):
                financial = {}
            if isinstance(performance, Exception):
                performance = {}
            if isinstance(charts, Exception):
                charts = {}
            if isinstance(dso, Exception):
                dso = {}
            
            detailed_analysis = {
                "financial_metrics": financial,
                "performance_metrics": performance,
                "chart_data": charts,
                "dso_analysis": dso,
                "last_updated": datetime.now().isoformat(),
                "calculation_time": round(time.time() - start_time, 3),
                "from_cache": False
            }
            
            # Cache resultado
            await self.set_cache(cache_key, detailed_analysis, CACHE_TTL["dashboard_detailed"])
            
            return detailed_analysis
            
        except Exception as e:
            logger.error(f"Error en dashboard detailed analysis: {e}")
            return self._get_empty_detailed_analysis()

    async def generate_complete_dashboard_context(
        self, 
        filters: Dict[str, Any] = None,
        background_tasks: BackgroundTasks = None
    ) -> Dict[str, Any]:
        """
        🔄 BACKGROUND - Análisis completo como en el original
        Usa la función original pero de forma asíncrona
        """
        cache_key = self._get_cache_key("dashboard_complete", **(filters or {}))
        
        # Verificar si ya está en proceso o completado
        processing_key = f"{cache_key}:processing"
        if self.redis_client:
            try:
                is_processing = await self.redis_client.get(processing_key)
                if is_processing:
                    return {
                        "status": "processing",
                        "message": "Análisis completo en progreso...",
                        "estimated_time": "30-60 segundos"
                    }
            except Exception:
                pass
        
        # Verificar cache existente
        cached = await self.get_cache(cache_key, CACHE_TTL["heavy_analysis"])
        if cached:
            return {
                "status": "completed",
                "data": cached,
                "from_cache": True
            }
        
        # Si hay background_tasks, procesar en background
        if background_tasks:
            background_tasks.add_task(
                self._process_complete_dashboard_background,
                cache_key,
                processing_key,
                filters or {}
            )
            
            return {
                "status": "processing",
                "message": "Iniciando análisis completo en background...",
                "cache_key": cache_key,
                "check_url": f"/api/v1/dashboard/status/{cache_key.split(':')[-1]}"
            }
        
        # Procesar sincrónicamente si no hay background_tasks
        return await self._process_complete_dashboard_sync(filters or {})

    async def _process_complete_dashboard_background(
        self, 
        cache_key: str, 
        processing_key: str, 
        filters: Dict[str, Any]
    ):
        """Procesar dashboard completo en background"""
        try:
            # Marcar como en proceso
            if self.redis_client:
                await self.redis_client.setex(processing_key, 300, "true")  # 5 min timeout
            
            start_time = time.time()
            
            # Ejecutar función original en thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_original_dashboard_context,
                filters
            )
            
            if result.success:
                # Agregar metadatos
                result.data["calculation_time"] = round(time.time() - start_time, 3)
                result.data["generated_at"] = datetime.now().isoformat()
                result.data["from_cache"] = False
                
                # Guardar resultado
                await self.set_cache(cache_key, result.data, CACHE_TTL["heavy_analysis"])
                
                logger.info(f"✅ Dashboard completo generado en {result.data['calculation_time']}s")
            else:
                # Guardar error
                error_result = {
                    "error": result.message,
                    "generated_at": datetime.now().isoformat(),
                    "status": "failed"
                }
                await self.set_cache(cache_key, error_result, 300)  # Cache error por 5 min
                
        except Exception as e:
            logger.error(f"Error en background dashboard: {e}")
            error_result = {
                "error": str(e),
                "generated_at": datetime.now().isoformat(), 
                "status": "failed"
            }
            await self.set_cache(cache_key, error_result, 300)
        finally:
            # Limpiar flag de procesamiento
            if self.redis_client:
                try:
                    await self.redis_client.delete(processing_key)
                except Exception:
                    pass

    def _run_original_dashboard_context(self, filters: Dict[str, Any]):
        """Ejecutar función original en thread pool"""
        try:
            # Cargar datos
            edps_response = self.original_service.edp_repo.find_all_dataframe()
            logs_response = self.original_service.log_repository.find_all_dataframe()
            
            # Extraer DataFrames
            df_edp = edps_response.get("data", pd.DataFrame()) if isinstance(edps_response, dict) else edps_response
            df_log = logs_response.get("data", pd.DataFrame()) if isinstance(logs_response, dict) else logs_response
            
            # Ejecutar función original
            return self.original_service.get_processed_dashboard_context(
                df_edp, df_log, filters
            )
            
        except Exception as e:
            from edp_mvp.app.services import ServiceResponse
            return ServiceResponse(
                success=False,
                message=f"Error ejecutando dashboard original: {str(e)}",
                data=None
            )

    async def check_dashboard_status(self, cache_key_suffix: str) -> Dict[str, Any]:
        """Verificar estado de dashboard en background"""
        cache_key = f"dashboard_complete:{cache_key_suffix}"
        processing_key = f"{cache_key}:processing"
        
        # Verificar si está procesando
        if self.redis_client:
            try:
                is_processing = await self.redis_client.get(processing_key)
                if is_processing:
                    return {
                        "status": "processing",
                        "message": "Análisis en progreso..."
                    }
            except Exception:
                pass
        
        # Verificar resultado
        result = await self.get_cache(cache_key, CACHE_TTL["heavy_analysis"])
        if result:
            if "error" in result:
                return {
                    "status": "failed",
                    "error": result["error"],
                    "generated_at": result.get("generated_at")
                }
            return {
                "status": "completed",
                "data": result
            }
        
        return {
            "status": "not_found",
            "message": "No se encontró el análisis solicitado"
        }

    # Métodos auxiliares optimizados
    async def _get_minimal_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Obtener solo columnas esenciales para KPIs rápidos"""
        loop = asyncio.get_event_loop()
        
        def get_minimal_edp_data():
            response = self.original_service.edp_repo.find_all_dataframe()
            df = response.get("data", pd.DataFrame()) if isinstance(response, dict) else response
            
            # Solo columnas necesarias para KPIs rápidos
            essential_cols = [
                "estado", "monto_aprobado", "dias_espera", "critico", 
                "mes", "cliente", "jefe_proyecto", "n_edp"
            ]
            available_cols = [col for col in essential_cols if col in df.columns]
            return df[available_cols] if not df.empty else df
        
        # Ejecutar en thread pool para no bloquear
        df_edp = await loop.run_in_executor(self.executor, get_minimal_edp_data)
        df_log = pd.DataFrame()  # No necesario para KPIs rápidos
        
        return df_edp, df_log

    async def _get_full_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Obtener datos completos"""
        loop = asyncio.get_event_loop()
        
        def get_data():
            edps_response = self.original_service.edp_repo.find_all_dataframe()
            logs_response = self.original_service.log_repository.find_all_dataframe()
            
            df_edp = edps_response.get("data", pd.DataFrame()) if isinstance(edps_response, dict) else edps_response
            df_log = logs_response.get("data", pd.DataFrame()) if isinstance(logs_response, dict) else logs_response
            
            return df_edp, df_log
        
        return await loop.run_in_executor(self.executor, get_data)

    async def _apply_basic_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Aplicar filtros básicos de forma eficiente"""
        if df.empty:
            return df
        
        filtered = df.copy()
        
        # Filtros más comunes primero (más eficiente)
        if filters.get("estado") and filters["estado"] != "todos":
            if filters["estado"] == "pendientes":
                filtered = filtered[filtered["estado"].isin(["enviado", "revisión"])]
            else:
                filtered = filtered[filtered["estado"] == filters["estado"]]
        
        if filters.get("mes"):
            filtered = filtered[filtered["mes"] == filters["mes"]]
        
        if filters.get("jefe_proyecto") and filters["jefe_proyecto"] != "todos":
            filtered = filtered[filtered["jefe_proyecto"] == filters["jefe_proyecto"]]
        
        if filters.get("cliente") and filters["cliente"] != "todos":
            filtered = filtered[filtered["cliente"] == filters["cliente"]]
        
        return filtered

    # Métodos de cálculo asíncronos
    async def _calculate_financial_metrics_async(self, df: pd.DataFrame, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular métricas financieras de forma asíncrona"""
        loop = asyncio.get_event_loop()
        
        def calculate():
            df_filtered = df.copy()  # Aplicar filtros si es necesario
            
            return {
                "total_revenue": float(df_filtered[df_filtered["estado"] == "pagado"]["monto_aprobado"].sum()),
                "pending_revenue": float(df_filtered[df_filtered["estado"].isin(["enviado", "validado","revisión"])]["monto_aprobado"].sum()),
                "total_proposed": float(df_filtered["monto_propuesto"].sum()) if "monto_propuesto" in df_filtered.columns else 0,
                "approval_rate": len(df_filtered[df_filtered["estado"] == "pagado"]) / len(df_filtered) * 100 if len(df_filtered) > 0 else 0
            }
        
        return await loop.run_in_executor(self.executor, calculate)

    async def _calculate_performance_metrics_async(self, df: pd.DataFrame, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular métricas de rendimiento"""
        loop = asyncio.get_event_loop()
        
        def calculate():
            return {
                "avg_processing_days": float(df["dias_espera"].mean()) if not df["dias_espera"].isna().all() else 0,
                "critical_edps": len(df[df.get("critico", False) == True]),
                "overdue_edps": len(df[df["dias_espera"] > 30]) if "dias_espera" in df.columns else 0,
                "completion_rate": len(df[df["estado"] == "pagado"]) / len(df) * 100 if len(df) > 0 else 0
            }
        
        return await loop.run_in_executor(self.executor, calculate)

    async def _generate_chart_data_async(self, df: pd.DataFrame, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generar datos para gráficos"""
        loop = asyncio.get_event_loop()
        
        def generate():
            charts = {}
            
            # Estado distribution
            if "estado" in df.columns:
                status_counts = df["estado"].value_counts()
                charts["status_distribution"] = {
                    "labels": status_counts.index.tolist(),
                    "data": status_counts.values.tolist()
                }
            
            # Monthly trend
            if "mes" in df.columns and "monto_aprobado" in df.columns:
                monthly = df.groupby("mes")["monto_aprobado"].sum()
                charts["monthly_trend"] = {
                    "labels": monthly.index.tolist(),
                    "data": (monthly / 1_000_000).round(2).tolist()  # En millones
                }
            
            return charts
        
        return await loop.run_in_executor(self.executor, generate)

    async def _calculate_dso_metrics_async(self, df: pd.DataFrame, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular métricas DSO"""
        loop = asyncio.get_event_loop()
        
        def calculate():
            if "dias_espera" in df.columns and "monto_aprobado" in df.columns:
                # DSO ponderado
                valid_data = df[(df["dias_espera"].notna()) & (df["monto_aprobado"] > 0)]
                if not valid_data.empty:
                    dso = np.average(valid_data["dias_espera"], weights=valid_data["monto_aprobado"])
                    return {
                        "dso": round(float(dso), 1),
                        "dso_variance": 0,  # Placeholder
                        "aging_buckets": self._calculate_aging_buckets(df)
                    }
            
            return {"dso": 0, "dso_variance": 0, "aging_buckets": {}}
        
        return await loop.run_in_executor(self.executor, calculate)

    def _calculate_aging_buckets(self, df: pd.DataFrame) -> Dict[str, int]:
        """Calcular buckets de aging"""
        if "dias_espera" not in df.columns:
            return {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
        
        dias = df["dias_espera"].fillna(0)
        return {
            "0-30": int((dias <= 30).sum()),
            "31-60": int(((dias > 30) & (dias <= 60)).sum()),
            "61-90": int(((dias > 60) & (dias <= 90)).sum()),
            "90+": int((dias > 90).sum())
        }

    # Métodos de datos vacíos
    def _get_empty_quick_kpis(self) -> Dict[str, Any]:
        """KPIs vacíos para respuesta rápida"""
        return {
            "total_edps": 0,
            "total_pagados": 0,
            "total_pendientes": 0,
            "monto_total": 0,
            "monto_pagado": 0,
            "dias_promedio": 0,
            "criticos": 0,
            "last_updated": datetime.now().isoformat(),
            "calculation_time": 0,
            "from_cache": False,
            "status": "no_data"
        }

    def _get_empty_detailed_analysis(self) -> Dict[str, Any]:
        """Análisis detallado vacío"""
        return {
            "financial_metrics": {},
            "performance_metrics": {},
            "chart_data": {},
            "dso_analysis": {},
            "last_updated": datetime.now().isoformat(),
            "calculation_time": 0,
            "from_cache": False,
            "status": "no_data"
        }

    async def _process_complete_dashboard_sync(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar dashboard completo de forma síncrona"""
        try:
            start_time = time.time()
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._run_original_dashboard_context,
                filters
            )
            
            if result.success:
                result.data["calculation_time"] = round(time.time() - start_time, 3)
                result.data["generated_at"] = datetime.now().isoformat()
                result.data["from_cache"] = False
                
                return {
                    "status": "completed",
                    "data": result.data
                }
            else:
                return {
                    "status": "failed",
                    "error": result.message
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            } 