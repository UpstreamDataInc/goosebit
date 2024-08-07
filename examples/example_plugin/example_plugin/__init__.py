from goosebit.api.routes import router as api_router
from goosebit.ui import router as ui_router

from . import api, ui

api_router.include_router(api.router)
ui_router.include_router(ui.router)
