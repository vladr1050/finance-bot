from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from bot.handlers.forecast.states import ForecastScenarioFSM

help_router = Router()

@help_router.message(Command("forecast_help"))
async def forecast_help(message: Message):
    await message.answer(
        "🧮 *Forecast Planning Help*\n\n"
        "/forecast — start a new planning session\n"
        "/my_scenarios — list your saved forecast scenarios\n"
        "/save_scenario <name> — save the current forecast\n"
        "/delete_scenario <id> — delete a saved forecast scenario\n\n"
        "Forecasting is available only for premium users.",
        parse_mode="Markdown"
    )
