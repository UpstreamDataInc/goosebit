from fastapi import APIRouter, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.api.responses import StatusResponse
from goosebit.auth import validate_user_permissions
from goosebit.models import Rollout
from goosebit.permissions import Permissions

from .requests import (
    CreateRolloutsRequest,
    DeleteRolloutsRequest,
    UpdateRolloutsRequest,
)
from .responses import CreateRolloutResponse, RolloutsAllResponse, RolloutsTableResponse

router = APIRouter(prefix="/rollouts", tags=["rollouts"])


@router.get(
    "/table",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.READ])],
)
async def rollouts_get_table(request: Request) -> RolloutsTableResponse:
    def search_filter(search_value):
        return Q(name__icontains=search_value) | Q(feed__icontains=search_value)

    query = Rollout.all().prefetch_related("firmware")
    total_records = await Rollout.all().count()

    return await RolloutsTableResponse.parse(request, query, search_filter, total_records)


@router.get(
    "/all",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.READ])],
)
async def rollouts_get_all(_: Request) -> RolloutsAllResponse:
    return await RolloutsAllResponse.parse(await Rollout.all().prefetch_related("firmware"))


@router.post(
    "/create",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.WRITE])],
)
async def rollouts_create(_: Request, rollout: CreateRolloutsRequest) -> CreateRolloutResponse:
    rollout = await Rollout.create(
        name=rollout.name,
        feed=rollout.feed,
        firmware_id=rollout.firmware_id,
    )
    return CreateRolloutResponse(success=True, id=rollout.id)


@router.post(
    "/update",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.WRITE])],
)
async def rollouts_update(_: Request, rollouts: UpdateRolloutsRequest) -> StatusResponse:
    await Rollout.filter(id__in=rollouts.ids).update(paused=rollouts.paused)
    return StatusResponse(success=True)


@router.post(
    "/delete",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.DELETE])],
)
async def rollouts_delete(_: Request, rollouts: DeleteRolloutsRequest) -> StatusResponse:
    await Rollout.filter(id__in=rollouts.ids).delete()
    return StatusResponse(success=True)
