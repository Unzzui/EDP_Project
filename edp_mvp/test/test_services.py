#!/usr/bin/env python3
"""
Service Import Test - Test if all services can be imported and instantiated
"""

def test_service_imports():
    """Test importing and instantiating all services"""
    print("🚀 Testing service imports...")
    
    try:
        # Test analytics service
        print("1. Testing AnalyticsService...")
        from edp_mvp.app.services.analytics_service import AnalyticsService
        analytics = AnalyticsService()
        print("   ✅ AnalyticsService OK")
        
        # Test cashflow service
        print("2. Testing CashFlowService...")
        from edp_mvp.app.services.cashflow_service import CashFlowService
        cashflow = CashFlowService()
        print("   ✅ CashFlowService OK")
        
        # Test other services
        print("3. Testing other services...")
        from edp_mvp.app.services.kanban_service import KanbanService
        from edp_mvp.app.services.edp_service import EDPService
        from edp_mvp.app.services.controller_service import DashboardService
        from edp_mvp.app.services.kpi_service import KPIService
        from edp_mvp.app.services.manager_service import ManagerService
        
        kanban = KanbanService()
        edp = EDPService()
        dashboard = DashboardService()
        kpi = KPIService()
        manager = ManagerService()
        print("   ✅ All other services OK")
        
        # Test controllers
        print("4. Testing controllers...")
        from edp_mvp.app.controllers.controller_controller import controller_controller_bp
        from edp_mvp.app.controllers.manager_controller import manager_controller_bp
        from edp_mvp.app.controllers.edp_controller import edp_controller_bp
        print("   ✅ All controllers OK")
        
        # Test app creation
        print("5. Testing Flask app creation...")
        from edp_mvp.app import create_app
        app = create_app()
        print("   ✅ Flask app creation OK")
        
        print("\n🎉 All tests passed! Architecture is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_service_imports()
    exit(0 if success else 1)
