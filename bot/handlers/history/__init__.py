from aiogram import Router

from .view import router as view_history_router
from .delete import router as delete_expense_router
from .edit import router as edit_expense_router
from .range import router as range_history_router
from .categories import router as category_report_router

history_router = Router()
history_router.include_router(view_history_router)
history_router.include_router(delete_expense_router)
history_router.include_router(edit_expense_router)
history_router.include_router(range_history_router)
history_router.include_router(category_report_router)
