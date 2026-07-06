"""プロンプト管理。"""
from __future__ import annotations

from pathlib import Path

from src.config import settings


def load_system_prompt(version: str | None = None) -> str:
    ver = version or settings.prompt_version
    path = settings.prompts_dir / f"system_{ver}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    fallback = settings.prompts_dir / "system_v1.txt"
    return fallback.read_text(encoding="utf-8") if fallback.exists() else "You are a maintenance expert."
