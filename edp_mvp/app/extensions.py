from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Configurar SocketIO para usar threading mode (más compatible con servidores WSGI estándar)
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',  # Usar threading en lugar de eventlet
    logger=True,
    engineio_logger=True
)
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para acceder a esta página."

db = SQLAlchemy()
