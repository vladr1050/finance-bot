from aiogram import Dispatcher
from .start import start_router
from app.bot.handlers.income.add import income_router
from .expenses import expenses_router
from .forecast import forecast_router
from .savings import savings_router

def register_all_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(income_router)
    dp.include_router(expenses_router)
    dp.include_router(forecast_router)
    dp.include_router(savings_router)
