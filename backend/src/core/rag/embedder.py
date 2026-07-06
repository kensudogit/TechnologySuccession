"""OpenAI Embedding。"""
from __future__ import annotations

from openai import AsyncOpenAI

from src.config import settings


class Embedder:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key or "sk-dummy")

    async def embed_text(self, text: str) -> list[float]:
        if not settings.openai_api_key:
            return [0.0] * settings.embedding_dimensions
        response = await self.client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_query(self, query: str) -> list[float]:
        return await self.embed_text(query)
