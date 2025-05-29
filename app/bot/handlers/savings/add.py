# app/bot/handlers/savings/add.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.states.savings_states import AddSavingsState
from app.services.savings_service import add_savings

add_savings_router = Router()

@add_savings_router.message(F.text.lower() == "/add_savings")
async def start_add_savings(message: Message, state: FSMContext):
    await message.answer("💾 Enter amount to add to savings:")
    await state.set_state(AddSavingsState.waiting_for_amount)

@add_savings_router.message(AddSavingsState.waiting_for_amount)
async def process_add_savings(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Please enter a valid positive number.")
        return

    await add_savings(message.from_user.id, amount)
    await message.answer(f"✅ Added {amount:.2f} to savings.")
    await state.clear()