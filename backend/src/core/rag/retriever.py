"""ハイブリッド検索（pgvector + PostgreSQL FTS）。"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.rag.embedder import Embedder
from src.core.rag.query_analyzer import QueryAnalysis
from src.db.models import MaintenanceRecord, RecordChunk


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


def _rrf_merge(*ranked_lists: list[RetrievedChunk], k: int = 60) -> list[RetrievedChunk]:
    scores: dict[str, tuple[RetrievedChunk, float]] = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            key = str(item.chunk_id)
            rrf = 1.0 / (k + rank)
            if key in scores:
                prev_item, prev_score = scores[key]
                scores[key] = (prev_item, prev_score + rrf)
            else:
                scores[key] = (item, rrf)
    merged = sorted(scores.values(), key=lambda x: x[1], reverse=True)
    return [item for item, score in merged[: settings.rrf_top_k]]


class HybridRetriever:
    def __init__(self) -> None:
        self.embedder = Embedder()

    async def vector_search(
        self, session: AsyncSession, query_vector: list[float], limit: int = 10
    ) -> list[RetrievedChunk]:
        sql = text(
            """
            SELECT rc.id, rc.record_id, rc.chunk_text, rc.metadata_json,
                   mr.equipment_name, mr.event_date, mr.source_file,
                   1 - (rc.embedding <=> CAST(:query_vec AS vector)) AS score
            FROM record_chunks rc
            JOIN maintenance_records mr ON mr.id = rc.record_id
            WHERE rc.embedding IS NOT NULL
            ORDER BY rc.embedding <=> CAST(:query_vec AS vector)
            LIMIT :limit
            """
        )
        vec_literal = "[" + ",".join(str(v) for v in query_vector) + "]"
        result = await session.execute(
            sql,
            {"query_vec": vec_literal, "limit": limit},
        )
        chunks = []
        for row in result:
            chunks.append(
                RetrievedChunk(
                    chunk_id=row.id,
                    record_id=row.record_id,
                    chunk_text=row.chunk_text,
                    score=float(row.score or 0),
                    equipment_name=row.equipment_name,
                    event_date=str(row.event_date) if row.event_date else None,
                    source_file=row.source_file,
                    rank_source="vector",
                )
            )
        return chunks

    async def keyword_search(
        self, session: AsyncSession, query: str, equipment_names: list[str], limit: int = 10
    ) -> list[RetrievedChunk]:
        terms = query.replace("?", " ").replace("？", " ")
        filter_sql = ""
        params: dict = {"query": terms, "limit": limit}
        if equipment_names:
            filter_sql = "AND mr.equipment_name = ANY(:equipments)"
            params["equipments"] = equipment_names

        sql = text(
            f"""
            SELECT rc.id, rc.record_id, rc.chunk_text,
                   mr.equipment_name, mr.event_date, mr.source_file,
                   ts_rank(mr.search_vector, plainto_tsquery('simple', :query)) AS score
            FROM record_chunks rc
            JOIN maintenance_records mr ON mr.id = rc.record_id
            WHERE mr.search_vector @@ plainto_tsquery('simple', :query)
               OR mr.raw_text ILIKE :like_query
               OR mr.symptom ILIKE :like_query
               OR mr.action_taken ILIKE :like_query
            {filter_sql}
            ORDER BY score DESC NULLS LAST
            LIMIT :limit
            """
        )
        params["like_query"] = f"%{terms[:50]}%"
        result = await session.execute(sql, params)
        chunks = []
        for row in result:
            chunks.append(
                RetrievedChunk(
                    chunk_id=row.id,
                    record_id=row.record_id,
                    chunk_text=row.chunk_text,
                    score=float(row.score or 0.1),
                    equipment_name=row.equipment_name,
                    event_date=str(row.event_date) if row.event_date else None,
                    source_file=row.source_file,
                    rank_source="keyword",
                )
            )
        return chunks

    async def retrieve(
        self, session: AsyncSession, query: str, analysis: QueryAnalysis
    ) -> list[RetrievedChunk]:
        query_vector = await self.embedder.embed_query(query)
        vector_results = await self.vector_search(session, query_vector)
        keyword_results = await self.keyword_search(
            session, query, analysis.equipment_names
        )
        return _rrf_merge(vector_results, keyword_results)
