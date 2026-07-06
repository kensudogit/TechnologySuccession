"""取り込み・インデックス化サービス。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cleansing.daily_report_parser import parse_daily_report_file
from src.core.cleansing.excel_cleaner import cleanse_excel
from src.core.rag.chunker import build_chunk_text, build_document
from src.core.rag.embedder import Embedder
from src.db.models import IngestJob, IngestStatus, MaintenanceRecord, RecordChunk, SourceType

logger = logging.getLogger(__name__)


async def _save_record(session: AsyncSession, data: dict[str, Any]) -> MaintenanceRecord | None:
    existing = await session.execute(
        select(MaintenanceRecord).where(MaintenanceRecord.content_hash == data["content_hash"])
    )
    if existing.scalar_one_or_none():
        return None

    record = MaintenanceRecord(
        source_type=data["source_type"],
        source_file=data["source_file"],
        record_category=data.get("record_category"),
        event_date=data.get("event_date"),
        equipment_id=data.get("equipment_id"),
        equipment_name=data.get("equipment_name"),
        line_name=data.get("line_name"),
        symptom=data.get("symptom"),
        root_cause=data.get("root_cause"),
        action_taken=data.get("action_taken"),
        parts_used=data.get("parts_used"),
        downtime_hours=data.get("downtime_hours"),
        measured_value=data.get("measured_value"),
        unit=data.get("unit"),
        result=data.get("result"),
        inspector=data.get("inspector"),
        raw_text=data["raw_text"],
        cleansing_issues={"issues": data.get("cleansing_issues", [])},
        content_hash=data["content_hash"],
    )
    session.add(record)
    await session.flush()

    await session.execute(
        text(
            """
            UPDATE maintenance_records
            SET search_vector = to_tsvector('simple',
                coalesce(equipment_name, '') || ' ' ||
                coalesce(symptom, '') || ' ' ||
                coalesce(root_cause, '') || ' ' ||
                coalesce(action_taken, '') || ' ' ||
                coalesce(raw_text, '')
            )
            WHERE id = :id
            """
        ),
        {"id": str(record.id)},
    )

    doc = build_document(record)
    chunk_text = doc.text
    embedder = Embedder()
    embedding = await embedder.embed_text(chunk_text)
    chunk = RecordChunk(
        record_id=record.id,
        chunk_text=chunk_text,
        chunk_type="summary",
        embedding=embedding,
        metadata_json=doc.metadata,
    )
    session.add(chunk)
    return record


async def ingest_excel(session: AsyncSession, file_path: str, source_file: str) -> IngestJob:
    job = IngestJob(source_type=SourceType.EXCEL, source_file=source_file, status=IngestStatus.PROCESSING)
    session.add(job)
    await session.flush()

    try:
        report = cleanse_excel(file_path, source_file)
        imported = 0
        for rec in report.records:
            data = {
                "source_type": rec.source_type,
                "source_file": rec.source_file,
                "record_category": rec.record_category,
                "event_date": rec.event_date,
                "equipment_id": rec.equipment_id,
                "equipment_name": rec.equipment_name,
                "line_name": rec.line_name,
                "symptom": rec.symptom,
                "root_cause": rec.root_cause,
                "action_taken": rec.action_taken,
                "parts_used": rec.parts_used,
                "downtime_hours": rec.downtime_hours,
                "measured_value": rec.measured_value,
                "unit": rec.unit,
                "result": rec.result,
                "inspector": rec.inspector,
                "raw_text": rec.raw_text,
                "cleansing_issues": rec.cleansing_issues,
                "content_hash": rec.content_hash,
            }
            saved = await _save_record(session, data)
            if saved:
                imported += 1

        job.status = IngestStatus.COMPLETED
        job.total_rows = report.total_rows
        job.imported_rows = imported
        job.skipped_rows = report.skipped_rows
        job.report = {"issues": report.issues[:100]}
        job.completed_at = datetime.now(timezone.utc)
    except Exception as exc:
        logger.exception("Excel ingest failed")
        job.status = IngestStatus.FAILED
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)

    return job


async def ingest_daily_report(session: AsyncSession, file_path: str, source_file: str) -> IngestJob:
    job = IngestJob(
        source_type=SourceType.DAILY_REPORT,
        source_file=source_file,
        status=IngestStatus.PROCESSING,
    )
    session.add(job)
    await session.flush()

    try:
        records = parse_daily_report_file(file_path, source_file)
        imported = 0
        for data in records:
            saved = await _save_record(session, data)
            if saved:
                imported += 1

        job.status = IngestStatus.COMPLETED
        job.total_rows = len(records)
        job.imported_rows = imported
        job.skipped_rows = len(records) - imported
        job.completed_at = datetime.now(timezone.utc)
    except Exception as exc:
        logger.exception("Daily report ingest failed")
        job.status = IngestStatus.FAILED
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)

    return job
