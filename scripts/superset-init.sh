#!/bin/bash
set -e

echo "🚀 Initializing Superset..."

# Upgrade database
echo "📊 Upgrading database schema..."
superset db upgrade

# Create admin user
echo "�� Creating admin user..."
superset fab create-admin \
    --username ${SUPERSET_ADMIN_USERNAME} \
    --firstname ${SUPERSET_ADMIN_FIRSTNAME} \
    --lastname ${SUPERSET_ADMIN_LASTNAME} \
    --email ${SUPERSET_ADMIN_EMAIL} \
    --password ${SUPERSET_ADMIN_PASSWORD} || echo "Admin user already exists"

# Initialize Superset
echo "🔐 Initializing Superset..."
superset init

# Sample data loading removed - using PostgreSQL only

echo "✅ Superset initialization complete!"

# Start the server
echo "🚀 Starting Superset server..."
exec gunicorn -w 4 -k gevent --timeout 300 \
    --bind 0.0.0.0:8088 \
    --forwarded-allow-ips=* \
    'superset.app:create_app()'
