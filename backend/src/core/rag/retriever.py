"""ハイブリッド検索（LlamaIndex Retriever + RRF 融合 + 再ランキング）。"""
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
    vector_scores: dict[str, float] = {}
    keyword_scores: dict[str, float] = {}

    for nodes in result_lists:
        for rank, node in enumerate(nodes, start=1):
            node_id = node.node.node_id or str(node.node.metadata.get("chunk_id"))
            scores[node_id] = scores.get(node_id, 0.0) + 1.0 / (_RRF_K + rank)
            source = node.node.metadata.get("rank_source", "")
            raw = float(node.score or 0)
            if source == "vector":
                vector_scores[node_id] = max(vector_scores.get(node_id, 0.0), raw)
            elif source == "keyword":
                keyword_scores[node_id] = max(keyword_scores.get(node_id, 0.0), raw)
            prev = best.get(node_id)
            if prev is None or raw > float(prev.score or 0):
                best[node_id] = node

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
    fused: list[RetrievedChunk] = []
    for node_id, rrf_score in ordered:
        chunk = node_to_retrieved_chunk(best[node_id])
        chunk.score = rrf_score
        chunk.rank_source = "fusion"
        chunk.vector_score = vector_scores.get(node_id)
        chunk.keyword_score = keyword_scores.get(node_id)
        fused.append(chunk)
    return fused


def _rerank(chunks: list[RetrievedChunk], analysis: QueryAnalysis) -> list[RetrievedChunk]:
    """設備名・症状キーワード一致とベクトル類似度で再スコアリング。"""
    if not chunks:
        return []

    rescored: list[RetrievedChunk] = []
    for chunk in chunks:
        text = chunk.chunk_text or ""
        boost = 0.0
        for name in analysis.equipment_names:
            if name and name in text:
                boost += 0.12
        for kw in analysis.symptom_keywords:
            if kw and kw in text:
                boost += 0.08

        vector_component = (chunk.vector_score or 0.0) * 0.55
        keyword_component = min((chunk.keyword_score or 0.0) / 6.0, 0.35)
        rrf_component = chunk.score * 8.0  # RRF(~0.03) を可視スケールへ

        chunk.score = vector_component + keyword_component + rrf_component + boost
        rescored.append(chunk)

    rescored.sort(key=lambda c: c.score, reverse=True)

    # 同一 record の重複チャンクは上位のみ残す（多様性確保）
    seen_records: set[str] = set()
    diversified: list[RetrievedChunk] = []
    for chunk in rescored:
        key = str(chunk.record_id)
        if key in seen_records:
            # 2件目までは許容（summary + field）
            count = sum(1 for c in diversified if str(c.record_id) == key)
            if count >= 2:
                continue
        else:
            seen_records.add(key)
        diversified.append(chunk)
        if len(diversified) >= settings.rerank_top_k:
            break
    return diversified


class HybridRetriever:
    """LangChain Embedding + LlamaIndex Retriever によるハイブリッド検索。"""

    def __init__(self) -> None:
        self.embedder = Embedder()

    async def retrieve(
        self, session: AsyncSession, query: str, analysis: QueryAnalysis
    ) -> list[RetrievedChunk]:
        vector_retriever = MaintenanceVectorRetriever(session, self.embedder, analysis)
        keyword_retriever = MaintenanceKeywordRetriever(session, analysis)

        # 同一 AsyncSession への並行アクセスを避けるため順次実行
        vector_nodes = await vector_retriever.aretrieve(query)
        keyword_nodes = await keyword_retriever.aretrieve(query)
        fused = _rrf_fuse([vector_nodes, keyword_nodes], settings.rrf_top_k)
        return _rerank(fused, analysis)
