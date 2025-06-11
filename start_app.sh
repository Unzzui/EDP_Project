#!/usr/bin/env bash

# ==============================================================================
# 🚀 SCRIPT DE INICIO COMPLETO - EDP MVP APPLICATION
# ==============================================================================
# Este script automatiza todo el proceso de setup y arranque de la aplicación
# Funcionalidad: entorno virtual, dependencias, servicios y aplicación Flask
# ==============================================================================

set -euo pipefail  # Salir en caso de error

# ========== VARIABLES DE CONFIGURACIÓN ==========
PROJECT_NAME="EDP_MVP"
VENV_DIR=".venv"
PYTHON_VERSION="python3"
REDIS_PORT="${REDIS_PORT:-6379}"
FLASK_PORT="${FLASK_PORT:-5000}"
FLASK_HOST="${FLASK_HOST:-127.0.0.1}"
REDIS_URL="redis://localhost:${REDIS_PORT}/0"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ========== FUNCIONES AUXILIARES ==========
log() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')] ${NC}$1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅ ${NC}$1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️  ${NC}$1"
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌ ${NC}$1"
}

log_info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] ℹ️  ${NC}$1"
}

# Función para limpiar procesos al salir
cleanup() {
    log_warning "Deteniendo todos los servicios..."
    
    # Detener Celery worker usando PID file
    if [ -f "/tmp/celery_worker.pid" ]; then
        local worker_pid=$(cat /tmp/celery_worker.pid 2>/dev/null)
        if [ ! -z "$worker_pid" ] && kill -0 "$worker_pid" 2>/dev/null; then
            kill -TERM "$worker_pid" 2>/dev/null || true
            sleep 2
            kill -KILL "$worker_pid" 2>/dev/null || true
        fi
        rm -f /tmp/celery_worker.pid
        log_info "Celery worker detenido"
    fi
    
    # Detener Celery beat usando PID file
    if [ -f "/tmp/celery_beat.pid" ]; then
        local beat_pid=$(cat /tmp/celery_beat.pid 2>/dev/null)
        if [ ! -z "$beat_pid" ] && kill -0 "$beat_pid" 2>/dev/null; then
            kill -TERM "$beat_pid" 2>/dev/null || true
            sleep 1
            kill -KILL "$beat_pid" 2>/dev/null || true
        fi
        rm -f /tmp/celery_beat.pid
        log_info "Celery beat detenido"
    fi
    
    # Detener Flower
    if pgrep -f "celery.*flower" > /dev/null; then
        pkill -f "celery.*flower" 2>/dev/null || true
        log_info "Flower detenido"
    fi
    
    # Detener Redis
    if pgrep -f "redis-server" > /dev/null; then
        pkill -f "redis-server" 2>/dev/null || true
        log_info "Redis detenido"
    fi
    
    # Detener Flask
    if pgrep -f "python.*run.py" > /dev/null; then
        pkill -f "python.*run.py" 2>/dev/null || true
        log_info "Flask app detenida"
    fi
    
    # Limpiar archivos temporales
    rm -f /tmp/celery_worker.pid /tmp/celery_beat.pid 2>/dev/null || true
    
    log_success "Limpieza completada. Hasta pronto! 👋"
}

# Configurar trap para limpieza al salir
trap cleanup EXIT INT TERM

# ========== VERIFICACIONES INICIALES ==========
check_dependencies() {
    log "🔍 Verificando dependencias del sistema..."
    
    # Verificar Python
    if ! command -v $PYTHON_VERSION &> /dev/null; then
        log_error "Python 3 no está instalado. Por favor instálalo primero."
        exit 1
    fi
    
    # Verificar Redis
    if ! command -v redis-server &> /dev/null; then
        log_warning "Redis no está instalado. Intentando instalar..."
        
        # Detectar el sistema operativo
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update && sudo apt-get install -y redis-server
            elif command -v yum &> /dev/null; then
                sudo yum install -y redis
            elif command -v pacman &> /dev/null; then
                sudo pacman -S redis
            else
                log_error "No se pudo instalar Redis automáticamente. Por favor instálalo manualmente."
                exit 1
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew install redis
            else
                log_error "Homebrew no está instalado. Por favor instala Redis manualmente."
                exit 1
            fi
        else
            log_error "Sistema operativo no soportado para instalación automática de Redis."
            exit 1
        fi
    fi
    
    log_success "Dependencias verificadas"
}

# ========== CONFIGURACIÓN DEL ENTORNO VIRTUAL ==========
setup_virtual_environment() {
    log "🐍 Configurando entorno virtual..."
    
    # Crear entorno virtual si no existe
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creando nuevo entorno virtual en $VENV_DIR..."
        $PYTHON_VERSION -m venv $VENV_DIR
        log_success "Entorno virtual creado"
    else
        log_info "Entorno virtual existente encontrado en $VENV_DIR"
    fi
    
    # Activar entorno virtual
    log_info "Activando entorno virtual..."
    source $VENV_DIR/bin/activate
    
    # Verificar Python en el entorno virtual
    log_info "Python activo: $(which python)"
    log_info "Versión Python: $(python --version)"
    
    log_success "Entorno virtual configurado y activado"
}

