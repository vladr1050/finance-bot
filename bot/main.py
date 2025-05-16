import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from db.database import init_db, async_session
from db.models import User, FixedExpense, DailyExpense, ExpenseCategory
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime
from states import Register, AddFixedExpense, EditExpense, EditIncome, AddDailyExpense, AddCategory
from keyboards import main_menu, settings_menu, after_expense_menu, skip_keyboard, cancel_keyboard, skip_cancel_keyboard, back_keyboard
from bot_setup import bot, dp
from savings import *
from admin import *
from history_editor import register_history_editor_handlers
from category_grouping import register_category_group_handlers
register_category_group_handlers(dp)
register_history_editor_handlers(dp)

# ----- START -----

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if not message.from_user:
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        existing_user = result.scalar()

    if existing_user:
        await message.answer("👋 Welcome back!", reply_markup=main_menu())
    else:
        await state.set_state(Register.waiting_for_name)
        await message.answer("👋 Hello! What is your name?")

@dp.message(Register.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.waiting_for_income)
    await message.answer("What is your monthly income (EUR)?")

from db.models import User, ExpenseCategory
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from db.database import async_session
from states import Register
from keyboards import main_menu

@dp.message(Register.waiting_for_income)
async def get_income(message: Message, state: FSMContext):
    try:
        income = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Please enter a valid number.")
        return

    data = await state.get_data()
    async with async_session() as session:
        user = User(
            telegram_id=message.from_user.id,
            name=data["name"],
            monthly_income=income
        )
        session.add(user)
        await session.commit()

        # ➕ Добавление дефолтных категорий
        default_categories = [
            # 🏠 Housing
            "Rent / Mortgage", "Utilities", "Home maintenance",
            # 🍽 Food & Drinks
            "Groceries", "Restaurants", "Coffee / Snacks",
            # 🚗 Transport
            "Fuel", "Public Transport", "Car Maintenance", "Parking / Taxi",
            # 🛍 Shopping
            "Clothing", "Household Goods", "Electronics",
            # 🧘‍♂️ Health & Fitness
            "Medical", "Pharmacy", "Gym / Fitness",
            # 🎉 Entertainment
            "Cinema / Theater", "Subscriptions / Streaming", "Travel",
            # 👨‍👩‍👧‍👦 Family & Kids
            "Education", "Kids supplies", "Gifts & Holidays",
            # 💼 Finance & Obligations
            "Loans / Debts", "Insurance", "Taxes",
            # 🐾 Other
            "Charity", "Pets", "Miscellaneous"
        ]

        for name in default_categories:
            category = ExpenseCategory(user_id=user.telegram_id, name=name)
            session.add(category)

        await session.commit()

    await message.answer("✅ Saved!", reply_markup=main_menu())
    await state.clear()

# ----- FIXED EXPENSES -----

@dp.callback_query(F.data == "edit_expense")
async def cb_edit_expense(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(FixedExpense).where(FixedExpense.user_id == callback.from_user.id)
        )
        expenses = result.scalars().all()

    if not expenses:
        await callback.message.answer("You have no fixed expenses yet.")
        await callback.message.answer("🔙 Back to Settings", reply_markup=back_keyboard("settings"))
        await callback.answer()
        return

    # Отправляем все фиксированные расходы
    for e in expenses:
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_fixed_{e.id}"),
                InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_fixed_{e.id}")
            ]
        ])
        await callback.message.answer(f"{e.name}: €{e.amount}", reply_markup=buttons)

    # Добавляем кнопку Back ОДИН РАЗ в конце
    await callback.message.answer("🔙 Back to Settings", reply_markup=back_keyboard("settings"))
    await callback.answer()


@dp.callback_query(F.data.startswith("delete_fixed_"))
async def delete_fixed(callback: CallbackQuery):
    expense_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        expense = await session.get(FixedExpense, expense_id)
        if expense:
            await session.delete(expense)
            await session.commit()
            await callback.message.answer("🗑 Expense deleted.", reply_markup=main_menu())
        else:
            await callback.message.answer("Expense not found.")
    await callback.answer()

@dp.callback_query(F.data.startswith("edit_fixed_"))
async def edit_fixed_start(callback: CallbackQuery, state: FSMContext):
    expense_id = int(callback.data.split("_")[-1])
    await state.update_data(editing_id=expense_id)
    await state.set_state(EditExpense.waiting_for_field_choice)
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Name", callback_data="edit_field_name"),
         InlineKeyboardButton(text="💶 Amount", callback_data="edit_field_amount")]
    ])
    await callback.message.answer("What would you like to edit?", reply_markup=buttons)
    await callback.answer()

