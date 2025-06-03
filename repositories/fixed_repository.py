# app/repositories/fixed_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.db.models import FixedExpense


async def add_fixed_expense(session: AsyncSession, user_uuid: UUID, name: str, amount: float):
    """
    Create a new fixed expense for the specified user.
    """
    expense = FixedExpense(user_id=user_uuid, name=name, amount=amount)
    session.add(expense)
    await session.commit()
    return expense


async def get_user_fixed_expenses(session: AsyncSession, user_uuid: UUID):
    """
    Retrieve all fixed expenses for the given user.
    """
    result = await session.execute(
        select(FixedExpense).where(FixedExpense.user_id == user_uuid)
    )
    return result.scalars().all()


async def delete_fixed_expense_by_name(session: AsyncSession, user_uuid: UUID, name: str) -> bool:
    """
    Delete a fixed expense by its name for the given user.
    """
    result = await session.execute(
        select(FixedExpense).where(FixedExpense.user_id == user_uuid, FixedExpense.name == name)
    )
    expense = result.scalar_one_or_none()

    if expense:
        await session.delete(expense)
        await session.commit()
        return True

    return False


async def update_fixed_expense_by_name(session: AsyncSession, user_uuid: UUID, original_name: str, new_name: str, new_amount: float) -> bool:
    """
    Update a user's fixed expense name and amount.
    """
    result = await session.execute(
        select(FixedExpense).where(FixedExpense.user_id == user_uuid, FixedExpense.name == original_name)
    )
    expense = result.scalar_one_or_none()

    if not expense:
        return False

    expense.name = new_name
    expense.amount = new_amount
    await session.commit()
    return True
