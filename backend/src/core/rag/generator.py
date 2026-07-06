"""RAG 回答生成。"""
from __future__ import annotations

from dataclasses import dataclass

from openai import AsyncOpenAI

from src.config import settings
from src.core.rag.context_builder import build_context
from src.core.rag.prompt_manager import load_system_prompt
from src.core.rag.retriever import RetrievedChunk


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

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    user_prompt = f"""## 質問
{query}

## 参照すべき保全実績
{context}

上記の実績のみを根拠に、指定フォーマットで回答してください。"""

    response = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1500,
    )
    answer = response.choices[0].message.content or ""
    return ChatResponse(answer=answer, sources=sources, confidence=confidence)
