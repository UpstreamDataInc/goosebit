import time
from typing import Any

from fastapi import APIRouter, Security
from fastapi.requests import Request
from pydantic import BaseModel
from tortoise.expressions import Q

from goosebit.api.helper import filter_data
from goosebit.auth import validate_user_permissions
from goosebit.models import Device, Firmware, UpdateModeEnum, UpdateStateEnum
from goosebit.permissions import Permissions
from goosebit.updater.manager import delete_devices, get_update_manager

router = APIRouter(prefix="/devices")


@router.get(
    "/all",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.HOME.READ])],
)
async def devices_get_all(request: Request) -> dict[str, int | list[Any] | Any]:
    query = Device.all().prefetch_related("assigned_firmware", "hardware")

    def search_filter(search_value):
        return (
            Q(uuid__icontains=search_value)
            | Q(name__icontains=search_value)
            | Q(feed__icontains=search_value)
            | Q(update_mode__icontains=UpdateModeEnum.from_str(search_value))
            | Q(last_state__icontains=UpdateStateEnum.from_str(search_value))
        )

    async def parse(device: Device) -> dict:
        manager = await get_update_manager(device.uuid)
        _, target_firmware = await manager.get_update()
        last_seen = device.last_seen
        if last_seen is not None:
            last_seen = round(time.time() - device.last_seen)
        return {
            "uuid": device.uuid,
            "name": device.name,
            "fw_installed_version": device.fw_version,
            "fw_target_version": (target_firmware.version if target_firmware is not None else None),
            "fw_assigned": (device.assigned_firmware.id if device.assigned_firmware is not None else None),
            "hw_model": device.hardware.model,
            "hw_revision": device.hardware.revision,
            "feed": device.feed,
            "progress": device.progress,
            "state": str(device.last_state),
            "update_mode": str(device.update_mode),
            "force_update": device.force_update,
            "last_ip": device.last_ip,
            "last_seen": last_seen,
            "online": (last_seen < manager.poll_seconds if last_seen is not None else None),
        }

    total_records = await Device.all().count()
    return await filter_data(request, query, search_filter, parse, total_records)


class UpdateDevicesModel(BaseModel):
    devices: list[str]
    firmware: str | None = None
    name: str | None = None
    pinned: bool | None = None
    feed: str | None = None


@router.post(
    "/update",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.DEVICE.WRITE])],
)
async def devices_update(_: Request, config: UpdateDevicesModel) -> dict:
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
    return {"success": True}


class ForceUpdateModel(BaseModel):
    devices: list[str]


@router.post(
    "/force_update",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.DEVICE.WRITE])],
)
async def devices_force_update(_: Request, config: ForceUpdateModel) -> dict:
    for uuid in config.devices:
        updater = await get_update_manager(uuid)
        await updater.update_force_update(True)
    return {"success": True}


@router.get(
    "/logs/{dev_id}",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.HOME.READ])],
)
async def device_logs(_: Request, dev_id: str) -> str:
    updater = await get_update_manager(dev_id)
    device = await updater.get_device()
    if device.last_log is not None:
        return device.last_log
    return "No logs found."


class DeleteModel(BaseModel):
    devices: list[str]


@router.post(
    "/delete",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.DEVICE.DELETE])],
)
async def devices_delete(_: Request, config: DeleteModel) -> dict:
    await delete_devices(config.devices)
    return {"success": True}
