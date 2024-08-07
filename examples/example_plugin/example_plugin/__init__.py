from goosebit.api.routes import router as api_router
from goosebit.ui import router as ui_router
from goosebit.ui.static import router as static_router

from . import api, static, ui

api_router.include_router(api.router)
ui_router.include_router(ui.router)
static_router.mount(path="/example_plugin", name="example_plugin_static", app=static.static)
