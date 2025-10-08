from aiogram import Dispatcher
from . import handlers
from .master import master_panel
from .client import booking  # добавлено
from .loyalty import points_system

def register_handlers(dp: Dispatcher):
    dp.include_router(handlers.router)
    dp.include_router(master_panel.router)
    dp.include_router(booking.router)
    dp.include_router(points_system.router)
