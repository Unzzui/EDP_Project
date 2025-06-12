#!/usr/bin/env python3
"""
Test script para verificar las optimizaciones de cache implementadas
"""

import os
import sys
import time
import requests
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'edp_mvp'))

def test_cache_system():
    """Prueba el sistema de cache mejorado"""
    print("🚀 TESTING OPTIMIZED CACHE SYSTEM")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Verificar que Redis esté funcionando
    print("\n1️⃣ Testing Redis Connection...")
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful")
        
        # Limpiar cache para empezar limpio
        gsheet_keys = r.keys("gsheet:*")
        if gsheet_keys:
            deleted = r.delete(*gsheet_keys)
            print(f"🧹 Cleared {deleted} Google Sheets cache keys")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False
    
    # Test 2: Verificar cache de Google Sheets
    print("\n2️⃣ Testing Google Sheets Cache...")
    try:
        # Simulamos múltiples solicitudes al dashboard que usan read_sheet()
        print("📊 Making first request (should hit Google Sheets API)...")
        start_time = time.time()
        response1 = requests.get(f"{base_url}/manager/dashboard", timeout=30)
        first_load_time = time.time() - start_time
        
        if response1.status_code == 200:
            print(f"✅ First load: {first_load_time:.2f}s")
            
            # Verificar que hay keys en Redis
            gsheet_keys = r.keys("gsheet:*")
            print(f"📊 Google Sheets cache keys created: {len(gsheet_keys)}")
            for key in gsheet_keys[:5]:  # Mostrar solo las primeras 5
                ttl = r.ttl(key.decode('utf-8'))
                print(f"   - {key.decode('utf-8')}: TTL {ttl}s")
            
            # Segunda solicitud (debería usar cache)
            print("\n📊 Making second request (should use cache)...")
            start_time = time.time()
            response2 = requests.get(f"{base_url}/manager/dashboard", timeout=30)
            second_load_time = time.time() - start_time
            
            if response2.status_code == 200:
                print(f"✅ Second load: {second_load_time:.2f}s")
                
                if first_load_time > second_load_time:
                    improvement = ((first_load_time - second_load_time) / first_load_time) * 100
                    print(f"🚀 Performance improvement: {improvement:.1f}%")
                    print(f"🚀 Speed ratio: {first_load_time/second_load_time:.2f}x faster")
                else:
                    print("⚠️ Second load wasn't significantly faster (cache might not be working)")
                
                return True
            else:
                print(f"❌ Second request failed: {response2.status_code}")
                return False
        else:
            print(f"❌ First request failed: {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False

def test_cache_invalidation():
    """Prueba la invalidación de cache"""
    print("\n3️⃣ Testing Cache Invalidation...")
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        
        # Contar keys antes
        before_count = len(r.keys("gsheet:*"))
        print(f"📊 Cache keys before invalidation: {before_count}")
        
        # Simular una actualización que debería limpiar el cache
        from app.utils.gsheet import clear_all_cache
        clear_all_cache()
        
        # Contar keys después
        after_count = len(r.keys("gsheet:*"))
        print(f"📊 Cache keys after invalidation: {after_count}")
        
        if after_count < before_count:
            print(f"✅ Cache invalidation working: {before_count - after_count} keys removed")
            return True
        elif before_count == 0:
            print("✅ Cache was already empty")
            return True
        else:
            print("⚠️ Cache invalidation may not be working properly")
            return False
            
    except Exception as e:
        print(f"❌ Cache invalidation test failed: {e}")
        return False

def test_cache_statistics():
    """Muestra estadísticas del cache"""
    print("\n4️⃣ Cache Statistics...")
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        
        # Estadísticas de Redis
        info = r.info()
        print(f"📊 Redis Memory Used: {info.get('used_memory_human', 'Unknown')}")
        print(f"📊 Total Commands: {info.get('total_commands_processed', 0)}")
        print(f"📊 Keyspace Hits: {info.get('keyspace_hits', 0)}")
        print(f"📊 Keyspace Misses: {info.get('keyspace_misses', 0)}")
        
        # Hit rate
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        if hits + misses > 0:
            hit_rate = (hits / (hits + misses)) * 100
            print(f"📊 Cache Hit Rate: {hit_rate:.1f}%")
        
        # Diferentes tipos de cache
        patterns = {
            "Google Sheets": "gsheet:*",
            "Manager Dashboard": "manager_dashboard:*",
            "KPIs": "kpis:*",
            "Charts": "charts:*"
        }
        
        print("\n📊 Cache Breakdown:")
        for name, pattern in patterns.items():
            count = len(r.keys(pattern))
            print(f"   {name}: {count} keys")
        
        return True
        
    except Exception as e:
        print(f"❌ Statistics failed: {e}")
        return False

def main():
    print("🏥 CACHE OPTIMIZATION TEST SUITE")
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check if Flask app is running
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        print("✅ Flask application is running")
    except:
        print("❌ Flask application is not running")
        print("   Please start the application first: python run.py")
        return False
    
    results = []
    
    # Run tests
    results.append(("Redis Connection", test_cache_system()))
    results.append(("Cache Invalidation", test_cache_invalidation()))
    results.append(("Cache Statistics", test_cache_statistics()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🏁 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All cache optimization tests passed!")
        print("💡 Recommendations:")
        print("   - Monitor Redis memory usage in production")
        print("   - Consider increasing cache TTL for stable data")
        print("   - Implement cache warming for critical paths")
    else:
        print("⚠️ Some tests failed. Check Redis configuration and connections.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
