from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.models import Device, Software, UpdateModeEnum
from goosebit.updater.manager import delete_devices, get_update_manager

from . import device
from .requests import DevicesDeleteRequest, DevicesPatchRequest
from .responses import DevicesResponse

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["home.read"])],
)
async def devices_get(_: Request) -> DevicesResponse:
    return await DevicesResponse.convert(await Device.all().prefetch_related("assigned_software", "hardware"))


@router.patch(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["device.write"])],
)
async def devices_patch(_: Request, config: DevicesPatchRequest) -> StatusResponse:
    for uuid in config.devices:
        updater = await get_update_manager(uuid)
        if config.software is not None:
            if config.software == "rollout":
                await updater.update_update(UpdateModeEnum.ROLLOUT, None)
            elif config.software == "latest":
                await updater.update_update(UpdateModeEnum.LATEST, None)
            else:
                software = await Software.get_or_none(id=config.software)
                await updater.update_update(UpdateModeEnum.ASSIGNED, software)
        if config.pinned is not None:
            await updater.update_update(UpdateModeEnum.PINNED, None)
        if config.name is not None:
            await updater.update_name(config.name)
        if config.feed is not None:
            await updater.update_feed(config.feed)
        if config.force_update is not None:
            await updater.update_force_update(config.force_update)
    return StatusResponse(success=True)


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["device.delete"])],
)
async def devices_delete(_: Request, config: DevicesDeleteRequest) -> StatusResponse:
    await delete_devices(config.devices)
    return StatusResponse(success=True)


router.include_router(device.router)