# ========== INSTALACIÓN DE DEPENDENCIAS ==========
install_dependencies() {
    log "📦 Instalando dependencias de Python..."
    
    # Actualizar pip
    log_info "Actualizando pip..."
    python -m pip install --upgrade pip
    
    # Instalar dependencias principales
    if [ -f "requirements.txt" ]; then
        log_info "Instalando dependencias desde requirements.txt..."
        pip install -r requirements.txt
        log_success "Dependencias principales instaladas"
    else
        log_error "Archivo requirements.txt no encontrado"
        exit 1
    fi
    
    # Instalar dependencias compatibles si existen
    if [ -f "requirements_flask_compatible.txt" ]; then
        log_info "Instalando dependencias compatibles..."
        pip install -r requirements_flask_compatible.txt
    fi
    
    log_success "Todas las dependencias instaladas"
}

# ========== CONFIGURACIÓN DE ARCHIVOS DE ENTORNO ==========
setup_environment_files() {
    log "⚙️  Configurando archivos de entorno..."
    
    # Crear .env si no existe
    if [ ! -f ".env" ]; then
        log_info "Creando archivo .env básico..."
        cat > .env << EOF
# Configuración de Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# Configuración de Redis
REDIS_URL=redis://localhost:6379/0

# Configuración de Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Configuración de la aplicación
DATABASE_URL=sqlite:///edp_mvp.db
EOF
        log_success "Archivo .env creado"
    else
        log_info "Archivo .env existente encontrado"
    fi
}

# ========== INICIO DE SERVICIOS ==========
start_redis() {
    log "🔴 Iniciando Redis/Valkey..."
    
    # Verificar si Redis ya está corriendo
    if pgrep -f "redis-server" > /dev/null; then
        log_warning "Redis ya está corriendo"
        return 0
    fi
    
    # Limpiar archivo RDB incompatible si existe
    if [ -f "dump.rdb" ]; then
        log_warning "Encontrado archivo dump.rdb incompatible, respaldando..."
        mv dump.rdb dump.rdb.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || rm dump.rdb 2>/dev/null || true
        log_success "Archivo RDB problemático limpiado"
    fi
    
    # Configurar memory overcommit (solo Linux y con permisos)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ "$(cat /proc/sys/vm/overcommit_memory 2>/dev/null || echo 0)" = "0" ]; then
            log_info "Configurando memory overcommit para mejor rendimiento..."
            if sudo -n sysctl vm.overcommit_memory=1 2>/dev/null; then
                log_success "Memory overcommit configurado"
            else
                log_warning "No se pudo configurar memory overcommit (requiere sudo)"
                log_info "Puedes configurarlo manualmente: sudo sysctl vm.overcommit_memory=1"
            fi
        fi
    fi
    
    # Iniciar Redis con configuración específica
    log_info "Iniciando Redis en puerto $REDIS_PORT..."
    redis-server --daemonize yes --port $REDIS_PORT --dir $(pwd) --dbfilename dump_edp_mvp.rdb
    
    # Esperar a que Redis esté listo
    local count=0
    while ! redis-cli -p $REDIS_PORT ping &> /dev/null; do
        count=$((count + 1))
        if [ $count -gt 15 ]; then
            log_error "Redis no pudo iniciarse correctamente"
            log_info "Verificando procesos..."
            if pgrep -f "redis-server" > /dev/null; then
                log_error "El proceso está corriendo pero no responde"
            else
                log_error "El proceso no se inició"
            fi
            exit 1
        fi
        sleep 1
        if [ $((count % 5)) -eq 0 ]; then
            log_info "Esperando Redis... (intento $count/15)"
        fi
    done
    
    log_success "Redis iniciado correctamente en puerto $REDIS_PORT"
}

start_celery_services() {
    log "🌿 Iniciando servicios de Celery..."
    
    # Activar entorno virtual
    source $VENV_DIR/bin/activate
    
    # Iniciar Celery worker con eventos habilitados
    log_info "Iniciando Celery worker..."
    celery -A edp_mvp.app.celery worker \
        --loglevel=info \
        --events \
        --detach \
        --pidfile=/tmp/celery_worker.pid \
        --logfile=/tmp/celery_worker.log
    
    # Esperar un momento para que el worker se establezca
    log_info "Esperando que el worker se establezca..."
    sleep 2
    
    # Iniciar Celery beat
    log_info "Iniciando Celery beat (scheduler)..."
    celery -A edp_mvp.app.celery beat \
        --loglevel=info \
        --detach \
        --pidfile=/tmp/celery_beat.pid \
        --logfile=/tmp/celery_beat.log
    
    # Esperar antes de iniciar Flower
    log_info "Esperando servicios base..."
    sleep 3
    
    # Iniciar Flower con configuración mejorada
    if command -v celery &> /dev/null; then
        log_info "Iniciando Flower (monitor) en http://localhost:5555..."
        celery -A edp_mvp.app.celery flower \
            --broker="$REDIS_URL" \
            --port=5555 \
            --broker_api="$REDIS_URL" \
            --basic_auth=admin:admin123 \
            --persistent=True \
            --max_tasks=10000 &
        
        # Dar tiempo para que Flower se conecte
        sleep 2
        log_success "Flower iniciado en http://localhost:5555 (admin/admin123)"
    else
        log_warning "Celery no encontró el subcomando flower, salteando Flower..."
    fi
    
    log_success "Servicios de Celery iniciados correctamente"
}

