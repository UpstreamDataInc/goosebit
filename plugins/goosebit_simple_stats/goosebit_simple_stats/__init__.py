from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from goosebit.schema.plugins import PluginSchema

from . import api, ui


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


simple_stats_router = APIRouter(lifespan=lifespan)
simple_stats_router.include_router(ui.router)
simple_stats_router.include_router(api.router)

config = PluginSchema(
    router=simple_stats_router,
    static_files=ui.static,
    templates=ui.templates,
)
