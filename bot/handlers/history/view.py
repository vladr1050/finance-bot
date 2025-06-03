# app/bot/handlers/history/view.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.states.history_states import HistoryFSM
from app.utils.custom_calendar import SimpleCalendar
from app.db.database import async_session
from app.db.models import DailyExpense
from sqlalchemy import select, func
from app.utils.keyboards import main_menu

router = Router()

@router.message(Command("history"))
async def start_history_calendar(message: Message, state: FSMContext):
    calendar = await SimpleCalendar().start_calendar()
    await message.answer("📅 Select a date to view your expenses:", reply_markup=calendar)
    await state.set_state(HistoryFSM.selecting_date)


@router.callback_query(HistoryFSM.selecting_date)
async def handle_calendar(callback: CallbackQuery, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback)

    if selected:
        await state.set_state(HistoryFSM.viewing_day)
        await state.update_data(selected_date=date)

        user_data = await state.get_data()
        user_uuid = user_data.get("user_uuid")

        if not user_uuid:
            await callback.message.edit_text("❌ User not authenticated. Please /login first.")
            await callback.answer()
            return

        async with async_session() as session:
            result = await session.execute(
                select(DailyExpense).where(
                    DailyExpense.user_id == user_uuid,
                    func.date(DailyExpense.created_at) == date
                ).order_by(DailyExpense.created_at)
            )
            expenses = result.scalars().all()

        if not expenses:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔁 View another day", callback_data="history_again")],
                [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
            ])
            await callback.message.edit_text(
                f"📭 No expenses found on {date.strftime('%Y-%m-%d')}",
                reply_markup=keyboard
            )
        else:
            text = f"📒 Expenses on {date.strftime('%Y-%m-%d')}:\n\n"
            buttons = []

            for e in expenses:
                label = f"{e.category}: {e.amount:.2f}"
                text += f"• {label}\n"
                buttons.append([
                    InlineKeyboardButton(text=f"✏️ Edit", callback_data=f"edit_exp_{e.id}"),
                    InlineKeyboardButton(text=f"🗑 Delete", callback_data=f"del_exp_{e.id}")
                ])

            buttons.append([
                InlineKeyboardButton(text="🔁 View another day", callback_data="history_again")
            ])
            buttons.append([
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")
            ])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await callback.message.edit_text(text, reply_markup=keyboard)

        await state.clear()

    await callback.answer()


@router.callback_query(F.data == "history_again")
async def repeat_history_calendar(callback: CallbackQuery, state: FSMContext):
    calendar = await SimpleCalendar().start_calendar()
    await callback.message.edit_text("📅 Select another date to view:", reply_markup=calendar)
    await state.set_state(HistoryFSM.selecting_date)
    await callback.answer()
