"""テストデータ投入サービス。"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.ingestion.ingest_service import ingest_daily_report, ingest_excel
from src.db.database import AsyncSessionLocal, init_db
from src.db.models import MaintenanceRecord

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(settings.data_dir).parent if settings.data_dir.endswith("data") else Path(settings.data_dir)


def create_sample_excel() -> str:
    samples_dir = Path(settings.data_dir) / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    path = samples_dir / "maintenance_records_sample.xlsx"
    df = pd.DataFrame(
        [
            {
                "点検日": "2024-03-15",
                "設備名": "コンプレッサA-03",
                "ライン": "ライン1",
                "異常内容": "運転中に異音発生",
                "原因": "ベアリング摩耗",
                "処置内容": "ベアリング交換、潤滑油交換",
                "結果": "OK",
                "担当者": "田中",
            },
            {
                "点検日": "2024-06-20",
                "設備名": "コンプレッサA-03",
                "ライン": "ライン1",
                "異常内容": "油温95℃でアラーム",
                "原因": "オイルフィルター詰まり",
                "処置内容": "フィルター交換",
                "結果": "OK",
                "担当者": "佐藤",
            },
            {
                "点検日": "2024-01-10",
                "設備名": "ポンプB-12",
                "ライン": "ライン2",
                "異常内容": "吐出圧力低下 80kPa",
                "原因": "インペラ摩耗",
                "処置内容": "インペラ交換、配管清掃",
                "結果": "OK",
                "担当者": "鈴木",
            },
            {
                "点検日": "2024-08-05",
                "設備名": "モータC-01",
                "ライン": "ライン3",
                "異常内容": "起動時過電流トリップ",
                "原因": "ベアリング固着",
                "処置内容": "ベアリング交換、軸芯調整",
                "結果": "OK",
                "担当者": "高橋",
            },
            {
                "点検日": "2024-11-12",
                "設備名": "コンプレッサA-03",
                "ライン": "ライン1",
                "測定値": "88",
                "単位": "℃",
                "異常内容": "定期点検で油温高め",
                "処置内容": "冷却ファン清掃",
                "結果": "OK",
                "担当者": "田中",
            },
            {
                "点検日": "2023-09-08",
                "設備名": "ポンプB-12",
                "ライン": "ライン2",
                "異常内容": "シール部から漏れ",
                "原因": "パッキン劣化",
                "処置内容": "パッキン交換",
                "結果": "OK",
                "担当者": "伊藤",
            },
            {
                "点検日": "2023-12-01",
                "設備名": "モータC-01",
                "ライン": "ライン3",
                "異常内容": "振動値上限超過",
                "原因": "アライメント不良",
                "処置内容": "アライメント調整",
                "結果": "OK",
                "担当者": "山本",
            },
        ]
    )
    df.to_excel(path, index=False)
    return str(path)


async def seed_test_data(session: AsyncSession) -> dict:
    excel_path = create_sample_excel()
    daily_path = Path(settings.data_dir) / "samples" / "daily_report_sample.txt"

    excel_job = await ingest_excel(session, excel_path, "maintenance_records_sample.xlsx")
    daily_imported = 0
    daily_skipped = 0
    if daily_path.exists():
        daily_job = await ingest_daily_report(session, str(daily_path), "daily_report_sample.txt")
        daily_imported = daily_job.imported_rows
        daily_skipped = daily_job.skipped_rows

    total = await session.scalar(select(func.count()).select_from(MaintenanceRecord))

    return {
        "excel_imported": excel_job.imported_rows,
        "excel_skipped": excel_job.skipped_rows,
        "daily_imported": daily_imported,
        "daily_skipped": daily_skipped,
        "total_records": total or 0,
    }


async def seed_if_empty() -> dict | None:
    await init_db()
    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(MaintenanceRecord))
        if count and count > 0:
            logger.info("DB already has %d records, skipping seed", count)
            return None
        result = await seed_test_data(session)
        await session.commit()
        logger.info("Seeded test data: %s", result)
        return result
