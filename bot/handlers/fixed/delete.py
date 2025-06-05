# bot/handlers/fixed/delete.py

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from services.auth_service import get_user_by_telegram_id
from services.fixed_service import delete_fixed_expense_by_id, get_fixed_expense_by_id
from utils.keyboards import confirm_delete_kb, success_menu

delete_fixed_router = Router()

@delete_fixed_router.callback_query(F.data.startswith("delete_fixed:"))
async def ask_delete_confirmation(callback: CallbackQuery, state: FSMContext):
    fixed_id = callback.data.split(":")[1]
    await state.update_data(fixed_id=fixed_id)
    await callback.message.edit_text("❗ Are you sure you want to delete this fixed expense?", reply_markup=confirm_delete_kb())

@delete_fixed_router.callback_query(F.data == "confirm_delete")
async def confirm_delete(callback: CallbackQuery, state: FSMContext):
    user = await get_user_by_telegram_id(callback.from_user.id)
    data = await state.get_data()
    fixed_id = data.get("fixed_id")

    expense = await get_fixed_expense_by_id(fixed_id)
    if not expense or expense.user_id != user.uuid:
        await callback.message.edit_text("❌ Expense not found or permission denied.")
        return

    await delete_fixed_expense_by_id(fixed_id)
    await callback.message.edit_text("✅ Expense deleted successfully.", reply_markup=success_menu())
    await state.clear()

@delete_fixed_router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❎ Deletion cancelled.", reply_markup=success_menu())
    await state.clear()
