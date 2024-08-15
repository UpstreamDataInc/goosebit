from fastapi import APIRouter, HTTPException, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.models import Firmware, Rollout
from goosebit.permissions import Permissions

from .requests import DeleteFirmwareRequest
from .responses import FirmwareAllResponse, FirmwareTableResponse

router = APIRouter(prefix="/firmware", tags=["firmware"])


@router.get(
    "/all",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])],
)
async def firmware_get_all(_: Request) -> FirmwareAllResponse:
    return await FirmwareAllResponse.convert(await Firmware.all().prefetch_related("compatibility"))


@router.get(
    "/table",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])],
)
async def firmware_get_table(request: Request) -> FirmwareTableResponse:
    def search_filter(search_value):
        return Q(uri__icontains=search_value) | Q(version__icontains=search_value)

    query = Firmware.all().prefetch_related("compatibility")
    total_records = await Firmware.all().count()

    return await FirmwareTableResponse.convert(request, query, search_filter, total_records)


@router.post(
    "/delete",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.DELETE])],
)
async def firmware_delete(_: Request, config: DeleteFirmwareRequest) -> StatusResponse:
    success = False
    for f_id in config.files:
        firmware = await Firmware.get_or_none(id=f_id)

        if firmware is None:
            continue

        rollout_count = await Rollout.filter(firmware=firmware).count()
        if rollout_count > 0:
            raise HTTPException(409, "Firmware is referenced by rollout")

        if firmware.local:
            path = firmware.path
            if path.exists():
                path.unlink()

        await firmware.delete()
        success = True
    return StatusResponse(success=success)
