#!/bin/sh
set -e

# 同一コンテナ内で FastAPI (8080) + Next.js (PORT) を起動
uvicorn src.main:app --host 127.0.0.1 --port 8080 --workers 1 &
export COMBINED_DEPLOY=1
export BACKEND_URL=http://127.0.0.1:8080
export NODE_ENV=production

cd /app/frontend
export PORT="${PORT:-3000}"
exec npm run start
