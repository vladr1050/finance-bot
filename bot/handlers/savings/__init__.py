from aiogram import Router
from .add import savings_add_router
from .set import savings_set_router
from .view import savings_view_router
from .edit import savings_edit_router

savings_router = Router()
savings_router.include_router(savings_add_router)
savings_router.include_router(savings_set_router)
savings_router.include_router(savings_view_router)
savings_router.include_router(savings_edit_router)