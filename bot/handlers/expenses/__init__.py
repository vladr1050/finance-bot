from aiogram import Router

from .add import expense_router
from .view import view_expenses_router
from .delete import delete_expense_router
from .edit import edit_expense_router

expenses_router = Router()
expenses_router.include_router(expense_router)
expenses_router.include_router(view_expenses_router)
expenses_router.include_router(delete_expense_router)
expenses_router.include_router(edit_expense_router)
