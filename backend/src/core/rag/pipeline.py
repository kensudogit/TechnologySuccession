"""RAG パイプライン統合（LangChain 生成 + LlamaIndex 検索）。"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.rag.generator import ChatResponse, generate_answer
from src.core.rag.llamaindex_settings import configure_llamaindex
from src.core.rag.query_analyzer import analyze_query
from src.core.rag.retriever import HybridRetriever

configure_llamaindex()


class RagPipeline:
    def __init__(self) -> None:
        self.retriever = HybridRetriever()

    async def ask(self, session: AsyncSession, question: str) -> ChatResponse:
        analysis = analyze_query(question)
        chunks = await self.retriever.retrieve(session, question, analysis)
        return await generate_answer(question, chunks)
