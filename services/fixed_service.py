# app/services/fixed_service.py

from uuid import UUID
from db.database import async_session
from repositories.fixed_repository import (
    add_fixed_expense,
    get_user_fixed_expenses,
    delete_fixed_expense_by_name,
    update_fixed_expense_by_name
)


async def create_fixed_expense(user_uuid: UUID, name: str, amount: float):
    """
    Create a new fixed expense for the user.
    """
    async with async_session() as session:
        return await add_fixed_expense(session, user_uuid, name, amount)


async def list_fixed_expenses(user_uuid: UUID):
    """
    List all fixed expenses for the user.
    """
    async with async_session() as session:
        return await get_user_fixed_expenses(session, user_uuid)


async def delete_fixed_expense(user_uuid: UUID, name: str) -> bool:
    """
    Delete a fixed expense by name.
    """
    async with async_session() as session:
        return await delete_fixed_expense_by_name(session, user_uuid, name)


async def update_fixed_expense(user_uuid: UUID, original_name: str, new_name: str, new_amount: float) -> bool:
    """
    Update a fixed expense's name and amount.
    """
    async with async_session() as session:
        return await update_fixed_expense_by_name(session, user_uuid, original_name, new_name, new_amount)
