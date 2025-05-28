import sys
import os
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True
)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from app.db.database import init_db, check_or_create_monthly_budgets
from app.db.models import MonthlyBudget
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime
from states import Register, AddFixedExpense, EditExpense, EditIncome, AddDailyExpense, ForecastScenarioFSM
from keyboards import settings_menu, after_expense_menu, skip_keyboard
from bot_setup import bot
from savings import *
from admin import *
from history_editor import register_history_editor_handlers

from category_grouping import register_category_group_handlers
register_category_group_handlers(dp)
register_history_editor_handlers(dp)

from adjustments import register_adjustment_handlers
register_adjustment_handlers(dp)

from forecast.handlers import router as forecast_router
dp.include_router(forecast_router)

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

from app.db.models import User, ExpenseCategory
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.db.database import async_session
from states import Register
from keyboards import main_menu

@dp.message(Register.waiting_for_income)
async def get_income(message: types.Message, state: FSMContext):
    income_str = message.text.replace(",", ".").strip()
    try:
        income = float(income_str)
        if income <= 0:
            await message.answer("🚫 Income must be greater than zero. Please enter a valid number.")
            return
    except ValueError:
        logging.warning(f"[Income] Invalid input from user {message.from_user.id}: {message.text}")
        await message.answer("❗ Please enter a valid number (e.g., 2500 or 2500.00)")
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
        await session.refresh(user)  # ✅ Get user.id

        # ➕ Default categories
        default_categories = [
            "Rent / Mortgage", "Utilities", "Home maintenance",
            "Groceries", "Restaurants", "Coffee / Snacks",
            "Fuel", "Public Transport", "Car Maintenance", "Parking / Taxi",
            "Clothing", "Household Goods", "Electronics",
            "Medical", "Pharmacy", "Gym / Fitness",
            "Cinema / Theater", "Subscriptions / Streaming", "Travel",
            "Education", "Kids supplies", "Gifts & Holidays",
            "Loans / Debts", "Insurance", "Taxes",
            "Charity", "Pets", "Miscellaneous"
        ]

        for name in default_categories:
            category = ExpenseCategory(user_id=user.id, name=name)
            session.add(category)

        await session.commit()

    await message.answer("✅ Saved!", reply_markup=main_menu())
    await state.clear()

# ----- FIXED EXPENSES -----

@dp.callback_query(F.data == "edit_expense")
async def cb_edit_expense(callback: CallbackQuery):
    async with async_session() as session:
        user_result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = user_result.scalar()

        if not user:
            await callback.message.answer("❌ User not found. Use /start.")
            await callback.answer()
            return

        result = await session.execute(
            select(FixedExpense).where(FixedExpense.user_id == user.id)
        )
        expenses = result.scalars().all()

    if not expenses:
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Add", callback_data="add_expense")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="settings")]
        ])
        await callback.message.answer("You have no fixed expenses yet.", reply_markup=buttons)
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

    # Добавляем кнопки Add и Back внизу
    final_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add", callback_data="add_expense")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="settings")]
    ])
    await callback.message.answer("➕ Add more or go back:", reply_markup=final_buttons)
    await callback.answer()

