# app/bot/handlers/fixed/delete.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.states.fixed_states import DeleteFixedExpenseState
from app.services.fixed_service import list_fixed_expenses, delete_fixed_expense
from app.db.database import async_session
from app.utils.keyboards import success_menu

delete_fixed_router = Router()

@delete_fixed_router.message(Command("delete_fixed"))
async def start_delete_fixed_expense(message: Message, state: FSMContext):
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

    text = "❌ Choose the expense to delete by typing its name:\n\n"
    text += "\n".join(f"• {e.name}" for e in expenses)
    await message.answer(text)
    await state.set_state(DeleteFixedExpenseState.select_expense)


@delete_fixed_router.message(DeleteFixedExpenseState.select_expense)
async def confirm_delete_fixed_expense(message: Message, state: FSMContext):
    name = message.text.strip()
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ You are not logged in. Please /login first.")
        await state.clear()
        return

    async with async_session() as session:
        success = await delete_fixed_expense(user_id=user_uuid, name=name)

    if success:
        await message.answer(f"✅ Deleted fixed expense: {name}", reply_markup=success_menu())
    else:
        await message.answer(f"⚠️ Could not find an expense named '{name}'")

    await state.clear()
