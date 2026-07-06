"""Excel クレンジング。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.core.cleansing.equipment_aliases import normalize_equipment_name
from src.core.cleansing.schema_mapper import map_columns
from src.core.cleansing.text_normalizer import (
    content_hash,
    normalize_date,
    normalize_text,
    parse_measured_value,
)
from src.db.models import RecordCategory, SourceType


@dataclass
class CleansedRecord:
    source_type: SourceType
    source_file: str
    record_category: RecordCategory
    event_date: Any
    equipment_id: str | None
    equipment_name: str | None
    line_name: str | None
    symptom: str | None
    root_cause: str | None
    action_taken: str | None
    parts_used: str | None
    downtime_hours: float | None
    measured_value: str | None
    unit: str | None
    result: str | None
    inspector: str | None
    raw_text: str
    cleansing_issues: list[str] = field(default_factory=list)
    content_hash: str = ""


@dataclass
class CleansingReport:
    total_rows: int = 0
    imported_rows: int = 0
    skipped_rows: int = 0
    issues: list[dict] = field(default_factory=list)
    records: list[CleansedRecord] = field(default_factory=list)


def _detect_header_row(df: pd.DataFrame) -> int:
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        non_empty = sum(1 for v in row if normalize_text(str(v)))
        if non_empty >= 3:
            return i
    return 0


def _category_from_text(text: str | None) -> RecordCategory:
    t = normalize_text(text).lower()
    if any(k in t for k in ("故障", "failure", "異常")):
        return RecordCategory.FAILURE
    if any(k in t for k in ("交換", "parts", "部品")):
        return RecordCategory.PARTS_REPLACEMENT
    if any(k in t for k in ("日報", "daily", "作業")):
        return RecordCategory.DAILY_WORK
    return RecordCategory.INSPECTION


def _build_raw_text(row: dict[str, Any]) -> str:
    parts = []
    for key, label in [
        ("equipment_name", "設備"),
        ("event_date", "日付"),
        ("symptom", "症状"),
        ("root_cause", "原因"),
        ("action_taken", "処置"),
        ("measured_value", "測定値"),
        ("result", "結果"),
    ]:
        val = row.get(key)
        if val:
            parts.append(f"{label}: {val}")
    return " / ".join(parts)


def cleanse_excel(file_path: str, source_file: str) -> CleansingReport:
    report = CleansingReport()
    xls = pd.ExcelFile(file_path)
    seen_hashes: set[str] = set()

    for sheet in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet, header=None)
        if df.empty:
            continue
        header_idx = _detect_header_row(df)
        headers = [normalize_text(str(v)) for v in df.iloc[header_idx].tolist()]
        col_map = map_columns(headers)
        data_df = df.iloc[header_idx + 1 :].copy()
        data_df.columns = headers
        report.total_rows += len(data_df)

        for idx, row in data_df.iterrows():
            mapped: dict[str, Any] = {}
            issues: list[str] = []
            for col, val in row.items():
                if col in col_map:
                    mapped[col_map[col]] = val

            event_date = normalize_date(mapped.get("event_date"))
            if not event_date:
                issues.append("日付が解析できませんでした")

            equipment_name = normalize_equipment_name(
                normalize_text(str(mapped.get("equipment_name", ""))) or None
            )
            measured, unit = parse_measured_value(
                normalize_text(str(mapped.get("measured_value", ""))) or None
            )
            if mapped.get("unit"):
                unit = normalize_text(str(mapped.get("unit"))) or unit

            record_category = _category_from_text(
                normalize_text(str(mapped.get("record_category", ""))) or None
            )
            if mapped.get("symptom") and "故障" in normalize_text(str(mapped.get("symptom"))):
                record_category = RecordCategory.FAILURE

            cleansed = CleansedRecord(
                source_type=SourceType.EXCEL,
                source_file=source_file,
                record_category=record_category,
                event_date=event_date,
                equipment_id=normalize_text(str(mapped.get("equipment_id", ""))) or None,
                equipment_name=equipment_name,
                line_name=normalize_text(str(mapped.get("line_name", ""))) or None,
                symptom=normalize_text(str(mapped.get("symptom", ""))) or None,
                root_cause=normalize_text(str(mapped.get("root_cause", ""))) or None,
                action_taken=normalize_text(str(mapped.get("action_taken", ""))) or None,
                parts_used=normalize_text(str(mapped.get("parts_used", ""))) or None,
                downtime_hours=None,
                measured_value=measured,
                unit=unit,
                result=normalize_text(str(mapped.get("result", ""))) or None,
                inspector=normalize_text(str(mapped.get("inspector", ""))) or None,
                raw_text="",
                cleansing_issues=issues,
            )
            cleansed.raw_text = _build_raw_text(cleansed.__dict__) or normalize_text(str(row.to_dict()))

            h = content_hash(
                cleansed.equipment_name or "",
                str(cleansed.event_date or ""),
                cleansed.symptom or cleansed.raw_text,
            )
            cleansed.content_hash = h

            if h in seen_hashes:
                report.skipped_rows += 1
                report.issues.append({"row": int(idx), "reason": "duplicate", "sheet": sheet})
                continue
            seen_hashes.add(h)

            if not cleansed.raw_text.strip():
                report.skipped_rows += 1
                report.issues.append({"row": int(idx), "reason": "empty", "sheet": sheet})
                continue

            report.records.append(cleansed)
            report.imported_rows += 1

    return report
