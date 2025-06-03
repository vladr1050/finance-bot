from aiogram import Router
from .add import router as add_adjustment_router
from .view import router as view_adjustments_router
from .delete import router as delete_adjustments_router

adjustments_router = Router()
adjustments_router.include_router(add_adjustment_router)
adjustments_router.include_router(view_adjustments_router)
adjustments_router.include_router(delete_adjustments_router)
