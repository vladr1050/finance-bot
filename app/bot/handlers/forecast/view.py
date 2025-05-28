from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.forecast.services import get_user_forecast_scenarios, delete_forecast_scenario
from app.db.database import async_session
from app.db.models import SavingsBalance
from sqlalchemy import select
from app.bot.handlers.forecast.states import ForecastScenarioFSM

view_router = Router()


@view_router.message(F.text.startswith("/my_scenarios"))
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


@view_router.callback_query(F.data.startswith("view_scenario_"))
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


@view_router.callback_query(F.data.startswith("delete_scenario_"))
async def delete_scenario_inline(callback: CallbackQuery):
    scenario_id = int(callback.data.split("_")[-1])
    success = await delete_forecast_scenario(scenario_id, callback.from_user.id)

    if success:
        await callback.message.edit_text("🗑 Scenario deleted.")
    else:
        await callback.message.answer("❌ Could not delete scenario.")
    await callback.answer()
