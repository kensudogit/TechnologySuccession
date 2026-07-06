"""データベース接続・セッション管理。"""
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url_normalized,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=settings.database_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

db_ready = False


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("DB connection check failed: %s", exc)
        return False


async def init_db() -> None:
    """拡張機能とテーブルを作成する。"""
    global db_ready
    from src.db import models  # noqa: F401

    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception as exc:
            logger.warning("pgvector extension unavailable: %s", exc)

        await conn.run_sync(Base.metadata.create_all)

        try:
            await conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_maintenance_records_search
                    ON maintenance_records USING gin (search_vector)
                    """
                )
            )
        except Exception as exc:
            logger.warning("search_vector index skipped: %s", exc)

        try:
            await conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_record_chunks_embedding
                    ON record_chunks USING hnsw (embedding vector_cosine_ops)
                    """
                )
            )
        except Exception as exc:
            logger.warning("embedding index skipped: %s", exc)

    db_ready = True
    logger.info("Database initialized")
