#!/usr/bin/env python3
"""
Test task registration
"""

import sys
import os
sys.path.insert(0, '/home/unzzui/Documents/coding/EDP_Project')

def test_task_imports():
    print("🔍 Probando importación de tareas...")
    
    try:
        # Import Celery app
        from edp_mvp.app import celery
        print("✅ Celery app importado")
        
        # Import tasks module
        from edp_mvp.app.tasks import metrics
        print("✅ Módulo metrics importado")
        
        # Import specific tasks
        from edp_mvp.app.tasks.metrics import refresh_manager_dashboard_async, refresh_executive_kpis
        print("✅ Tareas específicas importadas")
        
        # Check registered tasks
        print(f"\n📋 Tareas registradas en Celery ({len(celery.tasks)} total):")
        for task_name in sorted(celery.tasks.keys()):
            if 'refresh' in task_name.lower() or 'metrics' in task_name.lower():
                print(f"  ✅ {task_name}")
        
        # Test creating a task
        print(f"\n🧪 Probando creación de tarea...")
        task = refresh_manager_dashboard_async.delay({})
        print(f"✅ Tarea creada: {task.id}")
        print(f"📊 Estado: {task.state}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_task_imports()
