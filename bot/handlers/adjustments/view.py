from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from datetime import date
from db.database import async_session
from sqlalchemy import select
from db.models import MonthlyBudgetAdjustment
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("view_adjustments"))
async def view_adjustments(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ You are not logged in. Use /start to log in.")
        return

    month_start = date.today().replace(day=1)

    async with async_session() as session:
        result = await session.execute(
            select(MonthlyBudgetAdjustment).where(
                MonthlyBudgetAdjustment.user_id == user_uuid,
                MonthlyBudgetAdjustment.month == month_start
            )
        )
        adjustments = result.scalars().all()

    if not adjustments:
        await message.answer("📭 No adjustments found for this month.")
        return

    text = "🛠 Your budget adjustments:\n\n"
    for adj in adjustments:
        symbol = "+" if adj.type == "add" else "-"
        perm = "♾" if adj.apply_permanently else "📆"
        comment = f"\n   💬 {adj.comment}" if adj.comment else ""
        text += f"{perm} *{adj.source}* {symbol}{adj.amount:.2f}{comment}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Refresh", callback_data="view_adjustments")],
        [InlineKeyboardButton(text="➕ Add Adjustment", callback_data="add_adjust_again")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "view_adjustments")
async def refresh_adjustments(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await callback.message.edit_text("❌ You are not logged in. Use /start to log in.")
        await callback.answer()
        return

    month_start = date.today().replace(day=1)

    async with async_session() as session:
        result = await session.execute(
            select(MonthlyBudgetAdjustment).where(
                MonthlyBudgetAdjustment.user_id == user_uuid,
                MonthlyBudgetAdjustment.month == month_start
            )
        )
        adjustments = result.scalars().all()

    if not adjustments:
        await callback.message.edit_text("📭 No adjustments found for this month.")
        await callback.answer()
        return

    text = "🛠 Your budget adjustments:\n\n"
    for adj in adjustments:
        symbol = "+" if adj.type == "add" else "-"
        perm = "♾" if adj.apply_permanently else "📆"
        comment = f"\n   💬 {adj.comment}" if adj.comment else ""
        text += f"{perm} *{adj.source}* {symbol}{adj.amount:.2f}{comment}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Refresh", callback_data="view_adjustments")],
        [InlineKeyboardButton(text="➕ Add Adjustment", callback_data="add_adjust_again")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

