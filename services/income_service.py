# app/services/income_service.py

from uuid import UUID
from app.db.database import async_session
from app.db.models import User
from sqlalchemy import select


async def add_income_for_user(user_uuid: UUID, amount: float) -> bool:
    """
    Adds or updates the user's monthly income.
    Returns True if the user exists and was updated successfully.
    """
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_uuid == user_uuid))
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.monthly_income = amount
        await session.commit()
        return True


async def update_income_for_user(user_uuid: UUID, new_income: float) -> bool:
    """
    Updates the user's monthly income.
    Returns True if the user exists and update succeeds.
    """
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_uuid == user_uuid))
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.monthly_income = new_income
        await session.commit()
        return True


async def get_user_income(user_uuid: UUID) -> float:
    """
    Retrieves the user's current monthly income. Returns 0.0 if the user is not found.
    """
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_uuid == user_uuid))
        user = result.scalar_one_or_none()
        return user.monthly_income if user else 0.0
