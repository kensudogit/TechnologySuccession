"""テスト実行 API。"""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth.jwt_handler import require_auth
from src.core.testing.runner import SuiteName, run_test_suite
from src.db.database import get_db
from src.db.models import TestRun

router = APIRouter(prefix="/tests", tags=["tests"])


def _serialize_run(run: TestRun, include_details: bool = False) -> dict:
    payload = {
        "run_id": str(run.id),
        "suite": run.suite,
        "status": run.status,
        "summary": run.summary,
        "duration_sec": run.duration_sec,
        "created_at": str(run.created_at),
    }
    if include_details:
        payload["classes"] = run.class_results.get("classes", [])
    return payload


@router.post("/run")
async def run_tests(
    suite: SuiteName = Query(default="unit"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    run = await run_test_suite(db, suite=suite)
    return _serialize_run(run, include_details=True)


@router.get("/runs")
async def list_test_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    result = await db.execute(
        select(TestRun).order_by(TestRun.created_at.desc()).limit(limit)
    )
    runs = result.scalars().all()
    return {"items": [_serialize_run(run) for run in runs]}


@router.get("/runs/{run_id}")
async def get_test_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    run = await db.get(TestRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return _serialize_run(run, include_details=True)
