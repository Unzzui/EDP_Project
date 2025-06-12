from flask import Flask
from .config import get_config
from flask_login import LoginManager
from .extensions import socketio, login_manager, db
from celery import Celery
import os
import logging

# Celery application
celery = Celery(
    __name__,
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

# Configure task imports
celery.conf.imports = [
    'edp_mvp.app.tasks.metrics',
]


def init_celery(app: Flask) -> Celery:
    """Initialize Celery with Flask context."""

    celery.conf.update(app.config)
    celery.conf.broker_connection_retry_on_startup = True
    celery.conf.worker_send_task_events = True
    celery.conf.worker_enable_remote_control = True
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery

try:
    from werkzeug.middleware.profiler import ProfilerMiddleware
except Exception:  # pragma: no cover - optional dependency
    ProfilerMiddleware = None

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)

    # Initialize extensions
    login_manager.init_app(app)
    socketio.init_app(app)
    db.init_app(app)

    if os.getenv("ENABLE_PROFILER") == "1" and ProfilerMiddleware:
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])


    # Usar imports relativos (con punto) o absolutos
    from .auth.routes import auth_bp
    from .edp.routes import edp_bp

    # New refactored controllers using layered architecture
    from .controllers.main_controller import main_bp
    from .controllers.controller_controller import controller_controller_bp
    from .controllers.manager_controller import manager_controller_bp
    from .controllers.edp_controller import edp_controller_bp
    from .controllers.admin_controller import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(edp_bp, url_prefix="/edp")

    # Register main blueprint (landing page)
    app.register_blueprint(main_bp)

    # Register new refactored controllers
    app.register_blueprint(controller_controller_bp)
    app.register_blueprint(manager_controller_bp)
    app.register_blueprint(edp_controller_bp)
    app.register_blueprint(admin_bp)

    # Old monolithic controllers (comment out when fully migrated)
    # app.register_blueprint(controller_bp)
    # app.register_blueprint(manager_bp)

    init_celery(app)
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
    }

    # Import tasks to ensure they are registered with Celery
    from . import tasks
    
    return app
