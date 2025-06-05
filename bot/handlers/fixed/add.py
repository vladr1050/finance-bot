# bot/handlers/fixed/add.py

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from states.fixed_states import AddFixedExpenseState
from services.fixed_service import create_fixed_expense
from utils.keyboards import success_menu
from services.auth_service import get_user_by_telegram_id

add_fixed_router = Router()

@add_fixed_router.callback_query(F.data == "add_fixed")
async def start_add_fixed(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Enter the name of the fixed expense:")
    await state.set_state(AddFixedExpenseState.name)

@add_fixed_router.message(AddFixedExpenseState.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("💵 Now enter the amount:")
    await state.set_state(AddFixedExpenseState.amount)

@add_fixed_router.message(AddFixedExpenseState.amount, F.text.regexp(r"^\d+(\.\d{1,2})?$"))
async def process_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    amount = float(message.text)

    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("❌ You are not logged in. Please /login first.")
        return

    await create_fixed_expense(user_uuid=user.uuid, name=name, amount=amount)
    await message.answer(f"✅ Added fixed expense: {name} – {amount:.2f}", reply_markup=success_menu())
    await state.clear()

@add_fixed_router.message(AddFixedExpenseState.amount)
async def invalid_amount(message: Message):
    await message.answer("❌ Please enter a valid amount (e.g., 100 or 59.99).")

