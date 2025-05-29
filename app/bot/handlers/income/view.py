# app/bot/handlers/income/view.py

from aiogram import Router, F
from aiogram.types import Message
from app.services.income_service import get_user_income

income_view_router = Router()

@income_view_router.message(F.text.lower() == "/my_income")
async def show_income(message: Message):
    income = await get_user_income(user_id=message.from_user.id)
    await message.answer(f"💸 Your current income: {income:.2f}")
