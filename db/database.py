import logging
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from db.models import Base, User, FixedExpense, MonthlyBudget, SavingsBalance, DailyExpense
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
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    total_days = (month_start.replace(month=month_start.month % 12 + 1, day=1) - timedelta(days=1)).day
    days_left = (month_start.replace(month=month_start.month % 12 + 1, day=1) - today).days + 1
    coefficient = days_left / total_days if total_days else 1.0

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        for user in users:
            result = await session.execute(
                select(MonthlyBudget).where(
                    MonthlyBudget.user_id == user.id,
                    MonthlyBudget.month_start == month_start
                )
            )
            if result.scalar():
                logger.info(f"⏭ Skipping user {user.id}, budget already exists for {month_start}")
                continue

            income = user.monthly_income or 0.0
            savings_goal = user.monthly_savings or 0.0

            result = await session.execute(
                select(func.sum(FixedExpense.amount)).where(FixedExpense.user_id == user.id)
            )
            fixed_total = result.scalar() or 0.0

            adjusted_income = income * coefficient
            adjusted_fixed = fixed_total * coefficient
            adjusted_savings = savings_goal * coefficient
            remaining = adjusted_income - adjusted_fixed - adjusted_savings

            result = await session.execute(
                select(SavingsBalance).where(SavingsBalance.user_id == user.id)
            )
            savings = result.scalar()
            if not savings:
                savings = SavingsBalance(user_id=user.id, amount=0.0)
                session.add(savings)

            # Логика формирования сбережений с пояснением:
            log_parts = []

            result = await session.execute(
                select(MonthlyBudget).where(
                    MonthlyBudget.user_id == user.id,
                    MonthlyBudget.month_start == prev_month_start
                )
            )
            prev_budget = result.scalar()
            leftover = 0
            if prev_budget and prev_budget.remaining > 0:
                leftover = prev_budget.remaining
                savings.amount += leftover
                log_parts.append(f"💸 Leftover: €{leftover:.2f}")

            result = await session.execute(
                select(func.sum(DailyExpense.amount)).where(
                    DailyExpense.user_id == user.id,
                    func.date(DailyExpense.created_at) >= prev_month_start,
                    func.date(DailyExpense.created_at) <= prev_month_end
                )
            )
            real_spent = result.scalar() or 0.0
            allowed_spent = 0.0
            if prev_budget:
                allowed_spent = prev_budget.income - prev_budget.fixed - prev_budget.savings_goal

            overspent = real_spent - allowed_spent
            if overspent > 0:
                savings.amount -= overspent
                log_parts.append(f"❗ Overspent: €{overspent:.2f}")

            goal_addition = adjusted_savings
            savings.amount += goal_addition
            log_parts.append(f"📥 Current savings goal: €{goal_addition:.2f}")

            logger.info(
                f"🧮 Final savings for user {user.id}: {savings.amount:.2f} = " + " + ".join(log_parts)
            )

            logger.info(
                f"📝 Creating budget for user {user.id} on {month_start}: income={income}, fixed={fixed_total}, "
                f"savings_goal={savings_goal}, remaining={remaining:.2f}, coefficient={coefficient:.2f}"
            )
            new_budget = MonthlyBudget(
                user_id=user.id,
                month_start=month_start,
                income=income,
                fixed=fixed_total,
                savings_goal=savings_goal,
                remaining=remaining,
                coefficient=coefficient
            )
            session.add(new_budget)

        await session.commit()
        logger.info("✅ Monthly budgets updated (new + savings adjustments)")
