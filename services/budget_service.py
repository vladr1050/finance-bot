# app/services/budget_service.py

from uuid import UUID
from datetime import datetime, date, timedelta
from sqlalchemy import select, func
from db.database import async_session
from repositories.monthly_budget_adjustment import get_adjustments
from db.models import User, FixedExpense, DailyExpense, MonthlyBudget, MonthlyBudgetAdjustment


async def recalculate_budget(
    user_uuid: UUID,
    base_income: float,
    base_fixed: float,
    base_savings: float,
    month: datetime
):
    """
    Apply temporary budget adjustments for the given user and return recalculated values.
    """
    async with async_session() as session:
        adjustments = await get_adjustments(session, user_uuid, month)

        income_adj = 0.0
        fixed_adj = 0.0
        savings_adj = 0.0

        for adj in adjustments:
            sign = 1 if adj.type == "add" else -1
            if adj.source == "income":
                income_adj += sign * adj.amount
            elif adj.source == "fixed_expense":
                fixed_adj += sign * adj.amount
            elif adj.source == "savings":
                savings_adj += sign * adj.amount

        adjusted_income = base_income + income_adj
        adjusted_fixed = base_fixed + fixed_adj
        adjusted_savings = base_savings + savings_adj

        remaining = adjusted_income - adjusted_fixed - adjusted_savings

        return {
            "income": adjusted_income,
            "fixed": adjusted_fixed,
            "savings": adjusted_savings,
            "remaining": remaining
        }


async def apply_adjustments_for_current_month(user_uuid: UUID) -> bool:
    """
    Apply permanent adjustments to the current month's budget if MonthlyBudget exists.
    """
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_uuid == user_uuid))
        user = result.scalar()
        if not user:
            return False

        today = date.today()
        month_start = today.replace(day=1)
        month_end = (month_start.replace(month=month_start.month % 12 + 1, day=1) - timedelta(days=1))
        total_days = month_end.day

        income = user.monthly_income or 0
        savings_goal = user.monthly_savings or 0

        result = await session.execute(
            select(func.sum(FixedExpense.amount)).where(FixedExpense.user_id == user_uuid)
        )
        fixed_total = result.scalar() or 0

        result = await session.execute(
            select(func.min(DailyExpense.created_at)).where(
                DailyExpense.user_id == user_uuid,
                func.date(DailyExpense.created_at) >= month_start
            )
        )
        first_expense_date = result.scalar()
        from_date = first_expense_date.date() if first_expense_date else today

        days_left = (month_end - from_date).days + 1
        coefficient = days_left / total_days if total_days else 1.0

        result = await session.execute(
            select(MonthlyBudgetAdjustment).where(
                MonthlyBudgetAdjustment.user_id == user_uuid,
                MonthlyBudgetAdjustment.month == month_start,
                MonthlyBudgetAdjustment.processed == True
            )
        )
        adjustments = result.scalars().all()
        for adj in adjustments:
            delta = adj.amount if adj.type == 'add' else -adj.amount
            if adj.source == "income":
                income += delta
            elif adj.source == "fixed_expense":
                fixed_total += delta
            elif adj.source == "savings":
                savings_goal += delta

        full_remaining = income - fixed_total - savings_goal
        remaining = full_remaining * coefficient

        result = await session.execute(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == user_uuid,
                MonthlyBudget.month_start == month_start
            )
        )
        budget = result.scalar()
        if budget:
            budget.income = income
            budget.fixed = fixed_total
            budget.savings_goal = savings_goal
            budget.remaining = remaining
            budget.coefficient = coefficient
            await session.commit()
            return True

        return False
