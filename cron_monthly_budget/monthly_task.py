import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import logging
from app.db.database import check_or_create_monthly_budgets
from utils import handle_overspending, move_remaining_to_savings
from app.config import Config

if not Config.is_valid():
    raise RuntimeError("❌ Missing BOT_TOKEN or DB_URL environment variables")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("📅 Starting monthly cron task...")

    await check_or_create_monthly_budgets()
    logger.info("✅ Monthly budgets created (if needed)")

    await handle_overspending()
    logger.info("💸 Overspending handled")

    await move_remaining_to_savings()
    logger.info("💰 Remaining balances moved to savings")

    logger.info("🌟 Monthly task completed.")

if __name__ == "__main__":
    asyncio.run(main())
