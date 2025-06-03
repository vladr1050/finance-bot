# app/bot/handlers/income/add.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from app.utils.keyboards import success_menu

from app.states.income_states import IncomeState
from app.services.income_service import add_income_for_user

income_add_router = Router()

@income_add_router.message(Command("add_income"))
async def start_add_income_cmd(message: Message, state: FSMContext):
    await message.answer("💰 Enter income amount:")
    await state.set_state(IncomeState.waiting_for_amount)


@income_add_router.callback_query(F.data == "add_income")
async def start_add_income_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("💰 Enter income amount:")
    await state.set_state(IncomeState.waiting_for_amount)
    await callback.answer()


@income_add_router.message(IncomeState.waiting_for_amount)
async def process_income_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Please enter a valid number.")
        return

    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ You are not logged in. Use /start to log in.")
        return

    await add_income_for_user(user_uuid=user_uuid, amount=amount)

    await message.answer(f"✅ Income of {amount:.2f} saved.", reply_markup=success_menu())
    await state.clear()
