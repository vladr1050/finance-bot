# app/bot/handlers/fixed/view.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from services.fixed_service import list_fixed_expenses
from db.database import async_session

view_fixed_router = Router()

@view_fixed_router.message(Command("fixed"))
async def show_fixed_expenses(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ You are not logged in. Please /login first.")
        return

    async with async_session() as session:
        expenses = await list_fixed_expenses(user_id=user_uuid)

    if not expenses:
        await message.answer("📭 You have no fixed expenses.")
        return

    text = "📋 Your fixed expenses:\n\n"
    for e in expenses:
        text += f"• {e.name}: {e.amount:.2f}\n"

    await message.answer(text)
