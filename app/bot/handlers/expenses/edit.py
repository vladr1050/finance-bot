from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update
from app.db.database import async_session
from app.db.models import DailyExpense, ExpenseCategory
from app.states.expense_states import EditExpenseStates

edit_expense_router = Router()

@edit_expense_router.message(F.text == "/edit_expense")
async def start_edit_expense(message: Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(
            select(DailyExpense).where(DailyExpense.user_id == message.from_user.id)
        )
        expenses = result.scalars().all()

    if not expenses:
        await message.answer("❌ You don't have any daily expenses yet.")
        return

    # Generate buttons for selecting an expense to edit
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{e.amount}€ - {e.comment or 'No comment'}", callback_data=f"edit_expense_{e.id}")]
            for e in expenses[-10:]  # show last 10
        ]
    )

    await message.answer("📝 Select an expense to edit:", reply_markup=keyboard)
    await state.set_state(EditExpenseStates.choosing_expense)

@edit_expense_router.callback_query(F.data.startswith("edit_expense_"))
async def expense_chosen(callback: CallbackQuery, state: FSMContext):
    expense_id = int(callback.data.replace("edit_expense_", ""))
    await state.update_data(expense_id=expense_id)
    await state.set_state(EditExpenseStates.entering_new_amount)
    await callback.message.answer("✏️ Enter the new amount for this expense:")

@edit_expense_router.message(EditExpenseStates.entering_new_amount)
async def save_edited_expense(message: Message, state: FSMContext):
    try:
        new_amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❗ Please enter a valid number.")
        return

    data = await state.get_data()
    expense_id = data.get("expense_id")

    async with async_session() as session:
        await session.execute(
            update(DailyExpense)
            .where(DailyExpense.id == expense_id)
            .values(amount=new_amount)
        )
        await session.commit()

    await message.answer("✅ Expense updated.")
    await state.clear()
