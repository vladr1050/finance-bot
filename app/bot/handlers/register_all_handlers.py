from aiogram import Dispatcher
from .start import start_router
from .income import income_router
from .expenses import expense_router
from .forecast import forecast_router

def register_all_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(income_router)
    dp.include_router(expense_router)
    dp.include_router(forecast_router)
