# TechnologySuccession RAG

製造現場の保全実績データ（Excel・日報・PDF）を PostgreSQL + pgvector にデータベース化し、RAG によるトラブルシューティングを支援するシステムです。

## 技術スタック

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, pgvector
- **Frontend**: Next.js 14, React, TypeScript
- **DB**: PostgreSQL 16 + pgvector

## 前提

- **Python 3.11**（Docker イメージで同梱）。ローカル Python 3.14 では `asyncpg` のビルドが失敗する場合があります。
- Docker Desktop（推奨）または PostgreSQL 16 + pgvector

## クイックスタート

### 1. Docker Compose（推奨）

`docker compose build` が失敗する場合は、先に backend イメージを直接ビルドしてください:

```bash
cd TechnologySuccession
docker build -t tech-succession-backend ./backend
docker compose up -d postgres
```

```bash
cp backend/.env.example backend/.env
# OPENAI_API_KEY を設定（任意: 未設定でもルールベース回答で動作）

docker compose up backend
# または: docker run --rm -p 8000:8000 --network technologysuccession_default \
#   -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/technology_succession \
#   tech-succession-backend
```

別ターミナル:

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### 2. サンプルデータ投入

```bash
cd backend
pip install -r requirements.txt
python scripts/seed_data.py
```

### 3. アクセス

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## 主な機能

| 機能 | 説明 |
|------|------|
| データ取り込み | Excel / 日報 / PDF のクレンジング + DB 化 + Embedding |
| RAG チャット | ハイブリッド検索（pgvector + FTS）+ GPT-4o 回答 |
| 精度評価 | ゴールド Q&A セットによる Hit@k / キーワードカバレッジ |

## API エンドポイント

- `POST /ingest/excel` — Excel 取り込み
- `POST /ingest/daily-report` — 日報取り込み
- `POST /ingest/document` — PDF/画像取り込み
- `POST /chat/ask` — RAG 質問応答
- `POST /eval/run` — 精度評価実行
- `GET /records/stats` — 登録件数

## Railway デプロイ

### Backend（API）

リポジトリルートの `Dockerfile` と `railway.toml` を使用します。

1. Railway で GitHub リポジトリ `TechnologySuccession` を接続
2. **Root Directory**: 空（リポジトリルート）のまま
3. PostgreSQL プラグインを追加（pgvector 対応イメージ推奨）
4. 環境変数を設定:

| 変数 | 説明 |
|------|------|
| `DATABASE_URL` | PostgreSQL 接続 URL（Railway が自動設定） |
| `OPENAI_API_KEY` | OpenAI API キー（任意） |
| `ALLOWED_ORIGINS` | フロント URL（例: `https://your-app.up.railway.app`） |
| `DATA_DIR` | `/app/data`（Dockerfile で設定済み） |

起動時に DB が空の場合、サンプルデータが自動投入されます。

### Frontend（別サービス）

1. 新規 Railway サービスを追加
2. **Root Directory**: `frontend`
3. 環境変数: `NEXT_PUBLIC_API_BASE_URL=https://<backend-url>`

## テスト

```bash
cd backend
pytest
```

## プロジェクト構成

```
TechnologySuccession/
├── Dockerfile        # Railway 用（backend ビルド）
├── railway.toml      # Railway 設定
├── backend/          # FastAPI + RAG パイプライン
├── frontend/         # Next.js UI
├── data/samples/     # サンプルデータ
├── data/eval/        # 評価用 Q&A
└── docker-compose.yml
```
