from aiogram import Dispatcher
from .start import start_router
from app.bot.handlers.income.add import income_router
from .expenses import expense_router
from .forecast import forecast_router
from .savings import savings_router
from app.bot.handlers.expenses.edit import edit_expense_router
from app.bot.handlers.expenses.delete import delete_expense_router
from app.bot.handlers.expenses.view import view_expenses_router

def register_all_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(income_router)
    dp.include_router(expense_router)
    dp.include_router(forecast_router)
    dp.include_router(savings_router)
    dp.include_router(edit_expense_router)
    dp.include_router(delete_expense_router)
    dp.include_router(view_expenses_router)
