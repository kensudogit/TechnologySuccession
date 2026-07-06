"""管理 API。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.seed.seed_service import seed_test_data
from src.db.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/seed")
async def seed_database(db: AsyncSession = Depends(get_db)):
    """PostgreSQL にテストデータを投入する。"""
    result = await seed_test_data(db)
    return {"status": "ok", **result}
