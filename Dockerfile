FROM python:3.12.3-slim

# Configurar variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLASK_ENV=production

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Verificar que las credenciales de Google estén presentes
RUN if [ -f "edp_mvp/app/keys/edp-control-system-f3cfafc0093a.json" ]; then \
        echo "✅ Credenciales de Google Sheets encontradas"; \
    else \
        echo "⚠️ Credenciales de Google Sheets NO encontradas - funcionalidad limitada"; \
    fi

# Crear usuario no-root para seguridad (pero configurar permisos flexibles)
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Hacer el entrypoint script ejecutable
RUN chmod +x entrypoint.sh

# Cambiar al usuario no-root por defecto
USER appuser

# Configurar HOME para el usuario
ENV HOME=/app

# Exponer puerto
EXPOSE 5000

# Usar entrypoint script que maneja verificaciones
ENTRYPOINT ["./entrypoint.sh"] 