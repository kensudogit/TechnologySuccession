"""プロンプト管理。"""
from __future__ import annotations

from pathlib import Path

from src.config import settings

_INTENT_ADDENDA = {
    "troubleshooting": """
## 今回の質問意図: トラブルシューティング
- 想定原因と推奨処置を具体的に書く
- 類似症状の過去実績を優先して引用する
""",
    "history_lookup": """
## 今回の質問意図: 履歴照会
- 時系列（新しい順）で関連実績を整理する
- 原因・処置より「いつ・何が起きたか」を優先する
""",
    "procedure": """
## 今回の質問意図: 手順確認
- 過去の成功処置をステップ形式でまとめる
- 安全上の確認ポイントがあれば明示する
""",
}


def load_system_prompt(version: str | None = None, intent: str | None = None) -> str:
    ver = version or settings.prompt_version
    path = settings.prompts_dir / f"system_{ver}.txt"
    if path.exists():
        base = path.read_text(encoding="utf-8")
    else:
        fallback = settings.prompts_dir / "system_v1.txt"
        base = (
            fallback.read_text(encoding="utf-8")
            if fallback.exists()
            else "You are a maintenance expert."
        )

    # 意図別プロンプトがあれば優先
    if intent:
        intent_path = settings.prompts_dir / f"system_{ver}_{intent}.txt"
        if intent_path.exists():
            return intent_path.read_text(encoding="utf-8")
        addendum = _INTENT_ADDENDA.get(intent, "")
        if addendum:
            return f"{base}\n{addendum}"
    return base
