# app/bot/handlers/fixed/edit.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.fixed_states import EditFixedExpenseState
from services.fixed_service import list_fixed_expenses, update_fixed_expense
from utils.keyboards import success_menu

edit_fixed_router = Router()

@edit_fixed_router.message(Command("edit_fixed"))
async def start_edit_fixed(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ Internal error: user not identified.")
        return

    expenses = await list_fixed_expenses(user_id=user_uuid)

    if not expenses:
        await message.answer("📭 You have no fixed expenses.")
        return

    text = "✏️ Enter the name of the expense you want to edit:\n\n"
    text += "\n".join(f"• {e.name}" for e in expenses)
    await message.answer(text)
    await state.set_state(EditFixedExpenseState.select_expense)


@edit_fixed_router.message(EditFixedExpenseState.select_expense)
async def ask_new_name(message: Message, state: FSMContext):
    await state.update_data(original_name=message.text.strip())
    await message.answer("✏️ Enter the new name (or type the same name):")
    await state.set_state(EditFixedExpenseState.new_name)


@edit_fixed_router.message(EditFixedExpenseState.new_name)
async def ask_new_amount(message: Message, state: FSMContext):
    await state.update_data(new_name=message.text.strip())
    await message.answer("💰 Enter the new amount:")
    await state.set_state(EditFixedExpenseState.new_amount)


@edit_fixed_router.message(EditFixedExpenseState.new_amount, F.text.regexp(r"^\d+(\.\d{1,2})?$"))
async def save_edits(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ Internal error: user not identified.")
        await state.clear()
        return

    new_amount = float(message.text)

    success = await update_fixed_expense(
        user_id=user_uuid,
        original_name=data["original_name"],
        new_name=data["new_name"],
        new_amount=new_amount
    )

    if success:
        await message.answer("✅ Expense updated successfully.", reply_markup=success_menu())
    else:
        await message.answer("⚠️ Could not find that expense.")

    await state.clear()


@edit_fixed_router.message(EditFixedExpenseState.new_amount)
async def invalid_amount(message: Message):
    await message.answer("❌ Please enter a valid number (e.g., 120.00).")
