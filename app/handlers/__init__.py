from aiogram import Dispatcher

from .handlers import register_start_handler
from .client.booking import register_booking_handlers
# from .client.profile import register_profile_handlers  # закомментировано
# from .master.master_panel import register_master_handlers  # закомментировано
# from .master.offdays import register_offdays_handlers  # закомментировано
# from .master.records_management import register_records_handlers  # закомментировано
# from .loyalty.points_system import register_loyalty_handlers  # закомментировано

def register_handlers(dp):
    register_start_handler(dp)
    register_booking_handlers(dp)
    # register_profile_handlers(dp)
    # register_master_handlers(dp)
    # register_offdays_handlers(dp)
    # register_records_handlers(dp)
    # register_loyalty_handlers(dp)
