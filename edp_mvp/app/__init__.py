from flask import Flask
from .config import get_config
from flask_login import LoginManager
from .extensions import socketio, login_manager, db, mail
from celery import Celery
import os
import logging
import json
import numpy as np
import pandas as pd
from typing import Any



logger = logging.getLogger(__name__)


# Import Celery instance from celery.py to avoid conflicts
from .celery import celery


def init_celery(app: Flask) -> Celery:
    """Initialize Celery with Flask context."""

    celery.conf.update(app.config)
    celery.conf.broker_connection_retry_on_startup = True
    celery.conf.worker_send_task_events = False  # Deshabilitar eventos problemáticos
    celery.conf.worker_enable_remote_control = False  # Deshabilitar control remoto problemático
    celery.conf.task_events = False  # Deshabilitar eventos de tareas
    celery.conf.event_queue_expires = 60  # Expirar eventos rápidamente
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)
        
        def on_failure(self, exc, task_id, args, kwargs, einfo):
            """Handle task failures."""
            logger.error(f"❌ Task {task_id} failed: {exc}")
            super().on_failure(exc, task_id, args, kwargs, einfo)
        
        def after_return(self, status, retval, task_id, args, kwargs, einfo):
            """Clean up after task completion."""
            super().after_return(status, retval, task_id, args, kwargs, einfo)

    celery.Task = ContextTask
    return celery

try:
    from werkzeug.middleware.profiler import ProfilerMiddleware
except Exception:  # pragma: no cover - optional dependency
    ProfilerMiddleware = None

# 🔧 PATCH GLOBAL: Solución definitiva para "Object of type int64 is not JSON serializable"
import json
import numpy as np
import pandas as pd
from typing import Any

# Patch global de json.dumps usando la función centralizada
original_json_dumps = json.dumps

def patched_json_dumps(obj, *args, **kwargs):
    """Versión patcheada de json.dumps que maneja tipos numpy automáticamente"""
    try:
        return original_json_dumps(obj, *args, **kwargs)
    except TypeError as e:
        error_str = str(e)
        if any(error_type in error_str for error_type in ["int64", "float64", "bool_", "Timestamp", "DictToObject"]):
            # Usar la función centralizada de conversión
            from .utils.type_conversion import convert_numpy_types_for_json
            converted_obj = convert_numpy_types_for_json(obj)
            return original_json_dumps(converted_obj, *args, **kwargs)
        else:
            raise e

# Aplicar el patch globalmente
json.dumps = patched_json_dumps

# También patchear jsonify de Flask
from flask import json as flask_json

original_flask_dumps = flask_json.dumps

def patched_flask_dumps(obj, *args, **kwargs):
    """Versión patcheada de Flask json.dumps"""
    try:
        return original_flask_dumps(obj, *args, **kwargs)
    except TypeError as e:
        error_str = str(e)
        if any(error_type in error_str for error_type in ["int64", "float64", "bool_", "Timestamp", "DictToObject"]):
            # Usar la función centralizada de conversión
            from .utils.type_conversion import convert_numpy_types_for_json
            converted_obj = convert_numpy_types_for_json(obj)
            return original_flask_dumps(converted_obj, *args, **kwargs)
        else:
            raise e

flask_json.dumps = patched_flask_dumps

print("🔧 JSON SERIALIZATION PATCH APLICADO GLOBALMENTE")
print("   - json.dumps patcheado")
print("   - flask.json.dumps patcheado") 
print("   - Conversión automática de tipos numpy/pandas activada")
print("   - Montos convertidos específicamente a float para BD")

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)

    # Initialize extensions
    login_manager.init_app(app)
    socketio.init_app(app)
    db.init_app(app)
    mail.init_app(app)

    if os.getenv("ENABLE_PROFILER") == "1" and ProfilerMiddleware:
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

    # Register authentication context processor
    from .utils.auth_utils import inject_user_context
    app.context_processor(inject_user_context)

    # Usar imports relativos (con punto) o absolutos
    from .auth.routes import auth_bp
    from .edp.routes import edp_bp

    # New refactored routes using layered architecture
    from .routes.landing import landing_bp
    from .routes.dashboard import dashboard_bp
    from .routes.management import management_bp
    from .routes.edp import edp_management_bp
    from .routes.admin import admin_bp
    from .routes.projects import projects_bp
    from .routes.control_panel import control_panel_bp
    from .routes.analytics import analytics_bp
    from .routes.edp_upload import edp_upload_bp
    from .routes.email_notifications import email_bp
    from .routes.alert_routes import alert_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(edp_bp, url_prefix="/edp")

    # Register main blueprint (landing page)
    app.register_blueprint(landing_bp)

    # Register new refactored routes
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(management_bp)
    app.register_blueprint(edp_management_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(control_panel_bp)
    app.register_blueprint(analytics_bp)  # ✨ Analytics and insights
    app.register_blueprint(edp_upload_bp)  # 📋 Sistema de carga de EDPs
    app.register_blueprint(email_bp)  # 📧 Sistema de notificaciones por email
    app.register_blueprint(alert_bp)  # 🚨 Sistema de alertas progresivas

    # Old monolithic controllers (comment out when fully migrated)
    # app.register_blueprint(controller_bp)
    # app.register_blueprint(manager_bp)

    init_celery(app)
    # Beat schedule configuration moved to celery.py to avoid conflicts

    # Import tasks to ensure they are registered with Celery
    from . import tasks
    
    return app
