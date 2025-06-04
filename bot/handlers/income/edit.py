# app/bot/handlers/income/edit.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from states.income_states import IncomeEditState
from services.income_service import update_income_for_user, get_user_income
from utils.keyboards import success_menu

income_edit_router = Router()

@income_edit_router.message(F.text.lower() == "/edit_income")
async def start_edit_income(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ Internal error: user not authenticated.")
        return

    current_income = await get_user_income(user_uuid=user_uuid)
    if current_income is not None:
        await message.answer(f"✏️ Your current income is {current_income:.2f}.\nEnter new income amount:")
    else:
        await message.answer("ℹ️ You don't have any income set yet.\nEnter your income amount:")

    await state.set_state(IncomeEditState.waiting_for_new_amount)


@income_edit_router.message(IncomeEditState.waiting_for_new_amount)
async def process_new_income(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Please enter a valid number.")
        return

    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ Internal error: user not found.")
        return

    await update_income_for_user(user_uuid=user_uuid, new_amount=amount)
    await message.answer(f"✅ Your income has been updated to {amount:.2f}.", reply_markup=success_menu())
    await state.clear()
