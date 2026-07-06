"""取り込み API。"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.ingestion.ingest_service import ingest_daily_report, ingest_excel
from src.core.ocr.inspection_extractor import extract_structured_record
from src.core.ingestion.ingest_service import _save_record
from src.db.database import get_db
from src.db.models import IngestJob, IngestStatus, SourceType

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _ensure_upload_dir() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.post("/excel")
async def upload_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    upload_dir = _ensure_upload_dir()
    dest = upload_dir / f"{uuid.uuid4()}_{file.filename}"
    content = await file.read()
    dest.write_bytes(content)

    job = await ingest_excel(db, str(dest), file.filename or dest.name)
    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "imported_rows": job.imported_rows,
        "skipped_rows": job.skipped_rows,
        "report": job.report,
    }


@router.post("/daily-report")
async def upload_daily_report(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    upload_dir = _ensure_upload_dir()
    dest = upload_dir / f"{uuid.uuid4()}_{file.filename}"
    content = await file.read()
    dest.write_bytes(content)

    job = await ingest_daily_report(db, str(dest), file.filename or dest.name)
    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "imported_rows": job.imported_rows,
        "skipped_rows": job.skipped_rows,
    }


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    upload_dir = _ensure_upload_dir()
    dest = upload_dir / f"{uuid.uuid4()}_{file.filename}"
    content = await file.read()
    dest.write_bytes(content)

    job = IngestJob(
        source_type=SourceType.PAPER,
        source_file=file.filename or dest.name,
        status=IngestStatus.PROCESSING,
    )
    db.add(job)
    await db.flush()

    try:
        structured = await extract_structured_record(str(dest), file.filename or dest.name)
        saved = await _save_record(db, structured)
        job.status = IngestStatus.COMPLETED
        job.imported_rows = 1 if saved else 0
        job.skipped_rows = 0 if saved else 1
        job.total_rows = 1
    except Exception as exc:
        job.status = IngestStatus.FAILED
        job.error_message = str(exc)

    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "imported_rows": job.imported_rows,
    }
