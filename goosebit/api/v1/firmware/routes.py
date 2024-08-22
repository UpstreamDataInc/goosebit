from fastapi import APIRouter, HTTPException, Security
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.models import Firmware, Rollout
from goosebit.permissions import Permissions

from .requests import FirmwareDeleteRequest
from .responses import FirmwareResponse

router = APIRouter(prefix="/firmware", tags=["firmware"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.READ])],
)
async def firmware_get(_: Request) -> FirmwareResponse:
    return await FirmwareResponse.convert(await Firmware.all().prefetch_related("compatibility"))


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.FIRMWARE.DELETE])],
)
async def firmware_delete(_: Request, config: FirmwareDeleteRequest) -> StatusResponse:
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
