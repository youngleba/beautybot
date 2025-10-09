from aiogram import Dispatcher
from app.handlers.client import booking, profile
from app.handlers.master import master_panel, offdays, records_management
from app.handlers.loyalty import points_system

def register_handlers(dp: Dispatcher):
    dp.include_router(booking.router)
    dp.include_router(profile.router)
    dp.include_router(master_panel.router)
    dp.include_router(offdays.router)
    dp.include_router(records_management.router)
    dp.include_router(points_system.router)
