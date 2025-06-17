#!/usr/bin/env python3
"""
WSGI entry point SIN SocketIO para máxima compatibilidad en caso de emergencia
"""
import os
from edp_mvp.app import create_app

# Configurar variables de entorno para producción
os.environ.setdefault('FLASK_ENV', 'production')

# Crear la aplicación SIN inicializar SocketIO
app = create_app()

# Crear una aplicación WSGI pura sin SocketIO
application = app

if __name__ == "__main__":
    # Solo para testing local
    app.run(host='0.0.0.0', port=5000, debug=False)
