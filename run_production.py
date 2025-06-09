from edp_mvp.app import create_app
from edp_mvp.app.extensions import socketio
import os

app = create_app()

if __name__ == "__main__":
    # Configuración para producción con ngrok
    socketio.run(
        app,
        host="0.0.0.0",  # Permitir conexiones externas
        port=int(os.environ.get("PORT", 5000)),
        debug=False,  # Desactivar debug en producción
        allow_unsafe_werkzeug=True,  # Necesario para ngrok con SocketIO
        use_reloader=False,  # Evitar problemas con ngrok
    )
