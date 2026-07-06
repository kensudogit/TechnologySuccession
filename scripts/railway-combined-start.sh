#!/bin/sh
set -e

# 同一コンテナ内で FastAPI (8080) + Next.js (PORT) を起動
uvicorn src.main:app --host 127.0.0.1 --port 8080 --workers 1 &
export BACKEND_URL=http://127.0.0.1:8080

cd /app/frontend
exec npm run start -- -p "${PORT:-3000}"
