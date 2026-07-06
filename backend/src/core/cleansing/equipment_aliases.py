"""設備名別名辞書。"""
from __future__ import annotations

import json
from pathlib import Path

from src.config import settings
from src.core.cleansing.text_normalizer import normalize_text


def load_aliases() -> dict[str, list[str]]:
    path = Path(settings.config_dir) / "equipment_aliases.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_equipment_name(name: str | None) -> str | None:
    if not name:
        return None
    text = normalize_text(name)
    aliases = load_aliases()
    for canonical, variants in aliases.items():
        all_names = [canonical, *variants]
        if text in [normalize_text(v) for v in all_names]:
            return canonical
    return text


def expand_query_terms(query: str) -> list[str]:
    """検索クエリ用の同義語展開。"""
    terms = [normalize_text(query)]
    aliases = load_aliases()
    for canonical, variants in aliases.items():
        names = [canonical, *variants]
        if any(n in query for n in names):
            terms.extend(names)
    return list(dict.fromkeys(terms))
