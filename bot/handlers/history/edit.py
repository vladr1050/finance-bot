# app/bot/handlers/history/edit.py

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from app.states.history_states import EditExpenseFSM
from app.db.database import async_session
from app.db.models import DailyExpense, User
from app.utils.keyboards import success_menu

router = Router()

@router.callback_query(F.data.startswith("edit_exp_"))
async def start_edit(callback: CallbackQuery, state: FSMContext):
    expense_id = int(callback.data.replace("edit_exp_", ""))
    await state.update_data(expense_id=expense_id)

    await callback.message.answer("✏️ Enter new category:")
    await state.set_state(EditExpenseFSM.editing_category)
    await callback.answer()


@router.message(EditExpenseFSM.editing_category)
async def receive_new_category(message: Message, state: FSMContext):
    await state.update_data(new_category=message.text.strip())
    await message.answer("💵 Enter new amount:")
    await state.set_state(EditExpenseFSM.editing_amount)


@router.message(EditExpenseFSM.editing_amount, F.text.regexp(r"^\d+(\.\d{1,2})?$"))
async def apply_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    new_amount = float(message.text.strip())
    expense_id = data["expense_id"]

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ User not found.")
            await state.clear()
            return

        result = await session.execute(
            select(DailyExpense).where(
                DailyExpense.id == expense_id,
                DailyExpense.user_uuid == user.user_uuid
            )
        )
        expense = result.scalar_one_or_none()

        if not expense:
            await message.answer("❌ Expense not found.")
            await state.clear()
            return

        expense.category = data["new_category"]
        expense.amount = new_amount
        await session.commit()

    await message.answer("✅ Expense updated.", reply_markup=success_menu())
    await state.clear()


@router.message(EditExpenseFSM.editing_amount)
async def invalid_amount(message: Message):
    await message.answer("❌ Enter a valid number (e.g., 10.50)")
