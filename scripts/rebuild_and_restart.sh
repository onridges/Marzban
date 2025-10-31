#!/usr/bin/env bash
set -eo pipefail

# 项目根目录 (脚本在scripts子目录中，需要向上一级)
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 加载根目录下的 .env（如果存在），让脚本获得数据库、端口、SSL等配置
if [ -f "$ROOT_DIR/.env" ]; then
  echo "Loading env from $ROOT_DIR/.env"
  set -a
  . "$ROOT_DIR/.env"
  set +a
fi

echo "[1/3] 构建前端仪表盘..."
(
  cd "$ROOT_DIR/app/dashboard"
  if [ -f package.json ] && command -v npm >/dev/null 2>&1; then
    npm install
  fi
)

"$ROOT_DIR/build_dashboard.sh"

echo "[2/3] Restarting backend (uvicorn on :8000)..."
# Stop process occupying port 8000 (if any)
PID="$(lsof -ti tcp:8000 2>/dev/null || echo "")"
if [ -n "$PID" ]; then
  echo "Found running process PID=${PID}, terminating..."
  for p in $PID; do
  kill "$p" || true
 done
  sleep 1
fi

PORT="${UVICORN_PORT:-8000}"
SCHEME="http"
if [ -n "$UVICORN_SSL_CERTFILE" ] && [ -n "$UVICORN_SSL_KEYFILE" ]; then
  SCHEME="https"
fi
BASE_URL="$SCHEME://127.0.0.1:$PORT"

echo "Starting backend (respecting .env) and running migrations..."
(cd "$ROOT_DIR" && nohup bash -lc "alembic upgrade head; python3 main.py" >/tmp/marzban_backend.log 2>&1 &)

echo "[3/3] Waiting for backend to be ready..."
ATTEMPTS=0
until curl -sSf -k "$BASE_URL/" >/dev/null 2>&1; do
  ATTEMPTS=$((ATTEMPTS+1))
  if [ "$ATTEMPTS" -gt 20 ]; then
    echo "Backend startup timed out. Check /tmp/marzban_backend.log"
    exit 1
  fi
  sleep 0.5
done

echo "✅ Frontend built and backend restarted:"
echo "   - Backend: $BASE_URL/"
echo "   - Dashboard: $BASE_URL${DASHBOARD_PATH:-/dashboard/}"
echo "   - Statics: $BASE_URL/statics/"
