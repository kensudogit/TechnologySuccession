"""列名マッピング。"""
from __future__ import annotations

COLUMN_ALIASES: dict[str, list[str]] = {
    "event_date": ["点検日", "実施日", "日付", "date", "作業日", "報告日"],
    "equipment_id": ["設備ID", "機番", "設備番号", "equipment_id"],
    "equipment_name": ["設備名", "設備", "機器名", "equipment", "機械名"],
    "line_name": ["ライン", "ライン名", "line", "工程"],
    "symptom": ["症状", "異常内容", "異常", "故障内容", "symptom"],
    "root_cause": ["原因", "根本原因", "root_cause"],
    "action_taken": ["処置", "処置内容", "対応", "action", "作業内容"],
    "parts_used": ["使用部品", "部品", "parts"],
    "measured_value": ["測定値", "値", "measurement"],
    "unit": ["単位", "unit"],
    "result": ["結果", "判定", "result", "ok/ng"],
    "inspector": ["担当者", "点検者", "作業者", "inspector"],
    "record_category": ["種別", "カテゴリ", "category"],
}


def map_columns(headers: list[str]) -> dict[str, str]:
    """Excel ヘッダー → 正規化列名のマッピング。"""
    mapping: dict[str, str] = {}
    normalized_headers = {h: h.strip().lower() for h in headers if h}

    for canonical, aliases in COLUMN_ALIASES.items():
        for header, norm in normalized_headers.items():
            if norm in [a.lower() for a in aliases]:
                mapping[header] = canonical
                break
    return mapping
