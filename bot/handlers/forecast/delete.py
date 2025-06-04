# app/bot/handlers/forecast/delete.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from states.forecast_states import DeleteForecastState
from services.forecast_service import delete_forecast, get_user_forecasts
from db.database import async_session
from db.models import ForecastScenario
from sqlalchemy import select
from utils.keyboards import success_menu

router = Router()

@router.message(Command("delete_forecast"))
async def ask_forecast_id(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ Internal error: user not identified.")
        return

    forecasts = await get_user_forecasts(user_id=user_uuid)

    if not forecasts:
        await message.answer("📭 You have no saved forecasts.")
        return

    text = "🗑 Choose a forecast to delete. Send its ID:\n\n"
    for f in forecasts:
        text += f"• {f.id} — {f.name} ({f.months}m)\n"

    await message.answer(text)
    await state.set_state(DeleteForecastState.confirm)


@router.message(StateFilter(DeleteForecastState.confirm), F.text.regexp(r"^\d+$"))
async def confirm_delete(message: Message, state: FSMContext):
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ Internal error: user not identified.")
        await state.clear()
        return

    forecast_id = int(message.text.strip())
    success = await delete_forecast(user_id=user_uuid, forecast_id=forecast_id)

    if success:
        await message.answer(f"✅ Forecast #{forecast_id} deleted.", reply_markup=success_menu())
    else:
        await message.answer(f"⚠️ Forecast #{forecast_id} not found or doesn't belong to you.")

    await state.clear()


@router.message(DeleteForecastState.confirm)
async def invalid_input(message: Message):
    await message.answer("❌ Please enter a valid forecast ID (a number).")


@router.callback_query(F.data.startswith("del_forecast_"))
async def delete_forecast_inline(callback: CallbackQuery, state: FSMContext):
    forecast_id = int(callback.data.replace("del_forecast_", ""))
    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await callback.message.edit_text("❌ Internal error: user not identified.")
        await callback.answer()
        return

    async with async_session() as session:
        result = await session.execute(
            select(ForecastScenario).where(
                ForecastScenario.id == forecast_id,
                ForecastScenario.user_id == user_uuid
            )
        )
        forecast = result.scalar_one_or_none()

        if not forecast:
            await callback.message.edit_text("⚠️ Forecast scenario not found.")
            await callback.answer()
            return

        await session.delete(forecast)
        await session.commit()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 View remaining", callback_data="forecast_view_all")],
        [InlineKeyboardButton(text="➕ Add new", callback_data="forecast_add_another")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])

    await callback.message.edit_text("🗑 Forecast scenario deleted.", reply_markup=keyboard)
    await callback.answer()
