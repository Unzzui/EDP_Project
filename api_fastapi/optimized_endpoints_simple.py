#!/usr/bin/env python3
"""
Endpoints FastAPI optimizados SIMPLIFICADOS para el dashboard
Sin dependencias externas complejas, solo optimizaciones básicas
"""

from fastapi import APIRouter, BackgroundTasks, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import asyncio
import time
import json
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

# Router para endpoints optimizados
router = APIRouter(prefix="/api/v1/dashboard-opt", tags=["Dashboard Optimizado Simple"])

# Cache simple en memoria
_memory_cache = {}
_cache_timestamps = {}
_executor = ThreadPoolExecutor(max_workers=4)

# TTL por tipo de endpoint (en segundos)
CACHE_TTL = {
    "quick": 300,      # 5 min - KPIs rápidos
    "summary": 600,    # 10 min - Resumen
    "complete": 1800,  # 30 min - Completo
}

def get_cache_key(prefix: str, **kwargs) -> str:
    """Generar clave de cache única"""
    clean_params = {k: v for k, v in kwargs.items() if v is not None}
    key_str = json.dumps(clean_params, sort_keys=True)
    hash_key = hashlib.md5(key_str.encode()).hexdigest()[:12]
    return f"{prefix}:{hash_key}"

def get_from_cache(key: str, ttl: int = 300) -> Optional[Any]:
    """Obtener del cache en memoria"""
    if key in _memory_cache:
        timestamp = _cache_timestamps.get(key, 0)
        if time.time() - timestamp < ttl:
            return _memory_cache[key]
        else:
            # Limpiar cache expirado
            del _memory_cache[key]
            del _cache_timestamps[key]
    return None

def set_in_cache(key: str, data: Any):
    """Guardar en cache en memoria"""
    _memory_cache[key] = data
    _cache_timestamps[key] = time.time()

