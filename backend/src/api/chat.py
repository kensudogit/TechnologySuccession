"""チャット API。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.auth.jwt_handler import require_auth
from src.core.rag.pipeline import RagPipeline
from src.db.database import get_db
from src.db.models import ChatLog

router = APIRouter(prefix="/chat", tags=["chat"])


class AskRequest(BaseModel):
    question: str
    equipment_name: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    confidence: str


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    question = body.question
    if body.equipment_name:
        question = f"[設備: {body.equipment_name}] {question}"

    pipeline = RagPipeline()
    response = await pipeline.ask(db, question)

    log = ChatLog(
        question=body.question,
        answer=response.answer,
        sources={"items": response.sources},
        prompt_version=settings.prompt_version,
        confidence=response.confidence,
    )
    db.add(log)

    return AskResponse(
        answer=response.answer,
        sources=response.sources,
        confidence=response.confidence,
    )
