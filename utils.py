import logging
from datetime import date, timedelta
from sqlalchemy import func, select
from app.db.models import User, DailyExpense, MonthlyBudget, SavingsBalance
from app.db.database import async_session

logger = logging.getLogger(__name__)

async def deduct_from_savings_if_needed(user_id: int, spent: float, remaining: float):
    """
    Если пользователь потратил больше, чем у него есть в remaining,
    разница вычитается из savings.
    """
    overspent = spent - remaining
    if overspent <= 0:
        return  # перерасхода нет

    async with async_session() as session:
        user_result = await session.execute(select(User).where(User.id == user_id))
        user = user_result.scalar()

        savings_result = await session.execute(select(SavingsBalance).where(SavingsBalance.user_id == user.id))
        savings = savings_result.scalar()

        if not savings:
            savings = SavingsBalance(user_id=user.id, amount=0.0)
            session.add(savings)

        savings.amount -= overspent
        await session.commit()

        logger.info(f"💸 Overspending of €{overspent:.2f} deducted from savings for user {user_id}")

# ─────────────────────────────────────
# ⬇️ NEW: Handle overspending from last month
# ─────────────────────────────────────
async def handle_overspending():
    today = date.today()
    month_start = today.replace(day=1)
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        for user in users:
            # Предыдущий бюджет
            result = await session.execute(
                select(MonthlyBudget).where(
                    MonthlyBudget.user_id == user.id,
                    MonthlyBudget.month_start == prev_month_start
                )
            )
            prev_budget = result.scalar()
            if not prev_budget:
                continue

            allowed_spending = prev_budget.income - prev_budget.fixed - prev_budget.savings_goal

            result = await session.execute(
                select(func.sum(DailyExpense.amount)).where(
                    DailyExpense.user_id == user.id,
                    func.date(DailyExpense.created_at) >= prev_month_start,
                    func.date(DailyExpense.created_at) <= prev_month_end
                )
            )
            real_spent = result.scalar() or 0.0

            await deduct_from_savings_if_needed(user.id, real_spent, allowed_spending)

        await session.commit()

# ─────────────────────────────────────
# ⬇️ NEW: Move remaining budget to savings
# ─────────────────────────────────────
async def move_remaining_to_savings():
    today = date.today()
    month_start = today.replace(day=1)

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
            current_budget = result.scalar()
            if not current_budget or current_budget.remaining <= 0:
                continue

            result = await session.execute(
                select(SavingsBalance).where(SavingsBalance.user_id == user.id)
            )
            savings = result.scalar()
            if not savings:
                savings = SavingsBalance(user_id=user.id, amount=0.0)
                session.add(savings)

            savings.amount += current_budget.remaining
            current_budget.remaining = 0

        await session.commit()