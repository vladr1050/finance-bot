from aiogram import Router

from .add import add_fixed_router
from .view import view_fixed_router
from .edit import edit_fixed_router
from .delete import delete_fixed_router

fixed_router = Router()
fixed_router.include_router(add_fixed_router)
fixed_router.include_router(view_fixed_router)
fixed_router.include_router(edit_fixed_router)
fixed_router.include_router(delete_fixed_router)
