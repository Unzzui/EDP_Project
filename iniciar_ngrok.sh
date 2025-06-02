#!/bin/bash

echo "🚀 Iniciando EDP Project con ngrok..."

# Verificar que estamos en el directorio correcto
if [ ! -f "run.py" ]; then
    echo "❌ No se encuentra run.py. Asegúrate de estar en el directorio raíz del proyecto."
    exit 1
fi

# Verificar estructura
if [ ! -d "edp_mvp/app" ]; then
    echo "❌ No se encuentra la estructura edp_mvp/app"
    exit 1
fi

# Verificar que ngrok esté instalado
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok no está instalado. Instálalo primero."
    echo "💡 Instalar con: sudo snap install ngrok"
    exit 1
fi


# Instalar dependencias si es necesario
if [ -f "requirements.txt" ]; then
    echo "📦 Verificando dependencias..."
    pip install -r requirements.txt --quiet
fi

# Matar procesos anteriores
echo "🧹 Limpiando procesos anteriores..."
# pkill -f "python.*run" 2>/dev/null
# pkill -f "ngrok" 2>/dev/null
sleep 2

echo "🔧 Iniciando aplicación Flask..."

# Usar run_production.py si existe, sino run.py
if [ -f "run_production.py" ]; then
    python run_production.py &
    echo "📱 Usando configuración de producción"
else
    python run.py &
    echo "📱 Usando configuración de desarrollo"
fi

FLASK_PID=$!

# Esperar a que la aplicación inicie
echo "⏳ Esperando que Flask inicie..."
sleep 8

# Verificar que la aplicación esté corriendo
echo "🔍 Verificando que Flask esté corriendo..."
for i in {1..10}; do
    if curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "✅ Aplicación iniciada correctamente en http://localhost:5000"
        break
    elif [ $i -eq 10 ]; then
        echo "❌ Error: La aplicación no responde después de 10 intentos"
        echo "📋 Logs del proceso:"
        ps aux | grep python
        kill $FLASK_PID 2>/dev/null
        exit 1
    else
        echo "⏳ Intento $i/10 - Esperando..."
        sleep 2
    fi
done

echo ""
echo "🌐 Iniciando túnel ngrok..."
echo "📱 Panel de control ngrok: http://localhost:4040"
echo "🔗 La URL pública aparecerá a continuación..."
echo ""

# Iniciar ngrok
ngrok http 5000 --log=stdout

# Cleanup al salir
trap "echo '🧹 Limpiando procesos...'; kill $FLASK_PID 2>/dev/null; pkill -f ngrok 2>/dev/null" EXIT