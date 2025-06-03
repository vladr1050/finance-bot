# app/bot/handlers/income/__init__.py

from aiogram import Router
from .add import income_add_router
from .edit import income_edit_router
from .view import income_view_router

income_router = Router()
income_router.include_router(income_add_router)
income_router.include_router(income_edit_router)
income_router.include_router(income_view_router)
