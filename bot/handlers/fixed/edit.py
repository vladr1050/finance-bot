from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from states.fixed_states import EditFixedExpenseState
from services.fixed_service import update_fixed_expense_by_id, get_fixed_expense_by_id
from services.auth_service import get_user_by_telegram_id
from utils.keyboards import success_menu

edit_fixed_router = Router()

@edit_fixed_router.callback_query(F.data.startswith("edit_fixed:"))
async def start_edit_fixed(callback: CallbackQuery, state: FSMContext):
    fixed_id = callback.data.split(":")[1]
    await state.update_data(fixed_id=fixed_id)
    await callback.message.edit_text("✏️ Enter new name for the fixed expense:")
    await state.set_state(EditFixedExpenseState.new_name)

@edit_fixed_router.message(EditFixedExpenseState.new_name)
async def process_new_name(message: Message, state: FSMContext):
    await state.update_data(new_name=message.text)
    await message.answer("💵 Enter new amount:")
    await state.set_state(EditFixedExpenseState.new_amount)

@edit_fixed_router.message(EditFixedExpenseState.new_amount, F.text.regexp(r"^\d+(\.\d{1,2})?$"))
async def process_new_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    fixed_id = data.get("fixed_id")
    new_name = data.get("new_name")
    new_amount = float(message.text)

    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("❌ You are not logged in. Please /login first.")
        return

    expense = await get_fixed_expense_by_id(fixed_id)
    if not expense or expense.user_id != user.uuid:
        await message.answer("❌ Expense not found or permission denied.")
        return

    await update_fixed_expense_by_id(fixed_id, new_name, new_amount)
    await message.answer(f"✅ Fixed expense updated: {new_name} – {new_amount:.2f}", reply_markup=success_menu())
    await state.clear()

@edit_fixed_router.message(EditFixedExpenseState.new_amount)
async def invalid_amount(message: Message):
    await message.answer("❌ Please enter a valid amount (e.g., 100 or 59.99).")
