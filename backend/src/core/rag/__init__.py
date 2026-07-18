"""RAG モジュール — LangChain（生成・Embedding）+ LlamaIndex（検索・Document）。"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.rag.pipeline import RagPipeline

__all__ = ["RagPipeline", "get_rag_framework_info"]


def __getattr__(name: str) -> Any:
    if name == "RagPipeline":
        from src.core.rag.pipeline import RagPipeline

        return RagPipeline
    if name == "get_rag_framework_info":
        from src.core.rag.framework_info import get_rag_framework_info

        return get_rag_framework_info
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
