# app/services/fixed_service.py

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from db.database import async_session
from db.models import FixedExpense
from repositories.fixed_repository import (
    add_fixed_expense,
    get_user_fixed_expenses
)
async def create_fixed_expense(user_uuid: UUID, name: str, amount: float):
    async with async_session() as session:
        return await add_fixed_expense(session, user_uuid, name, amount)

async def list_fixed_expenses(user_uuid: UUID):
    async with async_session() as session:
        return await get_user_fixed_expenses(session, user_uuid)

async def get_fixed_expense_by_id(expense_id: UUID) -> Optional[FixedExpense]:
    async with async_session() as session:
        result = await session.execute(
            select(FixedExpense).where(FixedExpense.id == expense_id)
        )
        return result.scalar_one_or_none()

async def update_fixed_expense_by_id(expense_id: UUID, name: str, amount: float) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(FixedExpense).where(FixedExpense.id == expense_id)
        )
        expense = result.scalar_one_or_none()
        if expense:
            expense.name = name
            expense.amount = amount
            await session.commit()

async def delete_fixed_expense_by_id(expense_id: UUID) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(FixedExpense).where(FixedExpense.id == expense_id)
        )
        expense = result.scalar_one_or_none()
        if expense:
            await session.delete(expense)
            await session.commit()
