# app/bot/handlers/savings/view.py
from aiogram import Router, F
from aiogram.types import Message
from app.services.savings_service import get_savings_balance

view_savings_router = Router()

@view_savings_router.message(F.text.lower() == "/savings")
async def view_savings(message: Message):
    balance = await get_savings_balance(message.from_user.id)
    await message.answer(f"💰 Your current savings: {balance:.2f}")