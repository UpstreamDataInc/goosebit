from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request

from example_plugin.schema import ExamplePluginShow
from example_plugin.settings import config
from goosebit.auth import validate_user_permissions
from goosebit.db.models import Device, Software

from .responses import ExampleResponse

router = APIRouter(prefix="/example", tags=["example"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["example.read"])],
)
async def example_get(_: Request) -> ExampleResponse:
    data = {}

    if ExamplePluginShow.DEVICE_COUNT in config.example_plugin_show:
        data["device_count"] = await Device.all().count()
    if ExamplePluginShow.SOFTWARE_COUNT in config.example_plugin_show:
        data["software_count"] = await Software.all().count()

    return ExampleResponse(**data)
