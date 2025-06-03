# app/bot/handlers/expenses/delete.py

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, delete
from app.db.database import async_session
from app.db.models import DailyExpense
from app.states.expense_states import DeleteExpenseStates
from app.utils.keyboards import success_menu

delete_expense_router = Router()

@delete_expense_router.message(F.text == "/delete_expense")
async def start_delete_expense(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ You are not logged in. Please /login first.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(DailyExpense).where(DailyExpense.user_id == user_uuid)
        )
        expenses = result.scalars().all()

    if not expenses:
        await message.answer("❌ You have no daily expenses to delete.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.amount}€ - {e.comment or 'No comment'}", callback_data=f"delete_expense_{e.id}")]
            for e in expenses[-10:]
        ]
    )

    await message.answer("🗑 Select an expense to delete:", reply_markup=keyboard)
    await state.set_state(DeleteExpenseStates.choosing_expense)


@delete_expense_router.callback_query(F.data.startswith("delete_expense_"))
async def expense_selected(callback: CallbackQuery, state: FSMContext):
    expense_id = int(callback.data.replace("delete_expense_", ""))

    async with async_session() as session:
        await session.execute(delete(DailyExpense).where(DailyExpense.id == expense_id))
        await session.commit()

    await callback.message.answer("✅ Expense deleted successfully.", reply_markup=success_menu())
    await state.clear()
