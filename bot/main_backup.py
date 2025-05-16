import sys
import os

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
from datetime import datetime
from states import Register, AddFixedExpense, EditExpense, EditIncome, AddDailyExpense, AddCategory
from keyboards import main_menu
from bot_setup import bot, dp
from savings import *

# ----- START -----

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
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

@dp.message(Register.waiting_for_income)
async def get_income(message: Message, state: FSMContext):
    try:
        income = float(message.text)
    except ValueError:
        await message.answer("Please enter a number.")
        return
    data = await state.get_data()
    async with async_session() as session:
        user = User(telegram_id=message.from_user.id, name=data['name'], monthly_income=income)
        session.add(user)
        await session.commit()
    await message.answer("✅ Saved!", reply_markup=main_menu())
    await state.clear()

# ----- FIXED EXPENSES -----

@dp.callback_query(F.data == "edit_expense")
async def cb_edit_expense(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(FixedExpense).where(FixedExpense.user_id == callback.from_user.id))
        expenses = result.scalars().all()

    if not expenses:
        await callback.message.answer("You have no fixed expenses yet.")
        return

    for e in expenses:
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_fixed_{e.id}"),
                InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_fixed_{e.id}")
            ]
        ])
        await callback.message.answer(f"{e.name}: €{e.amount}", reply_markup=buttons)
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
    await callback.message.answer("Enter the name of your fixed expense:")
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
        savings = user.monthly_savings or 0
        available = user.monthly_income - total_expenses - savings

    await callback.message.answer(
        f"💼 Income: €{user.monthly_income:.2f}\n"
        f"📉 Fixed: €{total_expenses:.2f}\n"
        f"💰 Savings: €{savings:.2f}\n"
        f"✅ Left: €{available:.2f}"
    )
    await callback.answer()

# ----- DAILY EXPENSE ENTRY -----

from datetime import date

@dp.callback_query(F.data == "view_history")
async def view_today_history(callback: CallbackQuery):
    today = date.today()
    async with async_session() as session:
        result = await session.execute(
            select(DailyExpense).where(
                DailyExpense.user_id == callback.from_user.id,
                func.date(DailyExpense.created_at) == today
            )
        )
        expenses = result.scalars().all()

    if not expenses:
        await callback.message.answer("No daily expenses found for today.")
        await callback.answer()
        return

    total = 0
    lines = [f"📅 Daily expenses for {today}:"]
    for e in expenses:
        total += e.amount
        line = f"• {e.category} — €{e.amount:.2f}"
        if e.comment:
            line += f" ({e.comment})"
        lines.append(line)
    lines.append(f"Total: €{total:.2f}")

    await callback.message.answer("\n".join(lines), reply_markup=main_menu())
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
        await message.answer("Please enter a valid number.")
        return
    await state.update_data(amount=amount)
    await state.set_state(AddDailyExpense.entering_comment)
    await message.answer("Add a comment or type 'skip':")

@dp.message(AddDailyExpense.entering_comment)
async def enter_comment(message: Message, state: FSMContext):
    print("DEBUG: enter_comment reached")
    comment = message.text.strip()
    if comment.lower() == 'skip':
        comment = ""
    data = await state.get_data()
    async with async_session() as session:
        daily = DailyExpense(
            user_id=message.from_user.id,
            category=data["category_name"],
            amount=data["amount"],
            comment=comment,
            created_at=datetime.utcnow()
        )
        session.add(daily)
        await session.commit()
    comment_str = f" ({comment})" if comment else ""
    await message.answer(f"✅ Saved: {data['category_name']} - €{data['amount']}{comment_str}", reply_markup=main_menu())
    await state.clear()

@dp.callback_query(F.data == "daily_expense")
async def open_daily_expense_menu(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(
            select(ExpenseCategory).where(ExpenseCategory.user_id == callback.from_user.id)
        )
        categories = result.scalars().all()

    if not categories:
        await callback.message.answer("You have no categories yet. Use the 'Add Category' option first.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}")] for cat in categories] +
                        [[InlineKeyboardButton(text="➕ Add Category", callback_data="add_category")]]
    )
    await state.set_state(AddDailyExpense.choosing_category)
    await callback.message.answer("Select a category:", reply_markup=keyboard)
    await callback.answer()

async def main():
    print(f"BOT_TOKEN from .env: {Config.BOT_TOKEN}")
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

