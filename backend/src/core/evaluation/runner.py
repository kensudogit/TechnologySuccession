"""評価ランナー。"""
from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

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
from src.db.models import EvalRun


def load_gold_dataset() -> list[dict]:
    path = Path(settings.data_dir) / "eval" / "gold_qa.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("cases", [])


async def run_evaluation(session: AsyncSession) -> EvalRun:
    cases = load_gold_dataset()
    pipeline = RagPipeline()
    retriever = HybridRetriever()

    case_results = []
    hit3_total = hit5_total = citation_total = keyword_total = 0

    for case in cases:
        question = case["question"]
        expected_ids = [str(i) for i in case.get("expected_record_ids", [])]
        analysis = analyze_query(question)
        chunks = await retriever.retrieve(session, question, analysis)
        retrieved_ids = [str(c.record_id) for c in chunks]

        response = await pipeline.ask(session, question)

        h3 = hit_at_k(retrieved_ids, expected_ids, 3) if expected_ids else False
        h5 = hit_at_k(retrieved_ids, expected_ids, 5) if expected_ids else False
        cm = citation_match(retrieved_ids, expected_ids) if expected_ids else False
        kc = keyword_coverage(response.answer, case.get("expected_keywords", []))

        if expected_ids:
            hit3_total += int(h3)
            hit5_total += int(h5)
            citation_total += int(cm)
        keyword_total += kc

        case_results.append(
            {
                "case_id": case.get("id"),
                "hit_at_3": h3,
                "hit_at_5": h5,
                "citation_match": cm,
                "keyword_coverage": kc,
                "retrieved_ids": retrieved_ids[:5],
            }
        )

    n = len(cases) or 1
    n_expected = sum(1 for c in cases if c.get("expected_record_ids")) or 1
    metrics = {
        "retrieval_hit_at_3": hit3_total / n_expected,
        "retrieval_hit_at_5": hit5_total / n_expected,
        "citation_accuracy": citation_total / n_expected,
        "keyword_coverage_avg": keyword_total / n,
        "total_cases": len(cases),
    }

    run = EvalRun(
        prompt_version=settings.prompt_version,
        metrics=metrics,
        case_results={"cases": case_results},
    )
    session.add(run)
    await session.flush()
    return run
