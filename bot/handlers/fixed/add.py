# app/bot/handlers/fixed/add.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from app.states.fixed_states import AddFixedExpenseState
from app.services.fixed_service import create_fixed_expense
from app.db.database import async_session
from app.utils.keyboards import success_menu

add_fixed_router = Router()

@add_fixed_router.message(Command("add_fixed"))
async def cmd_add_fixed_expense(message: Message, state: FSMContext):
    await message.answer("📝 Enter the name of the fixed expense:")
    await state.set_state(AddFixedExpenseState.name)


@add_fixed_router.message(AddFixedExpenseState.name)
async def process_fixed_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("💵 Now enter the amount:")
    await state.set_state(AddFixedExpenseState.amount)


@add_fixed_router.message(AddFixedExpenseState.amount, F.text.regexp(r"^\d+(\.\d{1,2})?$"))
async def process_fixed_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    amount = float(message.text)

    user_data = await state.get_data()
    user_uuid = user_data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ You are not logged in. Please /login first.")
        return

    await create_fixed_expense(
        user_id=user_uuid,
        name=name,
        amount=amount
    )

    await message.answer(f"✅ Added fixed expense: {name} – {amount:.2f}", reply_markup=success_menu())
    await state.clear()


@add_fixed_router.message(AddFixedExpenseState.amount)
async def invalid_amount(message: Message):
    await message.answer("❌ Please enter a valid amount (e.g., 100 or 59.99).")
