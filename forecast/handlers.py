# forecast/handlers.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.filters import Command
from app.db.database import async_session
from sqlalchemy import select
from app.db.models import User, FixedExpense, SavingsBalance
from states import ForecastScenarioFSM
from app.bot.handlers.forecast.logic import calculate_forecast
from app.bot.handlers.forecast.services import create_forecast_scenario, get_user_forecast_scenarios, delete_forecast_scenario

router = Router()

@router.message(Command("forecast"))
async def start_forecast(message: Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar()

    if not user or not user.is_premium:
        await message.answer("🚫 This feature is available for premium users only.")
        return

    await state.set_state(ForecastScenarioFSM.choosing_months)
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
        await message.answer("Please enter a valid number.")
        return
    await state.set_state(ForecastScenarioFSM.entering_fixed_change)
    await message.answer("🏠 Enter expected change in fixed expenses (e.g. +100 or -50):")

@router.message(ForecastScenarioFSM.entering_fixed_change)
async def fixed_change(message: Message, state: FSMContext):
    try:
        fixed_change = float(message.text.replace(",", "."))
        await state.update_data(fixed_change=fixed_change)
    except ValueError:
        await message.answer("Please enter a valid number.")
        return
    await state.set_state(ForecastScenarioFSM.entering_savings_goal)
    await message.answer("💰 Enter your desired monthly savings goal:")

@router.message(ForecastScenarioFSM.entering_savings_goal)
async def savings_goal(message: Message, state: FSMContext):
    try:
        savings_goal = float(message.text.replace(",", "."))
        await state.update_data(savings_goal=savings_goal)
    except ValueError:
        await message.answer("Please enter a valid number.")
        return
    await state.set_state(ForecastScenarioFSM.entering_extra_expenses)
    await message.answer(
        "🛫 Enter additional planned expenses in format:\n"
        "`Trip to Spain, 800, 1`\n\n"
        "(name, amount, month offset)\n"
        "Send `done` when finished.", parse_mode="Markdown"
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
        await message.answer("✅ All data collected. Calculating forecast...")
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

async def show_forecast(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar()

        result = await session.execute(
            select(FixedExpense).where(FixedExpense.user_id == user.id)
        )
        fixed_expenses = result.scalars().all()
        base_fixed_expenses = sum(e.amount for e in fixed_expenses)

        forecast = calculate_forecast(
            base_income=user.monthly_income,
            base_fixed_expenses=base_fixed_expenses,
            base_savings_goal=data["savings_goal"],
            months=data["months"],
            income_changes=data["income_change"],
            fixed_changes=data["fixed_change"],
            extra_expenses=data["extra_expenses"]
        )

        # 🔁 Добавляем текущие накопления
        result = await session.execute(
            select(SavingsBalance).where(SavingsBalance.user_id == user.id)
        )
        savings = result.scalar()
        savings_amount = savings.amount if savings else 0.0

        forecast["savings_balance"] = savings_amount
        forecast["total_free_including_savings"] = forecast["total_free"] + savings_amount

        total_days = data["months"] * 30  # можно заменить на более точный подсчёт, если потребуется
        forecast["daily_budget_including_savings"] = (
            forecast["total_free_including_savings"] / total_days if total_days > 0 else 0.0
        )

    await message.answer(
        f"📊 *Forecast Summary*:\n\n"
        f"🗓 Period: {data['months']} months\n"
        f"💶 Income Δ: €{data['income_change']:.2f}\n"
        f"🏠 Fixed Δ: €{data['fixed_change']:.2f}\n"
        f"💰 Monthly Savings: €{data['savings_goal']:.2f}\n"
        f"➕ Extra Expenses: {len(data['extra_expenses'])} item(s)\n\n"
        f"📉 Total Free Cash: €{forecast['total_free']:.2f}\n"
        f"💾 Current Savings: €{forecast['savings_balance']:.2f}\n"
        f"💰 Total (Cash + Savings): €{forecast['total_free_including_savings']:.2f}\n"
        f"📆 Daily Budget: €{forecast['daily_budget']:.2f}\n"
        f"📆 Adjusted Daily Budget (w/ Savings): €{forecast['daily_budget_including_savings']:.2f}\n"
        f"📦 Projected Savings: €{forecast['projected_savings']:.2f}",
        parse_mode="Markdown"
    )

    await state.update_data(latest_forecast=forecast)
    await message.answer(
        "💾 *Would you like to save this scenario?*\n"
        "Send `/save_scenario` followed by a name.\n"
        "Example:\n`/save_scenario_Summer_2025`",
        parse_mode="Markdown"
    )

    @router.message(F.text.startswith("/save_scenario"))
    async def save_scenario(message: Message, state: FSMContext):
        args = message.text.split(" ", 1)
        if len(args) < 2:
            await message.answer("❌ Please provide a name. Example:\n`/save_scenario Summer Plan`",
                                 parse_mode="Markdown")
            return

        name = args[1].strip()
        data = await state.get_data()
        required_keys = {"months", "income_change", "fixed_change", "savings_goal", "extra_expenses"}

        if not required_keys.issubset(data.keys()):
            await message.answer("❌ No forecast data available. Please run /forecast first.")
            return

        scenario = None
        try:
            scenario = await create_forecast_scenario(
                telegram_id=message.from_user.id,
                name=name,
                months=data["months"],
                income_changes=data["income_change"],
                fixed_changes=data["fixed_change"],
                savings_goal=data["savings_goal"],
                extra_expenses=data["extra_expenses"]
            )
        finally:
            await state.clear()

        if scenario:
            await state.update_data(latest_forecast=scenario)
            await message.answer(
                "💾 Would you like to save this scenario?\nSend /save_scenario followed by a name.\n"
                "Example:\n`/save_scenario Summer 2025`",
                parse_mode="Markdown"
            )
        else:
            await message.answer("❌ Forecast creation failed.")

@router.message(F.text.startswith("/save_scenario"))
async def save_scenario(message: Message, state: FSMContext):
    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.answer("❌ Please provide a name. Example:\n`/save_scenario Summer Plan`", parse_mode="Markdown")
        return

    name = args[1].strip()
    data = await state.get_data()
    required_keys = {"months", "income_change", "fixed_change", "savings_goal", "extra_expenses", "latest_forecast"}

    if not required_keys.issubset(data.keys()):
        await message.answer("❌ No forecast data available. Please run /forecast first.")
        return

    try:
        scenario = await create_forecast_scenario(
            telegram_id=message.from_user.id,
            name=name,
            months=data["months"],
            income_changes=data["income_change"],
            fixed_changes=data["fixed_change"],
            savings_goal=data["savings_goal"],
            extra_expenses=data["extra_expenses"]
        )
        await message.answer(f"✅ Scenario '{scenario.name}' saved successfully!")
    except PermissionError:
        await message.answer("🚫 Only premium users can save scenarios.")

@router.message(Command("my_scenarios"))
async def list_scenarios(message: Message):
    scenarios = await get_user_forecast_scenarios(message.from_user.id)
    if not scenarios:
        await message.answer("📭 You have no saved scenarios.")
        return

    lines = ["📋 *Your Forecast Scenarios:*"]
    async with async_session() as session:
        for s in scenarios:
            # Получаем текущие накопления
            result = await session.execute(
                select(SavingsBalance).where(SavingsBalance.user_id == s.user_id)
            )
            savings = result.scalar()
            current_savings = savings.amount if savings else 0.0

            # Расчёт дневного бюджета с учётом накоплений
            total_days = s.months * 30
            adjusted_daily = (
                (s.total_free + current_savings) / total_days if total_days > 0 else 0.0
            )

            # Парсинг одноразовых расходов
            extras = []
            for item in s.extra_expenses:
                name = item.get("name", "Unknown")
                amount = item.get("amount", 0.0)
                extras.append(f"{name} = €{amount:.0f}")
            extras_text = ", ".join(extras) if extras else "—"

            # Формирование блока вывода
            lines.append(
                f"🆔 {s.id} — *{s.name}* ({s.months} months)\n"
                f"💰 Free Cash: €{s.total_free:.2f}\n"
                f"💾 Current Savings: €{current_savings:.2f}\n"
                f"📦 Savings (Goal): €{s.projected_savings:.2f}\n"
                f"📆 Daily Budget (w/ savings): €{adjusted_daily:.2f}\n"
                f"🛫 One-time Expenses: {extras_text}"
            )

    await message.answer("\n\n".join(lines), parse_mode="Markdown")


@router.message(F.text.startswith("/delete_scenario"))
async def delete_scenario_cmd(message: Message):
    parts = message.text.strip().split(" ")
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("❌ Use: /delete_scenario <scenario_id>")
        return

    scenario_id = int(parts[1])
    success = await delete_forecast_scenario(scenario_id, message.from_user.id)
    if success:
        await message.answer(f"🗑 Scenario {scenario_id} deleted.")
    else:
        await message.answer("❌ Failed to delete scenario. Make sure it exists and belongs to you.")

@router.message(Command("my_scenarios"))
async def interactive_list_scenarios(message: Message):
    scenarios = await get_user_forecast_scenarios(message.from_user.id)
    if not scenarios:
        await message.answer("📭 You have no saved scenarios.")
        return

    buttons = []
    for s in scenarios:
        buttons.append([
            InlineKeyboardButton(
                text=f"{s.name} ({s.months}m)",
                callback_data=f"view_scenario_{s.id}"
            ),
            InlineKeyboardButton(
                text="❌",
                callback_data=f"delete_scenario_{s.id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("📋 *Your Scenarios:*", parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data.startswith("view_scenario_"))
async def view_scenario(callback: CallbackQuery):
    scenario_id = int(callback.data.split("_")[-1])
    scenarios = await get_user_forecast_scenarios(callback.from_user.id)
    scenario = next((s for s in scenarios if s.id == scenario_id), None)

    if not scenario:
        await callback.message.answer("❌ Scenario not found.")
        await callback.answer()
        return

    await callback.message.answer(
        f"🔍 *{scenario.name}* ({scenario.months} months)\n\n"
        f"💶 Income Δ: €{scenario.income_changes:.2f}\n"
        f"🏠 Fixed Δ: €{scenario.fixed_changes:.2f}\n"
        f"💰 Savings/month: €{scenario.projected_savings / scenario.months:.2f}\n\n"
        f"📉 Total Free: €{scenario.total_free:.2f}\n"
        f"📆 Daily Budget: €{scenario.daily_budget:.2f}",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delete_scenario_"))
async def delete_scenario_inline(callback: CallbackQuery):
    scenario_id = int(callback.data.split("_")[-1])
    success = await delete_forecast_scenario(scenario_id, callback.from_user.id)

    if success:
        await callback.message.edit_text("🗑 Scenario deleted.")
    else:
        await callback.message.answer("❌ Could not delete scenario.")
    await callback.answer()

@router.message(Command("forecast_help"))
async def forecast_help(message: Message):
    await message.answer(
        "🧮 *Forecast Planning Help*\n\n"
        "/forecast — start new planning session\n"
        "/my_scenarios — list your saved scenarios\n"
        "/save_scenario <name> — save your current forecast\n"
        "/delete_scenario <id> — delete a saved scenario\n\n"
        "Forecasting is available only for premium users.",
        parse_mode="Markdown"
    )