"""pytest 共通設定。"""
from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: unit tests without external dependencies")
    config.addinivalue_line("markers", "integration: integration tests requiring database")
