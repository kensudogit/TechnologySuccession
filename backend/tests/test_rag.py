"""RAG クエリ分析・フレームワークテスト。"""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.core.rag.chunker import build_chunk_text, build_document, build_documents
from src.core.rag.context_builder import build_context
from src.core.rag.framework_info import get_rag_framework_info
from src.core.rag.generator import _confidence
from src.core.rag.langchain_client import build_rag_prompt
from src.core.rag.llamaindex_settings import configure_llamaindex
from src.core.rag.nodes import chunk_row_to_node
from src.core.rag.query_analyzer import analyze_query
from src.core.rag.retriever import _rerank, _rrf_fuse
from src.core.rag.types import RetrievedChunk


@pytest.mark.unit
class TestRagQueryAnalyzer:
    """クエリ意図・設備名抽出のユニットテスト。"""

    def test_analyze_troubleshooting_query(self) -> None:
        analysis = analyze_query("コンプレッサA-03が異音を出している。過去の原因は？")
        assert analysis.intent == "troubleshooting"
        assert "コンプレッサA-03" in analysis.equipment_names
        assert "異音" in analysis.symptom_keywords
        assert "異音" in analysis.embedding_query
        assert analysis.keyword_terms

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
        record.source_file = "sample.xlsx"

        text = build_chunk_text(record)
        doc = build_document(record)
        docs = build_documents(record)

        assert "コンプレッサA-03" in text
        assert doc.text == text
        assert doc.metadata["equipment_name"] == "コンプレッサA-03"
        assert doc.metadata["chunk_type"] == "summary"
        # summary + symptom + root_cause + action_taken
        assert len(docs) >= 4
        assert {d.metadata["chunk_type"] for d in docs} >= {
            "summary",
            "symptom",
            "root_cause",
            "action_taken",
        }


@pytest.mark.unit
class TestRagFramework:
    """LangChain / LlamaIndex 連携のユニットテスト。"""

    def test_framework_info(self) -> None:
        info = get_rag_framework_info()
        assert info["framework"] == "langchain+llamaindex"
        assert info["langchain"]["components"]["llm"] == "ChatOpenAI"
        assert "RRF" in info["llamaindex"]["components"]["fusion"]
        assert info["retrieval"]["vector_search"] is True
        assert info["retrieval"]["rerank"] is True
        assert info["retrieval"]["query_rewrite"] is True

    def test_langchain_prompt_template(self) -> None:
        prompt = build_rag_prompt("system prompt")
        messages = prompt.format_messages(query="Q", context="CTX")
        assert len(messages) == 2
        assert "Q" in messages[1].content

    def test_llamaindex_settings(self) -> None:
        configure_llamaindex()
        from llama_index.core import Settings

        assert Settings.embed_model is not None

    def test_rrf_fuse_merges_rankings(self) -> None:
        rid = uuid4()
        cid_a = uuid4()
        cid_b = uuid4()
        a = chunk_row_to_node(
            chunk_id=cid_a,
            record_id=rid,
            chunk_text="a",
            score=0.9,
            equipment_name="EQ",
            event_date=None,
            source_file="x.xlsx",
            rank_source="vector",
        )
        b = chunk_row_to_node(
            chunk_id=cid_b,
            record_id=rid,
            chunk_text="b",
            score=0.8,
            equipment_name="EQ",
            event_date=None,
            source_file="x.xlsx",
            rank_source="keyword",
        )
        fused = _rrf_fuse([[a], [b, a]], top_k=2)
        assert len(fused) == 2
        assert fused[0].chunk_id in {cid_a, cid_b}
        assert fused[0].vector_score is not None or fused[0].keyword_score is not None

    def test_context_keeps_retrieval_order(self) -> None:
        a = RetrievedChunk(
            chunk_id=uuid4(),
            record_id=uuid4(),
            chunk_text="newer-looking but lower rank",
            score=0.2,
            equipment_name="EQ",
            event_date="2025-01-01",
            source_file="a.xlsx",
            rank_source="fusion",
            vector_score=0.2,
        )
        b = RetrievedChunk(
            chunk_id=uuid4(),
            record_id=uuid4(),
            chunk_text="best match",
            score=0.9,
            equipment_name="EQ",
            event_date="2020-01-01",
            source_file="b.xlsx",
            rank_source="fusion",
            vector_score=0.9,
        )
        ctx = build_context([b, a])
        assert ctx.index("best match") < ctx.index("newer-looking")

    def test_confidence_uses_vector_score(self) -> None:
        high = RetrievedChunk(
            chunk_id=uuid4(),
            record_id=uuid4(),
            chunk_text="x",
            score=0.01,
            equipment_name="EQ",
            event_date=None,
            source_file="a.xlsx",
            rank_source="fusion",
            vector_score=0.8,
        )
        assert _confidence([high]) == "high"

    def test_rerank_boosts_equipment_match(self) -> None:
        analysis = analyze_query("コンプレッサA-03の異音")
        weak = RetrievedChunk(
            chunk_id=uuid4(),
            record_id=uuid4(),
            chunk_text="ポンプの圧力低下",
            score=0.05,
            equipment_name="ポンプB-12",
            event_date=None,
            source_file="a.xlsx",
            rank_source="fusion",
            vector_score=0.5,
            keyword_score=1.0,
        )
        strong = RetrievedChunk(
            chunk_id=uuid4(),
            record_id=uuid4(),
            chunk_text="コンプレッサA-03 異音 ベアリング",
            score=0.04,
            equipment_name="コンプレッサA-03",
            event_date=None,
            source_file="b.xlsx",
            rank_source="fusion",
            vector_score=0.45,
            keyword_score=2.0,
        )
        ranked = _rerank([weak, strong], analysis)
        assert ranked[0].equipment_name == "コンプレッサA-03"
