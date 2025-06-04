# app/bot/handlers/forecast/entry.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from db.database import async_session
from sqlalchemy import select
from db.models import User
from states.forecast_states import ForecastScenarioFSM
from utils.keyboards import success_menu

router = Router()

@router.message(Command("forecast"))
async def start_forecast(message: Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if not user or not user.is_premium:
        await message.answer("🚫 This feature is available for premium users only.")
        return

    await state.set_state(ForecastScenarioFSM.choosing_months)
    await state.update_data(user_uuid=str(user.user_uuid))  # 👈 ключевой момент

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 Month", callback_data="forecast_months_1")],
        [InlineKeyboardButton(text="3 Months", callback_data="forecast_months_3")],
        [InlineKeyboardButton(text="6 Months", callback_data="forecast_months_6")],
        [InlineKeyboardButton(text="12 Months", callback_data="forecast_months_12")]
    ])
    await message.answer("📅 Select forecast period:", reply_markup=buttons)

@router.callback_query(F.data.startswith("forecast_months_"))
async def choose_months(callback: CallbackQuery, state: FSMContext):
    months = int(callback.data.split("_")[-1])
    await state.update_data(months=months)
    await state.set_state(ForecastScenarioFSM.entering_income_change)
    await callback.message.edit_text("💶 Enter expected monthly income change (e.g. +200 or -150):")
    await callback.answer()

@router.message(ForecastScenarioFSM.entering_income_change)
async def income_change(message: Message, state: FSMContext):
    try:
        income_change = float(message.text.replace(",", "."))
        await state.update_data(income_change=income_change)
    except ValueError:
        await message.answer("❌ Please enter a valid number.")
        return
    await state.set_state(ForecastScenarioFSM.entering_fixed_change)
    await message.answer("🏠 Enter expected change in fixed expenses (e.g. +100 or -50):")

@router.message(ForecastScenarioFSM.entering_fixed_change)
async def fixed_change(message: Message, state: FSMContext):
    try:
        fixed_change = float(message.text.replace(",", "."))
        await state.update_data(fixed_change=fixed_change)
    except ValueError:
        await message.answer("❌ Please enter a valid number.")
        return
    await state.set_state(ForecastScenarioFSM.entering_savings_goal)
    await message.answer("💰 Enter your desired monthly savings goal:")

@router.message(ForecastScenarioFSM.entering_savings_goal)
async def savings_goal(message: Message, state: FSMContext):
    try:
        savings_goal = float(message.text.replace(",", "."))
        await state.update_data(savings_goal=savings_goal)
    except ValueError:
        await message.answer("❌ Please enter a valid number.")
        return
    await state.set_state(ForecastScenarioFSM.entering_extra_expenses)
    await message.answer(
        "🛫 Enter additional planned expenses in format:\n"
        "`Trip to Spain, 800, 1`\n\n"
        "(name, amount, month offset)\n"
        "Send `done` when finished.",
        parse_mode="Markdown"
    )

@router.message(ForecastScenarioFSM.entering_extra_expenses)
async def extra_expenses(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()

    if "extra_expenses" not in data:
        data["extra_expenses"] = []

    if text.lower() == "done":
        await state.update_data(extra_expenses=data["extra_expenses"])
        await state.set_state(ForecastScenarioFSM.confirming)
        await message.answer("✅ All data collected. Calculating forecast...", reply_markup=success_menu())
        from .save import show_forecast  # локальный импорт
        return await show_forecast(message, state)

    try:
        name, amount, offset = [s.strip() for s in text.split(",")]
        data["extra_expenses"].append({
            "name": name,
            "amount": float(amount),
            "month_offset": int(offset)
        })
        await state.update_data(extra_expenses=data["extra_expenses"])
        await message.answer("✔️ Added. Enter another or send `done`.")
    except Exception:
        await message.answer("❌ Invalid format. Try: `Trip to Spain, 800, 1`")
