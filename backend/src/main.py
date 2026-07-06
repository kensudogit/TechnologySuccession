"""TechnologySuccession RAG — FastAPI アプリケーション。"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import admin, auth, chat, ingest, records, root
from src.config import settings
from src.core.seed.seed_service import seed_if_empty
from src.db.database import init_db

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    await init_db()
    seeded = await seed_if_empty()
    if seeded:
        logger.info("Auto-seeded test data on startup: %s", seeded)
    logger.info(
        "Config: openai=%s auth=%s db=%s",
        "configured" if settings.openai_configured else "not set",
        "enabled" if settings.auth_enabled else "disabled",
        "configured" if settings.database_url else "missing",
    )
    logger.info("Application started")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="製造現場保全実績 RAG システム — トラブルシューティング支援",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root.router)
app.include_router(auth.router)
app.include_router(ingest.router)
app.include_router(chat.router)
app.include_router(records.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "openai_configured": settings.openai_configured,
        "auth_enabled": settings.auth_enabled,
    }
