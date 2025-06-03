# app/bot/handlers/adjustments/delete.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.db.database import async_session
from sqlalchemy import select
from app.db.models import MonthlyBudgetAdjustment
from datetime import date

router = Router()

@router.message(Command("delete_adjustments"))
@router.callback_query(F.data == "delete_adjustments")
async def list_adjustments_for_deletion(event: Message | CallbackQuery, state: FSMContext):
    """Handles both /delete_adjustments command and inline button callback"""
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        send_func = event.answer if isinstance(event, Message) else event.message.answer
        await send_func("❌ You are not logged in. Please /login first.")
        return

    send_func = event.answer if isinstance(event, Message) else event.message.edit_text

    async with async_session() as session:
        month_start = date.today().replace(day=1)
        result = await session.execute(
            select(MonthlyBudgetAdjustment).where(
                MonthlyBudgetAdjustment.user_id == user_uuid,
                MonthlyBudgetAdjustment.month == month_start
            )
        )
        adjustments = result.scalars().all()

    if not adjustments:
        await send_func("📭 No adjustments found for this month.")
        return

    buttons = []
    for adj in adjustments:
        symbol = "+" if adj.type == "add" else "-"
        label = f"{adj.source} {symbol}{adj.amount:.2f}"
        buttons.append(
            [InlineKeyboardButton(text=label, callback_data=f"del_adj_{adj.id}")]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    text = "🗑 Select an adjustment to delete:"
    if isinstance(event, Message):
        await event.answer(text, reply_markup=keyboard)
    else:
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()


@router.callback_query(F.data.startswith("del_adj_"))
async def delete_adjustment(callback: CallbackQuery, state: FSMContext):
    """Deletes selected adjustment and offers navigation options"""
    adj_id = int(callback.data.replace("del_adj_", ""))

    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await callback.message.edit_text("❌ You are not logged in. Please /login first.")
        await callback.answer()
        return

    async with async_session() as session:
        result = await session.execute(
            select(MonthlyBudgetAdjustment).where(
                MonthlyBudgetAdjustment.id == adj_id,
                MonthlyBudgetAdjustment.user_id == user_uuid
            )
        )
        adj = result.scalar_one_or_none()

        if not adj:
            await callback.message.edit_text("⚠️ Adjustment not found.")
            await callback.answer()
            return

        await session.delete(adj)
        await session.commit()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Delete another", callback_data="delete_adjustments")],
        [InlineKeyboardButton(text="📋 View adjustments", callback_data="view_adjustments")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])
    await callback.message.edit_text("✅ Adjustment deleted.", reply_markup=keyboard)
    await callback.answer()
