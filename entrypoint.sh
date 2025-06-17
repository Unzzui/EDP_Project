#!/bin/bash

# Entrypoint script para manejar permisos de Secret Files en Render
echo "🔧 Iniciando entrypoint script..."

# Verificar y ajustar permisos de Secret Files si existen
if [ -d "/etc/secrets" ]; then
    echo "📁 Directorio /etc/secrets encontrado"
    # Listar contenido con permisos
    ls -la /etc/secrets/ || echo "⚠️ No se puede listar /etc/secrets/"
    
    # Intentar cambiar permisos si somos root
    if [ "$(id -u)" = "0" ]; then
        echo "🔧 Ejecutando como root - ajustando permisos..."
        chmod -R 644 /etc/secrets/* 2>/dev/null || echo "⚠️ No se pudieron cambiar permisos de archivos en /etc/secrets/"
        # Cambiar a usuario no-root después de ajustar permisos
        export HOME=/app
        exec su-exec appuser "$@"
    else
        echo "👤 Ejecutando como usuario no-root"
    fi
else
    echo "📁 Directorio /etc/secrets no encontrado"
fi

# Verificaciones de entorno
echo "🔍 Iniciando verificaciones..."
python debug_env.py

echo "🔐 Verificando Secret Files..."
python verify_secrets.py

echo "🔍 Iniciando init_db..."
python init_db.py

echo "🚀 Iniciando Gunicorn..."
exec gunicorn --config gunicorn_config.py wsgi:application
