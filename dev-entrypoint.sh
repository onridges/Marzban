#!/usr/bin/env bash
set -euo pipefail

DB_HOST=${DB_HOST:-mariadb}
echo "Waiting for ${DB_HOST}..."
for i in $(seq 1 60); do
  (echo > /dev/tcp/${DB_HOST}/3306) >/dev/null 2>&1 && break || sleep 1
done

echo "Running alembic migrations..."
alembic upgrade heads

echo "Starting application..."
if [ "${DISABLE_DASHBOARD_DEV:-false}" != "true" ]; then
  echo "Starting dashboard dev in background..."
  (
    cd /app/app/dashboard || exit 1
    yarn install --silent || true
    yarn dev &
  )
else
  echo "Dashboard dev disabled; will serve built statics."
fi

exec python main.py
