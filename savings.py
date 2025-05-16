import logging
logger = logging.getLogger(__name__)

from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.database import async_session
from db.models import User
from keyboards import main_menu
from bot_setup import dp
from sqlalchemy import select

class SetSavings(StatesGroup):
    waiting_for_amount = State()

@dp.callback_query(F.data == "set_savings")
async def ask_savings_amount(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SetSavings.waiting_for_amount)
    await callback.message.answer("💰 How much would you like to save each month (EUR)?")
    await callback.answer()

@dp.message(SetSavings.waiting_for_amount)
async def save_savings_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Please enter a valid number.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar()
        if user:
            user.monthly_savings = amount
            await session.commit()
            logger.info(f"✅ Saved savings: {amount} for user {user.telegram_id}")
        else:
            await message.answer("⚠️ User not found in DB")

    await message.answer(f"✅ Monthly savings set to €{amount:.2f}", reply_markup=main_menu())
    await state.clear()

