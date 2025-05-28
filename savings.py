import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from app.db.database import async_session
from app.db.models import User, SavingsBalance
from keyboards import main_menu, savings_menu, cancel_keyboard
from bot_setup import dp

logger = logging.getLogger(__name__)

# ─────────────────────────────────────
# Цель накоплений на месяц
# ─────────────────────────────────────

class SetSavings(StatesGroup):
    waiting_for_amount = State()

#@dp.callback_query(F.data == "set_savings")
async def ask_savings_amount(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SetSavings.waiting_for_amount)
    await callback.message.answer("💰 How much would you like to save each month (EUR)?", reply_markup=cancel_keyboard())
    await callback.answer()

#@dp.message(SetSavings.waiting_for_amount)
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
            logger.info(f"✅ Saved savings goal: {amount} for user {user.telegram_id}")
        else:
            await message.answer("⚠️ User not found in DB")

    await message.answer(f"✅ Monthly savings goal set to €{amount:.2f}", reply_markup=main_menu())
    await state.clear()

# ─────────────────────────────────────
# Работа с балансом накоплений
# ─────────────────────────────────────

class ManualSavings(StatesGroup):
    entering_amount = State()
    mode = State()  # "add" or "withdraw"

@dp.callback_query(F.data == "view_savings")
async def view_savings(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar()
        if not user:
            await callback.message.answer("User not found.")
            return

        result = await session.execute(
            select(SavingsBalance).where(SavingsBalance.user_id == user.id)
        )
        savings = result.scalar()
        amount = savings.amount if savings else 0.0

    await callback.message.answer(
        f"💰 Your current savings: €{amount:.2f}",
        reply_markup=savings_menu()
    )
    await callback.answer()

@dp.callback_query(F.data.in_(["add_savings", "withdraw_savings"]))
async def enter_savings_amount(callback: CallbackQuery, state: FSMContext):
    mode = "add" if callback.data == "add_savings" else "withdraw"
    await state.update_data(mode=mode)
    await state.set_state(ManualSavings.entering_amount)
    await callback.message.answer(f"Enter amount to {mode} (€):")
    await callback.answer()

@dp.message(ManualSavings.entering_amount)
async def process_savings_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Enter a valid positive number.")
        return

    data = await state.get_data()
    mode = data.get("mode")

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar()
        if not user:
            await message.answer("User not found.")
            return

        result = await session.execute(
            select(SavingsBalance).where(SavingsBalance.user_id == user.id)
        )
        savings = result.scalar()
        if not savings:
            savings = SavingsBalance(user_id=user.id, amount=0.0)
            session.add(savings)

        if mode == "add":
            savings.amount += amount
        elif mode == "withdraw":
            savings.amount -= amount  # допускаем отрицательный баланс

        await session.commit()

    await message.answer(
        f"✅ Savings updated.\nNew balance: €{savings.amount:.2f}",
        reply_markup=main_menu()
    )
    await state.clear()

    from aiogram import F

