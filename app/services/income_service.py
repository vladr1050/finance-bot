from app.db.database import async_session
from app.db.models import Income
from datetime import datetime

async def add_income_for_user(user_id: int, amount: float):
    async with async_session() as session:
        income = Income(
            user_id=user_id,
            amount=amount,
            date=datetime.utcnow()
        )
        session.add(income)
        await session.commit()
