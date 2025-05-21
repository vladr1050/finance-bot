from aiogram import F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from collections import defaultdict
from datetime import datetime, timedelta, date

from db.models import User, DailyExpense, ExpenseCategory
from db.database import async_session
from states import EditDailyExpense
from keyboards import main_menu
from functools import partial

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from custom_calendar import show_start_calendar, process_calendar, show_end_calendar

def register_history_editor_handlers(dp):
    @dp.callback_query(F.data == "view_history")
    async def view_expense_history(callback: CallbackQuery, state: FSMContext):
        today = datetime.utcnow().date()
        start_date = today - timedelta(days=2)

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
        chunks = []
        chunk = ""
        message_ids = []

        for d in sorted_days:
            lines = [f"📅 {d.strftime('%Y-%m-%d')}"]
            total = 0
            for e, cat_name in grouped[d]:
                comment = f" ({e.comment})" if e.comment else ""
                lines.append(f"• {cat_name} — €{e.amount:.2f}{comment}")
                total += e.amount
            lines.append(f"💰 Total: €{total:.2f}")
            section = "\n".join(lines)

            if len(chunk) + len(section) + 2 > 4096:
                chunks.append(chunk)
                chunk = section
            else:
                chunk += f"\n\n{section}" if chunk else section

        if chunk:
            chunks.append(chunk)

        for part in chunks:
            msg = await callback.message.answer(part)
            message_ids.append(msg.message_id)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📆 Show custom range", callback_data="view_range_custom")],
            [InlineKeyboardButton(text="✏️ Edit Expenses", callback_data="edit_history")],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")
            ]
        ])
        menu_msg = await callback.message.answer("🔽 What next?", reply_markup=keyboard)
        message_ids.append(menu_msg.message_id)

        await state.update_data(view_messages=message_ids)
        await callback.answer()

    @dp.callback_query(F.data == "edit_history")
    async def handle_edit_history(callback: CallbackQuery, state: FSMContext):
        await state.update_data(view_mode="edit")
        await show_start_calendar(callback, state)
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
        await state.update_data(view_mode="edit")
        await show_start_calendar(callback, state)
        await callback.answer()

    @dp.callback_query(F.data.startswith("simple_calendar:DAY:"))
    async def on_calendar_select(callback: CallbackQuery, state: FSMContext):
        print(f"📅 Received raw callback: {callback.data}")
        callback_data = SimpleCalendarCallback.unpack(callback.data)
        data = await state.get_data()
        edit_mode = data.get("view_mode") == "edit"
        handler = partial(show_expense_history_for_range, edit_mode=edit_mode)
        await process_calendar(callback, callback_data, state, handler)
        await callback.answer()

    @dp.callback_query(F.data == "view_range_custom")
    async def custom_view_range(callback: CallbackQuery, state: FSMContext):
        await state.update_data(view_mode="view")
        await show_start_calendar(callback, state)
        await callback.answer()

    @dp.callback_query(F.data == "cancel")
    async def cancel_range(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        message_ids = data.get("view_messages", [])

        for msg_id in message_ids:
            try:
                await callback.bot.delete_message(callback.message.chat.id, msg_id)
            except:
                pass

        await state.clear()
        await callback.message.edit_text("❌ Cancelled.", reply_markup=main_menu())
        await callback.answer()

    @dp.callback_query(F.data == "calendar_today")
    async def select_today(callback: CallbackQuery, state: FSMContext):
        today = date.today()
        data = await state.get_data()
        stage = data.get("calendar_stage")

        if stage == "start":
            await state.update_data(start_date=today)
            await show_end_calendar(callback, state)
        elif stage == "end":
            start_date = data.get("start_date")
            end_date = today

            if not start_date or start_date > end_date:
                await callback.message.answer("❌ Invalid date range. Start must be before End.", reply_markup=main_menu())
                await state.clear()
                return

            await state.clear()
            view_mode = data.get("view_mode")
            edit_mode = view_mode == "edit"
            await show_expense_history_for_range(callback, start_date, end_date, edit_mode)

        await callback.answer()

    @dp.callback_query(F.data == "calendar_cancel")
    async def cancel_calendar(callback: CallbackQuery, state: FSMContext):
        await state.clear()
        await callback.message.edit_text("❌ Cancelled.", reply_markup=main_menu())
        await callback.answer()

async def show_expense_history_for_range(callback: CallbackQuery, start_date: date, end_date: date, edit_mode: bool = False):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar()

        if not user:
            await callback.message.answer("❌ User not found. Use /start.")
            return

        result = await session.execute(
            select(DailyExpense, ExpenseCategory.name)
            .join(ExpenseCategory, DailyExpense.category_id == ExpenseCategory.id)
            .where(
                DailyExpense.user_id == user.id,
                func.date(DailyExpense.created_at) >= start_date,
                func.date(DailyExpense.created_at) <= end_date
            )
        )
        rows = result.all()

    if not rows:
        await callback.message.answer("📭 No expenses found from "
                                      f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        return

    grouped = defaultdict(list)
    for expense, category_name in rows:
        grouped[expense.created_at.date()].append((expense, category_name))

    await callback.message.answer(
        f"{'✏️ Editing' if edit_mode else '📖 Viewing'} expenses from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}:"
    )

    if not edit_mode:
        # Normal view mode (chunked)
        chunks = []
        chunk = ""

        for d in sorted(grouped.keys(), reverse=True):
            lines = [f"📅 {d.strftime('%Y-%m-%d')}"]
            for e, cat_name in grouped[d]:
                comment = f" ({e.comment})" if e.comment else ""
                lines.append(f"• {cat_name} — €{e.amount:.2f}{comment}")
            section = "\n".join(lines)

            if len(chunk) + len(section) + 2 > 4096:
                chunks.append(chunk)
                chunk = section
            else:
                chunk += f"\n\n{section}" if chunk else section

        if chunk:
            chunks.append(chunk)

        for part in chunks:
            await callback.message.answer(part)

    else:
        # Edit mode (each row with buttons)
        for d in sorted(grouped.keys(), reverse=True):
            await callback.message.answer(f"📅 {d.strftime('%Y-%m-%d')}")
            for e, cat_name in grouped[d]:
                comment = f" ({e.comment})" if e.comment else ""
                text = f"• {cat_name} — €{e.amount:.2f}{comment}"
                buttons = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_daily_{e.id}"),
                        InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_daily_{e.id}")
                    ]
                ])
                await callback.message.answer(text, reply_markup=buttons)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Back to calendar", callback_data="view_range_custom")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
    ])
    await callback.message.answer("🔽 What next?", reply_markup=keyboard)


