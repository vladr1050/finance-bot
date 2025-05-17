import asyncio
from db.database import init_db, check_or_create_monthly_budgets

async def main():
    await init_db()
    await check_or_create_monthly_budgets()

if __name__ == "__main__":
    asyncio.run(main())
