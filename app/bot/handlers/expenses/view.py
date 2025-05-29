from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, desc
from datetime import datetime, timedelta
from app.db.database import async_session
from app.db.models import DailyExpense, ExpenseCategory
from collections import defaultdict

view_expenses_router = Router()

@view_expenses_router.message(F.text == "/expenses")
async def show_recent_expenses(message: Message):
    async with async_session() as session:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        result = await session.execute(
            select(DailyExpense, ExpenseCategory)
            .join(ExpenseCategory, DailyExpense.category_id == ExpenseCategory.id)
            .where(DailyExpense.user_id == message.from_user.id)
            .where(DailyExpense.created_at >= seven_days_ago)
            .order_by(desc(DailyExpense.created_at))
        )
        entries = result.all()

    if not entries:
        await message.answer("📭 No expenses found in the last 7 days.")
        return

    grouped = defaultdict(list)
    for expense, category in entries:
        date_str = expense.created_at.strftime("%Y-%m-%d")
        grouped[date_str].append((expense, category))

    for date, expenses in sorted(grouped.items(), reverse=True):
        text_lines = [f"📅 <b>{date}</b>"]
        buttons = []

        for expense, category in expenses:
            label = f"💰 {expense.amount}€ | 📂 {category.name}"
            if expense.comment:
                label += f" | 💬 {expense.comment}"
            text_lines.append(label)

            buttons.append([
                InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_expense_{expense.id}"),
                InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_expense_{expense.id}")
            ])

        await message.answer(
            "\n".join(text_lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
