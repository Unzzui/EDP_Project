.PHONY: help install dev prod clean test lint docker-up docker-down

# Variables
PYTHON := python3
PIP := pip
VENV := .venv
PROJECT := edp_mvp

help: ## Mostrar ayuda
	@echo "🚀 EDP MVP - Comandos disponibles:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo

install: ## Instalar dependencias
	@echo "📦 Instalando dependencias..."
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip setuptools wheel
	$(VENV)/bin/pip install -r requirements.txt
	@echo "✅ Dependencias instaladas"

dev: ## Iniciar en modo desarrollo (script optimizado)
	@echo "🚀 Iniciando modo desarrollo..."
	@chmod +x start_app_optimized.sh
	@./start_app_optimized.sh

dev-original: ## Iniciar con script original
	@echo "🚀 Iniciando modo desarrollo (original)..."
	@chmod +x start_app.sh
	@./start_app.sh

prod: ## Iniciar en modo producción
	@echo "🚀 Iniciando modo producción..."
	$(VENV)/bin/python run_production.py

clean: ## Limpiar archivos temporales
	@echo "🧹 Limpiando archivos temporales..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -f celerybeat-schedule*
	rm -f /tmp/edp_mvp_*/
	@echo "✅ Limpieza completada"

test: ## Ejecutar tests
	@echo "🧪 Ejecutando tests..."
	$(VENV)/bin/python -m pytest edp_mvp/test/ -v
	@echo "✅ Tests completados"

lint: ## Revisar código con linters
	@echo "🔍 Revisando código..."
	$(VENV)/bin/python -m flake8 edp_mvp/ --max-line-length=88
	$(VENV)/bin/python -m black edp_mvp/ --check
	@echo "✅ Código revisado"

format: ## Formatear código
	@echo "🎨 Formateando código..."
	$(VENV)/bin/python -m black edp_mvp/
	$(VENV)/bin/python -m isort edp_mvp/
	@echo "✅ Código formateado"

docker-up: ## Iniciar con Docker Compose
	@echo "🐳 Iniciando servicios con Docker..."
	docker-compose up -d
	@echo "✅ Servicios iniciados en:"
	@echo "   • Flask: http://localhost:5000"
	@echo "   • Flower: http://localhost:5555"

docker-down: ## Detener servicios Docker
	@echo "🐳 Deteniendo servicios Docker..."
	docker-compose down
	@echo "✅ Servicios detenidos"

docker-logs: ## Ver logs de Docker
	docker-compose logs -f

docker-rebuild: ## Reconstruir imágenes Docker
	@echo "🐳 Reconstruyendo imágenes..."
	docker-compose build --no-cache
	@echo "✅ Imágenes reconstruidas"

status: ## Verificar estado de servicios
	@echo "🏥 Estado de servicios:"
	@$(VENV)/bin/python status_check.py 2>/dev/null || echo "❌ status_check.py no disponible"

deps-check: ## Verificar dependencias
	@echo "🔍 Verificando dependencias del sistema..."
	@command -v python3 >/dev/null && echo "✅ Python3: $(shell python3 --version)" || echo "❌ Python3 no encontrado"
	@command -v redis-server >/dev/null && echo "✅ Redis: $(shell redis-server --version | head -1)" || echo "❌ Redis no encontrado"
	@command -v docker >/dev/null && echo "✅ Docker: $(shell docker --version)" || echo "⚠️  Docker no encontrado"

setup: install deps-check ## Setup inicial completo
	@echo "🎉 Setup completado. Usa 'make dev' para iniciar" 