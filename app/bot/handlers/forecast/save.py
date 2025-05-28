from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from app.db.database import async_session
from app.db.models import User, FixedExpense, SavingsBalance
from app.forecast.logic import calculate_forecast
from app.forecast.services import create_forecast_scenario
from app.bot.handlers.forecast.states import ForecastScenarioFSM

save_router = Router()

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

        result = await session.execute(
            select(SavingsBalance).where(SavingsBalance.user_id == user.id)
        )
        savings = result.scalar()
        savings_amount = savings.amount if savings else 0.0

        forecast["savings_balance"] = savings_amount
        forecast["total_free_including_savings"] = forecast["total_free"] + savings_amount

        total_days = data["months"] * 30
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
        "Send `/save_scenario YourNameHere`",
        parse_mode="Markdown"
    )


@save_router.message(F.text.startswith("/save_scenario"))
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
        await state.clear()
    except PermissionError:
        await message.answer("🚫 Only premium users can save scenarios.")
