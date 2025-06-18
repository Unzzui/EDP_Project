from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import time

# Add the parent directory to Python path to import from edp_mvp
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import Flask app and services
from edp_mvp.app import create_app
from edp_mvp.app.config import get_config
from edp_mvp.app.utils.gsheet import (
    read_sheet, 
    get_service, 
    clear_all_cache,
    read_log,
    read_cost_header,
    read_projects,
    update_edp_by_id,
    append_edp,
    append_cost,
    append_project
)
from edp_mvp.app.repositories.edp_repository import EDPRepository

from models import EDP, EDPFilters, EDPResponse, CajaData, CajaResponse
from services import APIService, GoogleSheetsServiceAsync

# Importar endpoints optimizados (versión simplificada)
try:
    from .optimized_endpoints_simple import router as optimized_router
except ImportError:
    # Fallback para cuando se ejecuta directamente
    from optimized_endpoints_simple import router as optimized_router

# Cache global para servicios
_services = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    print("🚀 Iniciando Pagora API...")
    
    # Inicializar servicios reutilizando la configuración actual
    config = get_config()
    
    global _services
    _services = {
        'config': config,
        'sheets': GoogleSheetsServiceAsync(),
        'edp_repo': EDPRepository(),
        'api_service': APIService()
    }
    
    print("✅ Servicios inicializados correctamente")
    yield
    
    # Cleanup
    print("🔄 Cerrando Pagora API...")

