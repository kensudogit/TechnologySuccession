"""OpenAI / DB なしで RAG 設計品質とゴールドセット適合を評価する。"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.rag.query_analyzer import analyze_query  # noqa: E402

SEED_RECORDS = [
    {
        "id": "seed-comp-noise",
        "equipment_name": "コンプレッサA-03",
        "symptom": "運転中に異音発生",
        "root_cause": "ベアリング摩耗",
        "action_taken": "ベアリング交換、潤滑油交換",
    },
    {
        "id": "seed-comp-oil",
        "equipment_name": "コンプレッサA-03",
        "symptom": "油温95℃でアラーム",
        "root_cause": "オイルフィルター詰まり",
        "action_taken": "フィルター交換",
    },
    {
        "id": "seed-pump-pressure",
        "equipment_name": "ポンプB-12",
        "symptom": "吐出圧力低下 80kPa",
        "root_cause": "インペラ摩耗",
        "action_taken": "インペラ交換、配管清掃",
    },
    {
        "id": "seed-motor-overcurrent",
        "equipment_name": "モータC-01",
        "symptom": "起動時過電流トリップ",
        "root_cause": "ベアリング固着",
        "action_taken": "ベアリング交換、軸芯調整",
    },
    {
        "id": "seed-comp-oil-inspect",
        "equipment_name": "コンプレッサA-03",
        "symptom": "定期点検で油温高め",
        "root_cause": "",
        "action_taken": "冷却ファン清掃",
    },
    {
        "id": "seed-pump-leak",
        "equipment_name": "ポンプB-12",
        "symptom": "シール部から漏れ",
        "root_cause": "パッキン劣化",
        "action_taken": "パッキン交換",
    },
    {
        "id": "seed-motor-vibration",
        "equipment_name": "モータC-01",
        "symptom": "振動値上限超過",
        "root_cause": "アライメント不良",
        "action_taken": "アライメント調整",
    },
]

# ゴールド設問ごとに「正解として期待する seed id」
GOLD_EXPECTED = {
    "ts-001": ["seed-comp-noise"],
    "ts-002": ["seed-comp-oil"],
    "ts-003": ["seed-pump-pressure"],
    "ts-004": ["seed-motor-overcurrent"],
}


@dataclass
class CaseEval:
    case_id: str
    question: str
    intent: str
    equipment_ok: bool
    symptom_ok: bool
    retrieval_hit_at_1: bool
    retrieval_hit_at_3: bool
    keyword_coverage: float
    top_record_id: str | None
    notes: str


def _text(rec: dict) -> str:
    return " ".join(
        [
            rec.get("equipment_name") or "",
            rec.get("symptom") or "",
            rec.get("root_cause") or "",
            rec.get("action_taken") or "",
        ]
    )


def rank_records(analysis, question: str) -> list[tuple[str, float]]:
    scored: list[tuple[str, float]] = []
    terms = analysis.keyword_terms + analysis.equipment_names + analysis.symptom_keywords
    terms = list(dict.fromkeys(t for t in terms if t))
    for rec in SEED_RECORDS:
        blob = _text(rec)
        score = 0.0
        for name in analysis.equipment_names:
            if name and name in blob:
                score += 2.0
        for kw in analysis.symptom_keywords:
            if kw and kw in blob:
                score += 1.2
        for term in terms:
            if term and term in blob:
                score += 0.4
        # 簡易ベクトル代替: 質問断片一致
        for token in question.replace("？", " ").replace("?", " ").split():
            if len(token) >= 2 and token in blob:
                score += 0.3
        scored.append((rec["id"], score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def keyword_coverage(answer: str, expected: list[str]) -> float:
    if not expected:
        return 1.0
    return sum(1 for kw in expected if kw in answer) / len(expected)


def evaluate() -> dict:
    gold_path = ROOT.parent / "data" / "eval" / "gold_qa.json"
    cases = json.loads(gold_path.read_text(encoding="utf-8")).get("cases", [])

    results: list[CaseEval] = []
    for case in cases:
        cid = case["id"]
        q = case["question"]
        expected_kw = case.get("expected_keywords", [])
        expected_ids = GOLD_EXPECTED.get(cid, [])
        analysis = analyze_query(q)
        ranked = rank_records(analysis, q)
        top_ids = [rid for rid, _ in ranked[:3] if _ > 0]
        top1 = ranked[0][0] if ranked and ranked[0][1] > 0 else None

        # ルールベース回答（トップレコードの原因+処置）
        top_rec = next((r for r in SEED_RECORDS if r["id"] == top1), None)
        answer = ""
        if top_rec:
            answer = f"{top_rec['root_cause']} {top_rec['action_taken']} {top_rec['symptom']}"

        equip_ok = any(e in q or e in (top_rec or {}).get("equipment_name", "") for e in analysis.equipment_names) if analysis.equipment_names else False
        # 設備抽出が正解設備を含むか
        if expected_ids:
            expected_equip = next(r["equipment_name"] for r in SEED_RECORDS if r["id"] == expected_ids[0])
            equip_ok = expected_equip in analysis.equipment_names or expected_equip in q

        symptom_ok = bool(analysis.symptom_keywords) and any(
            kw in q for kw in analysis.symptom_keywords
        )

        hit1 = bool(top1 and top1 in expected_ids)
        hit3 = any(rid in expected_ids for rid in top_ids)
        kc = keyword_coverage(answer, expected_kw)

        notes = []
        if not hit1:
            notes.append(f"top={top1}, expected={expected_ids}")
        if analysis.intent != case.get("category", analysis.intent):
            notes.append(f"intent={analysis.intent} vs {case.get('category')}")

        results.append(
            CaseEval(
                case_id=cid,
                question=q,
                intent=analysis.intent,
                equipment_ok=equip_ok,
                symptom_ok=symptom_ok,
                retrieval_hit_at_1=hit1,
                retrieval_hit_at_3=hit3,
                keyword_coverage=kc,
                top_record_id=top1,
                notes="; ".join(notes),
            )
        )

    n = len(results) or 1
    metrics = {
        "total_cases": len(results),
        "equipment_extraction_rate": sum(r.equipment_ok for r in results) / n,
        "symptom_extraction_rate": sum(r.symptom_ok for r in results) / n,
        "retrieval_hit_at_1": sum(r.retrieval_hit_at_1 for r in results) / n,
        "retrieval_hit_at_3": sum(r.retrieval_hit_at_3 for r in results) / n,
        "keyword_coverage_avg": sum(r.keyword_coverage for r in results) / n,
        "gold_has_expected_record_ids": any(
            c.get("expected_record_ids") for c in cases
        ),
    }

    # 設計成熟度（コードレビュー基準の固定スコア）
    architecture = {
        "hybrid_retrieval": 4,  # vector + keyword
        "query_understanding": 4,  # rewrite + intent
        "reranking": 4,
        "chunking_strategy": 4,  # multi-chunk
        "prompting": 3,  # intent addenda, single base prompt
        "evaluation_harness": 2,  # gold missing record ids; Hit@k inert in prod
        "observability": 3,  # scores in sources/context
        "latency_ops": 3,  # sequential retrieve, batch embed
    }

    return {
        "metrics": metrics,
        "cases": [asdict(r) for r in results],
        "architecture": architecture,
        "architecture_max": 5,
        "architecture_avg": sum(architecture.values()) / len(architecture),
    }


if __name__ == "__main__":
    report = evaluate()
    out = ROOT / "scripts" / "offline_rag_eval_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
