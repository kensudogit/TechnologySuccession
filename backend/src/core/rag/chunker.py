"""RAG チャンク生成（LlamaIndex Document）。"""
from __future__ import annotations

from llama_index.core import Document

from src.config import settings
from src.db.models import MaintenanceRecord


def _header(record: MaintenanceRecord) -> str:
    parts = []
    if record.equipment_name:
        parts.append(f"[設備: {record.equipment_name}]")
    if record.event_date:
        parts.append(f"[日付: {record.event_date}]")
    if record.record_category:
        parts.append(f"[種別: {record.record_category.value}]")
    if record.result:
        parts.append(f"[結果: {record.result}]")
    return " ".join(parts)


def build_chunk_text(record: MaintenanceRecord) -> str:
    header = _header(record)
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
        body_parts.append(record.raw_text or "")

    return f"{header}\n" + " / ".join(body_parts)


def _split_text(text: str, max_chars: int, overlap: int) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def build_documents(record: MaintenanceRecord) -> list[Document]:
    """summary + フィールド単位 + 長文分割の複数 Document を生成する。"""
    docs: list[Document] = []
    header = _header(record)
    base_meta = {
        "record_id": str(record.id),
        "equipment_name": record.equipment_name,
        "event_date": str(record.event_date) if record.event_date else None,
        "source_file": record.source_file,
    }

    summary = build_chunk_text(record)
    docs.append(
        Document(
            text=summary,
            metadata={**base_meta, "chunk_type": "summary"},
            id_=f"{record.id}-summary",
        )
    )

    field_map = {
        "symptom": record.symptom,
        "root_cause": record.root_cause,
        "action_taken": record.action_taken,
    }
    for field_name, value in field_map.items():
        if not value or not str(value).strip():
            continue
        label = {"symptom": "症状", "root_cause": "原因", "action_taken": "処置"}[field_name]
        docs.append(
            Document(
                text=f"{header}\n{label}: {value}",
                metadata={**base_meta, "chunk_type": field_name},
                id_=f"{record.id}-{field_name}",
            )
        )

    raw = (record.raw_text or "").strip()
    # summary と大きく異なる長文のみ分割追加
    if raw and len(raw) > settings.chunk_max_chars and raw not in summary:
        for idx, part in enumerate(
            _split_text(raw, settings.chunk_max_chars, settings.chunk_overlap)
        ):
            docs.append(
                Document(
                    text=f"{header}\n{part}",
                    metadata={**base_meta, "chunk_type": "raw_split", "part": idx},
                    id_=f"{record.id}-raw-{idx}",
                )
            )

    return docs


def build_document(record: MaintenanceRecord) -> Document:
    """後方互換: summary Document を返す。"""
    return build_documents(record)[0]
