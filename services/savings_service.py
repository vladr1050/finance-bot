# app/services/savings_service.py

from uuid import UUID
from db.database import async_session
from repositories.savings_repository import (
    get_savings,
    save_savings,
    increment_savings
)


async def get_savings_balance(user_uuid: UUID):
    """
    Retrieve the user's current savings balance.
    """
    async with async_session() as session:
        return await get_savings(session, user_uuid)


async def set_savings_balance(user_uuid: UUID, amount: float):
    """
    Set the user's savings balance to a specific amount.
    """
    async with async_session() as session:
        return await save_savings(session, user_uuid, amount)


async def add_to_savings(user_uuid: UUID, amount: float):
    """
    Increment the user's savings balance by a specified amount.
    """
    async with async_session() as session:
        return await increment_savings(session, user_uuid, amount)
