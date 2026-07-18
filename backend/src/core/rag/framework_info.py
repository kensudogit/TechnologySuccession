"""LangChain / LlamaIndex 利用状況の取得。"""
from __future__ import annotations

import importlib.metadata as metadata

from src.config import settings


def _pkg_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def get_rag_framework_info() -> dict:
    return {
        "framework": "langchain+llamaindex",
        "langchain": {
            "packages": {
                "langchain-core": _pkg_version("langchain-core"),
                "langchain-openai": _pkg_version("langchain-openai"),
            },
            "components": {
                "embeddings": "OpenAIEmbeddings",
                "llm": "ChatOpenAI",
                "prompt": "ChatPromptTemplate",
                "chain": "prompt | llm | StrOutputParser",
            },
            "models": {
                "embedding": settings.openai_embedding_model,
                "chat": settings.openai_chat_model,
            },
        },
        "llamaindex": {
            "packages": {
                "llama-index-core": _pkg_version("llama-index-core"),
                "llama-index-embeddings-langchain": _pkg_version("llama-index-embeddings-langchain"),
            },
            "components": {
                "document": "llama_index.core.Document",
                "embedding_bridge": "LangchainEmbedding(OpenAIEmbeddings)",
                "vector_retriever": "MaintenanceVectorRetriever (pgvector)",
                "keyword_retriever": "MaintenanceKeywordRetriever (FTS)",
                "fusion": "Sequential RRF (reciprocal_rerank)",
            },
            "llm_note": "回答生成は LangChain ChatOpenAI チェーンで実行",
        },
        "retrieval": {
            "vector_search": True,
            "keyword_search": True,
            "fusion_mode": "reciprocal_rerank",
            "top_k": settings.retrieval_top_k,
            "rrf_top_k": settings.rrf_top_k,
            "embedding_dimensions": settings.embedding_dimensions,
        },
        "openai_configured": settings.openai_configured,
        "prompt_version": settings.prompt_version,
    }
