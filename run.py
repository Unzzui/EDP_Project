from edp_mvp.app import create_app
from edp_mvp.app.extensions import socketio
from dotenv import load_dotenv
import os


load_dotenv()

app = create_app()

if __name__ == '__main__':
    # Configuración para desarrollo local
    socketio.run(
        app,
        host='127.0.0.1',  # Solo localhost para desarrollo
        port=5000,
        debug=True
    )