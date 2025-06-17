#!/bin/bash

# Script de inicio para producción con Gunicorn + Threading
set -e

echo "🚀 Iniciando aplicación EDP MVP en producción con Gunicorn + Threading..."

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

# Iniciar la aplicación con Gunicorn + Threading
echo "🌐 Iniciando servidor web con Gunicorn + Threading..."
exec gunicorn --config gunicorn_config.py wsgi:application
