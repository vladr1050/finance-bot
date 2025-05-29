# app/bot/handlers/savings/edit.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.states.savings_states import EditSavingsState
from app.services.savings_service import update_savings, get_savings_balance

edit_savings_router = Router()

@edit_savings_router.message(F.text.lower() == "/edit_savings")
async def start_edit_savings(message: Message, state: FSMContext):
    current_balance = await get_savings_balance(message.from_user.id)
    await message.answer(f"💰 Your current savings: {current_balance:.2f}\n\nEnter the new savings amount:")
    await state.set_state(EditSavingsState.waiting_for_new_amount)

@edit_savings_router.message(EditSavingsState.waiting_for_new_amount)
async def process_new_savings(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Please enter a valid positive number.")
        return

    await update_savings(message.from_user.id, amount)
    await message.answer(f"✅ Savings updated to {amount:.2f}")
    await state.clear()