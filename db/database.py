# db/database.py
import logging
from datetime import datetime, date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from db.models import Base, User, FixedExpense, MonthlyBudget
from config import Config

logger = logging.getLogger(__name__)

DATABASE_URL = Config.DB_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database initialized")

# ─────────────────────────────────────
# Monthly Budget Generator
# ─────────────────────────────────────

async def check_or_create_monthly_budgets():
    today = date.today()
    month_start = today.replace(day=1)

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        for user in users:
            # Check if budget for this month already exists
            result = await session.execute(
                select(MonthlyBudget).where(
                    MonthlyBudget.user_id == user.id,
                    MonthlyBudget.month_start == month_start
                )
            )
            existing = result.scalar()
            if existing:
                continue

            # Calculate total fixed expenses
            result = await session.execute(
                select(func.sum(FixedExpense.amount)).where(FixedExpense.user_id == user.id)
            )
            fixed_total = result.scalar() or 0.0
            savings_goal = user.monthly_savings or 0.0
            income = user.monthly_income or 0.0
            remaining = income - fixed_total - savings_goal

            logger.info(f"📝 Creating budget for user {user.id} on {month_start}: income={income}, fixed={fixed_total}, savings={savings_goal}, remaining={remaining}")

            new_budget = MonthlyBudget(
                user_id=user.id,
                month_start=month_start,
                income=income,
                fixed=fixed_total,
                savings_goal=savings_goal,
                remaining=remaining
            )
            session.add(new_budget)

        await session.commit()
        logger.info("✅ Monthly budgets created (if missing)")
