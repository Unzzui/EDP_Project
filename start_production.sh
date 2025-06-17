#!/bin/bash

# Script de inicio para producción en Render
set -e

echo "🚀 Iniciando aplicación EDP MVP en producción..."

# Verificar variables de entorno críticas
if [ -z "$REDIS_URL" ]; then
    echo "⚠️  REDIS_URL no configurado, usando valores por defecto"
    export REDIS_URL="redis://localhost:6379/0"
fi

if [ -z "$SECRET_KEY" ]; then
    echo "🔑 Generando SECRET_KEY temporal"
    export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
fi

# Establecer configuración de producción
export FLASK_ENV=production
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Ejecutar migraciones si es necesario
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🔄 Ejecutando migraciones de base de datos..."
    python -c "
from edp_mvp.app import create_app
from edp_mvp.app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Base de datos inicializada')
"
fi

# Verificar conectividad de Redis
echo "🔍 Verificando conectividad de Redis..."
python -c "
import redis
import os
import sys
try:
    r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    r.ping()
    print('✅ Redis conectado correctamente')
except Exception as e:
    print(f'⚠️  Redis no disponible: {e}')
    print('La aplicación continuará pero sin funcionalidades de cache')
"

# Iniciar la aplicación con Gunicorn
echo "🌐 Iniciando servidor web con Gunicorn..."
exec gunicorn --config gunicorn_config.py wsgi:application
