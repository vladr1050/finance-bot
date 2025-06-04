# app/bot/handlers/forecast/save.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from db.models import FixedExpense
from sqlalchemy import select, func
from services.forecast_logic import calculate_forecast
from db.database import async_session
from aiogram import Router, F
from aiogram.filters import StateFilter
from states.forecast_states import SaveForecastState
from aiogram.fsm.context import FSMContext
from services.forecast_service import save_forecast
from utils.keyboards import success_menu

router = Router()

@router.message(StateFilter(SaveForecastState.name))
async def process_forecast_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("⏳ How many months should the forecast cover? (e.g., 1, 3, 6, 12)")
    await state.set_state(SaveForecastState.months)


@router.message(StateFilter(SaveForecastState.months), F.text.in_(["1", "3", "6", "12"]))
async def process_forecast_months(message: Message, state: FSMContext):
    await state.update_data(months=int(message.text))
    await message.answer("💸 Enter expected extra expenses (comma-separated, optional):")
    await state.set_state(SaveForecastState.extra_expenses)


@router.message(StateFilter(SaveForecastState.extra_expenses))
async def process_forecast_extras(message: Message, state: FSMContext):
    raw = message.text.strip()
    extra_expenses = [e.strip() for e in raw.split(",") if e.strip()]
    await state.update_data(extra_expenses=extra_expenses)

    await message.answer("📊 Enter income change (positive or negative, e.g., -150):")
    await state.set_state(SaveForecastState.income_change)


@router.message(StateFilter(SaveForecastState.income_change))
async def process_income_change(message: Message, state: FSMContext):
    try:
        await state.update_data(income_changes=float(message.text.strip()))
    except ValueError:
        await message.answer("❌ Please enter a number.")
        return

    await message.answer("🏠 Enter fixed cost change (e.g., +80 or -50):")
    await state.set_state(SaveForecastState.fixed_change)


@router.message(StateFilter(SaveForecastState.fixed_change))
async def save_forecast_final(message: Message, state: FSMContext):
    try:
        await state.update_data(fixed_changes=float(message.text.strip()))
    except ValueError:
        await message.answer("❌ Please enter a valid number.")
        return

    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await message.answer("❌ Internal error: user not identified.")
        await state.clear()
        return

    async with async_session() as session:
        # Sum fixed expenses
        fixed_result = await session.execute(
            select(func.sum(FixedExpense.amount)).where(FixedExpense.user_uuid == user_uuid)
        )
        base_fixed_expenses = fixed_result.scalar() or 0.0

        # Get monthly income and savings from session
        result = await session.execute(
            f"SELECT monthly_income, monthly_savings FROM users WHERE user_uuid = '{user_uuid}'"
        )
        row = result.first()
        if not row or row[0] is None:
            await message.answer("❌ Please set your monthly income first using /income command.")
            return

        base_income, base_savings = row

    # Convert text list to expense dicts
    extra_expenses = []
    for i, e in enumerate(data["extra_expenses"]):
        try:
            extra_expenses.append({"name": f"Extra {i+1}", "amount": float(e), "month_offset": 0})
        except ValueError:
            continue

    forecast_result = calculate_forecast(
        base_income=base_income,
        base_fixed_expenses=base_fixed_expenses,
        base_savings_goal=base_savings,
        months=data["months"],
        income_changes=data["income_changes"],
        fixed_changes=data["fixed_changes"],
        extra_expenses=extra_expenses
    )

    await save_forecast(
        user_uuid=user_uuid,
        name=data["name"],
        months=data["months"],
        income_changes=data["income_changes"],
        fixed_changes=data["fixed_changes"],
        extra_expenses=data["extra_expenses"],
        projected_savings=forecast_result["projected_savings"],
        daily_budget=forecast_result["daily_budget"],
        total_free=forecast_result["total_free"]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add another", callback_data="forecast_add_another")],
        [InlineKeyboardButton(text="📋 View my forecasts", callback_data="forecast_view_all")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])
    await message.answer("✅ Forecast scenario saved successfully.", reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data == "forecast_add_another")
async def restart_forecast_flow(callback: CallbackQuery, state: FSMContext):
    from bot.handlers.forecast.entry import start_forecast
    await start_forecast(callback.message, state)
    await callback.answer()
