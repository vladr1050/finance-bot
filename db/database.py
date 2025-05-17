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
    from datetime import timedelta
    today = date.today()
    month_start = today.replace(day=1)
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        for user in users:
            # ── Пропускаем, если бюджет уже есть ─────────────
            result = await session.execute(
                select(MonthlyBudget).where(
                    MonthlyBudget.user_id == user.id,
                    MonthlyBudget.month_start == month_start
                )
            )
            if result.scalar():
                continue

            # ── Доходы, расходы, цели ─────────────
            income = user.monthly_income or 0.0
            savings_goal = user.monthly_savings or 0.0

            result = await session.execute(
                select(func.sum(FixedExpense.amount)).where(FixedExpense.user_id == user.id)
            )
            fixed_total = result.scalar() or 0.0

            # ── Считаем новый remaining ─────────────
            remaining = income - fixed_total - savings_goal

            # ── Получаем баланс накоплений или создаём ─────────────
            result = await session.execute(
                select(SavingsBalance).where(SavingsBalance.user_id == user.id)
            )
            savings = result.scalar()
            if not savings:
                savings = SavingsBalance(user_id=user.id, amount=0.0)
                session.add(savings)

            # ── Шаг 1: Добавляем остаток прошлого месяца в накопления ─────────────
            result = await session.execute(
                select(MonthlyBudget).where(
                    MonthlyBudget.user_id == user.id,
                    MonthlyBudget.month_start == prev_month_start
                )
            )
            prev_budget = result.scalar()
            if prev_budget and prev_budget.remaining > 0:
                logger.info(f"💸 Adding €{prev_budget.remaining:.2f} to savings from leftover")
                savings.amount += prev_budget.remaining

            # ── Шаг 2: Считаем фактические траты за прошлый месяц ─────────────
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
                logger.info(f"❗ Overspent €{overspent:.2f} in previous month → deducting from savings")
                savings.amount -= overspent

            # ── Добавляем бюджет нового месяца ─────────────
            logger.info(f"📝 Creating budget for user {user.id} on {month_start}: income={income}, fixed={fixed_total}, savings_goal={savings_goal}, remaining={remaining}")
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
        logger.info("✅ Monthly budgets updated (new + savings adjustments)")

