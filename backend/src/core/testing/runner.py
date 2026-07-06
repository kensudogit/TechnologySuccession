"""pytest 実行・結果集約。"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Literal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TestRun

SuiteName = Literal["unit", "integration", "all"]

TESTS_DIR = Path(__file__).resolve().parents[3] / "tests"


class _PytestResultCollector:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when != "call":
            return
        self.results.append(
            {
                "nodeid": report.nodeid,
                "outcome": report.outcome,
                "duration": round(report.duration, 4),
                "message": str(report.longrepr) if report.failed else None,
            }
        )


def _parse_nodeid(nodeid: str) -> tuple[str, str, str]:
    """nodeid を module / class / test に分解する。"""
    parts = nodeid.split("::")
    module = parts[0].replace("tests/", "").replace(".py", "")
    if len(parts) == 3:
        return module, parts[1], parts[2]
    if len(parts) == 2:
        return module, "(module)", parts[1]
    return module, "(module)", nodeid


def _group_by_class(raw_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classes: dict[str, dict[str, Any]] = {}
    for item in raw_results:
        module, class_name, test_name = _parse_nodeid(item["nodeid"])
        key = f"{module}::{class_name}"
        if key not in classes:
            classes[key] = {
                "module": module,
                "class_name": class_name,
                "tests": [],
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "total": 0,
            }
        bucket = classes[key]
        bucket["tests"].append(
            {
                "name": test_name,
                "outcome": item["outcome"],
                "duration": item["duration"],
                "message": item["message"],
            }
        )
        bucket["total"] += 1
        if item["outcome"] == "passed":
            bucket["passed"] += 1
        elif item["outcome"] == "failed":
            bucket["failed"] += 1
        else:
            bucket["skipped"] += 1
    return sorted(classes.values(), key=lambda c: c["class_name"])


def _run_pytest_sync(suite: SuiteName) -> dict[str, Any]:
    collector = _PytestResultCollector()
    args = [str(TESTS_DIR), "-q", "--tb=short"]
    if suite == "unit":
        args.extend(["-m", "unit"])
    elif suite == "integration":
        args.extend(["-m", "integration"])

    started = time.perf_counter()
    exit_code = pytest.main(args, plugins=[collector])
    exit_code_int = int(exit_code)
    duration_sec = round(time.perf_counter() - started, 3)

    class_results = _group_by_class(collector.results)
    passed = sum(1 for r in collector.results if r["outcome"] == "passed")
    failed = sum(1 for r in collector.results if r["outcome"] == "failed")
    skipped = sum(1 for r in collector.results if r["outcome"] == "skipped")
    total = len(collector.results)

    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_sec": duration_sec,
        "exit_code": exit_code_int,
    }

    return {
        "suite": suite,
        "status": "passed" if exit_code_int == 0 else "failed",
        "summary": summary,
        "classes": class_results,
    }


async def run_test_suite(session: AsyncSession, suite: SuiteName = "unit") -> TestRun:
    import asyncio

    result = await asyncio.to_thread(_run_pytest_sync, suite)
    run = TestRun(
        suite=suite,
        status=result["status"],
        summary=result["summary"],
        class_results={"classes": result["classes"]},
        duration_sec=result["summary"]["duration_sec"],
    )
    session.add(run)
    await session.flush()
    return run
