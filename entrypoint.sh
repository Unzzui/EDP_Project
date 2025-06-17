#!/bin/bash

# Entrypoint script para manejar permisos de Secret Files en Render
echo "🔧 Iniciando entrypoint script..."

# Verificar si somos root y ejecutar corrección de Secret Files
if [ "$(id -u)" = "0" ]; then
    echo "� Ejecutando como root - corrigiendo Secret Files..."
    
    # Ejecutar script de corrección de Secret Files
    python fix_render_secrets.py
    
    # Cambiar a usuario no-root para ejecutar la aplicación
    export HOME=/app
    echo "👤 Cambiando a usuario appuser..."
    exec gosu appuser "$0" "$@"
else
    echo "� Ejecutando como usuario no-root"
fi

# Verificaciones de entorno (como usuario appuser)
echo "🔍 Iniciando verificaciones..."
python debug_env.py

echo "🔐 Verificando Secret Files..."
python verify_secrets.py

echo "🔍 Inicializando base de datos..."
python init_db.py

echo "🚀 Iniciando Gunicorn..."
exec gunicorn --config gunicorn_config.py wsgi:application
