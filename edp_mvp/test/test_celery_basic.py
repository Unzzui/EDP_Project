#!/usr/bin/env python3
"""
Simple Celery test without circular imports
"""

import os
import sys
from celery import Celery

# Configure Celery directly
celery_app = Celery(
    'test_tasks',
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

@celery_app.task
def test_task():
    return "Hello from Celery!"

if __name__ == "__main__":
    print("🔍 Probando Celery básico...")
    
    # Test task registration
    print(f"📋 Tareas registradas: {list(celery_app.tasks.keys())}")
    
    # Test task execution
    try:
        result = test_task.delay()
        print(f"✅ Tarea creada: {result.id}")
        print(f"📊 Estado: {result.state}")
    except Exception as e:
        print(f"❌ Error: {e}")
