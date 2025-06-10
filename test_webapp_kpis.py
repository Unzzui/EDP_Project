#!/usr/bin/env python3
"""
Test webapp endpoints to verify KPI calculation
"""

import sys
import os
sys.path.insert(0, '/home/unzzui/Documents/coding/EDP_Project')

def test_webapp_kpis():
    print("🔍 Probando endpoints de la aplicación web...")
    
    try:
        # Import Flask app
        from edp_mvp.app import create_app
        print("✅ Flask app importado")
        
        # Create app instance
        app = create_app()
        print("✅ App instance creada")
        
        # Test with app context
        with app.app_context():
            print("🔍 Probando Manager Service dentro del contexto de Flask...")
            
            from edp_mvp.app.services.manager_service import ManagerService
            service = ManagerService()
            
            print("🔍 Llamando get_manager_dashboard_data()...")
            result = service.get_manager_dashboard_data()
            
            print(f"📊 Success: {result.success}")
            
            if result.success and result.data:
                kpis = result.data.get('executive_kpis', {})
                print(f"✅ KPIs encontrados: {len(kpis)} elementos")
                
                # Check essential KPIs
                essential_kpis = ['total_edps', 'monto_total_formatted', 'edps_pagados']
                for kpi in essential_kpis:
                    if kpi in kpis:
                        print(f"  ✅ {kpi}: {kpis[kpi]}")
                    else:
                        print(f"  ❌ {kpi}: MISSING")
                
                return True
            else:
                print(f"❌ Error: {result.message if hasattr(result, 'message') else 'Unknown error'}")
                return False
    
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_webapp_kpis()
