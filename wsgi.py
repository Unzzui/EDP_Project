#!/usr/bin/env python3
"""
WSGI entry point for production deployment
Optimizado para Gunicorn + Gevent
"""
import os
from edp_mvp.app import create_app

# Configurar variables de entorno para producción
os.environ.setdefault('FLASK_ENV', 'production')

# Crear la aplicación
application = create_app()

if __name__ == "__main__":
    # Solo para testing local del WSGI
    from edp_mvp.app.extensions import socketio
    socketio.run(application, host='0.0.0.0', port=5000, debug=False)
