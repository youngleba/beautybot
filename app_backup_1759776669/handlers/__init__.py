from .start import router as start_router
from .booking import router as booking_router
from .client import router as client_router
from .master_panel import router as master_router

routers = [start_router, booking_router, client_router, master_router]

