#!/bin/bash

echo "🧹 Eliminando entorno virtual anterior (si existe)..."
rm -rf .venv

echo "🚀 Creando nuevo entorno virtual..."
python3.12 -m venv .venv

echo "🔁 Activando entorno virtual..."
source .venv/bin/activate

echo "📦 Instalando dependencias compatibles..."
pip install --upgrade pip
pip install -r requirements_flask_compatible.txt

echo "✅ Entorno limpio y listo. Puedes ejecutar: source .venv/bin/activate && python run.py"
