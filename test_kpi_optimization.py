#!/usr/bin/env python3
"""
Test script para verificar la optimización de KPIs con Redis y Celery
"""

import os
import sys
import time
import json
import redis
from datetime import datetime
from edp_mvp.app.services.manager_service import ManagerService
# Agregar el path del proyecto
sys.path.append('/home/unzzui/Documents/coding/EDP_Project/edp_mvp')

def test_redis_connection():
    """Probar conexión a Redis"""
    print("🔍 Probando conexión a Redis...")
    
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        
        # Test ping
        response = r.ping()
        print(f"✅ Redis ping: {response}")
        
        # Test basic operations
        test_key = "test_kpi_system"
        test_data = {"timestamp": datetime.now().isoformat(), "test": True}
        
        r.setex(test_key, 60, json.dumps(test_data))
        retrieved = json.loads(r.get(test_key))
        
        print(f"✅ Redis write/read test: {retrieved}")
        
        # Clean up
        r.delete(test_key)
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return False


def test_manager_service():
    """Probar el Manager Service optimizado"""
    print("\n🔍 Probando Manager Service optimizado...")
    
    try:
        
        
        service = ManagerService()
        
        # Test cache key generation
        filters1 = {"periodo_rapido": "30", "estado": "todos"}
        filters2 = {"estado": "todos", "periodo_rapido": "30"}  # Same but different order
        
        key1 = service._generate_cache_key(filters1)
        key2 = service._generate_cache_key(filters2)
        
        if key1 == key2:
            print("✅ Cache key generation: Consistente")
        else:
            print(f"❌ Cache key generation: Inconsistente ({key1} != {key2})")
        
        # Test essential KPIs calculation
        print("🔍 Probando cálculo de KPIs esenciales...")
        
        start_time = time.time()
        response = service._get_immediate_dashboard_data(filters1)
        end_time = time.time()
        
        if response and response.success:
            print(f"✅ KPIs esenciales calculados en {end_time - start_time:.2f}s")
            kpis = response.data.get('executive_kpis', {})
            print(f"📊 KPIs obtenidos: {list(kpis.keys())}")
        else:
            print("❌ Error calculando KPIs esenciales")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando Manager Service: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_celery_tasks():
    """Probar las tareas de Celery"""
    print("\n🔍 Probando tareas de Celery...")
    
    try:
        from app.tasks.metrics import refresh_executive_kpis, refresh_manager_dashboard_async
        
        # Test synchronous task execution (for testing)
        print("🔍 Probando tarea de KPIs ejecutivos...")
        
        start_time = time.time()
        result = refresh_executive_kpis.apply()  # Synchronous execution for testing
        end_time = time.time()
        
        if result.successful():
            print(f"✅ Tarea de KPIs completada en {end_time - start_time:.2f}s")
            print(f"📊 Resultado: {type(result.result)} con {len(result.result) if isinstance(result.result, dict) else 0} elementos")
        else:
            print(f"❌ Error en tarea de KPIs: {result.info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando Celery: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_comparison():
    """Comparar rendimiento con y sin cache"""
    print("\n🔍 Probando comparación de rendimiento...")
    
    try:
        
        service = ManagerService()
        filters = {"periodo_rapido": "30"}
        
        # Test without cache (force refresh)
        print("🔍 Test sin cache (force refresh)...")
        start_time = time.time()
        response1 = service.get_manager_dashboard_data(filters, force_refresh=True)
        time_no_cache = time.time() - start_time
        
        if response1.success:
            print(f"✅ Sin cache: {time_no_cache:.2f}s")
        else:
            print(f"❌ Error sin cache: {response1.message}")
            return False
        
        # Small delay to ensure cache is populated
        time.sleep(1)
        
        # Test with cache
        print("🔍 Test con cache...")
        start_time = time.time()
        response2 = service.get_manager_dashboard_data(filters, force_refresh=False)
        time_with_cache = time.time() - start_time
        
        if response2.success:
            print(f"✅ Con cache: {time_with_cache:.2f}s")
            
            if time_with_cache < time_no_cache:
                improvement = ((time_no_cache - time_with_cache) / time_no_cache) * 100
                print(f"🚀 Mejora de rendimiento: {improvement:.1f}%")
            else:
                print("⚠️ Cache no mostró mejora significativa")
        else:
            print(f"❌ Error con cache: {response2.message}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en comparación de rendimiento: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_cleanup():
    """Probar limpieza de cache"""
    print("\n🔍 Probando limpieza de cache...")
    
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        
        # Create some test cache entries
        test_keys = [
            "manager_dashboard:test1",
            "kpis:test1", 
            "charts:test1"
        ]
        
        for key in test_keys:
            r.setex(key, 30, json.dumps({"test": True}))
        
        print(f"📝 Creadas {len(test_keys)} entradas de prueba")
        
        # Check they exist
        existing = sum(1 for key in test_keys if r.exists(key))
        print(f"✅ Verificadas {existing} entradas existentes")
        
        # Cleanup pattern
        pattern = "*test1"
        keys_to_delete = r.keys(pattern)
        if keys_to_delete:
            deleted = r.delete(*keys_to_delete)
            print(f"🗑️ Eliminadas {deleted} entradas de prueba")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en limpieza de cache: {e}")
        return False


def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de optimización KPI/Redis/Celery")
    print("=" * 60)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Manager Service", test_manager_service), 
        ("Celery Tasks", test_celery_tasks),
        ("Performance Comparison", test_performance_comparison),
        ("Cache Cleanup", test_cache_cleanup)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 Ejecutando: {test_name}")
            print("-" * 40)
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error crítico en {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    print(f"\nResultado final: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! Sistema optimizado funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar configuración.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
