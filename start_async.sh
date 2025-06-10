#!/usr/bin/env bash
set -euo pipefail

REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

echo "[$(date +"%T")] Iniciando Redis en background..."
redis-server &

sleep 2

echo "[$(date +"%T")] Iniciando Celery worker..."
celery -A edp_mvp.app.celery worker \
  --loglevel=info \
  --events \
  --broker_connection_retry_on_startup=True &

echo "[$(date +"%T")] Iniciando Celery beat (scheduler)..."
celery -A edp_mvp.app.celery beat --loglevel=info &

# Flower vía Celery subcomando
if command -v celery &> /dev/null; then
  echo "[$(date +"%T")] Iniciando Flower (monitor) en http://localhost:5555..."
  celery -A edp_mvp.app.celery --broker="$REDIS_URL" flower &
else
  echo "[$(date +"%T")] Celery no encontró el subcomando flower, salteando Flower..."
fi

echo "[$(date +"%T")] Todos los servicios se han iniciado."
echo "Presiona Ctrl+C para detenerlos."

wait
