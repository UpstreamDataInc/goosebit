from __future__ import annotations

import asyncio

from fastapi import APIRouter, Security
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.db.models import Device
from goosebit.device_manager import delete_devices, get_update_manager
from goosebit.schema.devices import DeviceSchema
from goosebit.schema.software import SoftwareSchema

from . import device
from .requests import DevicesDeleteRequest
from .responses import DevicesResponse

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["device.read"])],
)
async def devices_get(_: Request) -> DevicesResponse:
    devices = await Device.all().prefetch_related("hardware", "assigned_software", "assigned_software__compatibility")
    response = DevicesResponse(devices=devices)

    async def set_assigned_sw(d: DeviceSchema):
        updater = await get_update_manager(d.uuid)
        _, target = await updater.get_update()
        if target is not None:
            await target.fetch_related("compatibility")
            d.assigned_software = SoftwareSchema.model_validate(target)
        return d

    response.devices = await asyncio.gather(*[set_assigned_sw(d) for d in response.devices])
    return response


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["device.delete"])],
)
async def devices_delete(_: Request, config: DevicesDeleteRequest) -> StatusResponse:
    await delete_devices(config.devices)
    return StatusResponse(success=True)


router.include_router(device.router)
