from fastapi import APIRouter, Security
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.models import Rollout
from goosebit.permissions import Permissions

from .requests import RolloutsDeleteRequest, RolloutsPatchRequest, RolloutsPutRequest
from .responses import RolloutsPutResponse, RolloutsResponse

router = APIRouter(prefix="/rollouts", tags=["rollouts"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.READ])],
)
async def rollouts_get(_: Request) -> RolloutsResponse:
    return await RolloutsResponse.convert(await Rollout.all().prefetch_related("firmware"))


@router.post(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.WRITE])],
)
async def rollouts_put(_: Request, rollout: RolloutsPutRequest) -> RolloutsPutResponse:
    rollout = await Rollout.create(
        name=rollout.name,
        feed=rollout.feed,
        firmware_id=rollout.firmware_id,
    )
    return RolloutsPutResponse(success=True, id=rollout.id)


@router.patch(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.WRITE])],
)
async def rollouts_patch(_: Request, rollouts: RolloutsPatchRequest) -> StatusResponse:
    await Rollout.filter(id__in=rollouts.ids).update(paused=rollouts.paused)
    return StatusResponse(success=True)


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.DELETE])],
)
async def rollouts_delete(_: Request, rollouts: RolloutsDeleteRequest) -> StatusResponse:
    await Rollout.filter(id__in=rollouts.ids).delete()
    return StatusResponse(success=True)
