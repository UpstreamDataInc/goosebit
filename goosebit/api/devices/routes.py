from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.api.devices.models import (
    DeleteDevicesRequest,
    DeviceAllResponse,
    DeviceTableResponse,
    ForceUpdateDevicesRequest,
    LogsDeviceResponse,
    UpdateDevicesRequest,
)
from goosebit.api.model import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.models import Device, Firmware, UpdateModeEnum, UpdateStateEnum
from goosebit.permissions import Permissions
from goosebit.updater.manager import delete_devices, get_update_manager

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get(
    "/all",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.HOME.READ])],
)
async def devices_get_all(_: Request) -> DeviceAllResponse:
    return await DeviceAllResponse.parse(await Device.all().prefetch_related("assigned_firmware", "hardware"))


@router.get(
    "/table",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.HOME.READ])],
)
async def devices_get_table(request: Request) -> DeviceTableResponse:
    def search_filter(search_value):
        return (
            Q(uuid__icontains=search_value)
            | Q(name__icontains=search_value)
            | Q(feed__icontains=search_value)
            | Q(update_mode__icontains=UpdateModeEnum.from_str(search_value))
            | Q(last_state__icontains=UpdateStateEnum.from_str(search_value))
        )

    query = Device.all().prefetch_related("assigned_firmware", "hardware")
    total_records = await Device.all().count()

    return await DeviceTableResponse.parse(request, query, search_filter, total_records)


@router.post(
    "/update",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.DEVICE.WRITE])],
)
async def devices_update(_: Request, config: UpdateDevicesRequest) -> StatusResponse:
    for uuid in config.devices:
        updater = await get_update_manager(uuid)
        if config.firmware is not None:
            if config.firmware == "rollout":
                await updater.update_update(UpdateModeEnum.ROLLOUT, None)
            elif config.firmware == "latest":
                await updater.update_update(UpdateModeEnum.LATEST, None)
            else:
                firmware = await Firmware.get_or_none(id=config.firmware)
                await updater.update_update(UpdateModeEnum.ASSIGNED, firmware)
        if config.pinned is not None:
            await updater.update_update(UpdateModeEnum.PINNED, None)
        if config.name is not None:
            await updater.update_name(config.name)
        if config.feed is not None:
            await updater.update_feed(config.feed)
    return StatusResponse(success=True)


@router.post(
    "/force_update",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.DEVICE.WRITE])],
)
async def devices_force_update(_: Request, config: ForceUpdateDevicesRequest) -> StatusResponse:
    for uuid in config.devices:
        updater = await get_update_manager(uuid)
        await updater.update_force_update(True)
    return StatusResponse(success=True)


@router.get(
    "/logs/{dev_id}",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.HOME.READ])],
)
async def device_logs(_: Request, dev_id: str) -> LogsDeviceResponse:
    updater = await get_update_manager(dev_id)
    device = await updater.get_device()
    return LogsDeviceResponse(log=device.last_log)


@router.post(
    "/delete",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.DEVICE.DELETE])],
)
async def devices_delete(_: Request, config: DeleteDevicesRequest) -> StatusResponse:
    await delete_devices(config.devices)
    return StatusResponse(success=True)
