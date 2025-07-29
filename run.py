from edp_mvp.app import create_app
from edp_mvp.app.extensions import socketio
from dotenv import load_dotenv
import os


load_dotenv()

app = create_app()

if __name__ == "__main__":
    # Configuración para desarrollo local con acceso desde la red
    # Usar 0.0.0.0 permite acceso desde cualquier IP de la red local
    # También puedes especificar una IP específica como "192.168.1.100"
    socketio.run(
        app, 
        host="0.0.0.0",  # Permite acceso desde cualquier IP de la red
        port=5000, 
        debug=True,
        allow_unsafe_werkzeug=True  # Permite Werkzeug en modo debug con host 0.0.0.0
    )
