"""RAG クエリ分析・フレームワークテスト。"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.core.rag.chunker import build_chunk_text, build_document
from src.core.rag.framework_info import get_rag_framework_info
from src.core.rag.langchain_client import build_rag_prompt
from src.core.rag.llamaindex_settings import configure_llamaindex
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


@pytest.mark.unit
class TestRagFramework:
    """LangChain / LlamaIndex 連携のユニットテスト。"""

    def test_framework_info(self) -> None:
        info = get_rag_framework_info()
        assert info["framework"] == "langchain+llamaindex"
        assert info["langchain"]["components"]["llm"] == "ChatOpenAI"
        assert info["llamaindex"]["components"]["fusion"] == "QueryFusionRetriever (reciprocal_rerank)"
        assert info["retrieval"]["vector_search"] is True

    def test_langchain_prompt_template(self) -> None:
        prompt = build_rag_prompt("system prompt")
        messages = prompt.format_messages(query="Q", context="CTX")
        assert len(messages) == 2
        assert "Q" in messages[1].content

    def test_llamaindex_settings(self) -> None:
        configure_llamaindex()
        from llama_index.core import Settings

        assert Settings.embed_model is not None
