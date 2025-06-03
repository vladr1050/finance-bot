# app/bot/handlers/income/view.py

from aiogram import Router, F
from aiogram.types import Message
from app.services.income_service import get_user_income
from app.db.database import async_session
from app.db.models import User
from sqlalchemy import select

income_view_router = Router()

@income_view_router.message(F.text.lower() == "/view_income")
async def view_income(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ User not found.")
            return

        income = await get_user_income(user_uuid=user.user_uuid)

    if income is not None:
        await message.answer(f"💸 Your current income: {income:.2f}")
    else:
        await message.answer("ℹ️ You haven't set your income yet.")
