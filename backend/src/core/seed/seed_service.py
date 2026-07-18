"""サンプルデータを PostgreSQL に投入するサービス。"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.ingestion.ingest_service import ingest_daily_report, ingest_excel
from src.core.seed.sample_rows import SAMPLE_EXCEL_ROWS
from src.db.database import AsyncSessionLocal, init_db
from src.db.models import MaintenanceRecord

logger = logging.getLogger(__name__)

DAILY_REPORT_FALLBACK = """2024-03-15
設備: コンプレッサA-03
異常: 運転中に異音が発生。ベアリング部から金属音。
処置: ベアリング交換、潤滑油交換、試運転30分実施。異音解消を確認。

2024-06-20
設備: コンプレッサA-03
異常: 油温が95℃まで上昇しアラーム発報。
処置: オイルフィルター詰まりを確認。フィルター交換後、油温82℃に安定。

2024-01-10
設備: ポンプB-12
異常: 吐出圧力が低下。目圧120kPaに対し80kPa。
処置: インペラ摩耗を確認。インペラ交換、配管清掃実施。

2024-08-05
設備: モータC-01
異常: 起動時に過電流トリップ。
処置: ベアリング固着を確認。ベアリング交換、軸芯調整実施。
"""


def ensure_sample_excel() -> str:
    """サンプル Excel を用意してパスを返す。"""
    samples_dir = Path(settings.data_dir) / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    path = samples_dir / "maintenance_records_sample.xlsx"
    # 常に最新サンプル行で書き出し（取り込みは content_hash で重複スキップ）
    pd.DataFrame(SAMPLE_EXCEL_ROWS).to_excel(path, index=False)
    return str(path)


def ensure_sample_daily_report() -> str:
    """サンプル日報を用意してパスを返す。"""
    samples_dir = Path(settings.data_dir) / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    path = samples_dir / "daily_report_sample.txt"
    if not path.exists() or path.stat().st_size == 0:
        path.write_text(DAILY_REPORT_FALLBACK, encoding="utf-8")
    return str(path)


async def seed_test_data(session: AsyncSession) -> dict:
    """Excel + 日報サンプルを PostgreSQL に登録する。"""
    excel_path = ensure_sample_excel()
    daily_path = ensure_sample_daily_report()

    excel_job = await ingest_excel(session, excel_path, "maintenance_records_sample.xlsx")
    daily_job = await ingest_daily_report(session, daily_path, "daily_report_sample.txt")

    total = await session.scalar(select(func.count()).select_from(MaintenanceRecord))

    return {
        "excel_imported": excel_job.imported_rows,
        "excel_skipped": excel_job.skipped_rows,
        "daily_imported": daily_job.imported_rows,
        "daily_skipped": daily_job.skipped_rows,
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
        logger.info("Seeded sample data into PostgreSQL: %s", result)
        return result
