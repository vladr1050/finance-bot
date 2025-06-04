# app/repositories/expense_repository.py

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from uuid import UUID

from db.models import DailyExpense


async def get_daily_expenses_by_user(session: AsyncSession, user_uuid: UUID):
    """
    Fetch daily expenses for a user, ordered by date (newest first).
    """
    stmt = select(DailyExpense).where(DailyExpense.user_id == user_uuid).order_by(DailyExpense.date.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


async def add_daily_expense(session: AsyncSession, user_uuid: UUID, amount: float, category: str, target_date: date):
    """
    Add a new daily expense record for the user.
    """
    expense = DailyExpense(user_id=user_uuid, amount=amount, category=category, date=target_date)
    session.add(expense)
    await session.commit()
    return expense


async def delete_daily_expense(session: AsyncSession, user_uuid: UUID, expense_id: int):
    """
    Delete a user's daily expense by ID.
    """
    await session.execute(
        delete(DailyExpense).where(DailyExpense.id == expense_id, DailyExpense.user_id == user_uuid)
    )
    await session.commit()


async def save_daily_expense(session: AsyncSession, user_uuid: UUID, category: str, amount: float):
    """
    Adds a new DailyExpense entry for the given user and category.
    """
    expense = DailyExpense(
        user_id=user_uuid,
        category=category,
        amount=amount,
        date=date.today()
    )
    session.add(expense)
    await session.commit()
    return expense
