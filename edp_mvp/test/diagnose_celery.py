#!/usr/bin/env python3
"""
Script to diagnose Celery task registration issues
"""

import os
import sys
sys.path.insert(0, '/home/unzzui/Documents/coding/EDP_Project')

def diagnose_celery():
    print("🔍 Diagnosticando configuración de Celery...")
    
    try:
        # Import the Celery app
        from edp_mvp.app import celery
        
        print(f"✅ Celery app importado correctamente")
        print(f"📊 Broker: {celery.conf.broker_url}")
        print(f"📊 Backend: {celery.conf.result_backend}")
        
        # Check registered tasks
        print("\n📋 Tareas registradas:")
        registered_tasks = list(celery.tasks.keys())
        print(f"Total tareas: {len(registered_tasks)}")
        
        for task in registered_tasks:
            print(f"  - {task}")
        
        # Try to import the metrics module directly
        print("\n🔍 Importando módulo de métricas...")
        try:
            from edp_mvp.app.tasks.metrics import refresh_manager_dashboard_async
            print("✅ Tarea refresh_manager_dashboard_async importada correctamente")
            
            # Check if the task is registered
            task_name = 'edp_mvp.app.tasks.metrics.refresh_manager_dashboard_async'
            if task_name in celery.tasks:
                print(f"✅ Tarea '{task_name}' está registrada en Celery")
            else:
                print(f"❌ Tarea '{task_name}' NO está registrada en Celery")
                print("📋 Tareas disponibles que contienen 'refresh':")
                for task in registered_tasks:
                    if 'refresh' in task.lower():
                        print(f"  - {task}")
        
        except ImportError as e:
            print(f"❌ Error importando métricas: {e}")
        
        # Test task creation
        print("\n🧪 Probando creación de tarea...")
        try:
            # Create a simple task for testing
            task = refresh_manager_dashboard_async.delay({})
            print(f"✅ Tarea creada con ID: {task.id}")
            print(f"📊 Estado inicial: {task.state}")
            
            # Wait a bit and check status
            import time
            time.sleep(2)
            print(f"📊 Estado después de 2s: {task.state}")
            
        except Exception as e:
            print(f"❌ Error creando tarea: {e}")
    
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_celery()
