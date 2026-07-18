"""取り込み用サンプルデータ（Excel / PDF）を生成する。"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from src.core.seed.sample_rows import SAMPLE_EXCEL_ROWS  # noqa: E402

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None

SAMPLES = ROOT / "data" / "samples"

PDF_TEXT = """技術継承プラットフォーム 保全マニュアル抜粋

1. コンプレッサA-03 異音時の標準対応
症状: 運転中の金属音、ベアリング部からの異音
想定原因: ベアリング摩耗、潤滑不足
推奨処置:
  1) 安全停止し電源ロックアウト
  2) ベアリング状態を目視・触診で確認
  3) 必要に応じてベアリング交換と潤滑油交換
  4) 試運転30分で異音消失を確認

2. ポンプB-12 圧力低下時の標準対応
症状: 吐出圧力が目標より低い
想定原因: インペラ摩耗、配管閉塞
推奨処置:
  1) ストレーナと配管の詰まり確認
  2) インペラ摩耗量を測定
  3) 摩耗が大きい場合はインペラ交換
  4) 復旧後に圧力・流量を記録

3. モータC-01 過電流トリップ時の標準対応
症状: 起動時に過電流でトリップ
想定原因: ベアリング固着、芯出し不良
推奨処置:
  1) 手回しで回転抵抗を確認
  2) ベアリング交換または芯出し調整
  3) 絶縁抵抗測定後に再起動
"""


def write_excel() -> Path:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    path = SAMPLES / "maintenance_records_sample.xlsx"
    pd.DataFrame(SAMPLE_EXCEL_ROWS).to_excel(path, index=False)
    return path


def write_pdf() -> Path | None:
    if fitz is None:
        return None
    path = SAMPLES / "maintenance_manual_sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), PDF_TEXT, fontsize=11)
    doc.save(path)
    doc.close()
    return path


def main() -> None:
    excel = write_excel()
    pdf = write_pdf()
    print(f"Excel: {excel} ({len(SAMPLE_EXCEL_ROWS)} rows)")
    print(f"PDF: {pdf or 'skipped (PyMuPDF missing)'}")
    print(f"Daily report: {SAMPLES / 'daily_report_sample.txt'}")


if __name__ == "__main__":
    main()
