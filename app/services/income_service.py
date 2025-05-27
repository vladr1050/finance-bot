from app.db.database import async_session
from app.db.models import User
from sqlalchemy import select

async def add_income_for_user(user_id: int, amount: float):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            # Если пользователь ещё не создан, можно создать (опционально)
            user = User(telegram_id=user_id, monthly_income=amount)
            session.add(user)
        else:
            user.monthly_income = amount

        await session.commit()
