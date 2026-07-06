"""コンテキスト構築。"""
from __future__ import annotations

from src.core.rag.retriever import RetrievedChunk


def build_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""

    sorted_chunks = sorted(
        chunks,
        key=lambda c: c.event_date or "",
        reverse=True,
    )

    parts = []
    for i, chunk in enumerate(sorted_chunks, start=1):
        source = chunk.source_file or "unknown"
        equip = chunk.equipment_name or "不明"
        date = chunk.event_date or "日付不明"
        parts.append(
            f"[出典{i}: {source} / {date} / {equip} / record_id={chunk.record_id}]\n{chunk.chunk_text}"
        )
    return "\n\n".join(parts)
