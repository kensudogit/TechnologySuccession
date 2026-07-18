"""LangChain OpenAI Embedding。"""
from __future__ import annotations

from src.config import settings
from src.core.rag.langchain_client import get_embeddings


class Embedder:
    def __init__(self) -> None:
        self._embeddings = get_embeddings()

    async def embed_text(self, text: str) -> list[float]:
        if not settings.openai_api_key:
            return [0.0] * settings.embedding_dimensions
        return await self._embeddings.aembed_query(text)

    async def embed_query(self, query: str) -> list[float]:
        return await self.embed_text(query)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """複数テキストをバッチ Embedding する。"""
        if not texts:
            return []
        if not settings.openai_api_key:
            return [[0.0] * settings.embedding_dimensions for _ in texts]
        return await self._embeddings.aembed_documents(texts)
