# app/bot/handlers/savings/add.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from states.savings_states import AddSavingsState
from services.savings_service import add_to_savings
from utils.keyboards import success_menu

savings_add_router = Router()

@savings_add_router.message(Command("add_savings"))
async def cmd_add_savings(message: Message, state: FSMContext):
    await message.answer("➕ Enter the amount to add to savings:")
    await state.set_state(AddSavingsState.amount)

@savings_add_router.message(AddSavingsState.amount, F.text.regexp(r"^\d+(\.\d{1,2})?$"))
async def process_add_savings(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ Internal error: user not identified.")
        await state.clear()
        return

    amount = float(message.text)
    await add_to_savings(user_uuid=user_uuid, amount=amount)

    await message.answer(f"✅ Added {amount:.2f} to savings.", reply_markup=success_menu())
    await state.clear()

@savings_add_router.message(AddSavingsState.amount)
async def process_invalid_amount(message: Message):
    await message.answer("❌ Please enter a valid number (e.g., 100 or 99.99).")
