"""評価の正解レコード解決テスト。"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.evaluation.runner import resolve_expected_ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_expected_ids_by_equipment_and_terms() -> None:
    records = [
        SimpleNamespace(
            id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            equipment_name="コンプレッサA-03",
            symptom="運転中に異音発生",
            root_cause="ベアリング摩耗",
            action_taken="ベアリング交換",
            raw_text="",
        ),
        SimpleNamespace(
            id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            equipment_name="コンプレッサA-03",
            symptom="油温アラーム",
            root_cause="フィルター詰まり",
            action_taken="フィルター交換",
            raw_text="",
        ),
    ]
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = records
    session = AsyncMock()
    session.execute.return_value = result_mock

    ids = await resolve_expected_ids(
        session,
        {
            "expected_equipment": "コンプレッサA-03",
            "expected_match_terms": ["異音", "ベアリング"],
        },
    )
    assert ids == ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]
