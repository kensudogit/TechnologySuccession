"""ハイブリッド検索（LlamaIndex Retriever + RRF 融合）。"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from llama_index.core.schema import NodeWithScore

from src.config import settings
from src.core.rag.embedder import Embedder
from src.core.rag.llamaindex_retrievers import MaintenanceKeywordRetriever, MaintenanceVectorRetriever
from src.core.rag.nodes import node_to_retrieved_chunk
from src.core.rag.query_analyzer import QueryAnalysis
from src.core.rag.types import RetrievedChunk

_RRF_K = 60


def _rrf_fuse(
    result_lists: list[list[NodeWithScore]],
    top_k: int,
) -> list[RetrievedChunk]:
    """複数ランキングを Reciprocal Rank Fusion で統合する。"""
    scores: dict[str, float] = {}
    best: dict[str, NodeWithScore] = {}

    for nodes in result_lists:
        for rank, node in enumerate(nodes, start=1):
            node_id = node.node.node_id or str(node.node.metadata.get("chunk_id"))
            scores[node_id] = scores.get(node_id, 0.0) + 1.0 / (_RRF_K + rank)
            prev = best.get(node_id)
            if prev is None or float(node.score or 0) > float(prev.score or 0):
                best[node_id] = node

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
    fused: list[RetrievedChunk] = []
    for node_id, rrf_score in ordered:
        chunk = node_to_retrieved_chunk(best[node_id])
        chunk.score = rrf_score
        chunk.rank_source = "fusion"
        fused.append(chunk)
    return fused


class HybridRetriever:
    """LangChain Embedding + LlamaIndex Retriever によるハイブリッド検索。

    QueryFusionRetriever(use_async=True) は同一 AsyncSession を並行利用し、
    SQLAlchemy で失敗するため、vector / keyword を順次実行して RRF 融合する。
    """

    def __init__(self) -> None:
        self.embedder = Embedder()

    async def retrieve(
        self, session: AsyncSession, query: str, analysis: QueryAnalysis
    ) -> list[RetrievedChunk]:
        vector_retriever = MaintenanceVectorRetriever(session, self.embedder)
        keyword_retriever = MaintenanceKeywordRetriever(session, analysis.equipment_names)

        # 同一 AsyncSession への並行アクセスを避けるため順次実行
        vector_nodes = await vector_retriever.aretrieve(query)
        keyword_nodes = await keyword_retriever.aretrieve(query)
        return _rrf_fuse([vector_nodes, keyword_nodes], settings.rrf_top_k)
