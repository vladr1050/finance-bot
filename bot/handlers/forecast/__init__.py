from aiogram import Router

from .entry import router as entry_router
from .save import router as save_router
from .view import router as view_router
from .delete import router as delete_router

forecast_router = Router()
forecast_router.include_router(entry_router)
forecast_router.include_router(save_router)
forecast_router.include_router(view_router)
forecast_router.include_router(delete_router)
