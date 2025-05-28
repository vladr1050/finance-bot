from .entry import entry_router
from .save import save_router
from .view import view_router
from .help import help_router

forecast_router = (
    entry_router
    .include_router(save_router)
    .include_router(view_router)
    .include_router(help_router)
)
