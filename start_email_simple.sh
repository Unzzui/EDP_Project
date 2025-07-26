#!/usr/bin/env bash

# ==============================================================================
# 📧 SCRIPT SIMPLIFICADO - SISTEMA DE CORREOS AUTOMÁTICOS
# ==============================================================================
# Versión simplificada que evita problemas con variables de entorno complejas
# ==============================================================================

set -euo pipefail

# ========== VARIABLES DE CONFIGURACIÓN ==========
PROJECT_NAME="EDP_EMAIL_SYSTEM"
VENV_DIR=".venv"
PYTHON_VERSION="python3"
REDIS_PORT="${REDIS_PORT:-6379}"
PID_DIR="/tmp/edp_email_$$"
mkdir -p "$PID_DIR"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ========== FUNCIONES DE LOGGING ==========
log() { echo -e "${CYAN}[$(date +'%H:%M:%S')] ${NC}$1"; }
log_success() { echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅ ${NC}$1"; }
log_warning() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️  ${NC}$1"; }
log_error() { echo -e "${RED}[$(date +'%H:%M:%S')] ❌ ${NC}$1"; }
log_info() { echo -e "${BLUE}[$(date +'%H:%M:%S')] ℹ️  ${NC}$1"; }

# ========== CLEANUP ==========
cleanup() {
    log_warning "Limpiando servicios de email..."
    
    # Terminar procesos de Celery
    if [ -f "$PID_DIR/celery_worker.pid" ]; then
        local worker_pid=$(cat "$PID_DIR/celery_worker.pid" 2>/dev/null)
        [[ -n "$worker_pid" ]] && kill -TERM "$worker_pid" 2>/dev/null || true
    fi
    
    if [ -f "$PID_DIR/celery_beat.pid" ]; then
        local beat_pid=$(cat "$PID_DIR/celery_beat.pid" 2>/dev/null)
        [[ -n "$beat_pid" ]] && kill -TERM "$beat_pid" 2>/dev/null || true
    fi
    
    # Limpiar archivos
    rm -rf "$PID_DIR" 2>/dev/null || true
    
    log_success "Limpieza completada"
}

trap cleanup EXIT INT TERM

# ========== CONFIGURACIÓN DE EMAIL MANUAL ==========
setup_email_environment() {
    log "🔧 Configurando variables de email..."
    
    # Configurar variables de email manualmente (basado en tu .env)
    export MAIL_USERNAME="diegobravobe@gmail.com"
    export MAIL_PASSWORD="upaq hybg pqkt ufnf"
    export MAIL_SERVER="smtp.gmail.com"
    export MAIL_PORT="587"
    export MAIL_USE_TLS="True"
    export MAIL_USE_SSL="False"
    export MAIL_DEFAULT_SENDER="diegobravobe@gmail.com"
    export MAIL_MAX_EMAILS="100"
    export ENABLE_CRITICAL_ALERTS="True"
    export ENABLE_PAYMENT_REMINDERS="True"
    export ENABLE_WEEKLY_SUMMARY="True"
    export ENABLE_SYSTEM_ALERTS="True"
    export CRITICAL_EDP_DAYS="60"
    export PAYMENT_REMINDER_DAYS="30"
    export WEEKLY_SUMMARY_DAY="monday"
    export TEST_EMAIL_RECIPIENT="diegobravobe@gmail.com"
    
    log_success "Variables de email configuradas"
}

# ========== VERIFICACIONES ==========
check_dependencies() {
    log "🔍 Verificando dependencias..."
    
    # Verificar Python
    if ! command -v $PYTHON_VERSION &> /dev/null; then
        log_error "Python3 no encontrado"
        exit 1
    fi
    
    # Verificar Redis
    if ! command -v redis-server &> /dev/null; then
        log_warning "Redis no encontrado, intentando instalar..."
        if command -v pacman &> /dev/null; then
            sudo pacman -S redis --noconfirm
        elif command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y redis-server
        else
            log_error "No se pudo instalar Redis automáticamente"
            exit 1
        fi
    fi
    
    log_success "Dependencias verificadas"
}

# ========== VIRTUAL ENVIRONMENT ==========
setup_virtual_environment() {
    log "🐍 Configurando entorno virtual..."
    
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creando entorno virtual..."
        $PYTHON_VERSION -m venv "$VENV_DIR"
    fi
    
    source "$VENV_DIR/bin/activate"
    log_success "Entorno virtual activado"
}

# ========== INSTALAR DEPENDENCIAS ==========
install_dependencies() {
    log "📦 Instalando dependencias..."
    
    source "$VENV_DIR/bin/activate"
    
    # Instalar dependencias básicas
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Instalar dependencias adicionales si no están
    pip install redis psutil
    
    log_success "Dependencias instaladas"
}

# ========== INICIAR REDIS ==========
start_redis() {
    log "🔴 Iniciando Redis..."
    
    # Verificar si Redis ya está ejecutándose
    if redis-cli -p $REDIS_PORT ping &> /dev/null; then
        log_success "Redis ya está ejecutándose"
        return
    fi
    
    # Iniciar Redis
    redis-server --port $REDIS_PORT --daemonize yes
    
    # Esperar a que Redis esté listo
    sleep 2
    
    if redis-cli -p $REDIS_PORT ping &> /dev/null; then
        log_success "Redis iniciado correctamente"
    else
        log_error "Error iniciando Redis"
        exit 1
    fi
}

# ========== INICIAR SERVICIOS CELERY ==========
start_celery_services() {
    log "🌿 Iniciando servicios Celery para email..."
    
    source "$VENV_DIR/bin/activate"
    
    # Iniciar Celery Worker
    {
        celery -A edp_mvp.app.celery worker \
            --loglevel=info \
            --concurrency=2 \
            --detach \
            --pidfile="$PID_DIR/celery_worker.pid" \
            --logfile="$PID_DIR/celery_worker.log"
    } &
    
    # Esperar un momento
    sleep 2
    
    # Iniciar Celery Beat
    {
        celery -A edp_mvp.app.celery beat \
            --loglevel=info \
            --detach \
            --pidfile="$PID_DIR/celery_beat.pid" \
            --logfile="$PID_DIR/celery_beat.log"
    } &
    
    # Esperar a que los servicios estén listos
    sleep 3
    
    log_success "Servicios Celery iniciados"
}

# ========== VERIFICAR SERVICIOS ==========
verify_services() {
    log "🔍 Verificando servicios..."
    
    # Verificar Redis
    if redis-cli -p $REDIS_PORT ping &> /dev/null; then
        log_success "Redis: ✅"
    else
        log_error "Redis: ❌"
        return 1
    fi
    
    # Verificar Celery Worker
    if [ -f "$PID_DIR/celery_worker.pid" ]; then
        local worker_pid=$(cat "$PID_DIR/celery_worker.pid")
        if kill -0 "$worker_pid" 2>/dev/null; then
            log_success "Celery Worker: ✅ (PID: $worker_pid)"
        else
            log_error "Celery Worker: ❌"
            return 1
        fi
    else
        log_error "Celery Worker: ❌"
        return 1
    fi
    
    # Verificar Celery Beat
    if [ -f "$PID_DIR/celery_beat.pid" ]; then
        local beat_pid=$(cat "$PID_DIR/celery_beat.pid")
        if kill -0 "$beat_pid" 2>/dev/null; then
            log_success "Celery Beat: ✅ (PID: $beat_pid)"
        else
            log_error "Celery Beat: ❌"
            return 1
        fi
    else
        log_error "Celery Beat: ❌"
        return 1
    fi
    
    return 0
}

# ========== PRUEBA RÁPIDA ==========
run_quick_test() {
    log "🧪 Ejecutando prueba rápida del sistema..."
    
    source "$VENV_DIR/bin/activate"
    
    # Ejecutar script de prueba
    if python test_email_automation.py; then
        log_success "Prueba rápida completada"
        return 0
    else
        log_warning "Algunas pruebas fallaron, pero el sistema puede seguir funcionando"
        return 1
    fi
}

# ========== MOSTRAR ESTADO ==========
show_status() {
    echo
    log_success "🎉 Sistema de correos automáticos iniciado!"
    echo -e "${GREEN}📋 Estado de servicios:${NC}"
    echo -e "   • Redis:        localhost:$REDIS_PORT"
    echo -e "   • Celery Worker: PID $(cat "$PID_DIR/celery_worker.pid" 2>/dev/null || echo 'N/A')"
    echo -e "   • Celery Beat:   PID $(cat "$PID_DIR/celery_beat.pid" 2>/dev/null || echo 'N/A')"
    echo
    echo -e "${GREEN}📧 Tareas automáticas configuradas:${NC}"
    echo -e "   • 🚨 Alertas Críticas: Diario a las 00:00"
    echo -e "   • 💰 Recordatorios:    Diario a las 00:00"
    echo -e "   • 📊 Resumen Semanal:  Lunes a las 09:00"
    echo
    echo -e "${GREEN}🔧 Comandos útiles:${NC}"
    echo -e "   • Verificar estado: python verify_email_system.py"
    echo -e "   • Probar sistema:    python test_email_automation.py"
    echo -e "   • Ver logs:          tail -f $PID_DIR/celery_*.log"
    echo -e "   • Detener servicios: Ctrl+C"
    echo
    echo -e "${YELLOW}💡 El sistema está funcionando automáticamente!${NC}"
    echo -e "   Los correos se enviarán según los horarios configurados."
    echo
}

# ========== FUNCIÓN PRINCIPAL ==========
main() {
    echo -e "${PURPLE}📧 $PROJECT_NAME - INICIO SIMPLIFICADO${NC}"
    echo
    
    # Ejecutar fases
    check_dependencies
    setup_email_environment
    setup_virtual_environment
    install_dependencies
    
    # Iniciar servicios
    start_redis
    start_celery_services
    
    # Verificar servicios
    if verify_services; then
        # Ejecutar prueba rápida
        run_quick_test
        
        # Mostrar estado
        show_status
        
        # Mantener el script ejecutándose
        log_info "Presiona Ctrl+C para detener los servicios..."
        while true; do
            sleep 10
            # Verificar que los servicios sigan ejecutándose
            if ! verify_services &> /dev/null; then
                log_error "Algunos servicios se detuvieron"
                break
            fi
        done
    else
        log_error "Error iniciando servicios"
        exit 1
    fi
}

# ========== MANEJO DE ARGUMENTOS ==========
case "${1:-}" in
    --help|-h)
        echo "📧 Script simplificado para sistema de correos automáticos"
        echo "Uso: $0 [--help|--test|--verify]"
        echo ""
        echo "Opciones:"
        echo "  --help, -h     Mostrar esta ayuda"
        echo "  --test         Solo ejecutar pruebas"
        echo "  --verify       Solo verificar configuración"
        exit 0
        ;;
    --test)
        setup_email_environment
        setup_virtual_environment
        run_quick_test
        exit 0
        ;;
    --verify)
        setup_email_environment
        setup_virtual_environment
        python verify_email_system.py
        exit 0
        ;;
    *)
        main
        ;;
esac 