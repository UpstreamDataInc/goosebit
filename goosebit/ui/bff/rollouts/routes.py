from fastapi import APIRouter, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.auth import validate_user_permissions
from goosebit.db.models import Rollout

from ..responses import StatusResponse
from .requests import RolloutsDeleteRequest, RolloutsPatchRequest, RolloutsPutRequest
from .responses import BFFRolloutsResponse, RolloutsPutResponse

router = APIRouter(prefix="/rollouts")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["rollout.read"])],
)
async def rollouts_get(request: Request) -> BFFRolloutsResponse:
    def search_filter(search_value):
        return Q(name__icontains=search_value) | Q(feed__icontains=search_value)

    query = Rollout.all().prefetch_related("software")
    total_records = await Rollout.all().count()

    return await BFFRolloutsResponse.convert(request, query, search_filter, total_records)


@router.post(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.WRITE])],
)
async def rollouts_put(_: Request, rollout: RolloutsPutRequest) -> RolloutsPutResponse:
    rollout = await Rollout.create(
        name=rollout.name,
        feed=rollout.feed,
        software_id=rollout.software_id,
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
