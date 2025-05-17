from sqlalchemy import select
from db.database import async_session
from db.models import User, SavingsBalance
import logging

logger = logging.getLogger(__name__)

async def deduct_from_savings_if_needed(user_id: int, spent: float, remaining: float):
    """
    Если пользователь потратил больше, чем у него есть в remaining,
    разница вычитается из savings.
    """
    overspent = spent - remaining
    if overspent <= 0:
        return  # перерасхода нет

    async with async_session() as session:
        user_result = await session.execute(select(User).where(User.id == user_id))
        user = user_result.scalar()

        savings_result = await session.execute(select(SavingsBalance).where(SavingsBalance.user_id == user.id))
        savings = savings_result.scalar()

        if not savings:
            savings = SavingsBalance(user_id=user.id, amount=0.0)
            session.add(savings)

        savings.amount -= overspent
        await session.commit()

        logger.info(f"💸 Overspending of €{overspent:.2f} deducted from savings for user {user_id}")
