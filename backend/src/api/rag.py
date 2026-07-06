"""RAG フレームワーク情報 API。"""
from __future__ import annotations

from fastapi import APIRouter

from src.core.rag.framework_info import get_rag_framework_info

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/status")
async def rag_status():
    """LangChain / LlamaIndex の利用構成を返す。"""
    return get_rag_framework_info()
