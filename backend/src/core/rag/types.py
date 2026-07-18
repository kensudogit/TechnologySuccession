"""RAG 共通データ型。"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class RetrievedChunk:
    chunk_id: UUID
    record_id: UUID
    chunk_text: str
    score: float
    equipment_name: str | None
    event_date: str | None
    source_file: str | None
    rank_source: str
    vector_score: float | None = None
    keyword_score: float | None = None
