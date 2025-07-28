from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# Configurar SocketIO para usar threading mode (más compatible con servidores WSGI estándar)
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',  # Usar threading en lugar de eventlet
    logger=True,
    engineio_logger=True
)
login_manager = LoginManager()
login_manager.login_view = "landing.index"
login_manager.login_message = "Inicia sesión para acceder a esta página."

db = SQLAlchemy()
mail = Mail()
