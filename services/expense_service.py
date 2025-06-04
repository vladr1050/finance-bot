from datetime import date
from uuid import UUID

from db.database import async_session
from repositories.expense_repository import (
    get_daily_expenses_by_user,
    add_daily_expense,
    delete_daily_expense,
    save_daily_expense
)


async def list_user_expenses(user_uuid: UUID):
    """
    Retrieve all daily expenses for the given user.
    """
    async with async_session() as session:
        return await get_daily_expenses_by_user(session, user_uuid)


async def create_expense(user_uuid: UUID, amount: float, category: str, expense_date: date):
    """
    Create a new expense record.
    """
    async with async_session() as session:
        return await add_daily_expense(session, user_uuid, amount, category, expense_date)


async def remove_expense(user_uuid: UUID, expense_id: int):
    """
    Delete a specific expense by ID for the given user.
    """
    async with async_session() as session:
        return await delete_daily_expense(session, user_uuid, expense_id)


async def save_expense(user_uuid: UUID, category: str, amount: float):
    """
    Save an expense with the current date.
    """
    async with async_session() as session:
        return await save_daily_expense(session, user_uuid, category, amount)
