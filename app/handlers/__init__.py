from aiogram import Dispatcher
from . import handlers
from .master import master_panel

def register_handlers(dp: Dispatcher):
    dp.include_router(handlers.router)
    dp.include_router(master_panel.router)
