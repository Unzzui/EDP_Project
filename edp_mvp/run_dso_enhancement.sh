#!/bin/bash

# 🎯 SCRIPT DE IMPLEMENTACIÓN DSO INTELIGENTE
# Mejora Pagora MVP con cálculo automático de DSO
# Versión: 1.0
# Fecha: 2025-01-28

set -e  # Salir si algún comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "=================================================="
echo "🎯 PAGORA MVP - MEJORA DSO INTELIGENTE"
echo "=================================================="
echo -e "${NC}"

# Variables por defecto
DB_NAME="pagora_mvp"
DB_HOST="localhost"
DB_PORT="5432"
DB_USER="postgres"
BACKUP_DIR="backups"
LOG_FILE="dso_enhancement_$(date +%Y%m%d_%H%M%S).log"

# Función para logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  -d, --database    Nombre de la base de datos (default: pagora_mvp)"
    echo "  -h, --host        Host de PostgreSQL (default: localhost)"
    echo "  -p, --port        Puerto de PostgreSQL (default: 5432)"
    echo "  -u, --user        Usuario de PostgreSQL (default: postgres)"
    echo "  --dry-run         Solo mostrar lo que se haría, sin ejecutar"
    echo "  --help            Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0                                    # Configuración por defecto"
    echo "  $0 -d mi_db -u mi_usuario           # Base de datos personalizada"
    echo "  $0 --dry-run                        # Solo simular"
}

# Parsear argumentos
DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--database)
            DB_NAME="$2"
            shift 2
            ;;
        -h|--host)
            DB_HOST="$2"
            shift 2
            ;;
        -p|--port)
            DB_PORT="$2"
            shift 2
            ;;
        -u|--user)
            DB_USER="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Argumento desconocido: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Mostrar configuración
echo -e "${BLUE}📋 CONFIGURACIÓN:${NC}"
echo "  Database: $DB_NAME"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  User: $DB_USER"
echo "  Log: $LOG_FILE"
echo ""

# Verificar que existe psql
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ ERROR: psql no está instalado${NC}"
    exit 1
fi

# Verificar archivos necesarios
if [ ! -f "enhancement_dso_calculation.sql" ]; then
    echo -e "${RED}❌ ERROR: No se encuentra enhancement_dso_calculation.sql${NC}"
    exit 1
fi

# Función para ejecutar SQL
run_sql() {
    local sql_file="$1"
    local description="$2"
    
    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY-RUN] $description${NC}"
        return 0
    fi
    
    log "$description"
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file" >> "$LOG_FILE" 2>&1; then
        echo -e "${GREEN}✅ $description - EXITOSO${NC}"
        return 0
    else
        echo -e "${RED}❌ $description - FALLÓ${NC}"
        echo "Ver detalles en: $LOG_FILE"
        return 1
    fi
}

# Función para crear backup
create_backup() {
    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY-RUN] Creando backup de la tabla EDP${NC}"
        return 0
    fi
    
    mkdir -p "$BACKUP_DIR"
    local backup_file="$BACKUP_DIR/edp_backup_dso_$(date +%Y%m%d_%H%M%S).sql"
    
    log "Creando backup de tabla EDP"
    if PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t edp --data-only > "$backup_file" 2>> "$LOG_FILE"; then
        echo -e "${GREEN}✅ Backup creado: $backup_file${NC}"
        return 0
    else
        echo -e "${RED}❌ Error creando backup${NC}"
        return 1
    fi
}

# Función para verificar conexión
test_connection() {
    log "Verificando conexión a base de datos"
    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY-RUN] Verificando conexión${NC}"
        return 0
    fi
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >> "$LOG_FILE" 2>&1; then
        echo -e "${GREEN}✅ Conexión exitosa${NC}"
        return 0
    else
        echo -e "${RED}❌ Error de conexión${NC}"
        echo "Verifica que PostgreSQL esté ejecutándose y las credenciales sean correctas"
        return 1
    fi
}

# Función para verificar tabla EDP
verify_edp_table() {
    log "Verificando existencia de tabla EDP"
    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY-RUN] Verificando tabla EDP${NC}"
        return 0
    fi
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT COUNT(*) FROM edp;" >> "$LOG_FILE" 2>&1; then
        local count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM edp;" 2>/dev/null | xargs)
        echo -e "${GREEN}✅ Tabla EDP existe con $count registros${NC}"
        return 0
    else
        echo -e "${RED}❌ Tabla EDP no existe${NC}"
        return 1
    fi
}

