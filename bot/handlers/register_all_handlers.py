from aiogram import Dispatcher
from .start import start_router
from .income import income_router
from .expenses import expenses_router
from .forecast import forecast_router
from .savings import savings_router
from .fixed import fixed_router
from .adjustments import adjustments_router
from .history import history_router

from .auth.registration import router as registration_router
from .auth.login import router as login_router

def register_all_handlers(dp: Dispatcher):
    dp.include_router(registration_router)
    dp.include_router(login_router)
    dp.include_router(start_router)
    dp.include_router(income_router)
    dp.include_router(expenses_router)
    dp.include_router(forecast_router)
    dp.include_router(savings_router)
    dp.include_router(fixed_router)
    dp.include_router(adjustments_router)
    dp.include_router(history_router)
