from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from goosebit.schema.plugins import PluginSchema

from . import api, ui


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    yield


simple_stats_router = APIRouter(lifespan=lifespan)
simple_stats_router.include_router(ui.router)  # type: ignore[attr-defined]
simple_stats_router.include_router(api.router)  # type: ignore[attr-defined]

config = PluginSchema(
    router=simple_stats_router,
    static_files=ui.static,  # type: ignore[attr-defined]
    templates=ui.templates,  # type: ignore[attr-defined]
)
