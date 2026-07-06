"""LlamaIndex グローバル設定（LangChain Embedding ブリッジ）。"""
from __future__ import annotations

from llama_index.core import Settings
from llama_index.embeddings.langchain import LangchainEmbedding

from src.core.rag.langchain_client import get_embeddings


def configure_llamaindex() -> None:
    """LlamaIndex が LangChain OpenAIEmbeddings を使うよう設定する。"""
    Settings.embed_model = LangchainEmbedding(get_embeddings())
