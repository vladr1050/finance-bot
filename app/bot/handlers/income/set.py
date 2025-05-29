# app/bot/handlers/income/set.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.states.income_states import IncomeSetState
from app.services.income_service import set_income_for_user

income_set_router = Router()

@income_set_router.message(F.text.lower() == "/set_income")
async def set_income_start(message: Message, state: FSMContext):
    await message.answer("📥 Enter your income:")
    await state.set_state(IncomeSetState.waiting_for_income)

@income_set_router.message(IncomeSetState.waiting_for_income)
async def set_income_value(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Invalid number. Try again.")
        return

    await set_income_for_user(user_id=message.from_user.id, amount=amount)
    await message.answer(f"✅ Income set to {amount:.2f}.")
    await state.clear()
