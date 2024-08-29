from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.db.models import Device
from goosebit.updater.manager import delete_devices

from . import device
from .requests import DevicesDeleteRequest
from .responses import DevicesResponse

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["home.read"])],
)
async def devices_get(_: Request) -> DevicesResponse:
    return await DevicesResponse.convert(await Device.all().prefetch_related("assigned_software", "hardware"))


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["device.delete"])],
)
async def devices_delete(_: Request, config: DevicesDeleteRequest) -> StatusResponse:
    await delete_devices(config.devices)
    return StatusResponse(success=True)


router.include_router(device.router)
