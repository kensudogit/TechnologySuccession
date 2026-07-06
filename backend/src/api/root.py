"""ルートページ・静的 UI。"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from src.config import settings

router = APIRouter(tags=["root"])


@router.get("/api")
async def api_index():
  return {
      "app": settings.app_name,
      "version": settings.app_version,
      "docs": "/docs",
      "health": "/health",
      "endpoints": {
          "chat": "POST /chat/ask",
          "records": "GET /records/",
          "stats": "GET /records/stats",
          "ingest_excel": "POST /ingest/excel",
          "ingest_daily_report": "POST /ingest/daily-report",
          "ingest_document": "POST /ingest/document",
          "seed": "POST /admin/seed",
          "eval": "POST /eval/run",
      },
  }


@router.get("/", response_class=HTMLResponse)
async def root_page():
    return HTMLResponse(content=_LANDING_HTML.format(
        app_name=settings.app_name,
        version=settings.app_version,
    ))


_LANDING_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_name}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; font-family: system-ui, sans-serif;
      background: #0f172a; color: #e2e8f0; min-height: 100vh;
    }}
    .wrap {{ max-width: 960px; margin: 0 auto; padding: 2rem 1rem; }}
    h1 {{ color: #34d399; margin-bottom: .25rem; }}
    .sub {{ color: #94a3b8; margin-bottom: 2rem; }}
    .grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .card {{
      background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.25rem;
    }}
    .card h2 {{ margin: 0 0 .5rem; font-size: 1rem; }}
    .card p {{ margin: 0; color: #94a3b8; font-size: .9rem; }}
    a {{ color: #34d399; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{app_name}</h1>
    <p class="sub">保全実績 RAG システム v{version} — API は稼働中です</p>

    <div class="grid">
      <div class="card">
        <h2>API ドキュメント</h2>
        <p><a href="/docs">Swagger UI (/docs)</a></p>
      </div>
      <div class="card">
        <h2>ヘルスチェック</h2>
        <p><a href="/health">/health</a></p>
      </div>
      <div class="card">
        <h2>保全実績一覧</h2>
        <p><a href="/records/">/records/</a></p>
      </div>
      <div class="card">
        <h2>登録件数</h2>
        <p><a href="/records/stats">/records/stats</a></p>
      </div>
      <div class="card">
        <h2>認証 (JWT)</h2>
        <p><a href="/auth/status">/auth/status</a> — POST <code>/auth/login</code> でトークン取得</p>
      </div>
      <div class="card">
        <h2>API 一覧 (JSON)</h2>
        <p><a href="/api">/api</a></p>
      </div>
    </div>
  </div>
</body>
</html>"""
