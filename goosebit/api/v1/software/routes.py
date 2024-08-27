from fastapi import APIRouter, HTTPException, Security
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.models import Rollout, Software
from goosebit.permissions import Permissions

from .requests import SoftwareDeleteRequest
from .responses import SoftwareResponse

router = APIRouter(prefix="/software", tags=["software"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.SOFTWARE.READ])],
)
async def software_get(_: Request) -> SoftwareResponse:
    return await SoftwareResponse.convert(await Software.all().prefetch_related("compatibility"))


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.SOFTWARE.DELETE])],
)
async def software_delete(_: Request, config: SoftwareDeleteRequest) -> StatusResponse:
    success = False
    for f_id in config.root:
        software = await Software.get_or_none(id=f_id)

        if software is None:
            continue

        rollout_count = await Rollout.filter(software=software).count()
        if rollout_count > 0:
            raise HTTPException(409, "Software is referenced by rollout")

        if software.local:
            path = software.path
            if path.exists():
                path.unlink()

        await software.delete()
        success = True
    return StatusResponse(success=success)
