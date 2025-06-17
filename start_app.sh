#!/usr/bin/env bash

# ==============================================================================
# 🚀 SCRIPT DE INICIO OPTIMIZADO - EDP MVP APPLICATION
# ==============================================================================
# Versión optimizada con mejoras de rendimiento y eficiencia
# ==============================================================================

set -euo pipefail

# ========== VARIABLES DE CONFIGURACIÓN ==========
PROJECT_NAME="EDP_MVP"
VENV_DIR=".venv"
PYTHON_VERSION="python3"
REDIS_PORT="${REDIS_PORT:-6379}"
FLASK_PORT="${FLASK_PORT:-5000}"
FLASK_HOST="${FLASK_HOST:-127.0.0.1}"
REDIS_URL="redis://localhost:${REDIS_PORT}/0"

# Archivos PID más seguros
PID_DIR="/tmp/edp_mvp_$$"
mkdir -p "$PID_DIR"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ========== FUNCIONES DE LOGGING OPTIMIZADAS ==========
log() { echo -e "${CYAN}[$(date +'%H:%M:%S')] ${NC}$1"; }
log_success() { echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅ ${NC}$1"; }
log_warning() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️  ${NC}$1"; }
log_error() { echo -e "${RED}[$(date +'%H:%M:%S')] ❌ ${NC}$1"; }
log_info() { echo -e "${BLUE}[$(date +'%H:%M:%S')] ℹ️  ${NC}$1"; }

# ========== CLEANUP OPTIMIZADO ==========
cleanup() {
    log_warning "Iniciando limpieza de servicios..."
    
    # Array de servicios para limpieza paralela
    local pids_to_kill=()
    
    # Recolectar PIDs de forma eficiente
    if [ -f "$PID_DIR/celery_worker.pid" ]; then
        local worker_pid=$(cat "$PID_DIR/celery_worker.pid" 2>/dev/null)
        [[ -n "$worker_pid" ]] && pids_to_kill+=("$worker_pid")
    fi
    
    if [ -f "$PID_DIR/celery_beat.pid" ]; then
        local beat_pid=$(cat "$PID_DIR/celery_beat.pid" 2>/dev/null)
        [[ -n "$beat_pid" ]] && pids_to_kill+=("$beat_pid")
    fi
    
    # Terminar procesos en paralelo
    for pid in "${pids_to_kill[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null &
        fi
    done
    
    # Esperar brevemente y forzar si es necesario
    sleep 1
    for pid in "${pids_to_kill[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
    
    # Limpiar otros procesos
    pkill -f "celery.*flower" 2>/dev/null || true
    pkill -f "redis-server.*$REDIS_PORT" 2>/dev/null || true
    
    # Limpieza de archivos
    rm -rf "$PID_DIR" 2>/dev/null || true
    
    log_success "Limpieza completada 👋"
}

trap cleanup EXIT INT TERM

# ========== VERIFICACIONES OPTIMIZADAS ==========
check_dependencies() {
    log "🔍 Verificando dependencias..."
    
    local missing_deps=()
    
    # Verificar Python
    if ! command -v $PYTHON_VERSION &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Verificar Redis de forma más eficiente
    if ! command -v redis-server &> /dev/null; then
        missing_deps+=("redis-server")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Dependencias faltantes: ${missing_deps[*]}"
        log_info "Instalando automáticamente..."
        install_system_dependencies "${missing_deps[@]}"
    fi
    
    log_success "Dependencias verificadas"
}

install_system_dependencies() {
    local deps=("$@")
    
    # Detectar sistema y instalar en una sola operación
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y "${deps[@]/#/}"
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm "${deps[@]}"
        elif command -v yum &> /dev/null; then
            sudo yum install -y "${deps[@]}"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install "${deps[@]}"
        fi
    fi
}

# ========== SETUP OPTIMIZADO ==========
setup_virtual_environment() {
    log "🐍 Configurando entorno virtual..."
    
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creando entorno virtual..."
        $PYTHON_VERSION -m venv "$VENV_DIR" --prompt="$PROJECT_NAME"
    fi
    
    # Activar y verificar en una sola operación
    source "$VENV_DIR/bin/activate"
    log_success "Entorno virtual listo: $(python --version)"
}

install_dependencies() {
    log "📦 Instalando dependencias..."
    
    # Optimizar pip primero
    python -m pip install --upgrade pip setuptools wheel --no-warn-script-location -q
    
    # Instalar dependencias con cache y compilación paralela
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt --no-warn-script-location --compile -q
    else
        log_error "requirements.txt no encontrado"
        exit 1
    fi
    
    log_success "Dependencias instaladas"
}

# ========== SERVICIOS OPTIMIZADOS ==========
start_redis() {
    log "🔴 Iniciando Redis..."
    
    # Verificar si ya está corriendo en el puerto específico
    if redis-cli -p "$REDIS_PORT" ping &> /dev/null; then
        log_success "Redis ya está corriendo en puerto $REDIS_PORT"
        return 0
    fi
    
    # Limpiar dump RDB problemático
    [ -f "dump.rdb" ] && mv "dump.rdb" "dump.rdb.backup_$(date +%s)" 2>/dev/null || true
    
    # Configuración Redis optimizada
    redis-server \
        --daemonize yes \
        --port "$REDIS_PORT" \
        --dir "$(pwd)" \
        --dbfilename "dump_edp_mvp.rdb" \
        --save "900 1" \
        --maxmemory 256mb \
        --maxmemory-policy allkeys-lru \
        --tcp-keepalive 300 \
        --timeout 0
    
    # Verificación rápida con timeout
    local count=0
    while ! redis-cli -p "$REDIS_PORT" ping &> /dev/null && [ $count -lt 10 ]; do
        sleep 0.5
        ((count++))
    done
    
    if [ $count -ge 10 ]; then
        log_error "Redis no pudo iniciarse"
        exit 1
    fi
    
    log_success "Redis listo en puerto $REDIS_PORT"
}

start_celery_services() {
    log "🌿 Iniciando servicios Celery..."
    
    source "$VENV_DIR/bin/activate"
    
    # Iniciar servicios en paralelo con configuración optimizada
    {
        celery -A edp_mvp.app.celery worker \
            --loglevel=warning \
            --concurrency=2 \
            --events \
            --detach \
            --pidfile="$PID_DIR/celery_worker.pid" \
            --logfile="$PID_DIR/celery_worker.log"
    } &
    
    {
        sleep 1
        celery -A edp_mvp.app.celery beat \
            --loglevel=warning \
            --detach \
            --pidfile="$PID_DIR/celery_beat.pid" \
            --logfile="$PID_DIR/celery_beat.log"
    } &
    
    {
        sleep 2
        if command -v celery &> /dev/null && celery help | grep -q flower; then
            celery -A edp_mvp.app.celery flower \
                --broker="$REDIS_URL" \
                --port=5555 \
                --basic_auth=admin:admin123 \
                --max_tasks=1000 \
                --persistent=true \
                --logging=warning &
        fi
    } &
    
    wait
    sleep 1
    
    log_success "Servicios Celery iniciados"
}

# ========== VERIFICACIÓN RÁPIDA ==========
quick_health_check() {
    log "🏥 Verificación rápida..."
    
    local services=(
        "redis-cli -p $REDIS_PORT ping:Redis"
        "pgrep -f 'celery.*worker':Celery Worker"
        "pgrep -f 'celery.*beat':Celery Beat"
    )
    
    for service in "${services[@]}"; do
        local cmd="${service%%:*}"
        local name="${service##*:}"
        
        if eval "$cmd" &> /dev/null; then
            log_success "$name: ✅"
        else
            log_warning "$name: ⚠️ No disponible"
        fi
    done
}

# ========== INICIO FLASK OPTIMIZADO ==========
start_flask_app() {
    log "🌐 Iniciando aplicación Flask..."
    
    source "$VENV_DIR/bin/activate"
    
    # Mostrar resumen
    echo
    log_success "🎉 Servicios listos!"
    echo -e "${GREEN}📋 URLs disponibles:${NC}"
    echo -e "   • Flask App:    http://$FLASK_HOST:$FLASK_PORT"
    echo -e "   • Flower:       http://localhost:5555"
    echo -e "   • Redis:        localhost:$REDIS_PORT"
    echo
    
    # Iniciar Flask con configuración optimizada
    export FLASK_ENV=development
    export PYTHONUNBUFFERED=1
    python run.py
}

# ========== FUNCIÓN PRINCIPAL OPTIMIZADA ==========
main() {
    echo -e "${PURPLE}🚀 $PROJECT_NAME - INICIO RÁPIDO${NC}"
    echo
    
    # Ejecutar fases de forma más eficiente
    check_dependencies
    setup_virtual_environment
    install_dependencies
    
    # Iniciar servicios en paralelo donde sea posible
    start_redis
    start_celery_services
    
    # Verificación rápida
    quick_health_check
    
    # Iniciar Flask
    start_flask_app
}

# ========== MANEJO DE ARGUMENTOS ==========
case "${1:-}" in
    --help|-h)
        echo "🚀 Script optimizado para $PROJECT_NAME"
        echo "Uso: $0 [--help|--check|--setup|--services]"
        exit 0
        ;;
    --check)
        check_dependencies
        exit 0
        ;;
    --setup)
        check_dependencies
        setup_virtual_environment
        install_dependencies
        exit 0
        ;;
    --services)
        start_redis
        start_celery_services
        quick_health_check
        exit 0
        ;;
    *)
        main
        ;;
esac 