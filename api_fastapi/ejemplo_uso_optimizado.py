#!/usr/bin/env python3
"""
Ejemplo de uso de los endpoints optimizados del dashboard
Muestra las diferentes estrategias de cache y performance
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime
from typing import Dict, Any

class DashboardOptimizedClient:
    """Cliente para interactuar con los endpoints optimizados"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_quick_kpis(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """🚀 KPIs rápidos - < 500ms"""
        params = filters or {}
        async with self.session.get(
            f"{self.base_url}/api/v1/dashboard/quick-kpis",
            params=params
        ) as response:
            return await response.json()
    
    async def get_dashboard_summary(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """📊 Resumen ejecutivo - < 1s"""
        params = filters or {}
        async with self.session.get(
            f"{self.base_url}/api/v1/dashboard/summary",
            params=params
        ) as response:
            return await response.json()
    
    async def get_complete_dashboard(self, filters: Dict[str, Any] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """🔄 Dashboard completo - Background processing"""
        params = filters or {}
        if force_refresh:
            params["force_refresh"] = "true"
        
        async with self.session.get(
            f"{self.base_url}/api/v1/dashboard/complete",
            params=params
        ) as response:
            result = await response.json()
            
            # Si está procesando en background, esperar hasta que termine
            if result.get("status") == "processing":
                cache_key = result.get("cache_key", "").split(":")[-1]
                return await self._wait_for_completion(cache_key)
            
            return result
    
    async def _wait_for_completion(self, cache_key: str, max_wait: int = 120) -> Dict[str, Any]:
        """Esperar a que termine el procesamiento background"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            async with self.session.get(
                f"{self.base_url}/api/v1/dashboard/status/{cache_key}"
            ) as response:
                status_result = await response.json()
                
                if status_result.get("status") == "completed":
                    return {
                        "status": "completed",
                        "data": status_result.get("data"),
                        "wait_time": round(time.time() - start_time, 2)
                    }
                elif status_result.get("status") == "failed":
                    return status_result
                
                # Esperar antes del siguiente check
                await asyncio.sleep(5)
        
        return {
            "status": "timeout",
            "message": f"Procesamiento no completado en {max_wait}s"
        }
    
    async def get_charts_data(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """📈 Solo datos de gráficos"""
        params = filters or {}
        async with self.session.get(
            f"{self.base_url}/api/v1/dashboard/charts",
            params=params
        ) as response:
            return await response.json()
    
    async def get_health_status(self) -> Dict[str, Any]:
        """❤️ Estado del sistema"""
        async with self.session.get(
            f"{self.base_url}/api/v1/dashboard/health"
        ) as response:
            return await response.json()
    
    async def clear_cache(self, cache_type: str = "all") -> Dict[str, Any]:
        """🗑️ Limpiar cache"""
        async with self.session.delete(
            f"{self.base_url}/api/v1/dashboard/cache",
            params={"cache_type": cache_type}
        ) as response:
            return await response.json()

async def demo_performance_comparison():
    """🎯 DEMO: Comparación de performance"""
    print("🚀 DEMO: Comparación de Performance - Dashboard Optimizado")
    print("=" * 60)
    
    async with DashboardOptimizedClient() as client:
        
        # Test de KPIs rápidos
        print("\n📊 1. KPIs RÁPIDOS (< 500ms)")
        print("-" * 30)
        
        filters = {"mes": "2024-01", "cliente": "Cliente A"}
        
        for i in range(3):
            start_time = time.time()
            result = await client.get_quick_kpis(filters)
            response_time = round(time.time() - start_time, 3)
            
            cache_status = "🟢 CACHE HIT" if result.get("from_cache") else "🔴 CACHE MISS"
            calc_time = result.get("calculation_time", 0)
            
            print(f"  Llamada {i+1}: {response_time}s total | {calc_time}s cálculo | {cache_status}")
            
            if i == 0:
                print(f"    📈 Total EDPs: {result.get('total_edps', 0)}")
                print(f"    💰 Monto Total: ${result.get('monto_total', 0):,.0f}")

async def demo_cache_strategies():
    """
    🎯 DEMO: Estrategias de cache y su impacto
    """
    print("\n\n🔄 DEMO: Estrategias de Cache")
    print("=" * 60)
    
    async with DashboardOptimizedClient() as client:
        
        # Limpiar cache para empezar limpio
        print("🗑️ Limpiando cache...")
        await client.clear_cache("all")
        
        filters = {"mes": "2024-02", "jefe_proyecto": "Diego Bravo"}
        
        # Primera llamada (cache miss)
        print("\n1️⃣ Primera llamada (sin cache)")
        start_time = time.time()
        result1 = await client.get_quick_kpis(filters)
        time1 = round(time.time() - start_time, 3)
        print(f"   Tiempo: {time1}s | Cache: {'HIT' if result1.get('from_cache') else 'MISS'}")
        
        # Segunda llamada inmediata (cache hit)
        print("\n2️⃣ Segunda llamada (con cache)")
        start_time = time.time()
        result2 = await client.get_quick_kpis(filters)
        time2 = round(time.time() - start_time, 3)
        print(f"   Tiempo: {time2}s | Cache: {'HIT' if result2.get('from_cache') else 'MISS'}")
        
        # Mejora de performance
        if time1 > 0 and time2 > 0:
            improvement = round(((time1 - time2) / time1) * 100, 1)
            print(f"   🚀 Mejora: {improvement}% más rápido con cache")
        
        # Test con diferentes filtros (nuevos cache misses)
        print("\n3️⃣ Diferentes filtros (nuevos cache)")
        test_filters = [
            {"mes": "2024-03"},
            {"cliente": "Cliente B"},
            {"estado": "pagado"}
        ]
        
        for i, test_filter in enumerate(test_filters, 1):
            start_time = time.time()
            result = await client.get_quick_kpis(test_filter)
            response_time = round(time.time() - start_time, 3)
            cache_status = "HIT" if result.get("from_cache") else "MISS"
            print(f"   Filtro {i}: {response_time}s | Cache: {cache_status}")

async def demo_real_world_usage():
    """
    🎯 DEMO: Uso en el mundo real - Dashboard interactivo
    """
    print("\n\n🌍 DEMO: Uso Real - Dashboard Interactivo")
    print("=" * 60)
    
    async with DashboardOptimizedClient() as client:
        
        # Simular carga inicial de dashboard
        print("🏠 Carga inicial del dashboard...")
        
        # Cargar datos básicos en paralelo
        tasks = [
            client.get_quick_kpis(),
            client.get_charts_data(),
            client.get_health_status()
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = round(time.time() - start_time, 3)
        
        print(f"   ✅ Dashboard básico cargado en {total_time}s")
        print(f"   📊 Componentes: KPIs, Gráficos, Estado del sistema")
        
        # Simular interacción del usuario - cambio de filtros
        print("\n👤 Usuario cambia filtros...")
        
        user_filters = {"mes": "2024-01", "estado": "pendientes"}
        
        start_time = time.time()
        filtered_data = await client.get_quick_kpis(user_filters)
        filter_time = round(time.time() - start_time, 3)
        
        print(f"   ⚡ Datos filtrados en {filter_time}s")
        print(f"   📈 EDPs pendientes: {filtered_data.get('total_pendientes', 0)}")
        
        # Simular solicitud de reporte completo
        print("\n📋 Usuario solicita reporte completo...")
        
        print("   🔄 Iniciando análisis completo en background...")
        complete_start = time.time()
        
        complete_result = await client.get_complete_dashboard(user_filters)
        complete_time = round(time.time() - complete_start, 3)
        
        if complete_result.get("status") == "completed":
            print(f"   ✅ Reporte completo generado en {complete_time}s")
            
            # Mostrar estadísticas del reporte
            if "data" in complete_result:
                data = complete_result["data"]
                print(f"   📊 Total de registros: {len(data.get('registros', []))}")
                print(f"   💰 Monto total filtrado: ${data.get('total_pagado_filtrado', 0):,.0f}")
                print(f"   ⏱️ DSO filtrado: {data.get('dso_filtrado', 0)} días")
        
        # Mostrar resumen de performance
        print(f"\n📈 RESUMEN DE PERFORMANCE:")
        print(f"   Dashboard inicial: {total_time}s")
        print(f"   Filtros interactivos: {filter_time}s") 
        print(f"   Reporte completo: {complete_time}s")
        print(f"   🎯 Total experiencia: {round(total_time + filter_time + complete_time, 2)}s")

if __name__ == "__main__":
    asyncio.run(demo_performance_comparison()) 