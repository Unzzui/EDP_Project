#!/usr/bin/env python3
"""
Entry point para producción con eventlet monkey patching
DEBE hacerse antes de cualquier import de Flask/SocketIO
"""

# CRITICAL: Monkey patch DEBE ser lo primero
import eventlet
eventlet.monkey_patch()

import os
from edp_mvp.app import create_app
from edp_mvp.app.extensions import socketio

# Configurar variables de entorno para producción
os.environ.setdefault('FLASK_ENV', 'production')

# Crear la aplicación
application = create_app()

if __name__ == "__main__":
    # Solo para testing local del WSGI
    socketio.run(application, host='0.0.0.0', port=5000, debug=False)
