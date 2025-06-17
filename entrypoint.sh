#!/bin/bash

# Entrypoint script para manejar permisos de Secret Files en Render
echo "🔧 Iniciando entrypoint script..."
echo "👤 Usuario actual: $(whoami) (UID: $(id -u), GID: $(id -g))"
echo "📁 Directorio actual: $(pwd)"

# Verificar si somos root y ejecutar corrección de Secret Files
if [ "$(id -u)" = "0" ]; then
    echo "🔧 Ejecutando como root - corrigiendo Secret Files..."
    
    # Verificar que el script existe
    if [ -f "fix_render_secrets.py" ]; then
        echo "✅ Script fix_render_secrets.py encontrado"
        
        # Ejecutar script de corrección de Secret Files con output detallado
        echo "📋 Ejecutando fix_render_secrets.py..."
        python fix_render_secrets.py
        exit_code=$?
        echo "📊 Script terminó con código: $exit_code"
    else
        echo "❌ Script fix_render_secrets.py NO encontrado"
        ls -la *.py | head -10
    fi
    
    # Verificar resultado después del script
    echo "🔍 Verificando resultado de corrección..."
    if [ -d "/app/secrets" ]; then
        echo "✅ Directorio /app/secrets existe"
        ls -la /app/secrets/ 2>/dev/null || echo "⚠️ No se puede listar /app/secrets"
    else
        echo "❌ Directorio /app/secrets NO existe"
    fi
    
    # Cambiar a usuario no-root para ejecutar la aplicación
    export HOME=/app
    echo "👤 Cambiando a usuario appuser..."
    
    # Verificar que appuser existe
    if id appuser >/dev/null 2>&1; then
        echo "✅ Usuario appuser existe"
        exec gosu appuser "$0" "$@"
    else
        echo "❌ Usuario appuser NO existe, ejecutando como root (no recomendado)"
        # Continuar como root si no hay appuser
    fi
else
    echo "👤 Ejecutando como usuario no-root: $(whoami)"
fi

# Verificaciones de entorno (como usuario appuser o root)
echo ""
echo "🔍 === VERIFICACIONES DE ENTORNO ==="
python debug_env.py

echo ""
echo "🔍 === DIAGNÓSTICO COMPLETO ==="
python diagnose_render.py

echo ""
echo "🔐 === VERIFICANDO SECRET FILES ==="
python verify_secrets.py

echo ""
echo "🔍 === INICIALIZANDO BASE DE DATOS ==="
python init_db.py

echo ""
echo "🚀 === INICIANDO GUNICORN ==="
exec gunicorn --config gunicorn_config.py wsgi:application
