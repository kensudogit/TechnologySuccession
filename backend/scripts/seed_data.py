"""サンプルデータ投入スクリプト。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from src.core.seed.seed_service import seed_if_empty, seed_test_data
from src.db.database import AsyncSessionLocal, init_db


async def seed(force: bool = False) -> None:
    await init_db()
    if not force:
        result = await seed_if_empty()
        if result is None:
            print("DB already has data. Use --force to add more.")
            return
        print(f"Seed completed: {result}")
        return

    async with AsyncSessionLocal() as session:
        result = await seed_test_data(session)
        await session.commit()
        print(f"Force seed completed: {result}")


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    asyncio.run(seed(force=force_flag))
