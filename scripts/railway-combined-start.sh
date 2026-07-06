#!/bin/sh
set -e

# 同一コンテナ内で FastAPI (8080) + Next.js (PORT) を起動
cd /app
uvicorn src.main:app --host 127.0.0.1 --port 8080 --workers 1 &
UVICORN_PID=$!

export COMBINED_DEPLOY=1
export BACKEND_URL=http://127.0.0.1:8080
export NODE_ENV=production

# FastAPI の起動を待つ（最大 30 秒、失敗しても Next.js は起動する）
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8080/health >/dev/null 2>&1; then
    echo "Backend ready on :8080"
    break
  fi
  if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
    echo "WARNING: uvicorn exited early; starting Next.js anyway"
    break
  fi
  sleep 1
done

cd /app/frontend
export PORT="${PORT:-3000}"
export HOSTNAME="0.0.0.0"
echo "Starting Next.js on port ${PORT}"
exec node server.js
