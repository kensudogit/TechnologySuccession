"""RAG クエリ分析テスト。"""
from src.core.rag.query_analyzer import analyze_query


def test_analyze_troubleshooting_query():
    analysis = analyze_query("コンプレッサA-03が異音を出している。過去の原因は？")
    assert analysis.intent == "troubleshooting"
    assert "コンプレッサA-03" in analysis.equipment_names


def test_analyze_history_query():
    analysis = analyze_query("ポンプB-12の前回の故障履歴は？")
    assert analysis.intent == "history_lookup"
