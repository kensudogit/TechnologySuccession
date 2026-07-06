"""LangChain クライアント（Embedding / LLM）。"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.config import settings

RAG_USER_TEMPLATE = """## 質問
{query}

## 参照すべき保全実績
{context}

上記の実績のみを根拠に、指定フォーマットで回答してください。"""


@lru_cache
def get_embeddings() -> OpenAIEmbeddings:
    kwargs: dict = {
        "model": settings.openai_embedding_model,
        "api_key": settings.openai_api_key or "sk-dummy",
    }
    if "text-embedding-3" in settings.openai_embedding_model:
        kwargs["dimensions"] = settings.embedding_dimensions
    return OpenAIEmbeddings(**kwargs)


@lru_cache
def get_chat_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key or "sk-dummy",
        temperature=0.2,
        max_tokens=1500,
    )


def build_rag_prompt(system_prompt: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", RAG_USER_TEMPLATE),
        ]
    )
