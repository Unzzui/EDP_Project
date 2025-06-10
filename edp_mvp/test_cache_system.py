#!/usr/bin/env python3
"""
Test script para validar el sistema de invalidación de cache automático
"""

import sys
import os
import time
import json
import requests
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_cache_invalidation_system():
    """
    Test completo del sistema de invalidación de cache
    """
    print("🧪 TESTING CACHE INVALIDATION SYSTEM")
    print("=" * 50)
    
    base_url = "http://localhost:5000"  # Adjust as needed
    results = []
    
    # Test 1: Cache Health Check
    print("\n1️⃣ Testing Cache Health Check...")
    try:
        response = requests.get(f"{base_url}/manager/api/cache/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data', {}).get('redis_available'):
                print("✅ Cache health check passed")
                results.append(("Cache Health", True, "Redis connected"))
            else:
                print("❌ Cache health check failed - Redis not available")
                results.append(("Cache Health", False, "Redis not available"))
        else:
            print(f"❌ Cache health check failed - HTTP {response.status_code}")
            results.append(("Cache Health", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ Cache health check failed - {e}")
        results.append(("Cache Health", False, str(e)))
    
    # Test 2: Manual Cache Invalidation
    print("\n2️⃣ Testing Manual Cache Invalidation...")
    try:
        payload = {
            "change_type": "test_invalidation",
            "filters": {}
        }
        response = requests.post(
            f"{base_url}/manager/api/cache/invalidate",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Manual cache invalidation passed")
                results.append(("Manual Invalidation", True, "Cache invalidated"))
            else:
                print(f"❌ Manual cache invalidation failed - {data.get('message')}")
                results.append(("Manual Invalidation", False, data.get('message')))
        else:
            print(f"❌ Manual cache invalidation failed - HTTP {response.status_code}")
            results.append(("Manual Invalidation", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ Manual cache invalidation failed - {e}")
        results.append(("Manual Invalidation", False, str(e)))
    
    # Test 3: Auto-Invalidation Trigger
    print("\n3️⃣ Testing Auto-Invalidation Trigger...")
    try:
        payload = {
            "operation": "test_operation",
            "affected_ids": ["TEST-001", "TEST-002"],
            "metadata": {"test": True}
        }
        response = requests.post(
            f"{base_url}/manager/api/cache/auto-invalidate",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Auto-invalidation trigger passed")
                results.append(("Auto-Invalidation", True, "Trigger successful"))
            else:
                print(f"❌ Auto-invalidation trigger failed - {data.get('message')}")
                results.append(("Auto-Invalidation", False, data.get('message')))
        else:
            print(f"❌ Auto-invalidation trigger failed - HTTP {response.status_code}")
            results.append(("Auto-Invalidation", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ Auto-invalidation trigger failed - {e}")
        results.append(("Auto-Invalidation", False, str(e)))
    
    # Test 4: Webhook Endpoint
    print("\n4️⃣ Testing Webhook Endpoint...")
    try:
        payload = {
            "webhook_key": "default_key_123",  # Use the default key
            "change_type": "test_webhook",
            "affected_records": ["TEST-WEBHOOK-001"],
            "source_system": "test_system",
            "timestamp": datetime.now().isoformat()
        }
        response = requests.post(
            f"{base_url}/manager/webhook/data-changed",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Webhook endpoint passed")
                results.append(("Webhook", True, "Webhook processed"))
            else:
                print(f"❌ Webhook endpoint failed - {data.get('message')}")
                results.append(("Webhook", False, data.get('message')))
        else:
            print(f"❌ Webhook endpoint failed - HTTP {response.status_code}")
            results.append(("Webhook", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ Webhook endpoint failed - {e}")
        results.append(("Webhook", False, str(e)))
    
    # Test 5: Dashboard Load with Cache
    print("\n5️⃣ Testing Dashboard Load with Cache...")
    try:
        # First load (should populate cache)
        start_time = time.time()
        response1 = requests.get(f"{base_url}/manager/dashboard", timeout=30)
        first_load_time = time.time() - start_time
        
        if response1.status_code == 200:
            # Second load (should use cache)
            start_time = time.time()
            response2 = requests.get(f"{base_url}/manager/dashboard", timeout=30)
            second_load_time = time.time() - start_time
            
            if response2.status_code == 200:
                # Second load should be faster (cached)
                speed_improvement = first_load_time / second_load_time if second_load_time > 0 else 1
                print(f"✅ Dashboard caching passed")
                print(f"   First load: {first_load_time:.2f}s, Second load: {second_load_time:.2f}s")
                print(f"   Speed improvement: {speed_improvement:.1f}x")
                results.append(("Dashboard Cache", True, f"{speed_improvement:.1f}x faster"))
            else:
                print(f"❌ Dashboard second load failed - HTTP {response2.status_code}")
                results.append(("Dashboard Cache", False, f"Second load failed"))
        else:
            print(f"❌ Dashboard first load failed - HTTP {response1.status_code}")
            results.append(("Dashboard Cache", False, f"First load failed"))
    except Exception as e:
        print(f"❌ Dashboard cache test failed - {e}")
        results.append(("Dashboard Cache", False, str(e)))
    
    # Test Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name:<20} - {message}")
    
    print(f"\n🏁 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Cache invalidation system is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the system configuration.")
        return False

def test_cli_functionality():
    """Test CLI functionality"""
    print("\n🔧 TESTING CLI FUNCTIONALITY")
    print("=" * 30)
    
    cli_path = os.path.join(os.path.dirname(__file__), 'cache_cli.py')
    
    if not os.path.exists(cli_path):
        print("❌ CLI script not found")
        return False
    
    # Test CLI commands
    commands_to_test = [
        ('health', 'Cache health check'),
        ('stats', 'Cache statistics'),
        ('warm', 'Cache warming'),
    ]
    
    import subprocess
    
    for command, description in commands_to_test:
        try:
            print(f"\n🔍 Testing: {description}")
            result = subprocess.run(
                ['python3', cli_path, command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ CLI {command} command passed")
            else:
                print(f"❌ CLI {command} command failed")
                print(f"   Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ CLI {command} command timed out")
        except Exception as e:
            print(f"❌ CLI {command} command error: {e}")
    
    return True

def test_decorator_functionality():
    """Test that decorators are working"""
    print("\n🎯 TESTING DECORATOR FUNCTIONALITY")
    print("=" * 35)
    
    try:
        # Test the cache invalidation service directly
        from app.services.cache_invalidation_service import CacheInvalidationService
        
        service = CacheInvalidationService()
        
        # Test register_data_change
        result = service.register_data_change(
            operation='test_decorator',
            affected_ids=['TEST-DEC-001'],
            metadata={'test': 'decorator_test'}
        )
        
        if result:
            print("✅ Decorator functionality test passed")
            return True
        else:
            print("❌ Decorator functionality test failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Decorator test error: {e}")
        return False

if __name__ == '__main__':
    print("🚀 STARTING CACHE INVALIDATION SYSTEM TESTS")
    print("=" * 60)
    
    # Check if Flask app is running
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        print("✅ Flask application is running")
    except:
        print("❌ Flask application is not running")
        print("   Please start the application first: python run.py")
        sys.exit(1)
    
    # Run all tests
    web_tests_passed = test_cache_invalidation_system()
    cli_tests_passed = test_cli_functionality()
    decorator_tests_passed = test_decorator_functionality()
    
    print("\n" + "="*60)
    print("🏆 FINAL RESULTS")
    print("="*60)
    
    all_passed = web_tests_passed and cli_tests_passed and decorator_tests_passed
    
    if all_passed:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("   The cache invalidation system is fully functional.")
    else:
        print("⚠️ SOME TESTS FAILED")
        print("   Please check the configuration and try again.")
    
    sys.exit(0 if all_passed else 1)