@dp.callback_query(F.data.startswith("edit_field_"))
async def edit_field_prompt(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split("_")[-1]
    await state.update_data(field_to_edit=field)
    await state.set_state(EditExpense.waiting_for_new_value)
    await callback.message.answer(f"Enter new {field}:")
    await callback.answer()

@dp.message(EditExpense.waiting_for_new_value)
async def apply_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    expense_id = data.get("editing_id")
    field = data.get("field_to_edit")
    async with async_session() as session:
        expense = await session.get(FixedExpense, expense_id)
        if not expense:
            await message.answer("Expense not found.")
            return
        if field == "name":
            expense.name = message.text
        elif field == "amount":
            try:
                expense.amount = float(message.text)
            except ValueError:
                await message.answer("Amount must be a number.")
                return
        await session.commit()
    await message.answer("✅ Updated.", reply_markup=main_menu())
    await state.clear()

@dp.callback_query(F.data == "add_expense")
async def cb_add_expense(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddFixedExpense.waiting_for_name)
    await callback.message.answer("Enter the name of your fixed expense:", reply_markup=cancel_keyboard())
    await callback.answer()

@dp.message(AddFixedExpense.waiting_for_name)
async def get_fixed_name(message: Message, state: FSMContext):
    await state.update_data(fixed_name=message.text)
    await state.set_state(AddFixedExpense.waiting_for_amount)
    await message.answer("Enter the amount (EUR):")

@dp.message(AddFixedExpense.waiting_for_amount)
async def get_fixed_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("Amount must be a number.")
        return
    data = await state.get_data()
    async with async_session() as session:
        fixed = FixedExpense(
            user_id=message.from_user.id,
            name=data["fixed_name"],
            amount=amount
        )
        session.add(fixed)
        await session.commit()
    await message.answer("✅ Fixed expense saved!", reply_markup=main_menu())
    await state.clear()

# ----- REPORT -----

@dp.callback_query(F.data == "report")
async def cb_report(callback: CallbackQuery):
    from datetime import date
    from calendar import monthrange

    today = date.today()
    first_day = today.replace(day=1)
    total_days = monthrange(today.year, today.month)[1]
    days_left = total_days - today.day + 1

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar()
        if not user:
            await callback.message.answer("Please use /start first.")
            return

        result = await session.execute(
            select(func.sum(FixedExpense.amount)).where(FixedExpense.user_id == user.telegram_id)
        )
        total_expenses = result.scalar() or 0

        result = await session.execute(
            select(func.sum(DailyExpense.amount)).where(
                DailyExpense.user_id == user.telegram_id,
                func.date(DailyExpense.created_at) >= first_day
            )
        )
        daily_total = result.scalar() or 0

        monthly_savings = user.monthly_savings or 0
        planned_left = user.monthly_income - total_expenses - monthly_savings
        real_left = planned_left - daily_total
        daily_budget = real_left / days_left if days_left > 0 else 0

    await callback.message.answer(
        f"💼 Income: €{user.monthly_income:.2f}\n"
        f"📉 Fixed: €{total_expenses:.2f}\n"
        f"🪙 Savings: €{monthly_savings:.2f}\n"
        f"🍽 Spent (this month): €{daily_total:.2f}\n"
        f"✅ Left: €{real_left:.2f}\n"
        f"📆 Days left: {days_left}\n"
        f"💸 Daily budget: €{daily_budget:.2f}",
        reply_markup=main_menu()
    )
    await callback.answer()

# ----- DAILY EXPENSE ENTRY -----

# ✅ VIEW HISTORY (corrected)
@dp.callback_query(F.data == "view_history")
async def view_expense_history(callback: CallbackQuery):
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=9)

    async with async_session() as session:
        result = await session.execute(
            select(DailyExpense, ExpenseCategory.name)
            .join(ExpenseCategory, DailyExpense.category_id == ExpenseCategory.id)
            .where(
                DailyExpense.user_id == callback.from_user.id,
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

    sorted_days = sorted(grouped.keys(), reverse=True)
    messages = []
    for d in sorted_days:
        lines = [f"📅 {d.strftime('%Y-%m-%d')}"]
        total = 0
        for e, cat_name in grouped[d]:
            total += e.amount
            comment = f" ({e.comment})" if e.comment else ""
            lines.append(f"• {cat_name} — €{e.amount:.2f}{comment}")
        lines.append(f"Total: €{total:.2f}")
        messages.append("\n".join(lines))

    await callback.message.answer("\n\n".join(messages), reply_markup=main_menu())
    await callback.answer()

@dp.callback_query(F.data == "clear_daily_expenses")
async def clear_user_daily_expenses(callback: CallbackQuery):
    async with async_session() as session:
        await session.execute(
            DailyExpense.__table__.delete().where(DailyExpense.user_id == callback.from_user.id)
        )
        await session.commit()
    await callback.message.answer("🧹 All your daily expenses have been cleared.", reply_markup=main_menu())
    await callback.answer()


@dp.callback_query(F.data.startswith("cat_"))
async def choose_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        category = await session.get(ExpenseCategory, category_id)
    if not category:
        await callback.message.answer("Category not found.")
        await callback.answer()
        return
    await state.update_data(category_id=category_id, category_name=category.name)
    await state.set_state(AddDailyExpense.entering_amount)
    await callback.message.answer(f"Enter amount for {category.name} (in EUR):")
    await callback.answer()

@dp.message(AddDailyExpense.entering_amount)
async def enter_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer("Please enter a valid number.", reply_markup=cancel_keyboard())
        return
    await state.update_data(amount=amount)
    await state.set_state(AddDailyExpense.entering_comment)
    await message.answer("📝 Add a comment or skip:", reply_markup=skip_keyboard())

# ✅ SAVE DAILY EXPENSE (corrected version)
async def save_daily_expense(user_id: int, category_id: int, amount: float, comment: str = ""):
    async with async_session() as session:
        daily = DailyExpense(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            comment=comment,
            created_at=datetime.utcnow()
        )
        session.add(daily)
        await session.commit()

# ✅ ENTER COMMENT (corrected)
@dp.message(AddDailyExpense.entering_comment)
async def enter_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    data = await state.get_data()
    category_id = data["category_id"]
    amount = data["amount"]

    async with async_session() as session:
        category = await session.get(ExpenseCategory, category_id)
        category_name = category.name if category else "Unknown"

        daily = DailyExpense(
            user_id=message.from_user.id,
            category_id=category_id,
            amount=amount,
            comment=comment,
            created_at=datetime.utcnow()
        )
        session.add(daily)
        await session.commit()

    comment_str = f" ({comment})" if comment else ""
    await message.answer(
        f"✅ Saved: {category_name} - €{amount:.2f}{comment_str}",
        reply_markup=after_expense_menu()
    )
    await state.clear()

# ✅ SKIP COMMENT (corrected)
@dp.callback_query(F.data == "skip")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category_id = data["category_id"]
    amount = data["amount"]

    async with async_session() as session:
        category = await session.get(ExpenseCategory, category_id)
        category_name = category.name if category else "Unknown"

        daily = DailyExpense(
            user_id=callback.from_user.id,
            category_id=category_id,
            amount=amount,
            comment="",
            created_at=datetime.utcnow()
        )
        session.add(daily)
        await session.commit()

    await callback.message.edit_text(
        f"✅ Saved: {category_name} - €{amount:.2f}",
        reply_markup=after_expense_menu()
    )
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Cancelled.")
    await callback.answer()

# ----- MENU -----

@dp.callback_query(F.data == "settings")
async def open_settings(callback: CallbackQuery):
    await callback.message.edit_text("⚙️ Settings:", reply_markup=settings_menu())
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def return_to_main(callback: CallbackQuery):
    await callback.message.edit_text("🏠 Main Menu:", reply_markup=main_menu())
    await callback.answer()

@dp.callback_query(F.data == "edit_income")
async def edit_income_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditIncome.waiting_for_new_income)
    await callback.message.answer("💰 Enter your new monthly income (EUR):", reply_markup=cancel_keyboard())
    await callback.answer()

@dp.message(EditIncome.waiting_for_new_income)
async def update_income(message: Message, state: FSMContext):
    try:
        new_income = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Please enter a valid number.")
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar()
        if user:
            user.monthly_income = new_income
            await session.commit()

    await message.answer(f"✅ Monthly income updated to €{new_income:.2f}", reply_markup=main_menu())
    await state.clear()

@dp.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Cancelled.")
    await callback.message.edit_reply_markup()
    await callback.answer()

@dp.callback_query(F.data == "skip")
async def skip(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("⏭ Skipped.")
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def return_to_main(callback: CallbackQuery):
    await callback.message.edit_text("🔙 Back to main menu", reply_markup=main_menu())
    await callback.answer()

# ----- END OF CODE -----

async def main():
    logger.info(f"BOT_TOKEN loaded: {Config.BOT_TOKEN}")
    logger.info("🚀 Starting bot...")
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

