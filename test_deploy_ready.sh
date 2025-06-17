#!/bin/bash

# Script para probar la configuración local antes del deploy a Render
echo "🧪 SCRIPT DE TESTING LOCAL - EDP MVP"
echo "=" * 60

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success_count=0
total_tests=0

# Función para reportar resultados
report_test() {
    local test_name="$1"
    local success="$2"
    
    total_tests=$((total_tests + 1))
    
    if [ "$success" = true ]; then
        echo -e "✅ ${GREEN}$test_name${NC}"
        success_count=$((success_count + 1))
    else
        echo -e "❌ ${RED}$test_name${NC}"
    fi
}

echo "📋 VERIFICACIONES PREVIAS AL DEPLOY"
echo "=" * 40

# Test 1: Verificar archivos críticos
echo "🔍 Verificando archivos críticos..."
critical_files=(
    "Dockerfile"
    "entrypoint.sh"
    "requirements.txt" 
    "wsgi.py"
    "run_production.py"
    "fix_render_secrets.py"
    "verify_secrets.py"
    "debug_env.py"
    "render.yaml"
    ".env.production"
)

all_files_exist=true
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (FALTA)"
        all_files_exist=false
    fi
done

# Verificar archivos opcionales
optional_files=(
    "gunicorn_config.py"
    ".env.development"
    "DEPLOY_RENDER_DOCKER.md"
    "BRANCH_STRATEGY.md"
)

echo "  📋 Archivos opcionales:"
for file in "${optional_files[@]}"; do
    if [ -f "$file" ]; then
        echo "    ✅ $file"
    else
        echo "    ⚠️ $file (opcional, no crítico)"
    fi
done

report_test "Archivos críticos presentes" $all_files_exist

# Test 2: Verificar que el Dockerfile tiene sintaxis básica válida
echo "🐳 Verificando sintaxis del Dockerfile..."
dockerfile_ok=true

# Verificar que el Dockerfile existe y tiene contenido básico
if [ -f "Dockerfile" ]; then
    # Verificar que tiene las instrucciones básicas
    required_instructions=("FROM" "WORKDIR" "COPY" "RUN" "EXPOSE")
    
    for instruction in "${required_instructions[@]}"; do
        if grep -q "^$instruction" Dockerfile; then
            echo "  ✅ Instrucción $instruction encontrada"
        else
            echo "  ❌ Instrucción $instruction falta"
            dockerfile_ok=false
        fi
    done
    
    # Verificar que no hay errores de sintaxis obvios
    if grep -q "^FROM.*:.*$" Dockerfile; then
        echo "  ✅ FROM con tag válido"
    else
        echo "  ⚠️ FROM sin tag específico (puede estar bien)"
    fi
    
else
    echo "  ❌ Dockerfile no encontrado"
    dockerfile_ok=false
fi

report_test "Dockerfile válido" $dockerfile_ok

# Test 3: Verificar scripts de Python
echo "🐍 Verificando sintaxis de scripts Python..."
python_scripts=(
    "verify_secrets.py"
    "debug_env.py"
    "fix_render_secrets.py"
    "wsgi.py"
    "run_production.py"
)

all_python_ok=true
for script in "${python_scripts[@]}"; do
    if python3 -m py_compile "$script" 2>/dev/null; then
        echo "  ✅ $script"
    else
        echo "  ❌ $script (Error de sintaxis)"
        all_python_ok=false
    fi
done

report_test "Scripts Python válidos" $all_python_ok

# Test 4: Verificar variables de entorno requeridas
echo "🔧 Verificando configuración de entorno..."
required_vars=(
    "SHEET_ID"
)

env_file=".env.production"
if [ -f "$env_file" ]; then
    echo "  ✅ Archivo $env_file existe"
    
    all_vars_present=true
    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" "$env_file"; then
            echo "  ✅ $var configurado"
        else
            echo "  ❌ $var falta en $env_file"
            all_vars_present=false
        fi
    done
else
    echo "  ❌ Archivo $env_file no encontrado"
    all_vars_present=false
fi

report_test "Variables de entorno configuradas" $all_vars_present

# Test 5: Verificar credenciales de Google (opcional)
echo "🔑 Verificando credenciales de Google..."
google_creds_found=false

possible_creds=(
    "edp_mvp/app/keys/edp-control-system-f3cfafc0093a.json"
    "./edp-control-system-f3cfafc0093a.json"
)

for creds_file in "${possible_creds[@]}"; do
    if [ -f "$creds_file" ]; then
        echo "  ✅ Credenciales encontradas: $creds_file"
        
        # Verificar que es JSON válido
        if python3 -c "import json; json.load(open('$creds_file'))" 2>/dev/null; then
            echo "  ✅ Formato JSON válido"
            google_creds_found=true
            break
        else
            echo "  ❌ Formato JSON inválido"
        fi
    fi
done

if [ "$google_creds_found" = false ]; then
    echo "  ⚠️ No se encontraron credenciales locales (se usarán Secret Files en Render)"
    google_creds_found=true  # No es un error crítico
fi

report_test "Credenciales de Google" $google_creds_found

# Test 6: Verificar que los scripts de verificación funcionan
echo "🔍 Ejecutando scripts de verificación..."

# Verificar debug_env.py
if python3 debug_env.py > /dev/null 2>&1; then
    debug_env_ok=true
    echo "  ✅ debug_env.py ejecuta sin errores"
else
    debug_env_ok=false
    echo "  ❌ debug_env.py falla"
fi

report_test "Scripts de verificación funcionan" $debug_env_ok

# Test 7: Verificar estructura de directorios
echo "📁 Verificando estructura de proyecto..."
required_dirs=(
    "edp_mvp"
    "edp_mvp/app"
    "edp_mvp/app/controllers"
    "edp_mvp/app/models"
    "edp_mvp/app/services"
    "edp_mvp/app/templates"
    "edp_mvp/app/static"
)

all_dirs_exist=true
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir"
    else
        echo "  ❌ $dir (FALTA)"
        all_dirs_exist=false
    fi
done

report_test "Estructura de directorios" $all_dirs_exist

# Resumen final
echo ""
echo "🎯 RESUMEN DE TESTS"
echo "=" * 40

if [ $success_count -eq $total_tests ]; then
    echo -e "🎉 ${GREEN}TODOS LOS TESTS PASARON ($success_count/$total_tests)${NC}"
    echo -e "✅ ${GREEN}El proyecto está listo para deploy en Render${NC}"
    
    echo ""
    echo "📋 PRÓXIMOS PASOS PARA DEPLOY:"
    echo "1. Subir código a repositorio Git"
    echo "2. Crear servicio en Render desde GitHub"
    echo "3. Configurar Secret Files en Render:"
    echo "   - Filename: edp-control-system-f3cfafc0093a.json"
    echo "   - Content: [JSON de credenciales Google]"
    echo "4. Configurar variables de entorno en Render"
    echo "5. Realizar deploy"
    
    exit 0
else
    failed_tests=$((total_tests - success_count))
    echo -e "⚠️ ${YELLOW}$failed_tests/$total_tests tests fallaron${NC}"
    echo -e "❌ ${RED}Arreglar problemas antes del deploy${NC}"
    
    echo ""
    echo "🔧 ACCIONES RECOMENDADAS:"
    echo "- Revisar los tests fallidos arriba"
    echo "- Verificar configuración de archivos"
    echo "- Ejecutar nuevamente este script"
    
    exit 1
fi
