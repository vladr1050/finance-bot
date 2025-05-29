# app/bot/handlers/savings/set.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.states.savings_states import SetSavingsState
from app.services.savings_service import set_savings

set_savings_router = Router()

@set_savings_router.message(F.text.lower() == "/set_savings")
async def start_set_savings(message: Message, state: FSMContext):
    await message.answer("🔧 Enter your total savings amount:")
    await state.set_state(SetSavingsState.waiting_for_amount)

@set_savings_router.message(SetSavingsState.waiting_for_amount)
async def process_set_savings(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Please enter a valid positive number.")
        return

    await set_savings(message.from_user.id, amount)
    await message.answer(f"✅ Savings set to {amount:.2f}.")
    await state.clear()