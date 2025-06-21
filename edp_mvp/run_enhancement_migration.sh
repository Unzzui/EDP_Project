#!/bin/bash

# 🎯 SCRIPT DE MIGRACIÓN CRÍTICA: Conversión de Pagora MVP a Herramienta de Inteligencia Operacional
# 
# Este script ejecuta la migración completa que transforma la base de datos
# de un simple tracker transaccional a una plataforma de inteligencia operacional completa.
#
# Autor: Pagora MVP Enhancement Team
# Fecha: 2025-01-28

set -e  # Exit on any error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Banner
echo -e "${PURPLE}"
echo "================================================================================"
echo "🎯 MIGRACIÓN CRÍTICA: Pagora MVP → Herramienta de Inteligencia Operacional"
echo "================================================================================"
echo -e "${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "migration_database_enhancement.py" ]; then
    echo -e "${RED}❌ Error: No se encuentra el archivo de migración.${NC}"
    echo "Asegúrate de ejecutar este script desde el directorio edp_mvp/"
    exit 1
fi

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  -p, --python     Usar el script Python (recomendado)"
    echo "  -s, --sql        Usar el script SQL directo"
    echo "  -b, --backup     Solo crear backup de seguridad"
    echo "  -v, --verify     Solo verificar estado de la migración"
    echo "  -h, --help       Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 --python      # Ejecutar migración completa con Python"
    echo "  $0 --sql         # Ejecutar migración con SQL directo"
    echo "  $0 --backup      # Solo crear backup"
    echo "  $0 --verify      # Verificar estado actual"
}

# Función para crear backup
create_backup() {
    echo -e "${BLUE}📋 Creando backup de seguridad...${NC}"
    
    # Crear directorio de backup si no existe
    mkdir -p backups
    
    # Generar timestamp
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
    # Backup de SQLite si existe
    if [ -f "instance/database.db" ]; then
        cp "instance/database.db" "backups/database_backup_${TIMESTAMP}.db"
        echo -e "${GREEN}✅ Backup SQLite creado: backups/database_backup_${TIMESTAMP}.db${NC}"
    fi
    
    # Backup de logs
    if [ -f "migration_enhancement.log" ]; then
        cp "migration_enhancement.log" "backups/migration_log_${TIMESTAMP}.log"
    fi
    
    echo -e "${GREEN}✅ Backup de seguridad completado${NC}"
}

# Función para verificar estado
verify_migration() {
    echo -e "${BLUE}🔍 Verificando estado de la migración...${NC}"
    
    python3 -c "
import sqlite3
import os

db_path = 'instance/database.db'
if not os.path.exists(db_path):
    print('❌ Base de datos no encontrada')
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar tablas nuevas
tables_to_check = ['edp_status_history', 'client_profiles', 'kpi_snapshots']
for table in tables_to_check:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'✅ {table}: {count} registros')
    except:
        print(f'❌ {table}: No existe')

# Verificar campos nuevos en EDP
try:
    cursor.execute('PRAGMA table_info(edp)')
    columns = [row[1] for row in cursor.fetchall()]
    
    new_fields = ['prioridad', 'complejidad_tecnica', 'dias_en_cliente', 'fecha_aprobacion_interna']
    for field in new_fields:
        if field in columns:
            print(f'✅ Campo {field}: Existe')
        else:
            print(f'❌ Campo {field}: No existe')
except Exception as e:
    print(f'❌ Error verificando campos: {e}')

conn.close()
"
}

# Función para ejecutar migración con Python
run_python_migration() {
    echo -e "${BLUE}🐍 Ejecutando migración con Python...${NC}"
    
    # Verificar que existe el entorno virtual
    if [ ! -d "../.venv" ] && [ ! -d ".venv" ]; then
        echo -e "${YELLOW}⚠️  No se encontró entorno virtual. Instalando dependencias...${NC}"
        python3 -m pip install -r ../requirements.txt || python3 -m pip install -r requirements.txt
    fi
    
    # Activar entorno virtual si existe
    if [ -d "../.venv" ]; then
        source ../.venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Ejecutar migración
    python3 migration_database_enhancement.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Migración Python completada exitosamente${NC}"
    else
        echo -e "${RED}❌ Error en migración Python${NC}"
        exit 1
    fi
}

# Función para ejecutar migración con SQL
run_sql_migration() {
    echo -e "${BLUE}📊 Ejecutando migración con SQL directo...${NC}"
    
    # Verificar que existe la base de datos
    if [ ! -f "instance/database.db" ]; then
        echo -e "${RED}❌ No se encontró la base de datos SQLite${NC}"
        exit 1
    fi
    
    # Ejecutar script SQL
    sqlite3 instance/database.db < enhancement_migration.sql
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Migración SQL completada exitosamente${NC}"
    else
        echo -e "${RED}❌ Error en migración SQL${NC}"
        exit 1
    fi
}

# Función para mostrar resumen final
show_summary() {
    echo -e "${PURPLE}"
    echo "================================================================================"
    echo "🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE"
    echo "================================================================================"
    echo -e "${NC}"
    echo -e "${GREEN}Tu base de datos ahora incluye:${NC}"
    echo -e "${GREEN}✅ Tipos monetarios DECIMAL para precisión financiera${NC}"
    echo -e "${GREEN}✅ Historial automático de cambios de estado${NC}"
    echo -e "${GREEN}✅ Perfiles de clientes para análisis predictivo${NC}"
    echo -e "${GREEN}✅ Tracking temporal granular de procesos${NC}"
    echo -e "${GREEN}✅ KPI snapshots para análisis de tendencias${NC}"
    echo -e "${GREEN}✅ Triggers automáticos para consistencia${NC}"
    echo -e "${GREEN}✅ Índices optimizados para performance${NC}"
    echo ""
    echo -e "${BLUE}🚀 Pagora MVP ahora es una herramienta de inteligencia operacional completa!${NC}"
    echo ""
    echo -e "${YELLOW}📋 Próximos pasos recomendados:${NC}"
    echo "1. Verificar la migración: $0 --verify"
    echo "2. Reiniciar la aplicación para cargar nuevos modelos"
    echo "3. Probar las nuevas funcionalidades en el dashboard"
    echo "4. Revisar los logs de migración: tail -f migration_enhancement.log"
}

# Procesar argumentos
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -b|--backup)
        create_backup
        exit 0
        ;;
    -v|--verify)
        verify_migration
        exit 0
        ;;
    -s|--sql)
        echo -e "${YELLOW}🚨 ADVERTENCIA: Ejecutando migración SQL directa${NC}"
        echo "Esto modificará permanentemente tu base de datos."
        read -p "¿Estás seguro? (s/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            create_backup
            run_sql_migration
            verify_migration
            show_summary
        else
            echo "Migración cancelada."
            exit 0
        fi
        ;;
    -p|--python|"")
        echo -e "${YELLOW}🚨 ADVERTENCIA: Ejecutando migración crítica de base de datos${NC}"
        echo "Esto transformará tu base de datos en una herramienta de inteligencia operacional."
        echo "Se creará un backup automático antes de proceder."
        echo ""
        read -p "¿Continuar con la migración? (s/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            create_backup
            run_python_migration
            verify_migration
            show_summary
        else
            echo "Migración cancelada."
            exit 0
        fi
        ;;
    *)
        echo -e "${RED}❌ Opción no válida: $1${NC}"
        show_help
        exit 1
        ;;
esac 