from flask import Flask
from .config import Config
from flask_login import LoginManager
from .extensions import socketio, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager.init_app(app)
    socketio.init_app(app)

    # Usar imports relativos (con punto) o absolutos
    from .auth.routes import auth_bp
    from .edp.routes import edp_bp
    
    # New refactored controllers using layered architecture
    from .controllers.controller_controller import controller_controller_bp
    from .controllers.manager_controller import manager_controller_bp
    from .controllers.edp_controller import edp_controller_bp
    
    # Keep old imports as fallback during migration (comment out when fully migrated)
    # from .dashboard.controller import controller_bp
    # from .dashboard.manager import manager_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(edp_bp, url_prefix="/edp")
    
    # Register new refactored controllers
    app.register_blueprint(controller_controller_bp)
    app.register_blueprint(manager_controller_bp)
    app.register_blueprint(edp_controller_bp)
    
    # Old monolithic controllers (comment out when fully migrated)
    # app.register_blueprint(controller_bp)
    # app.register_blueprint(manager_bp)

    return app