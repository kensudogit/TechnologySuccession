"""クレンジングテスト。"""
from datetime import date

from src.core.cleansing.excel_cleaner import cleanse_excel
from src.core.cleansing.text_normalizer import normalize_date, normalize_text, content_hash


def test_normalize_text():
    assert normalize_text("　コンプレッサA-03　") == "コンプレッサA-03"


def test_normalize_date():
    assert normalize_date("2024-03-15") == date(2024, 3, 15)


def test_content_hash_stable():
    h1 = content_hash("コンプレッサA-03", "2024-03-15", "異音")
    h2 = content_hash("コンプレッサA-03", "2024-03-15", "異音")
    assert h1 == h2


def test_cleanse_excel(tmp_path):
    import pandas as pd

    path = tmp_path / "test.xlsx"
    pd.DataFrame(
        [
            {
                "点検日": "2024-03-15",
                "設備名": "コンプレッサA-03",
                "異常内容": "異音",
                "原因": "ベアリング摩耗",
                "処置内容": "交換",
            }
        ]
    ).to_excel(path, index=False)

    report = cleanse_excel(str(path), "test.xlsx")
    assert report.imported_rows == 1
    assert report.records[0].equipment_name == "コンプレッサA-03"
