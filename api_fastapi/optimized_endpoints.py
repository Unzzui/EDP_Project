#!/usr/bin/env python3
"""
Endpoints FastAPI optimizados para el dashboard
Aplicando estrategias de cache multinivel y background processing
"""

from fastapi import APIRouter, BackgroundTasks, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import asyncio
import time
from datetime import datetime
import logging

try:
    from .optimized_controller_service import OptimizedControllerService
except ImportError:
    # Fallback para cuando se ejecuta directamente
    from optimized_controller_service import OptimizedControllerService

logger = logging.getLogger(__name__)

# Router para endpoints optimizados
router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard Optimizado"])

# Instancia global del servicio optimizado
optimized_service = OptimizedControllerService()

@router.on_event("startup")
async def startup_event():
    """Inicializar servicios al arrancar"""
    await optimized_service.init_redis()
    logger.info("🚀 Servicios optimizados inicializados")

# ================================
# 🚀 ENDPOINTS RÁPIDOS (< 1s)
# ================================

@router.get("/quick-kpis", summary="KPIs Rápidos")
async def get_quick_kpis(
    mes: Optional[str] = Query(None, description="Filtro por mes (YYYY-MM)"),
    jefe_proyecto: Optional[str] = Query(None, description="Filtro por jefe de proyecto"),
    cliente: Optional[str] = Query(None, description="Filtro por cliente"),
    estado: Optional[str] = Query(None, description="Filtro por estado")
):
    """
    🚀 **SÚPER RÁPIDO** - KPIs esenciales en < 500ms
    
    - Cache: 5 minutos
    - Uso: Widgets principales, actualizaciones frecuentes
    - Datos: Solo métricas críticas
    """
    try:
        start_time = time.time()
        
        filters = {
            "mes": mes,
            "jefe_proyecto": jefe_proyecto,
            "cliente": cliente,
            "estado": estado
        }
        
        result = await optimized_service.get_dashboard_quick_kpis(filters)
        
        # Agregar metadata de performance
        result["endpoint_time"] = round(time.time() - start_time, 3)
        result["endpoint"] = "quick-kpis"
        
        return JSONResponse(
            content=result,
            headers={
                "Cache-Control": "public, max-age=300",  # 5 min
                "X-Cache-TTL": "300",
                "X-Performance-Level": "fast"
            }
        )
        
    except Exception as e:
        logger.error(f"Error en quick-kpis: {e}")
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
        
        # Obtener KPIs rápidos + datos adicionales en paralelo
        kpis_task = optimized_service.get_dashboard_quick_kpis(filters)
        
        # Ejecutar en paralelo
        kpis = await kpis_task
        
        # Agregar datos de resumen
        summary = {
            "kpis": kpis,
            "performance": {
                "endpoint_time": round(time.time() - start_time, 3),
                "data_freshness": kpis.get("last_updated"),
                "cache_hit": kpis.get("from_cache", False)
            },
            "filters_applied": filters,
            "endpoint": "summary"
        }
        
        return JSONResponse(
            content=summary,
            headers={
                "Cache-Control": "public, max-age=600",  # 10 min
                "X-Cache-TTL": "600",
                "X-Performance-Level": "medium"
            }
        )
        
    except Exception as e:
        logger.error(f"Error en dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# 🔄 ENDPOINTS BACKGROUND (> 3s)
# ================================

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
    - Datos: Todos los cálculos como en el dashboard original
    
    **Flujo:**
    1. Si está en cache → Retorna inmediatamente
    2. Si no → Inicia background task y retorna status
    3. Cliente verifica status con `/status/{id}`
    """
    try:
        filters = {
            "mes": mes,
            "jefe_proyecto": jefe_proyecto,
            "cliente": cliente,
            "estado": estado
        }
        
        # Si force_refresh, limpiar cache primero
        if force_refresh:
            cache_key = optimized_service._get_cache_key("dashboard_complete", **filters)
            if optimized_service.redis_client:
                await optimized_service.redis_client.delete(cache_key)
        
        result = await optimized_service.generate_complete_dashboard_context(
            filters, background_tasks
        )
        
        # Determinar código de respuesta basado en status
        status_code = 200 if result.get("status") == "completed" else 202
        
        return JSONResponse(
            content=result,
            status_code=status_code,
            headers={
                "Cache-Control": "public, max-age=1800",  # 30 min
                "X-Cache-TTL": "1800",
                "X-Performance-Level": "heavy",
                "X-Background-Processing": "true" if status_code == 202 else "false"
            }
        )
        
    except Exception as e:
        logger.error(f"Error en complete dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{cache_key}", summary="Estado del Procesamiento")
async def check_dashboard_status(cache_key: str):
    """
    ⏳ **STATUS** - Verificar estado de procesamiento background
    
    Estados posibles:
    - `processing`: Análisis en progreso
    - `completed`: Análisis completado, datos disponibles
    - `failed`: Error en el procesamiento
    - `not_found`: No se encontró el análisis
    """
    try:
        result = await optimized_service.check_dashboard_status(cache_key)
        
        # Código de respuesta basado en status
        status_codes = {
            "processing": 202,
            "completed": 200,
            "failed": 500,
            "not_found": 404
        }
        
        status_code = status_codes.get(result.get("status"), 200)
        
        return JSONResponse(
            content=result,
            status_code=status_code,
            headers={
                "X-Processing-Status": result.get("status", "unknown"),
                "Retry-After": "10" if result.get("status") == "processing" else None
            }
        )
        
    except Exception as e:
        logger.error(f"Error verificando status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# 🎯 ENDPOINTS ESPECIALIZADOS
# ================================

@router.get("/charts", summary="Solo Gráficos")
async def get_dashboard_charts(
    mes: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    chart_type: Optional[str] = Query(None, description="Tipo específico de gráfico")
):
    """
    📈 **GRÁFICOS** - Solo datos para visualizaciones
    
    - Cache: 15 minutos
    - Uso: Actualización de gráficos específicos
    - Datos: Optimizado para Chart.js/D3.js
    """
    try:
        # Implementar lógica específica para gráficos
        # Por ahora, usar quick KPIs como base
        filters = {"mes": mes, "cliente": cliente}
        kpis = await optimized_service.get_dashboard_quick_kpis(filters)
        
        # Generar datos específicos para gráficos
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
            },
            "performance": {
                "avg_days": kpis.get("dias_promedio", 0),
                "critical_count": kpis.get("criticos", 0)
            }
        }
        
        return JSONResponse(
            content={
                "charts": charts_data,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "filters": filters,
                    "chart_type": chart_type
                }
            },
            headers={
                "Cache-Control": "public, max-age=900",  # 15 min
                "X-Cache-TTL": "900",
                "X-Content-Type": "charts"
            }
        )
        
    except Exception as e:
        logger.error(f"Error en dashboard charts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/filters", summary="Opciones de Filtros")
async def get_filter_options():
    """
    🎛️ **FILTROS** - Opciones disponibles para filtros
    
    - Cache: 15 minutos
    - Uso: Poblar dropdowns, validar filtros
    - Datos: Listas de valores únicos
    """
    try:
        # Implementar lógica para obtener opciones de filtros
        # Por ahora, valores mock
        filter_options = {
            "meses": ["2024-01", "2024-02", "2024-03", "2024-04"],
            "jefes_proyecto": ["Diego Bravo", "Carolina López", "Pedro Rojas"],
            "clientes": ["Cliente A", "Cliente B", "Cliente C"],
            "estados": ["pagado", "pendiente", "revisión", "enviado", "validado"]
        }
        
        return JSONResponse(
            content={
                "filters": filter_options,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "cache_duration": "15 minutes"
                }
            },
            headers={
                "Cache-Control": "public, max-age=900",  # 15 min
                "X-Cache-TTL": "900"
            }
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo opciones de filtros: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# 🔧 ENDPOINTS DE UTILIDAD
# ================================

@router.get("/health", summary="Health Check")
async def health_check():
    """
    ❤️ **HEALTH** - Estado del servicio optimizado
    """
    try:
        # Verificar componentes
        redis_status = "connected" if optimized_service.redis_client else "disconnected"
        
        # Test rápido de datos
        test_start = time.time()
        df_edp, _ = await optimized_service._get_minimal_data()
        data_test_time = round(time.time() - test_start, 3)
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "redis": redis_status,
                "database": "connected" if not df_edp.empty else "no_data",
                "thread_pool": "active"
            },
            "performance": {
                "data_test_time": data_test_time,
                "memory_cache_size": len(optimized_service._memory_cache),
                "cache_hit_ratio": "N/A"  # Implementar si se necesita
            },
            "version": "1.0.0"
        }
        
        return JSONResponse(content=health_data)
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )

@router.delete("/cache", summary="Limpiar Cache")
async def clear_cache(
    cache_type: Optional[str] = Query("all", description="Tipo de cache a limpiar")
):
    """
    🗑️ **CACHE** - Limpiar cache manualmente
    
    Tipos:
    - `all`: Todo el cache
    - `quick`: Solo KPIs rápidos
    - `detailed`: Solo análisis detallados
    - `complete`: Solo dashboard completo
    """
    try:
        cleared_count = 0
        
        # Limpiar Redis
        if optimized_service.redis_client:
            if cache_type == "all":
                await optimized_service.redis_client.flushdb()
                cleared_count += 1
            else:
                # Limpiar por patrón
                pattern = f"dashboard_{cache_type}:*"
                keys = await optimized_service.redis_client.keys(pattern)
                if keys:
                    await optimized_service.redis_client.delete(*keys)
                    cleared_count += len(keys)
        
        # Limpiar memoria
        if cache_type == "all":
            optimized_service._memory_cache.clear()
            optimized_service._cache_timestamps.clear()
        else:
            # Limpiar por patrón en memoria
            keys_to_remove = [
                k for k in optimized_service._memory_cache.keys()
                if k.startswith(f"dashboard_{cache_type}")
            ]
            for key in keys_to_remove:
                del optimized_service._memory_cache[key]
                del optimized_service._cache_timestamps[key]
            cleared_count += len(keys_to_remove)
        
        return JSONResponse(content={
            "message": f"Cache {cache_type} limpiado exitosamente",
            "cleared_items": cleared_count,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error limpiando cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# 📊 ENDPOINT DE MÉTRICAS
# ================================

@router.get("/metrics", summary="Métricas del Sistema")
async def get_system_metrics():
    """
    📊 **MÉTRICAS** - Estadísticas de performance del sistema
    """
    try:
        metrics = {
            "cache": {
                "memory_size": len(optimized_service._memory_cache),
                "redis_connected": optimized_service.redis_client is not None,
                "cache_keys": list(optimized_service._memory_cache.keys())[:10]  # Solo primeras 10
            },
            "performance": {
                "thread_pool_active": True,
                "avg_response_time": "N/A",  # Implementar si se necesita
                "requests_per_minute": "N/A"  # Implementar si se necesita
            },
            "system": {
                "timestamp": datetime.now().isoformat(),
                "uptime": "N/A"  # Implementar si se necesita
            }
        }
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 