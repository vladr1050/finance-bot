# app/bot/handlers/forecast/view.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from db.database import async_session
from db.models import ForecastScenario
from sqlalchemy import select
from typing import Union

router = Router()

@router.message(Command("forecasts"))
@router.callback_query(F.data == "forecast_view_all")
async def show_forecasts(event: Union[Message, CallbackQuery], state: FSMContext):
    """Show all saved forecast scenarios with buttons"""

    send_func = event.answer if isinstance(event, Message) else event.message.edit_text
    state_data = await state.get_data()
    user_uuid = state_data.get("user_uuid")

    if not user_uuid:
        await send_func("❌ Internal error: user not authenticated.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(ForecastScenario)
            .where(ForecastScenario.user_uuid == user_uuid)
            .order_by(ForecastScenario.created_at.desc())
        )
        forecasts = result.scalars().all()

    if not forecasts:
        await send_func("📭 You don't have any saved forecasts yet.")
        return

    text = "📊 Your forecast scenarios:\n\n"
    buttons = []

    for f in forecasts:
        text += f"• *{f.name}* – {f.months} months\n"
        buttons.append([
            InlineKeyboardButton(text=f"🗑 Delete: {f.name}", callback_data=f"del_forecast_{f.id}")
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        *buttons,
        [InlineKeyboardButton(text="➕ Add new", callback_data="forecast_add_another")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])

    if isinstance(event, Message):
        await event.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await event.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        await event.answer()
