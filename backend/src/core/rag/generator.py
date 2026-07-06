"""LangChain による RAG 回答生成。"""
from __future__ import annotations

from dataclasses import dataclass

from langchain_core.output_parsers import StrOutputParser

from src.config import settings
from src.core.rag.context_builder import build_context
from src.core.rag.langchain_client import build_rag_prompt, get_chat_llm
from src.core.rag.prompt_manager import load_system_prompt
from src.core.rag.types import RetrievedChunk


@dataclass
class ChatResponse:
    answer: str
    sources: list[dict]
    confidence: str


def _build_sources(chunks: list[RetrievedChunk]) -> list[dict]:
    sources = []
    seen: set[str] = set()
    for chunk in chunks:
        key = str(chunk.record_id)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "record_id": str(chunk.record_id),
                "equipment_name": chunk.equipment_name,
                "event_date": chunk.event_date,
                "source_file": chunk.source_file,
                "excerpt": chunk.chunk_text[:200],
            }
        )
    return sources


def _confidence(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "low"
    top_score = max(c.score for c in chunks)
    if top_score >= 0.7:
        return "high"
    if top_score >= 0.3:
        return "medium"
    return "low"


async def generate_answer(query: str, chunks: list[RetrievedChunk]) -> ChatResponse:
    sources = _build_sources(chunks)
    confidence = _confidence(chunks)

    if not chunks:
        return ChatResponse(
            answer="該当する保全実績が見つかりませんでした。設備名や症状を変えて再度お試しください。",
            sources=[],
            confidence="low",
        )

    context = build_context(chunks)
    system_prompt = load_system_prompt()

    if not settings.openai_api_key:
        top = chunks[0]
        return ChatResponse(
            answer=(
                f"### 想定原因\n過去実績より: {top.chunk_text}\n\n"
                f"### 参考実績\n- [{top.event_date}] {top.equipment_name} ({top.source_file})"
            ),
            sources=sources,
            confidence=confidence,
        )

    prompt = build_rag_prompt(system_prompt)
    chain = prompt | get_chat_llm() | StrOutputParser()
    answer = await chain.ainvoke({"query": query, "context": context})
    return ChatResponse(answer=answer, sources=sources, confidence=confidence)