# ========== VERIFICACIÓN DE SALUD ==========
health_check() {
    log "🏥 Verificando salud de los servicios..."
    
    local all_healthy=true
    
    # Verificar Redis
    if redis-cli -p $REDIS_PORT ping &> /dev/null; then
        log_success "Redis: ✅ Funcionando"
    else
        log_error "Redis: ❌ No responde"
        all_healthy=false
    fi
    
    # Verificar Celery worker
    if pgrep -f "celery.*worker" > /dev/null; then
        log_success "Celery Worker: ✅ Funcionando"
    else
        log_error "Celery Worker: ❌ No está corriendo"
        all_healthy=false
    fi
    
    # Verificar Celery beat
    if pgrep -f "celery.*beat" > /dev/null; then
        log_success "Celery Beat: ✅ Funcionando"
    else
        log_error "Celery Beat: ❌ No está corriendo"
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        log_success "Todos los servicios están saludables"
        return 0
    else
        log_error "Algunos servicios tienen problemas"
        return 1
    fi
}

# ========== INICIO DE LA APLICACIÓN FLASK ==========
start_flask_app() {
    log "🌐 Iniciando aplicación Flask..."
    
    # Activar entorno virtual
    source $VENV_DIR/bin/activate
    
    # Verificar que el archivo run.py existe
    if [ ! -f "run.py" ]; then
        log_error "Archivo run.py no encontrado"
        exit 1
    fi
    
    log_info "Iniciando Flask en http://$FLASK_HOST:$FLASK_PORT"
    log_info "Presiona Ctrl+C para detener todos los servicios"
    
    # Mostrar resumen de servicios antes de iniciar Flask
    echo
    log_success "🎉 Todos los servicios están listos!"
    echo
    echo -e "${GREEN}📋 RESUMEN DE SERVICIOS:${NC}"
    echo -e "   • Redis:        http://localhost:$REDIS_PORT"
    echo -e "   • Flower:       http://localhost:5555"
    echo -e "   • Flask App:    http://$FLASK_HOST:$FLASK_PORT"
    echo
    echo -e "${YELLOW}💡 COMANDOS ÚTILES:${NC}"
    echo -e "   • Redis CLI:              redis-cli -p $REDIS_PORT"
    echo -e "   • Monitor procesos:       ps aux | grep -E '(celery|redis)'"
    echo
    
    # Iniciar Flask app
    python run.py
}

# ========== FUNCIÓN PRINCIPAL ==========
main() {
    echo
    echo -e "${PURPLE}================================"
    echo -e "🚀 $PROJECT_NAME - INICIO COMPLETO"
    echo -e "================================${NC}"
    echo
    
    # Mostrar información del sistema
    log_info "Sistema: $(uname -s)"
    log_info "Directorio: $(pwd)"
    log_info "Usuario: $(whoami)"
    echo
    
    # Ejecutar todas las fases
    check_dependencies
    setup_virtual_environment
    install_dependencies
    setup_environment_files
    start_redis
    start_celery_services
    
    # Pequeña pausa para que todo se estabilice
    sleep 3
    
    # Iniciar Flask (esto bloquea hasta Ctrl+C)
    start_flask_app
}

# ========== MANEJO DE ARGUMENTOS ==========
case "${1:-}" in
    --help|-h)
        echo "🚀 Script de inicio completo para $PROJECT_NAME"
        echo
        echo "Uso: $0 [OPCIÓN]"
        echo
        echo "Opciones:"
        echo "  --help, -h          Mostrar esta ayuda"
        echo "  --check-only        Solo verificar dependencias"
        echo "  --setup-only        Solo configurar entorno (sin iniciar servicios)"
        echo "  --services-only     Solo iniciar servicios (asume entorno configurado)"
        echo
        echo "Variables de entorno:"
        echo "  REDIS_PORT          Puerto para Redis (default: 6379)"
        echo "  FLASK_PORT          Puerto para Flask (default: 5000)"
        echo "  FLASK_HOST          Host para Flask (default: 127.0.0.1)"
        echo
        exit 0
        ;;
    --check-only)
        check_dependencies
        log_success "Verificación completada"
        exit 0
        ;;
    --setup-only)
        check_dependencies
        setup_virtual_environment
        install_dependencies
        setup_environment_files
        log_success "Setup completado. Usa '$0 --services-only' para iniciar servicios"
        exit 0
        ;;
    --services-only)
        start_redis
        start_celery_services
        start_flask_app
        ;;
    "")
        main
        ;;
    *)
        log_error "Opción desconocida: $1"
        echo "Usa '$0 --help' para ver las opciones disponibles"
        exit 1
        ;;
esac
