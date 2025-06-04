# app/bot/handlers/history/range.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.history_states import RangeHistoryFSM
from utils.custom_calendar import SimpleCalendar
from db.database import async_session
from db.models import DailyExpense
from sqlalchemy import select, func
from datetime import timedelta

router = Router()

@router.message(Command("history_range"))
async def start_range_selection(message: Message, state: FSMContext):
    calendar = await SimpleCalendar().start_calendar()
    await message.answer("📅 Select the *start* date:", reply_markup=calendar, parse_mode="Markdown")
    await state.set_state(RangeHistoryFSM.selecting_start)


@router.callback_query(RangeHistoryFSM.selecting_start)
async def select_start_date(callback: CallbackQuery, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback)
    if selected:
        await state.update_data(start_date=date)
        calendar = await SimpleCalendar().start_calendar()
        await callback.message.edit_text("📅 Select the *end* date:", reply_markup=calendar, parse_mode="Markdown")
        await state.set_state(RangeHistoryFSM.selecting_end)
    await callback.answer()


@router.callback_query(RangeHistoryFSM.selecting_end)
async def select_end_date(callback: CallbackQuery, state: FSMContext):
    selected, end_date = await SimpleCalendar().process_selection(callback)
    if not selected:
        await callback.answer()
        return

    data = await state.get_data()
    start_date = data.get("start_date")
    user_uuid = data.get("user_uuid")

    if not start_date or not user_uuid:
        await callback.message.edit_text("❌ Internal error: user or date not found.")
        await state.clear()
        return

    if end_date < start_date:
        await callback.message.edit_text("❌ End date cannot be before start date.")
        await state.clear()
        return

    await state.clear()

    async with async_session() as session:
        text = f"📆 Expenses from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}:\n\n"
        total_all = 0.0
        current = start_date

        while current <= end_date:
            result = await session.execute(
                select(DailyExpense).where(
                    DailyExpense.user_uuid == user_uuid,
                    func.date(DailyExpense.created_at) == current
                ).order_by(DailyExpense.created_at)
            )
            expenses = result.scalars().all()
            if expenses:
                text += f"📌 *{current.strftime('%A, %b %d')}*\n"
                day_total = 0.0
                for e in expenses:
                    text += f"• {e.category}: {e.amount:.2f}\n"
                    day_total += e.amount
                text += f"💰 Day total: {day_total:.2f}\n\n"
                total_all += day_total
            current += timedelta(days=1)

    text += f"🧾 **Total for period: {total_all:.2f}**"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Select another range", callback_data="history_range_again")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "history_range_again")
async def restart_range_flow(callback: CallbackQuery, state: FSMContext):
    calendar = await SimpleCalendar().start_calendar()
    await callback.message.edit_text("📅 Select the *start* date:", reply_markup=calendar, parse_mode="Markdown")
    await state.set_state(RangeHistoryFSM.selecting_start)
    await callback.answer()
