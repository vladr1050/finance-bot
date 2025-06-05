# bot/handlers/fixed/view.py

from aiogram import Router, F
from aiogram.types import Message
from services.auth_service import get_user_by_telegram_id
from services.fixed_service import list_fixed_expenses
from utils.keyboards import fixed_expense_item_kb

view_fixed_router = Router()

@view_fixed_router.message(F.text.lower() == "💼 fixed expenses")
async def show_fixed_expenses(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("❌ You are not logged in. Please /login first.")
        return

    expenses = await list_fixed_expenses(user.uuid)

    if not expenses:
        await message.answer("📭 You don’t have any fixed expenses yet.")
        return

    for expense in expenses:
        await message.answer(
            text=f"📌 {expense.name}: {expense.amount:.2f}",
            reply_markup=fixed_expense_item_kb(expense.id)
        )
