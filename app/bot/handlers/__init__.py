from aiogram import Router

from .entry import forecast_entry_router
from .save import forecast_save_router
from .view import forecast_view_router
from .help import forecast_help_router

forecast_router = Router()
forecast_router.include_router(forecast_entry_router)
forecast_router.include_router(forecast_save_router)
forecast_router.include_router(forecast_view_router)
forecast_router.include_router(forecast_help_router)
