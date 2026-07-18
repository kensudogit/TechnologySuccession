"""LlamaIndex ベースの保全実績リトリーバー。"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle

from src.config import settings
from src.core.rag.embedder import Embedder
from src.core.rag.nodes import chunk_row_to_node
from src.core.rag.query_analyzer import QueryAnalysis


class MaintenanceVectorRetriever(BaseRetriever):
    """pgvector コサイン類似度検索（LlamaIndex Retriever）。"""

    def __init__(
        self,
        session: AsyncSession,
        embedder: Embedder,
        analysis: QueryAnalysis | None = None,
        limit: int | None = None,
    ) -> None:
        self._session = session
        self._embedder = embedder
        self._analysis = analysis
        self._limit = limit or settings.retrieval_top_k
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        raise NotImplementedError("Use aretrieve() with async SQLAlchemy session")

    async def _aretrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        query_text = (
            self._analysis.embedding_query
            if self._analysis is not None
            else query_bundle.query_str
        )
        query_vector = await self._embedder.embed_query(query_text)
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
    """日本語向けキーワード検索（ILIKE OR + 簡易スコア）。"""

    def __init__(
        self,
        session: AsyncSession,
        analysis: QueryAnalysis,
        limit: int | None = None,
    ) -> None:
        self._session = session
        self._analysis = analysis
        self._limit = limit or settings.retrieval_top_k
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        raise NotImplementedError("Use aretrieve() with async SQLAlchemy session")

    async def _aretrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        terms = self._analysis.keyword_terms
        if not terms:
            cleaned = query_bundle.query_str.replace("?", " ").replace("？", " ").strip()
            terms = [cleaned[:50]] if cleaned else []
        if not terms:
            return []

        # 各語に対する ILIKE 条件（日本語は FTS simple より ILIKE の方が実用的）
        like_clauses = []
        params: dict = {"limit": self._limit}
        for i, term in enumerate(terms[:8]):
            key = f"like_{i}"
            params[key] = f"%{term}%"
            like_clauses.append(
                f"""(
                    mr.equipment_name ILIKE :{key}
                    OR mr.symptom ILIKE :{key}
                    OR mr.root_cause ILIKE :{key}
                    OR mr.action_taken ILIKE :{key}
                    OR mr.raw_text ILIKE :{key}
                    OR rc.chunk_text ILIKE :{key}
                )"""
            )

        where_sql = " OR ".join(like_clauses)

        # 設備名一致はブースト（ハードフィルタにしない）
        equip_boost_sql = "0"
        if self._analysis.equipment_names:
            params["equipments"] = self._analysis.equipment_names
            equip_boost_sql = """
                CASE WHEN mr.equipment_name = ANY(:equipments) THEN 2.0 ELSE 0.0 END
            """

        # ヒット語数のおおよそのスコア
        hit_score_parts = []
        for i in range(min(len(terms), 8)):
            key = f"like_{i}"
            hit_score_parts.append(
                f"(CASE WHEN mr.symptom ILIKE :{key} OR mr.root_cause ILIKE :{key} "
                f"OR mr.action_taken ILIKE :{key} OR rc.chunk_text ILIKE :{key} THEN 1 ELSE 0 END)"
            )
        hit_score_sql = " + ".join(hit_score_parts) if hit_score_parts else "0"

        sql = text(
            f"""
            SELECT rc.id, rc.record_id, rc.chunk_text,
                   mr.equipment_name, mr.event_date, mr.source_file,
                   ({hit_score_sql})::float + ({equip_boost_sql}) AS score
            FROM record_chunks rc
            JOIN maintenance_records mr ON mr.id = rc.record_id
            WHERE {where_sql}
            ORDER BY score DESC NULLS LAST, mr.event_date DESC NULLS LAST
            LIMIT :limit
            """
        )
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
