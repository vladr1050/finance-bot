from aiogram import F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from collections import defaultdict
from datetime import datetime, timedelta

from db.models import User, DailyExpense, ExpenseCategory
from db.database import async_session
from states import EditDailyExpense
from keyboards import main_menu

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from custom_calendar import show_start_calendar, process_calendar

def register_history_editor_handlers(dp):
    @dp.callback_query(F.data == "view_history")
    async def view_expense_history(callback: CallbackQuery):
        today = datetime.utcnow().date()
        start_date = today - timedelta(days=9)

        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == callback.from_user.id)
            )
            user = result.scalar()

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
            await callback.message.answer("📭 No daily expenses found.")
            await callback.answer()
            return

        grouped = defaultdict(list)
        for expense, category_name in rows:
            grouped[expense.created_at.date()].append((expense, category_name))

        sorted_days = sorted(grouped.keys(), reverse=True)
        messages = []

        for d in sorted_days:
            lines = [f"📅 {d.strftime('%Y-%m-%d')}"]
            total = 0
            for e, cat_name in grouped[d]:
                comment = f" ({e.comment})" if e.comment else ""
                lines.append(f"• {cat_name} — €{e.amount:.2f}{comment}")
                total += e.amount
            lines.append(f"💰 Total: €{total:.2f}")
            messages.append("\n".join(lines))

        text = "\n\n".join(messages)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Edit Expenses", callback_data="edit_history")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
        ])
        await callback.message.answer(text, reply_markup=keyboard)
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

    @dp.callback_query(F.data == "edit_range_custom")
    async def custom_range(callback: CallbackQuery, state: FSMContext):
        await show_start_calendar(callback, state)
        await callback.answer()

    @dp.callback_query(SimpleCalendarCallback.filter())
    async def process_calendar_callback(callback: CallbackQuery, callback_data: SimpleCalendarCallback,
                                        state: FSMContext):
        await process_calendar(callback, callback_data, state)
        await callback.answer()
