from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.api.responses import StatusResponse
from goosebit.api.v1.devices import routes
from goosebit.auth import validate_user_permissions
from goosebit.db.models import Device, Software, UpdateModeEnum, UpdateStateEnum
from goosebit.updater.manager import get_update_manager

from .requests import DevicesPatchRequest
from .responses import BFFDeviceResponse

router = APIRouter(prefix="/devices")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["home.read"])],
)
async def devices_get(request: Request) -> BFFDeviceResponse:
    def search_filter(search_value):
        return (
            Q(uuid__icontains=search_value)
            | Q(name__icontains=search_value)
            | Q(feed__icontains=search_value)
            | Q(sw_version__icontains=search_value)
            | Q(update_mode=int(UpdateModeEnum.from_str(search_value)))
            | Q(last_state=int(UpdateStateEnum.from_str(search_value)))
        )

    query = Device.all().prefetch_related("assigned_software", "hardware")
    total_records = await Device.all().count()

    return await BFFDeviceResponse.convert(request, query, search_filter, total_records)


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


router.add_api_route(
    "",
    routes.devices_delete,
    methods=["DELETE"],
    dependencies=[Security(validate_user_permissions, scopes=["device.delete"])],
    name="bff_devices_delete",
)
