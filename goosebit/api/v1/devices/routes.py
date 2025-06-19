from __future__ import annotations

import asyncio
from http.client import HTTPException

from fastapi import APIRouter, Security
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db.models import Device, Software, UpdateModeEnum
from goosebit.device_manager import DeviceManager, get_device
from goosebit.schema.devices import DeviceSchema
from goosebit.schema.software import SoftwareSchema

from . import device
from .requests import DevicesDeleteRequest, DevicesPatchRequest, DevicesPutRequest
from .responses import DevicesResponse

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["read"]()])],
)
async def devices_get(_: Request) -> DevicesResponse:
    devices = await Device.all().prefetch_related("hardware", "assigned_software", "assigned_software__compatibility")
    response = DevicesResponse(devices=devices)

    async def set_assigned_sw(d: DeviceSchema):
        device = await get_device(d.id)
        _, target = await DeviceManager.get_update(device)
        if target is not None:
            await target.fetch_related("compatibility")
            d.assigned_software = SoftwareSchema.model_validate(target)
        return d

    response.devices = await asyncio.gather(*[set_assigned_sw(d) for d in response.devices])
    return response


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["delete"]()])],
)
async def devices_delete(_: Request, config: DevicesDeleteRequest) -> StatusResponse:
    await DeviceManager.delete_devices(config.devices)
    return StatusResponse(success=True)


@router.patch(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["write"]()])],
)
async def devices_patch(_: Request, config: DevicesPatchRequest) -> StatusResponse:
    for dev_id in config.devices:
        if await Device.get_or_none(id=dev_id) is None:
            raise HTTPException(404, f"Device with ID {dev_id} not found")
        device = await DeviceManager.get_device(dev_id)
        if config.feed is not None:
            await DeviceManager.update_feed(device, config.feed)
        if config.software is not None:
            if config.software == "rollout":
                await DeviceManager.update_update(device, UpdateModeEnum.ROLLOUT, None)
            elif config.software == "latest":
                await DeviceManager.update_update(device, UpdateModeEnum.LATEST, None)
            else:
                software = await Software.get_or_none(id=config.software)
                await DeviceManager.update_update(device, UpdateModeEnum.ASSIGNED, software)
        if config.pinned is not None:
            await DeviceManager.update_update(device, UpdateModeEnum.PINNED, None)
        if config.name is not None:
            await DeviceManager.update_name(device, config.name)
        if config.force_update is not None:
            await DeviceManager.update_force_update(device, config.force_update)
        if config.auth_token is not None:
            await DeviceManager.update_auth_token(device, config.auth_token)
    return StatusResponse(success=True)


@router.put(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["write"]()])],
)
async def devices_put(_: Request, config: DevicesPutRequest) -> StatusResponse:
    for dev_id in config.devices:
        device = await DeviceManager.get_device(dev_id)
        if config.feed is not None:
            await DeviceManager.update_feed(device, config.feed)
        if config.software is not None:
            if config.software == "rollout":
                await DeviceManager.update_update(device, UpdateModeEnum.ROLLOUT, None)
            elif config.software == "latest":
                await DeviceManager.update_update(device, UpdateModeEnum.LATEST, None)
            else:
                software = await Software.get_or_none(id=config.software)
                await DeviceManager.update_update(device, UpdateModeEnum.ASSIGNED, software)
        if config.pinned is not None:
            await DeviceManager.update_update(device, UpdateModeEnum.PINNED, None)
        if config.name is not None:
            await DeviceManager.update_name(device, config.name)
        if config.force_update is not None:
            await DeviceManager.update_force_update(device, config.force_update)
        if config.auth_token is not None:
            await DeviceManager.update_auth_token(device, config.auth_token)
    return StatusResponse(success=True)


router.include_router(device.router)
