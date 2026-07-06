"""クエリ理解。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.core.cleansing.equipment_aliases import expand_query_terms, load_aliases


@dataclass
class QueryAnalysis:
    original_query: str
    intent: str = "troubleshooting"
    equipment_names: list[str] = field(default_factory=list)
    symptom_keywords: list[str] = field(default_factory=list)
    expanded_terms: list[str] = field(default_factory=list)


SYMPTOM_KEYWORDS = ["異音", "停止", "漏れ", "異常", "故障", "アラーム", "オーバー", "温度", "圧力"]


def analyze_query(query: str) -> QueryAnalysis:
    analysis = QueryAnalysis(original_query=query)
    analysis.expanded_terms = expand_query_terms(query)

    aliases = load_aliases()
    for canonical, variants in aliases.items():
        names = [canonical, *variants]
        if any(n in query for n in names):
            analysis.equipment_names.append(canonical)

    for kw in SYMPTOM_KEYWORDS:
        if kw in query:
            analysis.symptom_keywords.append(kw)

    if any(k in query for k in ("手順", "方法", "どうやって")):
        analysis.intent = "procedure"
    elif any(k in query for k in ("履歴", "前回", "いつ")) and not any(
        k in query for k in ("原因", "処置", "どうすれば")
    ):
        analysis.intent = "history_lookup"
    elif analysis.symptom_keywords or any(
        k in query for k in ("原因", "処置", "故障", "トラブル", "異音")
    ):
        analysis.intent = "troubleshooting"
    elif any(k in query for k in ("過去", "履歴")):
        analysis.intent = "history_lookup"
    else:
        analysis.intent = "troubleshooting"

    # 設備名が明示されていない場合、英数字パターンを拾う
    if not analysis.equipment_names:
        match = re.search(r"[A-Za-z\u3040-\u30ff\u4e00-\u9fff]+[-\d]+", query)
        if match:
            analysis.equipment_names.append(match.group(0))

    return analysis
