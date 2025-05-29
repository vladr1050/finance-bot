# app/bot/handlers/income/edit.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.states.income_states import IncomeEditState
from app.services.income_service import update_income_for_user, get_user_income

income_edit_router = Router()

@income_edit_router.message(F.text.lower() == "/edit_income")
async def start_edit_income(message: Message, state: FSMContext):
    current_income = await get_user_income(user_id=message.from_user.id)
    await message.answer(f"✏️ Your current income is {current_income:.2f}.\nEnter new income amount:")
    await state.set_state(IncomeEditState.waiting_for_new_amount)

@income_edit_router.message(IncomeEditState.waiting_for_new_amount)
async def process_new_income(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Please enter a valid number.")
        return

    await update_income_for_user(user_id=message.from_user.id, new_amount=amount)
    await message.answer(f"✅ Your income has been updated to {amount:.2f}.")
    await state.clear()
