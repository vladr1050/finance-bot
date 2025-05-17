from aiogram import F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from collections import defaultdict
from datetime import datetime, timedelta

from db.models import DailyExpense, ExpenseCategory
from db.database import async_session
from states import EditDailyExpense
from keyboards import main_menu


def register_history_editor_handlers(dp):
    @dp.callback_query(F.data == "view_history")
    async def view_expense_history(callback: CallbackQuery):
        today = datetime.utcnow().date()
        start_date = today - timedelta(days=9)

        async with async_session() as session:
            user_result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
            user = user_result.scalar()

            if not user:
                await callback.message.answer("❌ User not found. Use /start.")
                await callback.answer()
                return

            result = await session.execute(
                select(DailyExpense, ExpenseCategory.name)
                .join(ExpenseCategory, DailyExpense.category_id == ExpenseCategory.id)
                .where(
                    DailyExpense.user_id == user.id,
                    func.date(DailyExpense.created_at) >= start_date
                )
            )
            rows = result.all()

        if not rows:
            await callback.message.answer("📭 No daily expenses found in the last 10 days.")
            await callback.answer()
            return

        grouped = defaultdict(list)
        for expense, category_name in rows:
            grouped[expense.created_at.date()].append((expense, category_name))

        for date_key in sorted(grouped.keys(), reverse=True):
            await callback.message.answer(f"📅 {date_key.strftime('%Y-%m-%d')}")
            for e, cat_name in grouped[date_key]:
                text = f"• {cat_name} — €{e.amount:.2f}"
                if e.comment:
                    text += f" ({e.comment})"

                buttons = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_daily_{e.id}"),
                        InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_daily_{e.id}")
                    ]
                ])
                await callback.message.answer(text, reply_markup=buttons)

        await callback.answer()

    @dp.callback_query(F.data.startswith("delete_daily_"))
    async def delete_daily_expense(callback: CallbackQuery):
        expense_id = int(callback.data.split("_")[-1])
        async with async_session() as session:
            expense = await session.get(DailyExpense, expense_id)
            if expense:
                await session.delete(expense)
                await session.commit()
                await callback.message.edit_text("🗑 Deleted.")
            else:
                await callback.message.answer("Expense not found.")
        await callback.answer()

    @dp.callback_query(F.data.startswith("edit_daily_"))
    async def edit_daily_expense_start(callback: CallbackQuery, state: FSMContext):
        expense_id = int(callback.data.split("_")[-1])
        await state.update_data(editing_id=expense_id)
        await state.set_state(EditDailyExpense.choosing_field)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💶 Amount", callback_data="edit_amount")],
            [InlineKeyboardButton(text="📝 Comment", callback_data="edit_comment")]
        ])
        await callback.message.answer("What would you like to edit?", reply_markup=keyboard)
        await callback.answer()

    @dp.callback_query(F.data == "edit_amount")
    async def edit_amount_prompt(callback: CallbackQuery, state: FSMContext):
        await state.set_state(EditDailyExpense.editing_amount)
        await callback.message.answer("Enter new amount (EUR):")
        await callback.answer()

    @dp.callback_query(F.data == "edit_comment")
    async def edit_comment_prompt(callback: CallbackQuery, state: FSMContext):
        await state.set_state(EditDailyExpense.editing_comment)
        await callback.message.answer("Enter new comment (or leave blank):")
        await callback.answer()

    @dp.message(EditDailyExpense.editing_amount)
    async def update_daily_amount(message: Message, state: FSMContext):
        try:
            new_amount = float(message.text.replace(",", "."))
        except ValueError:
            await message.answer("Please enter a valid number.")
            return

        data = await state.get_data()
        async with async_session() as session:
            expense = await session.get(DailyExpense, data["editing_id"])
            if expense:
                expense.amount = new_amount
                await session.commit()

        await message.answer("✅ Amount updated.", reply_markup=main_menu())
        await state.clear()

    @dp.message(EditDailyExpense.editing_comment)
    async def update_daily_comment(message: Message, state: FSMContext):
        new_comment = message.text.strip()
        data = await state.get_data()
        async with async_session() as session:
            expense = await session.get(DailyExpense, data["editing_id"])
            if expense:
                expense.comment = new_comment
                await session.commit()

        await message.answer("✅ Comment updated.", reply_markup=main_menu())
        await state.clear()