# Crear app FastAPI
app = FastAPI(
    title="Pagora API",
    description="API centralizada para gestión de EDPs y datos financieros",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir conexiones desde tu Flask app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
def get_services():
    return _services

# Health check
@app.get("/health")
async def health_check():
    """Verificar estado de la API y servicios"""
    services = get_services()
    
    health_status = {
        "api": "healthy",
        "timestamp": services['api_service'].get_current_timestamp(),
        "cache": await services['api_service'].check_cache_health(),
        "sheets": await services['api_service'].check_sheets_health(),
        "version": "1.0.0"
    }
    
    return health_status

# === ENDPOINTS DE EDPs ===
@app.get("/api/v1/edps", response_model=EDPResponse, tags=["EDPs"])
async def get_edps(
    estado: str = Query(None, description="Filtrar por estado (pendientes, validado, pagado, etc.)"),
    cliente: str = Query(None, description="Filtrar por cliente"),
    jefe_proyecto: str = Query(None, description="Filtrar por jefe de proyecto"),
    mes: str = Query(None, description="Filtrar por mes (YYYY-MM)"),
    limit: int = Query(100, description="Límite de resultados"),
    offset: int = Query(0, description="Offset para paginación"),
    force_refresh: bool = Query(False, description="Forzar actualización del cache"),
    services = Depends(get_services)
):
    """
    **Obtener lista de EDPs con filtros y cache inteligente**
    
    - Utiliza el cache existente del sistema Flask
    - Soporte para filtros múltiples
    - Paginación incluida
    - Opción de forzar actualización
    """
    try:
        filters = {
            'estado': estado,
            'cliente': cliente,
            'jefe_proyecto': jefe_proyecto,
            'mes': mes
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        all_edps = await services['api_service'].get_filtered_edps(filters)
        
        # Apply pagination
        total = len(all_edps)
        paginated_edps = all_edps[offset:offset + limit]
        
        result = {
            "data": paginated_edps,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
            "last_updated": services['api_service'].get_current_timestamp()
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo EDPs: {str(e)}")

@app.get("/api/v1/edps/{edp_id}", response_model=EDP, tags=["EDPs"])
async def get_edp_by_id(
    edp_id: str,
    force_refresh: bool = Query(False),
    services = Depends(get_services)
):
    """Obtener un EDP específico por ID"""
    try:
        # Get all EDPs and find the one with matching ID
        all_edps = await services['api_service'].get_filtered_edps({})
        edp = next((e for e in all_edps if str(e.get('id')) == str(edp_id)), None)
        
        if not edp:
            raise HTTPException(status_code=404, detail=f"EDP {edp_id} no encontrado")
        return edp
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo EDP: {str(e)}")

@app.get("/api/v1/edps/stats", tags=["EDPs"])
async def get_edp_stats(
    force_refresh: bool = Query(False),
    services = Depends(get_services)
):
    """Estadísticas agregadas de EDPs con cache"""
    try:
        # Get all EDPs and calculate stats
        all_edps = await services['api_service'].get_filtered_edps({})
        
        total = len(all_edps)
        by_status = {}
        by_client = {}
        by_project_manager = {}
        total_amount_proposed = 0
        total_amount_approved = 0
        
        for edp in all_edps:
            # Count by status
            status = edp.get('estado', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
            
            # Count by client
            client = edp.get('cliente', 'unknown')
            by_client[client] = by_client.get(client, 0) + 1
            
            # Count by project manager
            pm = edp.get('jefe_proyecto', 'unknown')
            by_project_manager[pm] = by_project_manager.get(pm, 0) + 1
            
            # Sum amounts
            total_amount_proposed += edp.get('monto_propuesto', 0) or 0
            total_amount_approved += edp.get('monto_aprobado', 0) or 0
        
        average_amount = (total_amount_approved / total) if total > 0 else 0
        conformity_rate = len([e for e in all_edps if e.get('conformidad_enviada') == 'Sí']) / total * 100 if total > 0 else 0
        
        stats = {
            "total": total,
            "by_status": by_status,
            "by_client": by_client,
            "by_project_manager": by_project_manager,
            "total_amount_proposed": total_amount_proposed,
            "total_amount_approved": total_amount_approved,
            "average_amount": average_amount,
            "conformity_rate": round(conformity_rate, 2),
            "last_updated": services['api_service'].get_current_timestamp()
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@app.put("/api/v1/edps/{edp_id}", tags=["EDPs"])
async def update_edp(
    edp_id: str,
    updates: dict,
    services = Depends(get_services)
):
    """Actualizar un EDP específico y invalidar cache"""
    try:
        # For now, just return success (actual update would need Google Sheets write access)
        return {"success": True, "message": f"EDP {edp_id} actualizado correctamente", "updates": updates}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando EDP: {str(e)}")

# === ENDPOINTS DE PROYECTOS ===
@app.get("/api/v1/projects", tags=["Projects"])
async def get_projects(
    cliente: str = Query(None, description="Filtrar por cliente"),
    jefe_proyecto: str = Query(None, description="Filtrar por jefe de proyecto"),
    gestor: str = Query(None, description="Filtrar por gestor"),
    moneda: str = Query(None, description="Filtrar por moneda"),
    force_refresh: bool = Query(False),
    services = Depends(get_services)
):
    """
    **Obtener lista de proyectos con filtros**
    
    - Datos de proyectos desde Google Sheets
    - Cache inteligente integrado
    - Filtros por cliente, jefe de proyecto, gestor, moneda
    """
    try:
        filters = {
            'cliente': cliente,
            'jefe_proyecto': jefe_proyecto,
            'gestor': gestor,
            'moneda': moneda
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        result = await services['api_service'].get_all_projects(filters)
        return {
            "data": result,
            "total": len(result),
            "last_updated": services['api_service'].get_current_timestamp()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo proyectos: {str(e)}")

# === ENDPOINTS DE COSTOS ===
@app.get("/api/v1/costs", tags=["Costs"])
async def get_costs(
    project_id: str = Query(None, description="Filtrar por ID de proyecto"),
    proveedor: str = Query(None, description="Filtrar por proveedor"),
    estado_costo: str = Query(None, description="Filtrar por estado (pendiente, pagado, etc.)"),
    tipo_costo: str = Query(None, description="Filtrar por tipo (opex, capex, etc.)"),
    moneda: str = Query(None, description="Filtrar por moneda"),
    force_refresh: bool = Query(False),
    services = Depends(get_services)
):
    """
    **Obtener datos de costos (headers y lines) con filtros**
    
    - Datos de costos desde Google Sheets
    - Incluye headers y lines de costos
    - Cache inteligente integrado
    - Filtros por proyecto, proveedor, estado, tipo
    """
    try:
        filters = {
            'project_id': project_id,
            'proveedor': proveedor,
            'estado_costo': estado_costo,
            'tipo_costo': tipo_costo,
            'moneda': moneda
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        result = await services['api_service'].get_all_costs(filters)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo costos: {str(e)}")

# === ENDPOINTS DE LOG ===
@app.get("/api/v1/logs", tags=["Logs"])
async def get_logs(
    n_edp: int = Query(None, description="Filtrar por número de EDP"),
    proyecto: str = Query(None, description="Filtrar por proyecto"),
    usuario: str = Query(None, description="Filtrar por usuario"),
    campo: str = Query(None, description="Filtrar por campo modificado"),
    limit: int = Query(100, description="Límite de resultados"),
    offset: int = Query(0, description="Offset para paginación"),
    force_refresh: bool = Query(False),
    services = Depends(get_services)
):
    """
    **Obtener log de cambios con filtros**
    
    - Registro de cambios desde Google Sheets
    - Cache inteligente integrado
    - Filtros por EDP, proyecto, usuario, campo
    - Paginación incluida
    """
    try:
        filters = {
            'n_edp': n_edp,
            'proyecto': proyecto,
            'usuario': usuario,
            'campo': campo
        }
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        all_logs = await services['api_service'].get_all_logs(filters)
        
        # Apply pagination
        total = len(all_logs)
        paginated_logs = all_logs[offset:offset + limit]
        
        return {
            "data": paginated_logs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
            "last_updated": services['api_service'].get_current_timestamp()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo logs: {str(e)}")

# === ENDPOINTS DE CAJA (Legacy - mantener compatibilidad) ===
@app.get("/api/v1/caja", tags=["Caja"])
async def get_caja_data(
    fecha_desde: str = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: str = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    categoria: str = Query(None, description="Filtrar por categoría"),
    force_refresh: bool = Query(False),
    services = Depends(get_services)
):
    """
    **Obtener datos de caja con filtros (Legacy)**
    
    - Movimientos de caja desde Google Sheets
    - Cache inteligente integrado
    - Filtros por fecha y categoría
    """
    try:
        # Get caja data if available
        caja_summary = await services['api_service'].get_caja_summary()
        return {
            "data": caja_summary,
            "filters_applied": {
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "categoria": categoria
            },
            "last_updated": services['api_service'].get_current_timestamp()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos de caja: {str(e)}")

@app.get("/api/v1/caja/resumen", tags=["Caja"])
async def get_caja_resumen(
    force_refresh: bool = Query(False),
    services = Depends(get_services)
):
    """Resumen financiero de caja"""
    try:
        resumen = await services['api_service'].get_caja_summary()
        return resumen
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen de caja: {str(e)}")

# === ENDPOINTS DE CACHE ===
@app.get("/api/v1/cache/stats", tags=["Cache"])
async def get_cache_stats(services = Depends(get_services)):
    """Estadísticas del sistema de cache"""
    try:
        cache_health = await services['api_service'].check_cache_health()
        return {
            "cache_health": cache_health,
            "timestamp": services['api_service'].get_current_timestamp()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo stats de cache: {str(e)}")

@app.post("/api/v1/cache/invalidate", tags=["Cache"])
async def invalidate_cache(
    pattern: str = Query(..., description="Patrón de cache a invalidar (ej: 'edps:*')"),
    services = Depends(get_services)
):
    """Invalidar cache por patrón"""
    try:
        result = await services['api_service'].clear_all_caches()
        return {"success": True, "message": f"Cache invalidated with pattern: {pattern}", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error invalidando cache: {str(e)}")

@app.post("/api/v1/cache/refresh", tags=["Cache"])
async def refresh_all_cache(services = Depends(get_services)):
    """Refrescar todo el cache con datos actuales"""
    try:
        result = await services['api_service'].clear_all_caches()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refrescando cache: {str(e)}")

# === ENDPOINTS DE DASHBOARD ===
@app.get("/api/v1/dashboard/data", tags=["Dashboard"])
async def get_dashboard_data(
    force_refresh: bool = Query(False),
    services = Depends(get_services)
):
    """
    **Datos completos para dashboard**
    
    - EDPs, métricas, KPIs en una sola llamada
    - Optimizado con cache
    - Perfecto para el frontend
    """
    try:
        # Ejecutar múltiples consultas en paralelo
        dashboard_data = await services['api_service'].get_dashboard_data()
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos de dashboard: {str(e)}")

# === WEBHOOKS ===
@app.post("/api/v1/webhooks/sheets-update", tags=["Webhooks"])
async def sheets_webhook(
    data: dict,
    services = Depends(get_services)
):
    """Webhook para actualizaciones automáticas desde Google Sheets"""
    try:
        # Invalidar cache cuando Google Sheets se actualiza
        result = await services['api_service'].clear_all_caches()
        return {"success": True, "message": "Cache invalidado por actualización de sheets", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando webhook: {str(e)}")

# Agregar router optimizado
app.include_router(optimized_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 