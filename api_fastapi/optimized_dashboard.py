#!/usr/bin/env python3
"""
Dashboard optimizado para FastAPI con cache inteligente y cálculos eficientes
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from functools import lru_cache
from fastapi import FastAPI, BackgroundTasks, Query, HTTPException
from fastapi.responses import StreamingResponse
import redis.asyncio as redis

# Cache configuration
CACHE_TTL = {
    "dashboard_summary": 300,    # 5 minutos - métricas principales
    "detailed_metrics": 600,     # 10 minutos - métricas detalladas  
    "heavy_reports": 1800,       # 30 minutos - reportes pesados
    "real_time": 30              # 30 segundos - datos en tiempo real
}

class OptimizedDashboardService:
    """Servicio de dashboard optimizado para FastAPI"""
    
    def __init__(self):
        self.redis_client = None
        self._memory_cache = {}
        self._cache_timestamps = {}
        
    async def init_redis(self):
        """Inicializar conexión Redis (opcional)"""
        try:
            self.redis_client = redis.from_url("redis://localhost:6379")
            await self.redis_client.ping()
            print("✅ Redis conectado para cache")
        except Exception as e:
            print(f"⚠️ Redis no disponible, usando cache en memoria: {e}")
    
    async def get_cache(self, key: str, ttl: int = 300) -> Optional[Any]:
        """Obtener datos del cache (Redis + memoria)"""
        
        # 1. Intentar Redis primero
        if self.redis_client:
            try:
                cached = await self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
        
        # 2. Cache en memoria como fallback
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
                await self.redis_client.setex(key, ttl, json.dumps(data))
            except Exception:
                pass
        
        # Memoria
        self._memory_cache[key] = data
        self._cache_timestamps[key] = time.time()
    
    async def get_dashboard_summary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Métricas principales del dashboard - RÁPIDO
        Solo los KPIs más importantes, actualizados frecuentemente
        """
        cache_key = "dashboard:summary"
        
        if not force_refresh:
            cached = await self.get_cache(cache_key, CACHE_TTL["dashboard_summary"])
            if cached:
                cached["from_cache"] = True
                return cached
        
        # Cálculo ligero - solo métricas esenciales
        start_time = time.time()
        
        # Simular obtención de datos (reemplazar con tu lógica real)
        total_edps = await self._get_edp_count()
        pending_edps = await self._get_pending_edp_count()
        total_amount = await self._get_total_amount()
        
        summary = {
            "kpis": {
                "total_edps": total_edps,
                "pending_edps": pending_edps,
                "approval_rate": round((total_edps - pending_edps) / total_edps * 100, 1) if total_edps > 0 else 0,
                "total_amount": total_amount
            },
            "alerts": await self._get_critical_alerts(),
            "last_updated": datetime.now().isoformat(),
            "calculation_time": round(time.time() - start_time, 3),
            "from_cache": False
        }
        
        await self.set_cache(cache_key, summary, CACHE_TTL["dashboard_summary"])
        return summary
    
    async def get_detailed_metrics(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Métricas detalladas - MEDIO
        Gráficos, distribuciones, tendencias
        """
        cache_key = "dashboard:detailed"
        
        if not force_refresh:
            cached = await self.get_cache(cache_key, CACHE_TTL["detailed_metrics"])
            if cached:
                cached["from_cache"] = True
                return cached
        
        start_time = time.time()
        
        # Cálculos más complejos pero no excesivos
        detailed = {
            "charts": {
                "edp_by_status": await self._get_edp_by_status(),
                "monthly_trend": await self._get_monthly_trend(),
                "client_distribution": await self._get_client_distribution()
            },
            "tables": {
                "top_projects": await self._get_top_projects(limit=10),
                "recent_activity": await self._get_recent_activity(limit=20)
            },
            "last_updated": datetime.now().isoformat(),
            "calculation_time": round(time.time() - start_time, 3),
            "from_cache": False
        }
        
        await self.set_cache(cache_key, detailed, CACHE_TTL["detailed_metrics"])
        return detailed
    
    async def generate_heavy_report(self, task_id: str):
        """
        Reporte pesado en background - LENTO
        Análisis completo, exportes, cálculos complejos
        """
        try:
            start_time = time.time()
            
            # Simular cálculo pesado
            await asyncio.sleep(2)  # Simular procesamiento
            
            report = {
                "full_analysis": await self._get_full_analysis(),
                "detailed_breakdown": await self._get_detailed_breakdown(),
                "predictions": await self._get_predictions(),
                "export_data": await self._get_export_data(),
                "generated_at": datetime.now().isoformat(),
                "calculation_time": round(time.time() - start_time, 3)
            }
            
            # Guardar resultado
            await self.set_cache(f"report:{task_id}", report, CACHE_TTL["heavy_reports"])
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "generated_at": datetime.now().isoformat(),
                "status": "failed"
            }
            await self.set_cache(f"report:{task_id}", error_result, 300)
    
    # Métodos auxiliares (implementar según tus datos reales)
    async def _get_edp_count(self) -> int:
        """Contar EDPs total - consulta rápida"""
        # Implementar con tu lógica real
        await asyncio.sleep(0.1)  # Simular consulta DB
        return 150
    
    async def _get_pending_edp_count(self) -> int:
        """Contar EDPs pendientes - consulta rápida"""
        await asyncio.sleep(0.1)
        return 45
    
    async def _get_total_amount(self) -> float:
        """Monto total - consulta rápida"""
        await asyncio.sleep(0.1)
        return 2500000.0
    
    async def _get_critical_alerts(self) -> List[Dict]:
        """Alertas críticas - consulta rápida"""
        return [
            {"type": "warning", "message": "15 EDPs vencidos", "priority": "high"},
            {"type": "info", "message": "5 nuevos proyectos", "priority": "low"}
        ]
    
    async def _get_edp_by_status(self) -> Dict:
        """Distribución por estado - consulta media"""
        await asyncio.sleep(0.3)
        return {
            "aprobado": 60,
            "pendiente": 45,
            "rechazado": 15,
            "en_revision": 30
        }
    
    async def _get_monthly_trend(self) -> List[Dict]:
        """Tendencia mensual - consulta media"""
        await asyncio.sleep(0.5)
        return [
            {"month": "2024-10", "count": 25, "amount": 500000},
            {"month": "2024-11", "count": 30, "amount": 600000},
            {"month": "2024-12", "count": 35, "amount": 700000}
        ]
    
    async def _get_client_distribution(self) -> Dict:
        """Distribución por cliente - consulta media"""
        await asyncio.sleep(0.2)
        return {
            "Arauco": 40,
            "CMPC": 35,
            "Otros": 75
        }
    
    async def _get_top_projects(self, limit: int = 10) -> List[Dict]:
        """Top proyectos - consulta media"""
        await asyncio.sleep(0.4)
        return [
            {"name": "Proyecto A", "amount": 500000, "status": "active"},
            {"name": "Proyecto B", "amount": 300000, "status": "pending"}
        ][:limit]
    
    async def _get_recent_activity(self, limit: int = 20) -> List[Dict]:
        """Actividad reciente - consulta media"""
        await asyncio.sleep(0.3)
        return [
            {"action": "EDP creado", "project": "OT7286", "time": "2024-12-18T10:30:00"},
            {"action": "EDP aprobado", "project": "OT7287", "time": "2024-12-18T09:15:00"}
        ][:limit]
    
    async def _get_full_analysis(self) -> Dict:
        """Análisis completo - consulta pesada"""
        await asyncio.sleep(2.0)
        return {"detailed_stats": "complex_analysis_result"}
    
    async def _get_detailed_breakdown(self) -> Dict:
        """Desglose detallado - consulta pesada"""
        await asyncio.sleep(1.5)
        return {"breakdown": "detailed_breakdown_result"}
    
    async def _get_predictions(self) -> Dict:
        """Predicciones - consulta pesada"""
        await asyncio.sleep(1.0)
        return {"predictions": "ml_predictions_result"}
    
    async def _get_export_data(self) -> List[Dict]:
        """Datos para exportar - consulta pesada"""
        await asyncio.sleep(0.8)
        return [{"export": "data"}] * 1000  # Simular datos grandes

# Ejemplo de uso con FastAPI
app = FastAPI(title="Dashboard Optimizado")
dashboard_service = OptimizedDashboardService()

@app.on_event("startup")
async def startup():
    await dashboard_service.init_redis()

@app.get("/api/v1/dashboard/summary")
async def get_dashboard_summary(force_refresh: bool = Query(False)):
    """
    Métricas principales - RÁPIDO (< 1 segundo)
    Ideal para widgets, indicadores principales
    """
    return await dashboard_service.get_dashboard_summary(force_refresh)

@app.get("/api/v1/dashboard/detailed")
async def get_detailed_metrics(force_refresh: bool = Query(False)):
    """
    Métricas detalladas - MEDIO (1-3 segundos)
    Ideal para gráficos, tablas, análisis
    """
    return await dashboard_service.get_detailed_metrics(force_refresh)

@app.post("/api/v1/dashboard/heavy-report")
async def generate_heavy_report(background_tasks: BackgroundTasks):
    """
    Generar reporte pesado - BACKGROUND
    Ideal para exportes, análisis complejos
    """
    import uuid
    task_id = str(uuid.uuid4())
    
    background_tasks.add_task(dashboard_service.generate_heavy_report, task_id)
    
    return {
        "task_id": task_id,
        "status": "processing",
        "check_url": f"/api/v1/dashboard/report-status/{task_id}"
    }

@app.get("/api/v1/dashboard/report-status/{task_id}")
async def check_report_status(task_id: str):
    """Verificar estado del reporte pesado"""
    result = await dashboard_service.get_cache(f"report:{task_id}", CACHE_TTL["heavy_reports"])
    
    if result:
        if "error" in result:
            return {"status": "failed", "error": result["error"]}
        return {"status": "completed", "data": result}
    
    return {"status": "processing"}

@app.get("/api/v1/dashboard/stream")
async def stream_real_time_data():
    """
    Stream de datos en tiempo real - STREAMING
    Ideal para dashboards en vivo
    """
    async def generate_real_time():
        for i in range(10):  # Simular 10 actualizaciones
            data = {
                "timestamp": datetime.now().isoformat(),
                "edps_count": 150 + i,
                "pending_count": 45 - i,
                "update_number": i + 1
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(1)  # Actualizar cada segundo
    
    return StreamingResponse(generate_real_time(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 