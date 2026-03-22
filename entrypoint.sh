#!/bin/sh
set -e

echo "Running database migrations..."
flask db upgrade

echo "Starting application..."
exec gunicorn --bind 0.0.0.0:5060 --workers 2 "app:create_app()"
