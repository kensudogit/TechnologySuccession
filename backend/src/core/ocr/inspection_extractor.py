"""PDF/画像からの点検記録抽出。"""
from __future__ import annotations

import base64
import logging
from pathlib import Path

import fitz

from src.config import settings
from src.core.cleansing.text_normalizer import content_hash, normalize_text
from src.db.models import RecordCategory, SourceType

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    parts = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return normalize_text("\n".join(parts))


async def extract_with_vision(file_path: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        text = extract_text_from_pdf(file_path)
        if len(text) > 50:
            return text

    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    mime = "application/pdf" if suffix == ".pdf" else "image/jpeg"
    response = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "この点検記録からテキストをすべて抽出してください。",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            }
        ],
        max_tokens=2000,
    )
    return normalize_text(response.choices[0].message.content or "")


async def extract_structured_record(file_path: str, source_file: str) -> dict:
    from openai import AsyncOpenAI

    raw = extract_text_from_pdf(file_path) if Path(file_path).suffix.lower() == ".pdf" else ""
    if len(raw) < 50 and settings.openai_api_key:
        raw = await extract_with_vision(file_path)

    if not raw:
        raw = normalize_text(Path(file_path).read_bytes().decode("utf-8", errors="replace"))

    structured = {
        "source_type": SourceType.PAPER,
        "source_file": source_file,
        "record_category": RecordCategory.INSPECTION,
        "raw_text": raw,
        "cleansing_issues": [],
    }

    if settings.openai_api_key and raw:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        prompt = f"""以下の点検記録テキストから JSON で抽出してください。
フィールド: event_date, equipment_name, symptom, root_cause, action_taken, result

テキスト:
{raw[:3000]}
"""
        response = await client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        import json

        try:
            parsed = json.loads(response.choices[0].message.content or "{}")
            structured.update(parsed)
        except json.JSONDecodeError:
            structured["cleansing_issues"] = ["LLM構造化に失敗"]

    structured["content_hash"] = content_hash(
        structured.get("equipment_name") or "",
        str(structured.get("event_date") or ""),
        raw,
    )
    return structured
