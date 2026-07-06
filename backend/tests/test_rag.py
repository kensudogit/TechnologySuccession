"""RAG クエリ分析テスト。"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.core.rag.chunker import build_chunk_text, build_document
from src.core.rag.query_analyzer import analyze_query


@pytest.mark.unit
class TestRagQueryAnalyzer:
    """クエリ意図・設備名抽出のユニットテスト。"""

    def test_analyze_troubleshooting_query(self) -> None:
        analysis = analyze_query("コンプレッサA-03が異音を出している。過去の原因は？")
        assert analysis.intent == "troubleshooting"
        assert "コンプレッサA-03" in analysis.equipment_names

    def test_analyze_history_query(self) -> None:
        analysis = analyze_query("ポンプB-12の前回の故障履歴は？")
        assert analysis.intent == "history_lookup"


@pytest.mark.unit
class TestRagChunker:
    """LlamaIndex Document 生成のユニットテスト。"""

    def test_build_llamaindex_document(self) -> None:
        record = MagicMock()
        record.id = "00000000-0000-0000-0000-000000000001"
        record.equipment_name = "コンプレッサA-03"
        record.event_date = None
        record.record_category = None
        record.result = None
        record.symptom = "異音"
        record.root_cause = "ベアリング摩耗"
        record.action_taken = "交換"
        record.measured_value = None
        record.unit = None
        record.raw_text = "raw"

        text = build_chunk_text(record)
        doc = build_document(record)

        assert "コンプレッサA-03" in text
        assert doc.text == text
        assert doc.metadata["equipment_name"] == "コンプレッサA-03"
        assert doc.metadata["chunk_type"] == "summary"
