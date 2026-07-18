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

    @property
    def embedding_query(self) -> str:
        """ベクトル検索用に設備・症状を強調したクエリ。"""
        parts = [self.original_query]
        parts.extend(self.equipment_names)
        parts.extend(self.symptom_keywords)
        # 別名展開は短語のみ付与（ノイズ抑制）
        for term in self.expanded_terms:
            if term != self.original_query and len(term) <= 40:
                parts.append(term)
        return " ".join(dict.fromkeys(p for p in parts if p))

    @property
    def keyword_terms(self) -> list[str]:
        """キーワード検索用の短い語リスト。"""
        terms: list[str] = []
        terms.extend(self.equipment_names)
        terms.extend(self.symptom_keywords)
        for term in self.expanded_terms:
            if term and term != self.original_query and len(term) <= 40:
                terms.append(term)
        # 元クエリから記号を除いた断片も追加
        cleaned = re.sub(r"[?？。、,.！!]", " ", self.original_query)
        for token in cleaned.split():
            if len(token) >= 2:
                terms.append(token)
        return list(dict.fromkeys(terms))[:12]


SYMPTOM_KEYWORDS = [
    "異音",
    "停止",
    "漏れ",
    "異常",
    "故障",
    "アラーム",
    "オーバー",
    "温度",
    "油温",
    "圧力",
    "過電流",
    "振動",
    "発熱",
    "トリップ",
    "詰まり",
    "摩耗",
    "固着",
]


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

    if any(k in query for k in ("手順", "方法", "どうやって", "やり方")):
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
