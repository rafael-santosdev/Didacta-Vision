#!/bin/bash
set -e

cd /app

echo ">>> Aplicando migrações..."
python manage.py migrate --noinput

echo ">>> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo ">>> Iniciando Gunicorn..."
PORT="${PORT:-8000}"
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers 2 \
    --threads 2 \
    --worker-class gthread \
    --access-logfile - \
    --error-logfile - \
    --capture-output
