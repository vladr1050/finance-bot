# app/bot/handlers/add.py

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from states.expense_states import AddExpenseStates
from services.expense_service import save_expense
from db.database import async_session
from db.models import ExpenseCategory
from utils.keyboards import success_menu

expense_router = Router()

@expense_router.message(F.text == "/add_expense")
async def cmd_add_expense(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user_uuid = user_data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ User not authenticated. Please /login first.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(ExpenseCategory).where(ExpenseCategory.user_id == user_uuid)
        )
        categories = result.scalars().all()

    if not categories:
        await message.answer("❌ You don't have any categories yet.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}")]
            for cat in categories
        ]
    )

    await state.set_state(AddExpenseStates.choosing_category)
    await message.answer("🧾 Choose a category:", reply_markup=keyboard)


@expense_router.callback_query(F.data.startswith("cat_"))
async def category_chosen(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.replace("cat_", ""))
    await state.update_data(category_id=category_id)
    await state.set_state(AddExpenseStates.entering_amount)
    await callback.message.answer("💰 Enter the amount spent:")
    await callback.answer()


@expense_router.message(AddExpenseStates.entering_amount)
async def amount_entered(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❗ Please enter a valid number.")
        return

    data = await state.get_data()
    category_id = data.get("category_id")
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ User not authenticated. Please /login first.")
        return

    await save_expense(user_id=user_uuid, category_id=category_id, amount=amount)

    await message.answer("✅ Expense saved.", reply_markup=success_menu())
    await state.clear()
