"""評価ランナー。"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.evaluation.metrics import (
    citation_match,
    hit_at_k,
    keyword_coverage,
)
from src.core.rag.pipeline import RagPipeline
from src.core.rag.query_analyzer import analyze_query
from src.core.rag.retriever import HybridRetriever
from src.db.models import EvalRun, MaintenanceRecord

logger = logging.getLogger(__name__)


def load_gold_dataset() -> list[dict]:
    path = Path(settings.data_dir) / "eval" / "gold_qa.json"
    if not path.exists():
        logger.warning("Gold QA dataset not found: %s", path)
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("cases", [])


async def resolve_expected_ids(session: AsyncSession, case: dict) -> list[str]:
    """UUID 固定ではなく、設備名 + マッチ語で正解レコードを動的解決する。"""
    explicit = [str(i) for i in case.get("expected_record_ids", []) if i]
    if explicit:
        return explicit

    equipment = (case.get("expected_equipment") or "").strip()
    match_terms = case.get("expected_match_terms") or case.get("expected_keywords") or []
    if not equipment and not match_terms:
        return []

    stmt = select(MaintenanceRecord)
    if equipment:
        stmt = stmt.where(MaintenanceRecord.equipment_name.ilike(f"%{equipment}%"))
    records = (await session.execute(stmt)).scalars().all()

    matched: list[str] = []
    for record in records:
        blob = " ".join(
            [
                record.equipment_name or "",
                record.symptom or "",
                record.root_cause or "",
                record.action_taken or "",
                record.raw_text or "",
            ]
        )
        if match_terms and not any(term in blob for term in match_terms):
            continue
        matched.append(str(record.id))
    return matched


async def run_evaluation(session: AsyncSession) -> EvalRun:
    cases = load_gold_dataset()
    if not cases:
        raise FileNotFoundError(
            f"評価用データがありません: {Path(settings.data_dir) / 'eval' / 'gold_qa.json'}"
        )

    pipeline = RagPipeline()
    retriever = HybridRetriever()

    case_results = []
    hit3_total = hit5_total = citation_total = keyword_total = 0
    scored_retrieval_cases = 0

    for case in cases:
        question = case["question"]
        expected_ids = await resolve_expected_ids(session, case)
        analysis = analyze_query(question)

        try:
            chunks = await retriever.retrieve(session, question, analysis)
            retrieved_ids = [str(c.record_id) for c in chunks]
            response = await pipeline.ask(session, question, chunks=chunks)
        except Exception as exc:
            logger.exception("Eval case failed: %s", case.get("id"))
            case_results.append(
                {
                    "case_id": case.get("id"),
                    "question": question,
                    "error": str(exc),
                    "hit_at_3": False,
                    "hit_at_5": False,
                    "citation_match": False,
                    "keyword_coverage": 0.0,
                    "expected_ids": expected_ids,
                    "retrieved_ids": [],
                    "expected_resolved": len(expected_ids) > 0,
                }
            )
            continue

        has_expected = len(expected_ids) > 0
        h3 = hit_at_k(retrieved_ids, expected_ids, 3) if has_expected else False
        h5 = hit_at_k(retrieved_ids, expected_ids, 5) if has_expected else False
        cm = citation_match(retrieved_ids, expected_ids) if has_expected else False
        kc = keyword_coverage(response.answer, case.get("expected_keywords", []))

        if has_expected:
            scored_retrieval_cases += 1
            hit3_total += int(h3)
            hit5_total += int(h5)
            citation_total += int(cm)
        keyword_total += kc

        case_results.append(
            {
                "case_id": case.get("id"),
                "question": question,
                "hit_at_3": h3,
                "hit_at_5": h5,
                "citation_match": cm,
                "keyword_coverage": kc,
                "expected_ids": expected_ids[:5],
                "retrieved_ids": retrieved_ids[:5],
                "expected_resolved": has_expected,
                "top_equipment": chunks[0].equipment_name if chunks else None,
            }
        )

    n = len(cases) or 1
    n_expected = scored_retrieval_cases or 0
    metrics = {
        "retrieval_hit_at_3": (hit3_total / n_expected) if n_expected else None,
        "retrieval_hit_at_5": (hit5_total / n_expected) if n_expected else None,
        "citation_accuracy": (citation_total / n_expected) if n_expected else None,
        "keyword_coverage_avg": keyword_total / n,
        "total_cases": len(cases),
        "scored_retrieval_cases": scored_retrieval_cases,
        "failed_cases": sum(1 for c in case_results if c.get("error")),
    }

    run = EvalRun(
        prompt_version=settings.prompt_version,
        metrics=metrics,
        case_results={"cases": case_results},
    )
    session.add(run)
    await session.flush()
    return run
