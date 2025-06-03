# app/repositories/monthly_budget_adjustment.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from app.db.models import MonthlyBudgetAdjustment


async def add_adjustment(
    session: AsyncSession,
    user_uuid: UUID,
    month: datetime,
    source: str,
    adjustment_type: str,
    amount: float,
    comment: str = None,
    apply_permanently: bool = False
):
    """
    Create a new monthly budget adjustment entry for the user.
    """
    adj = MonthlyBudgetAdjustment(
        user_id=user_uuid,
        month=month,
        source=source,
        type=adjustment_type,
        amount=amount,
        comment=comment,
        apply_permanently=apply_permanently,
        processed=False
    )
    session.add(adj)
    await session.commit()
    return adj


async def get_adjustments(session: AsyncSession, user_uuid: UUID, month: datetime):
    """
    Retrieve all adjustments for the given user and month.
    """
    result = await session.execute(
        select(MonthlyBudgetAdjustment).where(
            MonthlyBudgetAdjustment.user_id == user_uuid,
            MonthlyBudgetAdjustment.month == month
        )
    )
    return result.scalars().all()