# Función principal
main() {
    echo -e "${BLUE}🚀 INICIANDO MEJORA DSO...${NC}"
    echo ""
    
    # Solicitar contraseña si no está en variables de entorno
    if [ -z "$DB_PASSWORD" ] && [ -z "$PGPASSWORD" ]; then
        read -s -p "🔐 Contraseña de PostgreSQL: " DB_PASSWORD
        echo ""
        export PGPASSWORD="$DB_PASSWORD"
    fi
    
    # Paso 1: Verificar conexión
    echo -e "${BLUE}📡 PASO 1: Verificando conexión...${NC}"
    if ! test_connection; then
        exit 1
    fi
    echo ""
    
    # Paso 2: Verificar tabla EDP
    echo -e "${BLUE}🔍 PASO 2: Verificando tabla EDP...${NC}"
    if ! verify_edp_table; then
        exit 1
    fi
    echo ""
    
    # Paso 3: Crear backup
    echo -e "${BLUE}💾 PASO 3: Creando backup...${NC}"
    if ! create_backup; then
        echo -e "${YELLOW}⚠️  Continuando sin backup${NC}"
    fi
    echo ""
    
    # Paso 4: Ejecutar mejora DSO
    echo -e "${BLUE}⚡ PASO 4: Implementando mejora DSO...${NC}"
    if ! run_sql "enhancement_dso_calculation.sql" "Aplicando mejoras DSO"; then
        echo -e "${RED}❌ Error en la implementación${NC}"
        exit 1
    fi
    echo ""
    
    # Paso 5: Verificar instalación
    echo -e "${BLUE}✅ PASO 5: Verificando instalación...${NC}"
    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY-RUN] Verificando nuevos campos${NC}"
    else
        local new_fields=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'edp' AND column_name IN ('dso_actual', 'esta_vencido', 'categoria_aging');" 2>/dev/null | xargs)
        
        if [ "$new_fields" -eq "3" ]; then
            echo -e "${GREEN}✅ Nuevos campos DSO instalados correctamente${NC}"
        else
            echo -e "${RED}❌ Algunos campos DSO no se instalaron${NC}"
        fi
        
        # Verificar vistas
        local views=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.views WHERE table_name IN ('v_dso_activos', 'v_aging_analysis');" 2>/dev/null | xargs)
        
        if [ "$views" -eq "2" ]; then
            echo -e "${GREEN}✅ Vistas DSO creadas correctamente${NC}"
        else
            echo -e "${RED}❌ Algunas vistas DSO no se crearon${NC}"
        fi
    fi
    echo ""
    
    # Resumen final
    echo -e "${GREEN}"
    echo "=================================================="
    echo "🎉 MEJORA DSO COMPLETADA EXITOSAMENTE"
    echo "=================================================="
    echo -e "${NC}"
    
    if ! $DRY_RUN; then
        echo "📊 NUEVAS FUNCIONALIDADES DISPONIBLES:"
        echo "  • Campo 'dso_actual' - DSO calculado automáticamente"
        echo "  • Campo 'categoria_aging' - Clasificación automática"
        echo "  • Campo 'esta_vencido' - Flag de vencimiento"
        echo "  • Vista 'v_dso_activos' - Dashboard DSO"
        echo "  • Vista 'v_aging_analysis' - Análisis de aging"
        echo "  • Función 'get_dso_promedio_ponderado()' - KPI DSO"
        echo "  • Función 'get_edps_criticos_dso()' - Alertas"
        echo ""
        echo "📋 EJEMPLOS DE USO:"
        echo "  SELECT * FROM v_dso_activos;"
        echo "  SELECT * FROM v_aging_analysis;"
        echo "  SELECT get_dso_promedio_ponderado();"
        echo ""
    fi
    
    echo "📁 Log completo: $LOG_FILE"
    echo ""
    echo -e "${BLUE}🎯 ¡Tu sistema Pagora MVP ahora tiene DSO inteligente!${NC}"
}

# Ejecutar función principal
main "$@" 