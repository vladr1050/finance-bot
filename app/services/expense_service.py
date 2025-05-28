# app/services/expense_service.py

from datetime import datetime
from app.db.models import DailyExpense
from app.db.database import async_session

async def save_expense(user_id: int, category_id: int, amount: float):
    async with async_session() as session:
        expense = DailyExpense(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            created_at=datetime.utcnow()
        )
        session.add(expense)
        await session.commit()
