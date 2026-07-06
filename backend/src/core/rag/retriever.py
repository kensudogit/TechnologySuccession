"""ハイブリッド検索（LlamaIndex QueryFusion + pgvector + FTS）。"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from llama_index.core.retrievers import QueryFusionRetriever

from src.config import settings
from src.core.rag.embedder import Embedder
from src.core.rag.llamaindex_retrievers import MaintenanceKeywordRetriever, MaintenanceVectorRetriever
from src.core.rag.nodes import node_to_retrieved_chunk
from src.core.rag.query_analyzer import QueryAnalysis
from src.core.rag.types import RetrievedChunk


class HybridRetriever:
    """LangChain Embedding + LlamaIndex QueryFusionRetriever によるハイブリッド検索。"""

    def __init__(self) -> None:
        self.embedder = Embedder()

    async def retrieve(
        self, session: AsyncSession, query: str, analysis: QueryAnalysis
    ) -> list[RetrievedChunk]:
        vector_retriever = MaintenanceVectorRetriever(session, self.embedder)
        keyword_retriever = MaintenanceKeywordRetriever(session, analysis.equipment_names)

        fusion = QueryFusionRetriever(
            [vector_retriever, keyword_retriever],
            similarity_top_k=settings.rrf_top_k,
            num_queries=1,
            mode="reciprocal_rerank",
            use_async=True,
        )

        nodes = await fusion.aretrieve(query)
        return [node_to_retrieved_chunk(node) for node in nodes]
