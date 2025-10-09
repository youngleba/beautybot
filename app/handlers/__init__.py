from aiogram import Dispatcher
from app.handlers.client import booking
from app.handlers.master import master_panel

def register_handlers(dp: Dispatcher):
    dp.include_router(booking.router)
    dp.include_router(master_panel.router)
