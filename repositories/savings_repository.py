# app/repositories/savings_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from db.models import SavingsBalance

async def get_savings(session: AsyncSession, user_uuid: UUID):
    """
    Fetch current savings balance for a user.
    """
    stmt = select(SavingsBalance).where(SavingsBalance.user_id == user_uuid)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def save_savings(session: AsyncSession, user_uuid: UUID, amount: float):
    """
    Set savings balance to a specific amount (overwrite if exists).
    """
    savings = await get_savings(session, user_uuid)

    if savings:
        savings.amount = amount
    else:
        savings = SavingsBalance(user_id=user_uuid, amount=amount)
        session.add(savings)

    await session.commit()
    return savings


async def increment_savings(session: AsyncSession, user_uuid: UUID, amount: float):
    """
    Add the given amount to current savings (create if missing).
    """
    savings = await get_savings(session, user_uuid)

    if savings:
        savings.amount += amount
    else:
        savings = SavingsBalance(user_id=user_uuid, amount=amount)
        session.add(savings)

    await session.commit()
    return savings
