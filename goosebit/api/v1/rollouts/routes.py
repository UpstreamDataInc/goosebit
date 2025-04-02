from fastapi import APIRouter, HTTPException, Security
from fastapi.requests import Request

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db.models import Rollout, Software

from .requests import RolloutsDeleteRequest, RolloutsPatchRequest, RolloutsPutRequest
from .responses import RolloutsPutResponse, RolloutsResponse

router = APIRouter(prefix="/rollouts", tags=["rollouts"])


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["rollout"]["read"]()])],
)
async def rollouts_get(_: Request) -> RolloutsResponse:
    rollouts = await Rollout.all().prefetch_related("software", "software__compatibility")
    return RolloutsResponse(rollouts=rollouts)


@router.post(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["rollout"]["write"]()])],
)
async def rollouts_put(_: Request, rollout: RolloutsPutRequest) -> RolloutsPutResponse:
    software = await Software.filter(id=rollout.software_id)
    if len(software) == 0:
        raise HTTPException(404, f"No software with ID {rollout.software_id} found")
    rollout = await Rollout.create(
        name=rollout.name,
        feed=rollout.feed,
        software_id=rollout.software_id,
    )
    return RolloutsPutResponse(success=True, id=rollout.id)


@router.patch(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["rollout"]["write"]()])],
)
async def rollouts_patch(_: Request, rollouts: RolloutsPatchRequest) -> StatusResponse:
    await Rollout.filter(id__in=rollouts.ids).update(paused=rollouts.paused)
    return StatusResponse(success=True)


@router.delete(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["rollout"]["delete"]()])],
)
async def rollouts_delete(_: Request, rollouts: RolloutsDeleteRequest) -> StatusResponse:
    await Rollout.filter(id__in=rollouts.ids).delete()
    return StatusResponse(success=True)
