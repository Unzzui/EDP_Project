#!/bin/bash

# 🚀 Script para iniciar Pagora FastAPI
# Integración con el sistema Flask existente

echo "🚀 Iniciando Pagora FastAPI..."

# Verificar que estamos en el directorio correcto
if [ ! -f "api_fastapi/main.py" ]; then
    echo "❌ Error: No se encuentra api_fastapi/main.py"
    echo "   Asegúrate de ejecutar este script desde el directorio raíz del proyecto"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    echo "🔧 Activando entorno virtual..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "🔧 Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar e instalar dependencias de FastAPI
echo "📦 Verificando dependencias de FastAPI..."
if ! pip show fastapi > /dev/null 2>&1; then
    echo "📥 Instalando dependencias de FastAPI..."
    pip install -r api_fastapi/requirements.txt
fi

# Configurar variables de entorno (reutilizar del Flask)
if [ -f ".env" ]; then
    echo "🔧 Cargando variables de entorno..."
    # Cargar variables de entorno de forma segura
    set -a  # Automatically export all variables
    source .env
    set +a  # Turn off automatic export
fi

# Configurar puerto de la API (diferente al Flask)
export API_PORT=${API_PORT:-8000}
export API_HOST=${API_HOST:-0.0.0.0}

echo "📡 Configuración de la API:"
echo "   🌐 Host: $API_HOST"
echo "   🔌 Puerto: $API_PORT"
echo "   📊 Documentación: http://$API_HOST:$API_PORT/docs"
echo "   📋 ReDoc: http://$API_HOST:$API_PORT/redoc"

# Iniciar la API FastAPI
echo "🚀 Iniciando servidor FastAPI..."
cd api_fastapi

# Usar uvicorn con recarga automática en desarrollo
if [ "$ENVIRONMENT" = "development" ] || [ "$FLASK_ENV" = "development" ]; then
    echo "🔧 Modo desarrollo - Recarga automática activada"
    uvicorn main:app \
        --host $API_HOST \
        --port $API_PORT \
        --reload \
        --log-level info \
        --access-log
else
    echo "🏭 Modo producción"
    uvicorn main:app \
        --host $API_HOST \
        --port $API_PORT \
        --workers 4 \
        --log-level info
fi 