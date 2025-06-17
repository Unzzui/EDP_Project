#!/bin/bash

# Script para probar el build de Docker localmente antes del deploy a Render
echo "🔧 Probando build de Docker para deploy en Render..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[BUILD]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "Dockerfile" ]; then
    error "No se encontró Dockerfile en el directorio actual"
    exit 1
fi

# Limpiar builds anteriores
log "Limpiando imágenes anteriores..."
docker image rm edp-mvp-test 2>/dev/null || true

# Build de la imagen
log "Construyendo imagen Docker..."
docker build -t edp-mvp-test . 

if [ $? -ne 0 ]; then
    error "Error en el build de Docker"
    exit 1
fi

log "✅ Build exitoso!"

# Verificar que la imagen se creó correctamente
log "Verificando imagen creada..."
docker images edp-mvp-test

# Probar que el contenedor puede iniciarse
log "Probando inicio del contenedor..."
CONTAINER_ID=$(docker run -d \
    -p 8080:5000 \
    -e FLASK_ENV=production \
    -e SECRET_KEY=test-secret-key-for-local-testing \
    -e DEBUG=False \
    edp-mvp-test)

if [ $? -ne 0 ]; then
    error "Error al iniciar el contenedor"
    exit 1
fi

log "✅ Contenedor iniciado con ID: $CONTAINER_ID"

# Esperar unos segundos para que inicie
log "Esperando que la aplicación inicie..."
sleep 10

# Verificar que la aplicación responde
log "Verificando que la aplicación responde..."
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    log "✅ Aplicación responde correctamente en puerto 8080"
else
    warn "⚠️ Endpoint /health no responde, verificando logs..."
    docker logs $CONTAINER_ID
fi

# Mostrar logs del contenedor
log "Mostrando logs del contenedor:"
docker logs $CONTAINER_ID

# Limpiar
log "Deteniendo y limpiando contenedor de prueba..."
docker stop $CONTAINER_ID > /dev/null
docker rm $CONTAINER_ID > /dev/null

log "🚀 Build test completado. La imagen está lista para deploy en Render."
log "Para hacer push a Render, asegúrate de:"
log "  1. Hacer commit de todos los cambios"
log "  2. Push a la branch 'production'"
log "  3. Render detectará automáticamente los cambios y hará el deploy"

echo
log "Para deploy manual, usa estos comandos:"
echo "  git add ."
echo "  git commit -m 'Fix: Resolved su-exec issue and improved Docker config'"
echo "  git push origin production"
