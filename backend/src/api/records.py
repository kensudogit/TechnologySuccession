"""記録・評価 API。"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.evaluation.runner import run_evaluation
from src.db.database import get_db
from src.db.models import EvalRun, IngestJob, MaintenanceRecord

router = APIRouter(tags=["records"])


@router.get("/records/")
async def list_records(
    skip: int = 0,
    limit: int = 50,
    equipment_name: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MaintenanceRecord).order_by(MaintenanceRecord.event_date.desc().nullslast())
    if equipment_name:
        stmt = stmt.where(MaintenanceRecord.equipment_name.ilike(f"%{equipment_name}%"))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    records = result.scalars().all()
    return {
        "items": [
            {
                "id": str(r.id),
                "equipment_name": r.equipment_name,
                "equipment_id": r.equipment_id,
                "line_name": r.line_name,
                "event_date": str(r.event_date) if r.event_date else None,
                "record_category": r.record_category.value if r.record_category else None,
                "symptom": r.symptom,
                "root_cause": r.root_cause,
                "action_taken": r.action_taken,
                "measured_value": r.measured_value,
                "unit": r.unit,
                "result": r.result,
                "inspector": r.inspector,
                "source_file": r.source_file,
                "source_type": r.source_type.value,
            }
            for r in records
        ],
        "total": len(records),
    }


@router.get("/records/stats")
async def record_stats(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count()).select_from(MaintenanceRecord))
    return {"total_records": total or 0}


@router.get("/records/ingest/{job_id}")
async def get_ingest_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(IngestJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "source_file": job.source_file,
        "imported_rows": job.imported_rows,
        "skipped_rows": job.skipped_rows,
        "report": job.report,
        "error_message": job.error_message,
    }


@router.get("/records/ingest/{job_id}/report")
async def get_ingest_report(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(IngestJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": str(job.id),
        "total_rows": job.total_rows,
        "imported_rows": job.imported_rows,
        "skipped_rows": job.skipped_rows,
        "issues": (job.report or {}).get("issues", []),
    }


@router.post("/eval/run")
async def evaluate(db: AsyncSession = Depends(get_db)):
    run = await run_evaluation(db)
    return {
        "run_id": str(run.id),
        "prompt_version": run.prompt_version,
        "metrics": run.metrics,
    }


@router.get("/eval/runs/{run_id}")
async def get_eval_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    run = await db.get(EvalRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return {
        "run_id": str(run.id),
        "prompt_version": run.prompt_version,
        "metrics": run.metrics,
        "case_results": run.case_results,
        "created_at": str(run.created_at),
    }