@dp.callback_query(F.data.startswith("delete_fixed_"))
async def delete_fixed(callback: CallbackQuery):
    expense_id = int(callback.data.split("_")[-1])
    today = date.today()
    month_start = today.replace(day=1)

    async with async_session() as session:
        expense = await session.get(FixedExpense, expense_id)
        if not expense:
            await callback.message.answer("Expense not found.")
            await callback.answer()
            return

        amount = expense.amount
        user_id = expense.user_id
        await session.delete(expense)

        result = await session.execute(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == user_id,
                MonthlyBudget.month_start == month_start
            )
        )
        budget = result.scalar()
        if budget:
            budget.fixed -= amount
            budget.remaining += amount
        await session.commit()

    await callback.message.answer("🗑 Expense deleted and budget updated.", reply_markup=main_menu())
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
    today = date.today()
    month_start = today.replace(day=1)

    async with async_session() as session:
        expense = await session.get(FixedExpense, expense_id)
        if not expense:
            await message.answer("Expense not found.")
            return

        old_amount = expense.amount

        if field == "name":
            expense.name = message.text
        elif field == "amount":
            try:
                new_amount = float(message.text)
            except ValueError:
                await message.answer("Amount must be a number.")
                return
            expense.amount = new_amount

            delta = new_amount - old_amount
            result = await session.execute(
                select(MonthlyBudget).where(
                    MonthlyBudget.user_id == expense.user_id,
                    MonthlyBudget.month_start == month_start
                )
            )
            budget = result.scalar()
            if budget:
                budget.fixed += delta
                budget.remaining -= delta

        await session.commit()

    await message.answer("✅ Updated and budget recalculated.", reply_markup=main_menu())
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
    amount_str = message.text.replace(",", ".").strip()

    try:
        amount = float(amount_str)
        if amount <= 0:
            await message.answer("🚫 Amount must be greater than zero. Please enter a valid number.")
            return
    except ValueError:
        logging.warning(f"[FixedExpense] Invalid input from user {message.from_user.id}: {message.text}")
        await message.answer("❗ Please enter a valid number (e.g., 120 or 85.50)")
        return

    data = await state.get_data()
    today = date.today()
    month_start = today.replace(day=1)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar()
        if not user:
            await message.answer("❌ User not found. Please restart with /start.")
            return

        fixed = FixedExpense(
            user_id=user.id,
            name=data["fixed_name"],
            amount=amount
        )
        session.add(fixed)

        result = await session.execute(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == user.id,
                MonthlyBudget.month_start == month_start
            )
        )
        budget = result.scalar()
        if budget:
            budget.fixed += amount
            budget.remaining -= amount

        await session.commit()

    await message.answer("✅ Fixed expense saved and budget updated!", reply_markup=main_menu())
    await state.clear()

# ----- REPORT -----

@dp.callback_query(F.data == "report")
async def cb_report(callback: CallbackQuery):
    from datetime import date
    from calendar import monthrange

    today = date.today()
    first_day_of_month = today.replace(day=1)
    total_days = monthrange(today.year, today.month)[1]
    days_left = total_days - today.day + 1

    async with async_session() as session:
        # Получаем пользователя
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar()
        if not user:
            await callback.message.answer("Please use /start first.")
            return

        # Получаем бюджет пользователя
        result = await session.execute(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == user.id,
                MonthlyBudget.month_start == first_day_of_month
            )
        )
        budget = result.scalar()
        if not budget:
            await callback.message.answer("❌ Monthly budget not found.")
            return

        # Идеальный бюджет
        monthly_budget = budget.income - budget.fixed - budget.savings_goal
        coefficient = budget.coefficient or 1.0
        adjusted_budget = monthly_budget * coefficient

        # Считаем общие расходы за месяц
        result = await session.execute(
            select(func.sum(DailyExpense.amount)).where(
                DailyExpense.user_id == user.id,
                func.date(DailyExpense.created_at) >= first_day_of_month
            )
        )
        real_spent = result.scalar() or 0.0

        # Новый расчёт
        spent = real_spent
        remaining = adjusted_budget - spent
        daily_budget = max(remaining, 0) / days_left if days_left > 0 else 0  # 🔒 Защита от отрицательных значений

        # Баланс накоплений
        result = await session.execute(
            select(SavingsBalance).where(SavingsBalance.user_id == user.id)
        )
        savings = result.scalar()
        savings_amount = savings.amount if savings else 0.0

    # ⚠️ Предупреждение о перерасходе
    savings_note = ""
    if savings_amount < 0:
        savings_note = "\n⚠️ You are overspending and now in **debt**!"

    await callback.message.answer(
        f"💼 Income: €{budget.income:.2f}\n"
        f"📋 Fixed Expenses: €{budget.fixed:.2f}\n"
        f"💰 Savings Goal: €{budget.savings_goal:.2f}\n"
        f"📆 Budget coverage: {coefficient:.2f} of month\n"
        f"🧮 Monthly Budget: €{adjusted_budget:.2f}\n\n"
        f"📉 Spent: €{spent:.2f}\n"
        f"✅ Remaining: €{remaining:.2f}\n"
        f"📆 Days left: {days_left}\n"
        f"💸 Daily budget: €{daily_budget:.2f}\n\n"
        f"💰 Savings Balance: €{savings_amount:.2f}"
        f"{savings_note}",
        reply_markup=main_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "category_report")
