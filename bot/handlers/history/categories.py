# app/bot/handlers/history/categories.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.history_states import CategoryReportFSM
from utils.custom_calendar import SimpleCalendar
from db.database import async_session
from db.models import DailyExpense
from sqlalchemy import select
from collections import defaultdict
from datetime import timedelta

router = Router()

@router.message(Command("category_report"))
async def start_category_report(message: Message, state: FSMContext):
    user_data = await state.get_data()
    if not user_data.get("user_uuid"):
        await message.answer("❌ User not authenticated. Please /login first.")
        return

    calendar = await SimpleCalendar().start_calendar()
    await message.answer("📅 Select the *start* date:", reply_markup=calendar, parse_mode="Markdown")
    await state.set_state(CategoryReportFSM.selecting_start)


@router.callback_query(CategoryReportFSM.selecting_start)
async def select_start(callback: CallbackQuery, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback)
    if selected:
        await state.update_data(start_date=date)
        calendar = await SimpleCalendar().start_calendar()
        await callback.message.edit_text("📅 Select the *end* date:", reply_markup=calendar, parse_mode="Markdown")
        await state.set_state(CategoryReportFSM.selecting_end)
    await callback.answer()


@router.callback_query(CategoryReportFSM.selecting_end)
async def generate_category_report(callback: CallbackQuery, state: FSMContext):
    selected, end_date = await SimpleCalendar().process_selection(callback)
    if not selected:
        await callback.answer()
        return

    data = await state.get_data()
    start_date = data.get("start_date")
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await callback.message.edit_text("❌ User not authenticated.")
        return

    if end_date < start_date:
        await callback.message.edit_text("❌ End date cannot be before start date.")
        await state.clear()
        return

    await state.clear()

    # Group expenses by category
    category_totals = defaultdict(float)
    total_all = 0.0

    async with async_session() as session:
        result = await session.execute(
            select(DailyExpense).where(
                DailyExpense.user_uuid == user_uuid,
                DailyExpense.created_at >= start_date,
                DailyExpense.created_at <= end_date + timedelta(days=1)
            )
        )
        expenses = result.scalars().all()
        for e in expenses:
            category_totals[e.category] += e.amount
            total_all += e.amount

    if not category_totals:
        await callback.message.edit_text("📭 No expenses found in this period.")
        await callback.answer()
        return

    text = f"📂 Category Report ({start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}):\n\n"
    for category, amount in sorted(category_totals.items(), key=lambda x: -x[1]):
        percent = (amount / total_all) * 100 if total_all else 0
        text += f"• {category}: {amount:.2f} ({percent:.1f}%)\n"

    text += f"\n🧾 Total: {total_all:.2f}\n\n_Sorted by highest spending first_"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Select another period", callback_data="category_report_again")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "category_report_again")
async def restart_category_report(callback: CallbackQuery, state: FSMContext):
    calendar = await SimpleCalendar().start_calendar()
    await callback.message.edit_text("📅 Select the *start* date:", reply_markup=calendar, parse_mode="Markdown")
    await state.set_state(CategoryReportFSM.selecting_start)
    await callback.answer()
