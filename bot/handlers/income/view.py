# app/bot/handlers/income/view.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from services.income_service import get_user_income

income_view_router = Router()

# Shared function to display income
async def view_income_by_uuid(user_uuid: str, answer_func):
    income = await get_user_income(user_uuid=user_uuid)

    if income is not None:
        await answer_func(f"💸 Your current income: {income:.2f}")
    else:
        await answer_func("ℹ️ You haven't set your income yet.")

# Handler for the /view_income command
@income_view_router.message(F.text.lower() == "/view_income")
async def handle_view_income_command(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ You are not logged in. Please /login first.")
        return

    await view_income_by_uuid(user_uuid, message.answer)

# Handler for the view_income button
@income_view_router.callback_query(F.data == "view_income")
async def handle_view_income_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await callback.message.answer("❌ You are not logged in. Please /login first.")
        await callback.answer()
        return

    await view_income_by_uuid(user_uuid, callback.message.answer)
    await callback.answer()