async def show_category_report(callback: CallbackQuery):
    today = date.today()
    month_start = today.replace(day=1)

    async with async_session() as session:
        # Получаем пользователя
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar()
        if not user:
            await callback.message.answer("❌ User not found. Use /start.")
            return

        # Получаем все траты по категориям
        result = await session.execute(
            select(
                ExpenseCategory.name,
                func.sum(DailyExpense.amount)
            ).join(ExpenseCategory, DailyExpense.category_id == ExpenseCategory.id)
            .where(
                DailyExpense.user_id == user.id,
                func.date(DailyExpense.created_at) >= month_start
            )
            .group_by(ExpenseCategory.name)
            .order_by(func.sum(DailyExpense.amount).desc())
        )
        rows = result.all()

    if not rows:
        await callback.message.answer("📭 No expenses recorded this month.")
        await callback.answer()
        return

    total = sum(amount for _, amount in rows)
    lines = ["📊 Expenses by Category\n"]
    for name, amount in rows:
        percent = (amount / total) * 100 if total else 0
        lines.append(f"• {name} — €{amount:.2f} ({percent:.0f}%)")

    lines.append(f"\nTotal: €{total:.2f}")
    await callback.message.answer("\n".join(lines), reply_markup=main_menu())
    await callback.answer()

# ----- DAILY EXPENSE ENTRY -----

# ✅ VIEW HISTORY (corrected)
#@dp.callback_query(F.data == "view_history")
async def view_expense_history(callback: CallbackQuery):
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=3)

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
        await callback.message.answer("📭 No daily expenses found in the last 3 days.")
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
    amount_str = message.text.replace(',', '.').strip()

    try:
        amount = float(amount_str)
        if amount <= 0:
            await message.answer("🚫 Amount must be greater than zero. Please enter a valid number.", reply_markup=cancel_keyboard())
            return
    except ValueError:
        logging.warning(f"[DailyExpense] Invalid input from user {message.from_user.id}: {message.text}")
        await message.answer("❗ Please enter a valid number (e.g., 15 or 12.50)", reply_markup=cancel_keyboard())
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

        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar()
        if not user:
            await message.answer("❌ User not found.")
            return

        daily = DailyExpense(
            user_id=user.id,
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

        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar()
        if not user:
            await callback.message.answer("❌ User not found.")
            await callback.answer()
            return

        daily = DailyExpense(
            user_id=user.id,
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

@dp.callback_query(F.data == "skip")
async def skip(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("⏭ Skipped.")
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def return_to_main(callback: CallbackQuery):
    await callback.message.edit_text("🔙 Back to main menu", reply_markup=main_menu())
    await callback.answer()

# ----- FORECAST -----

async def start_forecast_fsm(entry_point: Message | CallbackQuery, state: FSMContext):
    await state.set_state(ForecastScenarioFSM.choosing_months)
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 Month", callback_data="forecast_months_1")],
        [InlineKeyboardButton(text="3 Months", callback_data="forecast_months_3")],
        [InlineKeyboardButton(text="6 Months", callback_data="forecast_months_6")],
        [InlineKeyboardButton(text="12 Months", callback_data="forecast_months_12")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
    ])
    await entry_point.answer("📅 Select forecast period:", reply_markup=buttons)

@dp.callback_query(F.data == "forecast_menu")
async def open_forecast_menu(callback: CallbackQuery, state: FSMContext):
    await start_forecast_fsm(callback.message, state)
    await callback.answer()

# ----- END OF CODE -----

from app.config import Config, ENVIRONMENT

async def main():
    logger.info(f"🔧 ENVIRONMENT: {ENVIRONMENT}")
    logger.info(f"🔐 BOT_TOKEN loaded: {Config.BOT_TOKEN}")
    logger.info(f"🚀 Starting bot in {ENVIRONMENT.upper()} mode")

    await init_db()
    await check_or_create_monthly_budgets()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
