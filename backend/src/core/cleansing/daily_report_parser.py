"""日報パーサ。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from src.core.cleansing.equipment_aliases import normalize_equipment_name
from src.core.cleansing.text_normalizer import content_hash, normalize_date, normalize_text
from src.db.models import RecordCategory, SourceType


@dataclass
class DailyReportSection:
    event_date: object | None
    equipment_name: str | None
    line_name: str | None
    symptom: str | None
    action_taken: str | None
    raw_text: str
    cleansing_issues: list[str] = field(default_factory=list)


DATE_PATTERN = re.compile(r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})")
EQUIPMENT_PATTERN = re.compile(r"(?:設備|機器)[:：]\s*(.+)")


def parse_daily_report_text(text: str, source_file: str) -> list[DailyReportSection]:
    sections: list[DailyReportSection] = []
    blocks = re.split(r"\n{2,}", text.strip())
    current_date = None

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        issues: list[str] = []
        date_match = DATE_PATTERN.search(block)
        if date_match:
            current_date = normalize_date(date_match.group(1))
        event_date = current_date

        equipment_name = None
        equip_match = EQUIPMENT_PATTERN.search(block)
        if equip_match:
            equipment_name = normalize_equipment_name(equip_match.group(1).split("\n")[0])

        symptom = None
        action_taken = None
        for line in block.split("\n"):
            line = line.strip()
            if line.startswith(("異常", "故障", "症状")):
                symptom = normalize_text(line.split(":", 1)[-1])
            if line.startswith(("処置", "対応", "作業")):
                action_taken = normalize_text(line.split(":", 1)[-1])

        if not event_date:
            issues.append("日付が見つかりませんでした")

        sections.append(
            DailyReportSection(
                event_date=event_date,
                equipment_name=equipment_name,
                line_name=None,
                symptom=symptom,
                action_taken=action_taken,
                raw_text=normalize_text(block),
                cleansing_issues=issues,
            )
        )

    return sections


def parse_daily_report_file(file_path: str, source_file: str) -> list[dict]:
    path = Path(file_path)
    text = path.read_text(encoding="utf-8", errors="replace")
    sections = parse_daily_report_text(text, source_file)
    records = []
    for sec in sections:
        h = content_hash(sec.equipment_name or "", str(sec.event_date or ""), sec.raw_text)
        records.append(
            {
                "source_type": SourceType.DAILY_REPORT,
                "source_file": source_file,
                "record_category": RecordCategory.DAILY_WORK,
                "event_date": sec.event_date,
                "equipment_name": sec.equipment_name,
                "line_name": sec.line_name,
                "symptom": sec.symptom,
                "action_taken": sec.action_taken,
                "raw_text": sec.raw_text,
                "cleansing_issues": sec.cleansing_issues,
                "content_hash": h,
            }
        )
    return records
