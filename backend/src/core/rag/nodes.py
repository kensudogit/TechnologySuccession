"""LlamaIndex ノードと内部型の変換。"""
from __future__ import annotations

from uuid import UUID

from llama_index.core.schema import NodeWithScore, TextNode

from src.core.rag.types import RetrievedChunk


def chunk_row_to_node(
    *,
    chunk_id: UUID,
    record_id: UUID,
    chunk_text: str,
    score: float,
    equipment_name: str | None,
    event_date: str | None,
    source_file: str | None,
    rank_source: str,
) -> NodeWithScore:
    node = TextNode(
        text=chunk_text,
        id_=str(chunk_id),
        metadata={
            "chunk_id": str(chunk_id),
            "record_id": str(record_id),
            "equipment_name": equipment_name,
            "event_date": event_date,
            "source_file": source_file,
            "rank_source": rank_source,
        },
    )
    return NodeWithScore(node=node, score=score)


def node_to_retrieved_chunk(node: NodeWithScore) -> RetrievedChunk:
    meta = node.node.metadata
    return RetrievedChunk(
        chunk_id=UUID(meta["chunk_id"]),
        record_id=UUID(meta["record_id"]),
        chunk_text=node.node.get_content(),
        score=float(node.score or 0),
        equipment_name=meta.get("equipment_name"),
        event_date=meta.get("event_date"),
        source_file=meta.get("source_file"),
        rank_source=meta.get("rank_source", "fusion"),
    )
