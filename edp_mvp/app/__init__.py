from flask import Flask
from .config import get_config
from flask_login import LoginManager
from .extensions import socketio, login_manager
import os

try:
    from werkzeug.middleware.profiler import ProfilerMiddleware
except Exception:  # pragma: no cover - optional dependency
    ProfilerMiddleware = None


def create_app():
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)

    login_manager.init_app(app)
    socketio.init_app(app)

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

    # Keep old imports as fallback during migration (comment out when fully migrated)
    # from .dashboard.controller import controller_bp
    # from .dashboard.manager import manager_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(edp_bp, url_prefix="/edp")

    # Register main blueprint (landing page)
    app.register_blueprint(main_bp)

    # Register new refactored controllers
    app.register_blueprint(controller_controller_bp)
    app.register_blueprint(manager_controller_bp)
    app.register_blueprint(edp_controller_bp)

    # Old monolithic controllers (comment out when fully migrated)
    # app.register_blueprint(controller_bp)
    # app.register_blueprint(manager_bp)

    return app
