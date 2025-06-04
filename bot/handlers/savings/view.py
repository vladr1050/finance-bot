# app/bot/handlers/savings/view.py

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from services.savings_service import get_savings_balance

savings_view_router = Router()

@savings_view_router.message(Command("savings"))
async def show_savings(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ You are not logged in. Please /login first.")
        return

    savings = await get_savings_balance(user_uuid=user_uuid)

    if savings:
        await message.answer(f"💰 Your current savings balance is: {savings.amount:.2f}")
    else:
        await message.answer("💼 You don't have any savings yet.")
