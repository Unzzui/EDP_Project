from flask import Flask
from .config import Config
from flask_login import LoginManager
from .extensions import socketio, login_manager  # <---




def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager.init_app(app)
    socketio.init_app(app)

    from app.auth.routes import auth_bp
    from app.edp.routes import edp_bp
    from app.dashboard.controller import controller_bp
    from app.dashboard.manager import manager_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(edp_bp, url_prefix="/edp")
    app.register_blueprint(controller_bp)
    app.register_blueprint(manager_bp)

    return app

