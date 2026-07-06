"""テキスト正規化ユーティリティ。"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime

from dateutil import parser as date_parser


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_date(value: object | None) -> date | None:
    if value is None or (isinstance(value, float) and str(value) == "nan"):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = normalize_text(str(value))
    if not text:
        return None
    try:
        return date_parser.parse(text, dayfirst=False, yearfirst=True).date()
    except (ValueError, TypeError, OverflowError):
        return None


def parse_measured_value(value: str | None) -> tuple[str | None, str | None]:
    text = normalize_text(value)
    if not text:
        return None, None
    match = re.match(r"^([\d.]+)\s*([a-zA-Z℃%°]+)?$", text)
    if match:
        return match.group(1), match.group(2)
    return text, None


def content_hash(*parts: str) -> str:
    joined = "|".join(normalize_text(p) for p in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
