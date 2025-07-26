"""
Celery configuration for the EDP MVP application.
"""
import os
from celery import Celery

def create_celery():
    """Create Celery instance with better error handling for production."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Test Redis connection
    try:
        import redis
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis conectado correctamente")
    except Exception as e:
        print(f"⚠️ Redis no disponible para cache: {e}")
        # En producción sin Redis, usar un broker en memoria (no recomendado para producción real)
        # Render debería proporcionar Redis
        
    return Celery(
        __name__,
        broker=redis_url,
        backend=redis_url,
    )

# Create the Celery instance
celery = create_celery()

# Configure task imports
celery.conf.imports = [
    'edp_mvp.app.tasks.metrics',
    'edp_mvp.app.tasks.email_tasks',
]

# Configure Celery settings
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    worker_send_task_events=False,
    worker_enable_remote_control=False,
    task_events=False,
    event_queue_expires=60
)

# Beat schedule for periodic tasks
celery.conf.beat_schedule = {
    "refresh-kpis": {
        "task": "edp_mvp.app.tasks.metrics.refresh_executive_kpis",
        "schedule": 600,  # Every 10 minutes
    },
    "refresh-kanban": {
        "task": "edp_mvp.app.tasks.metrics.refresh_kanban_metrics",
        "schedule": 300,  # Every 5 minutes
    },
    "refresh-cashflow": {
        "task": "edp_mvp.app.tasks.metrics.refresh_cashflow",
        "schedule": 3600,  # Every hour
    },
    "refresh-global-analytics": {
        "task": "edp_mvp.app.tasks.metrics.refresh_global_analytics",
        "schedule": 900,  # Every 15 minutes
    },
    "precompute-dashboards": {
        "task": "edp_mvp.app.tasks.metrics.precompute_dashboard_variants",
        "schedule": 1800,  # Every 30 minutes
    },
    "cleanup-cache": {
        "task": "edp_mvp.app.tasks.metrics.cleanup_stale_cache", 
        "schedule": 3600,  # Every hour
    },
    # Email notification tasks (TESTING MODE - 60 seconds)
    "send-critical-alerts": {
        "task": "edp_mvp.app.tasks.email_tasks.send_critical_edp_alerts",
        "schedule": 10,  # Every 60 seconds for testing
    },
    "send-payment-reminders": {
        "task": "edp_mvp.app.tasks.email_tasks.send_payment_reminders",
        "schedule": 15,  # Every 60 seconds for testing
    },
    "send-weekly-summary": {
        "task": "edp_mvp.app.tasks.email_tasks.send_weekly_summary",
        "schedule": 15,  # Every 60 seconds for testing
    },
}

if __name__ == '__main__':
    celery.start() 