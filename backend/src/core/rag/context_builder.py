"""コンテキスト構築。"""
from __future__ import annotations

from src.core.rag.types import RetrievedChunk


def build_context(chunks: list[RetrievedChunk]) -> str:
    """検索スコア順を維持したまま LLM 用コンテキストを組み立てる。"""
    if not chunks:
        return ""

    parts = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.source_file or "unknown"
        equip = chunk.equipment_name or "不明"
        date = chunk.event_date or "日付不明"
        relevance = f"relevance={chunk.score:.3f}"
        if chunk.vector_score is not None:
            relevance += f", vector={chunk.vector_score:.3f}"
        parts.append(
            f"[出典{i}: {source} / {date} / {equip} / record_id={chunk.record_id} / {relevance}]\n"
            f"{chunk.chunk_text}"
        )
    return "\n\n".join(parts)
