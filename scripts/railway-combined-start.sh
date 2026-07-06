#!/bin/sh
set -e

# Railway の PORT と衝突しないよう FastAPI は別ポートで起動
INTERNAL_BACKEND_PORT="${INTERNAL_BACKEND_PORT:-18080}"

# 同一コンテナ内で FastAPI (内部) + Next.js (Railway PORT) を起動
cd /app
uvicorn src.main:app --host 127.0.0.1 --port "$INTERNAL_BACKEND_PORT" --workers 1 &
UVICORN_PID=$!

export COMBINED_DEPLOY=1
export INTERNAL_BACKEND_PORT
export BACKEND_URL="http://127.0.0.1:${INTERNAL_BACKEND_PORT}"
export NODE_ENV=production

# FastAPI の起動を待つ（最大 30 秒、失敗しても Next.js は起動する）
for i in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${INTERNAL_BACKEND_PORT}/health" >/dev/null 2>&1; then
    echo "Backend ready on :${INTERNAL_BACKEND_PORT}"
    break
  fi
  if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
    echo "WARNING: uvicorn exited early; starting Next.js anyway"
    break
  fi
  sleep 1
done

cd /app/frontend
export HOSTNAME="0.0.0.0"
echo "Starting Next.js on port ${PORT:-3000} (backend :${INTERNAL_BACKEND_PORT})"
exec node server.js
