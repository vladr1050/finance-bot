# app/bot/handlers/savings/edit.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from sqlalchemy import select
from states.savings_states import SetSavingsState
from services.savings_service import set_savings_balance
from db.database import async_session
from db.models import User
from utils.keyboards import success_menu

savings_edit_router = Router()

@savings_edit_router.message(Command("edit_savings"))
async def start_edit_savings(message: Message, state: FSMContext):
    await message.answer("✏️ Enter the new savings amount:")
    await state.set_state(SetSavingsState.amount)


@savings_edit_router.message(SetSavingsState.amount, F.text.regexp(r"^\d+(\.\d{1,2})?$"))
async def confirm_edit_savings(message: Message, state: FSMContext):
    amount = float(message.text)

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("❌ User not found.")
            return

        await set_savings_balance(user_uuid=user.user_uuid, amount=amount)

    await message.answer(f"✅ Savings updated to {amount:.2f}", reply_markup=success_menu())
    await state.clear()


@savings_edit_router.message(SetSavingsState.amount)
async def invalid_edit_amount(message: Message):
    await message.answer("❌ Invalid amount. Enter a number like 100 or 50.50.")