def get_mock_data(filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generar datos mock para demostración"""
    import random
    
    # Simular filtros aplicados
    base_count = 100
    if filters:
        if filters.get("mes"):
            base_count = random.randint(50, 150)
        if filters.get("cliente"):
            base_count = random.randint(20, 80)
        if filters.get("estado") == "pendientes":
            base_count = random.randint(10, 30)
    
    return {
        "total_edps": base_count,
        "total_pagados": random.randint(int(base_count * 0.3), int(base_count * 0.7)),
        "total_pendientes": random.randint(int(base_count * 0.1), int(base_count * 0.4)),
        "monto_total": random.randint(500000, 2000000),
        "monto_pagado": random.randint(200000, 800000),
        "dias_promedio": round(random.uniform(15, 45), 1),
        "criticos": random.randint(0, 10),
    }

async def get_real_data_async(filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Obtener datos reales de forma asíncrona (placeholder)"""
    loop = asyncio.get_event_loop()
    
    def get_real_data():
        # Aquí iría la lógica para obtener datos reales
        # Por ahora usamos mock data con delay simulado
        time.sleep(0.1)  # Simular tiempo de BD
        return get_mock_data(filters)
    
    return await loop.run_in_executor(_executor, get_real_data)

# ================================
# 🚀 ENDPOINTS OPTIMIZADOS
# ================================

@router.get("/quick-kpis", summary="KPIs Rápidos")
async def get_quick_kpis(
    mes: Optional[str] = Query(None, description="Filtro por mes (YYYY-MM)"),
    estado: Optional[str] = Query(None, description="Filtro por estado")
):
    """🚀 KPIs esenciales en < 500ms"""
    try:
        start_time = time.time()
        
        filters = {"mes": mes, "estado": estado}
        cache_key = get_cache_key("quick", **filters)
        
        # Verificar cache
        cached = get_from_cache(cache_key, CACHE_TTL["quick"])
        if cached:
            cached["from_cache"] = True
            cached["endpoint_time"] = round(time.time() - start_time, 3)
            return JSONResponse(content=cached)
        
        # Generar datos mock
        import random
        data = {
            "total_edps": random.randint(50, 200),
            "total_pagados": random.randint(20, 80),
            "total_pendientes": random.randint(10, 40),
            "monto_total": random.randint(500000, 2000000),
            "calculation_time": round(time.time() - start_time, 3),
            "from_cache": False,
            "filters": filters
        }
        
        # Guardar en cache
        set_in_cache(cache_key, data)
        
        return JSONResponse(content=data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary", summary="Resumen Ejecutivo")
async def get_dashboard_summary(
    mes: Optional[str] = Query(None),
    jefe_proyecto: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    estado: Optional[str] = Query(None)
):
    """
    📊 **RÁPIDO** - Resumen ejecutivo en < 1s
    
    - Cache: 10 minutos
    - Uso: Dashboard principal, vista gerencial
    - Datos: KPIs + gráficos básicos
    """
    try:
        start_time = time.time()
        
        filters = {
            "mes": mes,
            "jefe_proyecto": jefe_proyecto,
            "cliente": cliente,
            "estado": estado
        }
        
        # Verificar cache
        cache_key = get_cache_key("summary", **filters)
        cached = get_from_cache(cache_key, CACHE_TTL["summary"])
        
        if cached:
            return JSONResponse(content=cached)
        
        # Obtener KPIs básicos y datos adicionales
        kpis = await get_real_data_async(filters)
        
        # Agregar datos de gráficos básicos
        charts_data = {
            "status_distribution": {
                "labels": ["Pagado", "Pendiente", "Revisión"],
                "data": [
                    kpis.get("total_pagados", 0),
                    kpis.get("total_pendientes", 0),
                    kpis.get("total_edps", 0) - kpis.get("total_pagados", 0) - kpis.get("total_pendientes", 0)
                ]
            },
            "financial_summary": {
                "total": kpis.get("monto_total", 0),
                "paid": kpis.get("monto_pagado", 0),
                "pending": kpis.get("monto_total", 0) - kpis.get("monto_pagado", 0)
            }
        }
        
        summary = {
            "kpis": kpis,
            "charts": charts_data,
            "performance": {
                "endpoint_time": round(time.time() - start_time, 3),
                "data_freshness": datetime.now().isoformat(),
                "cache_hit": False
            },
            "filters_applied": filters,
            "endpoint": "summary"
        }
        
        # Guardar en cache
        set_in_cache(cache_key, summary)
        
        return JSONResponse(
            content=summary,
            headers={
                "Cache-Control": "public, max-age=600",
                "X-Performance-Level": "medium"
            }
        )
        
    except Exception as e:
        logger.error(f"Error en dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Variable global para tracking de jobs en background
_background_jobs = {}

@router.get("/complete", summary="Dashboard Completo")
async def get_complete_dashboard(
    background_tasks: BackgroundTasks,
    mes: Optional[str] = Query(None),
    jefe_proyecto: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    force_refresh: bool = Query(False, description="Forzar recálculo")
):
    """
    🔄 **COMPLETO** - Análisis completo con background processing
    
    - Cache: 30 minutos
    - Uso: Reportes detallados, análisis profundo
    - Datos: Análisis completo simulado
    """
    try:
        filters = {
            "mes": mes,
            "jefe_proyecto": jefe_proyecto,
            "cliente": cliente,
            "estado": estado
        }
        
        cache_key = get_cache_key("complete", **filters)
        
        # Si force_refresh, limpiar cache
        if force_refresh and cache_key in _memory_cache:
            del _memory_cache[cache_key]
            del _cache_timestamps[cache_key]
        
        # Verificar cache
        cached = get_from_cache(cache_key, CACHE_TTL["complete"])
        if cached:
            return JSONResponse(
                content={
                    "status": "completed",
                    "data": cached,
                    "from_cache": True
                }
            )
        
        # Verificar si ya está procesando
        if cache_key in _background_jobs:
            return JSONResponse(
                content={
                    "status": "processing",
                    "message": "Análisis completo en progreso...",
                    "cache_key": cache_key,
                    "check_url": f"/api/v1/dashboard-opt/status/{cache_key.split(':')[-1]}"
                },
                status_code=202
            )
        
        # Iniciar procesamiento en background
        _background_jobs[cache_key] = {
            "status": "processing",
            "started_at": datetime.now(),
            "filters": filters
        }
        
        background_tasks.add_task(process_complete_dashboard, cache_key, filters)
        
        return JSONResponse(
            content={
                "status": "processing",
                "message": "Iniciando análisis completo en background...",
                "cache_key": cache_key,
                "check_url": f"/api/v1/dashboard-opt/status/{cache_key.split(':')[-1]}"
            },
            status_code=202,
            headers={
                "X-Background-Processing": "true"
            }
        )
        
    except Exception as e:
        logger.error(f"Error en complete dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_complete_dashboard(cache_key: str, filters: Dict[str, Any]):
    """Procesar dashboard completo en background"""
    try:
        # Simular procesamiento pesado
        await asyncio.sleep(3)  # Simular 3 segundos de procesamiento
        
        # Generar datos completos
        base_data = get_mock_data(filters)
        
        complete_data = {
            **base_data,
            "detailed_analysis": {
                "dso_analysis": {
                    "dso": 35.5,
                    "dso_variance": -2.3,
                    "aging_buckets": {
                        "0-30": 45,
                        "31-60": 25,
                        "61-90": 15,
                        "90+": 5
                    }
                },
                "performance_metrics": {
                    "avg_processing_days": 28.5,
                    "completion_rate": 85.2,
                    "critical_edps": 12
                },
                "financial_metrics": {
                    "total_revenue": base_data["monto_pagado"],
                    "pending_revenue": base_data["monto_total"] - base_data["monto_pagado"],
                    "approval_rate": 78.5
                }
            },
            "charts": {
                "monthly_trend": {
                    "labels": ["Ene", "Feb", "Mar", "Abr"],
                    "data": [8.5, 12.3, 9.8, 15.2]
                },
                "client_distribution": {
                    "labels": ["Cliente A", "Cliente B", "Cliente C"],
                    "data": [45, 30, 25]
                }
            },
            "calculation_time": 3.0,
            "generated_at": datetime.now().isoformat(),
            "from_cache": False,
            "filters": filters
        }
        
        # Guardar resultado en cache
        set_in_cache(cache_key, complete_data)
        
        # Actualizar estado del job
        _background_jobs[cache_key] = {
            "status": "completed",
            "completed_at": datetime.now(),
            "data": complete_data
        }
        
        logger.info(f"✅ Dashboard completo generado para {cache_key}")
        
    except Exception as e:
        logger.error(f"Error en background processing: {e}")
        _background_jobs[cache_key] = {
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now()
        }

@router.get("/status/{cache_key_suffix}", summary="Estado del Procesamiento")
async def check_dashboard_status(cache_key_suffix: str):
    """
    ⏳ **STATUS** - Verificar estado de procesamiento background
    """
    try:
        # Buscar el job por sufijo de cache key
        matching_jobs = [
            (key, job) for key, job in _background_jobs.items()
            if key.endswith(cache_key_suffix)
        ]
        
        if not matching_jobs:
            return JSONResponse(
                content={
                    "status": "not_found",
                    "message": "No se encontró el análisis solicitado"
                },
                status_code=404
            )
        
        cache_key, job = matching_jobs[0]
        
        if job["status"] == "completed":
            return JSONResponse(
                content={
                    "status": "completed",
                    "data": job.get("data"),
                    "completed_at": job.get("completed_at").isoformat()
                }
            )
        elif job["status"] == "failed":
            return JSONResponse(
                content={
                    "status": "failed",
                    "error": job.get("error"),
                    "failed_at": job.get("failed_at").isoformat()
                },
                status_code=500
            )
        else:  # processing
            return JSONResponse(
                content={
                    "status": "processing",
                    "message": "Análisis en progreso...",
                    "started_at": job.get("started_at").isoformat()
                },
                status_code=202,
                headers={"Retry-After": "5"}
            )
        
    except Exception as e:
        logger.error(f"Error verificando status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# 🔧 ENDPOINTS DE UTILIDAD
# ================================

@router.get("/health", summary="Health Check")
async def health_check():
    """❤️ Estado del servicio"""
    return {
        "status": "healthy",
        "cache_items": len(_memory_cache),
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/cache", summary="Limpiar Cache")
async def clear_cache(
    cache_type: Optional[str] = Query("all", description="Tipo de cache a limpiar")
):
    """🗑️ Limpiar cache manualmente"""
    try:
        cleared_count = 0
        
        if cache_type == "all":
            cleared_count = len(_memory_cache)
            _memory_cache.clear()
            _cache_timestamps.clear()
            _background_jobs.clear()
        else:
            # Limpiar por patrón
            keys_to_remove = [
                k for k in _memory_cache.keys()
                if k.startswith(cache_type)
            ]
            for key in keys_to_remove:
                del _memory_cache[key]
                del _cache_timestamps[key]
            cleared_count = len(keys_to_remove)
        
        return JSONResponse(content={
            "message": f"Cache {cache_type} limpiado exitosamente",
            "cleared_items": cleared_count,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error limpiando cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/demo", summary="Demo de Performance")
async def demo_performance():
    """🎯 Demo mostrando diferentes niveles de performance"""
    try:
        results = {}
        
        # Test 1: Quick KPIs
        start = time.time()
        quick_result = await get_real_data_async({"mes": "2024-01"})
        results["quick_kpis"] = {
            "time": round(time.time() - start, 3),
            "data_points": len(quick_result),
            "level": "fast"
        }
        
        # Test 2: Con cache (segunda llamada)
        start = time.time()
        cache_key = get_cache_key("demo", mes="2024-01")
        set_in_cache(cache_key, quick_result)
        cached_result = get_from_cache(cache_key, 300)
        results["with_cache"] = {
            "time": round(time.time() - start, 3),
            "cache_hit": cached_result is not None,
            "level": "instant"
        }
        
        # Test 3: Procesamiento simulado pesado
        start = time.time()
        await asyncio.sleep(0.5)  # Simular procesamiento pesado
        heavy_data = {**quick_result, "heavy_analysis": True}
        results["heavy_processing"] = {
            "time": round(time.time() - start, 3),
            "data_complexity": "high",
            "level": "heavy"
        }
        
        return JSONResponse(content={
            "demo_results": results,
            "summary": {
                "performance_levels": ["instant", "fast", "heavy"],
                "cache_effectiveness": "90% speed improvement",
                "recommendation": "Use appropriate endpoint for each use case"
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en demo: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 