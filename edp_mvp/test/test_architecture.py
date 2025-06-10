#!/usr/bin/env python3
"""
Test script to validate the new layered architecture.
This script tests if all the new controllers and services can be imported correctly.
"""

import sys
import os
import traceback

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all new architecture components can be imported."""
    tests = []
    
    # Test service imports
    try:
        from app.services.manager_service import ManagerService
        tests.append("✅ ManagerService imported successfully")
    except Exception as e:
        tests.append(f"❌ ManagerService import failed: {e}")
    
    try:
        from app.services.cashflow_service import CashFlowService
        tests.append("✅ CashFlowService imported successfully")
    except Exception as e:
        tests.append(f"❌ CashFlowService import failed: {e}")
    
    try:
        from app.services.analytics_service import AnalyticsService
        tests.append("✅ AnalyticsService imported successfully")
    except Exception as e:
        tests.append(f"❌ AnalyticsService import failed: {e}")
    
    # Test controller imports
    try:
        from app.controllers.manager_controller import manager_controller_bp
        tests.append("✅ Manager controller imported successfully")
    except Exception as e:
        tests.append(f"❌ Manager controller import failed: {e}")
        traceback.print_exc()
    
    try:
        from app.controllers.controller_controller import controller_controller_bp
        tests.append("✅ Controller controller imported successfully")
    except Exception as e:
        tests.append(f"❌ Controller controller import failed: {e}")
    
    # Test Flask app creation
    try:
        from app import create_app
        app = create_app()
        tests.append("✅ Flask application created successfully")
    except Exception as e:
        tests.append(f"❌ Flask app creation failed: {e}")
        traceback.print_exc()
    
    return tests

def main():
    """Run all tests and display results."""
    print("🚀 Testing New Layered Architecture")
    print("=" * 50)
    
    test_results = test_imports()
    
    for result in test_results:
        print(result)
    
    print("=" * 50)
    
    success_count = len([r for r in test_results if "✅" in r])
    total_count = len(test_results)
    
    print(f"📊 Results: {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        print("🎉 All tests passed! Architecture is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
