"""評価メトリクス。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EvalCaseResult:
    case_id: str
    hit_at_3: bool
    hit_at_5: bool
    citation_match: bool
    keyword_coverage: float
    retrieved_ids: list[str]


def hit_at_k(retrieved_ids: list[str], expected_ids: list[str], k: int) -> bool:
    top = retrieved_ids[:k]
    return any(eid in top for eid in expected_ids)


def keyword_coverage(answer: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 1.0
    found = sum(1 for kw in expected_keywords if kw in answer)
    return found / len(expected_keywords)


def citation_match(retrieved_ids: list[str], expected_ids: list[str]) -> bool:
    return any(eid in retrieved_ids[:3] for eid in expected_ids)
