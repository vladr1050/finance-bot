# app/bot/handlers/history/delete.py

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from app.db.database import async_session
from sqlalchemy import select
from app.db.models import DailyExpense

router = Router()

@router.callback_query(F.data.startswith("del_exp_"))
async def delete_expense(callback: CallbackQuery, state: FSMContext):
    expense_id = int(callback.data.replace("del_exp_", ""))

    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await callback.message.edit_text("❌ User not authenticated.")
        await callback.answer()
        return

    async with async_session() as session:
        result = await session.execute(
            select(DailyExpense).where(
                DailyExpense.id == expense_id,
                DailyExpense.user_uuid == user_uuid
            )
        )
        expense = result.scalar_one_or_none()

        if not expense:
            await callback.message.edit_text("❌ Expense not found or already deleted.")
            await callback.answer()
            return

        await session.delete(expense)
        await session.commit()

    await callback.message.edit_text("🗑 Expense deleted successfully.")
    await callback.answer()
