"""RAG チャンク生成（LlamaIndex Document）。"""
from __future__ import annotations

from llama_index.core import Document

from src.db.models import MaintenanceRecord


def build_chunk_text(record: MaintenanceRecord) -> str:
    parts = []
    if record.equipment_name:
        parts.append(f"[設備: {record.equipment_name}]")
    if record.event_date:
        parts.append(f"[日付: {record.event_date}]")
    if record.record_category:
        parts.append(f"[種別: {record.record_category.value}]")
    if record.result:
        parts.append(f"[結果: {record.result}]")

    header = " ".join(parts)
    body_parts = []
    if record.symptom:
        body_parts.append(f"症状: {record.symptom}")
    if record.root_cause:
        body_parts.append(f"原因: {record.root_cause}")
    if record.action_taken:
        body_parts.append(f"処置: {record.action_taken}")
    if record.measured_value:
        unit = f" {record.unit}" if record.unit else ""
        body_parts.append(f"測定値: {record.measured_value}{unit}")
    if not body_parts:
        body_parts.append(record.raw_text)

    return f"{header}\n" + " / ".join(body_parts)


def build_document(record: MaintenanceRecord) -> Document:
    """LlamaIndex Document としてチャンクを構築する。"""
    return Document(
        text=build_chunk_text(record),
        metadata={
            "record_id": str(record.id),
            "equipment_name": record.equipment_name,
            "event_date": str(record.event_date) if record.event_date else None,
            "source_file": record.source_file,
            "chunk_type": "summary",
        },
        id_=str(record.id),
    )
