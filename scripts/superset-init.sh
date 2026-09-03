#!/bin/bash
set -e

echo "🚀 Initializing Superset..."
superset db upgrade

superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
    --firstname "${SUPERSET_ADMIN_FIRSTNAME:-Admin}" \
    --lastname "${SUPERSET_ADMIN_LASTNAME:-User}" \
    --email "${SUPERSET_ADMIN_EMAIL:-admin@twinlab.local}" \
    --password "${SUPERSET_ADMIN_PASSWORD:-admin}" || echo "Admin user already exists"

superset init

# Register the twin database so dashboards can be built against it right away.
if [ -n "${TWIN_DATABASE_URI}" ]; then
    echo "🔗 Registering twin database connection..."
    superset set-database-uri --database-name twin --uri "${TWIN_DATABASE_URI}" || \
        echo "twin database connection already present"
fi

echo "✅ Superset ready. Starting server..."

# Provision the reference dashboard once the API is up (idempotent, non-fatal).
if [ -f /app/bootstrap_assets.py ] && [ "${TWINLAB_BOOTSTRAP_DASHBOARD:-true}" = "true" ]; then
    ( python /app/bootstrap_assets.py || true ) &
fi

# gthread workers: no gevent C-extension build needed in the slim base image.
exec gunicorn -w "${SUPERSET_WORKERS:-4}" -k gthread --threads 4 --timeout 300 \
    --bind 0.0.0.0:8088 --forwarded-allow-ips='*' \
    'superset.app:create_app()'
