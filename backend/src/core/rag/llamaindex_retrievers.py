"""LlamaIndex ベースの保全実績リトリーバー。"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle

from src.config import settings
from src.core.rag.embedder import Embedder
from src.core.rag.nodes import chunk_row_to_node


class MaintenanceVectorRetriever(BaseRetriever):
    """pgvector コサイン類似度検索（LlamaIndex Retriever）。"""

    def __init__(self, session: AsyncSession, embedder: Embedder, limit: int | None = None) -> None:
        self._session = session
        self._embedder = embedder
        self._limit = limit or settings.retrieval_top_k
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        raise NotImplementedError("Use aretrieve() with async SQLAlchemy session")

    async def _aretrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        query_vector = await self._embedder.embed_query(query_bundle.query_str)
        sql = text(
            """
            SELECT rc.id, rc.record_id, rc.chunk_text,
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
        result = await self._session.execute(
            sql,
            {"query_vec": vec_literal, "limit": self._limit},
        )
        return [
            chunk_row_to_node(
                chunk_id=row.id,
                record_id=row.record_id,
                chunk_text=row.chunk_text,
                score=float(row.score or 0),
                equipment_name=row.equipment_name,
                event_date=str(row.event_date) if row.event_date else None,
                source_file=row.source_file,
                rank_source="vector",
            )
            for row in result
        ]


class MaintenanceKeywordRetriever(BaseRetriever):
    """PostgreSQL FTS + ILIKE キーワード検索（LlamaIndex Retriever）。"""

    def __init__(
        self,
        session: AsyncSession,
        equipment_names: list[str],
        limit: int | None = None,
    ) -> None:
        self._session = session
        self._equipment_names = equipment_names
        self._limit = limit or settings.retrieval_top_k
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        raise NotImplementedError("Use aretrieve() with async SQLAlchemy session")

    async def _aretrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        terms = query_bundle.query_str.replace("?", " ").replace("？", " ")
        filter_sql = ""
        params: dict = {"query": terms, "limit": self._limit}
        if self._equipment_names:
            filter_sql = "AND mr.equipment_name = ANY(:equipments)"
            params["equipments"] = self._equipment_names

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
        result = await self._session.execute(sql, params)
        return [
            chunk_row_to_node(
                chunk_id=row.id,
                record_id=row.record_id,
                chunk_text=row.chunk_text,
                score=float(row.score or 0.1),
                equipment_name=row.equipment_name,
                event_date=str(row.event_date) if row.event_date else None,
                source_file=row.source_file,
                rank_source="keyword",
            )
            for row in result
        ]
