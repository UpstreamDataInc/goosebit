from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from goosebit.schema.plugins import PluginSchema

from . import api, ui


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


example_plugin_router = APIRouter(lifespan=lifespan)
example_plugin_router.include_router(ui.router)
example_plugin_router.include_router(api.router)

config = PluginSchema(
    router=example_plugin_router,
    static_files=ui.static,
    templates=ui.templates,
)
