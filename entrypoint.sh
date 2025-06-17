#!/bin/bash

#!/bin/bash

# Entrypoint script para manejar Secret Files y verificaciones en Render
echo "🔧 Iniciando entrypoint script..."

# Función para verificar permisos y contenido de Secret Files
check_secret_files() {
    if [ -d "/etc/secrets" ]; then
        echo "📁 Directorio /etc/secrets encontrado"
        echo "👤 Usuario actual: $(whoami) (UID: $(id -u))"
        echo "📋 Listando Secret Files disponibles:"
        ls -la /etc/secrets/ 2>/dev/null || echo "⚠️ No se puede listar /etc/secrets/ - verificando acceso..."
        
        # Intentar leer archivos específicos si existen
        for secret_file in "/etc/secrets/GOOGLE_CREDENTIALS" "/etc/secrets/google-credentials.json"; do
            if [ -f "$secret_file" ]; then
                echo "✅ Secret File encontrado: $secret_file"
                echo "📄 Permisos: $(ls -l "$secret_file" 2>/dev/null || echo 'No se pueden ver permisos')"
                # Verificar si es legible
                if [ -r "$secret_file" ]; then
                    echo "✅ Archivo legible"
                    head -c 50 "$secret_file" 2>/dev/null && echo "..." || echo "⚠️ No se puede leer contenido"
                else
                    echo "❌ Archivo no legible"
                fi
            fi
        done
    else
        echo "📁 Directorio /etc/secrets no encontrado - usando modo demo"
    fi
}

# Ejecutar verificación de Secret Files
check_secret_files

# Verificaciones de entorno
echo "🔍 Iniciando verificaciones..."
python debug_env.py

echo "🔐 Verificando Secret Files..."
python verify_secrets.py

echo "🔍 Iniciando init_db..."
python init_db.py

echo "🚀 Iniciando Gunicorn..."
exec gunicorn --config gunicorn_config.py wsgi:application
