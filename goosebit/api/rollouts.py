from fastapi import APIRouter, Security
from fastapi.requests import Request
from pydantic import BaseModel
from tortoise.expressions import Q

from goosebit.api.helper import filter_data
from goosebit.auth import validate_user_permissions
from goosebit.models import Rollout
from goosebit.permissions import Permissions

router = APIRouter(prefix="/rollouts")


@router.get(
    "/all",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.READ])],
)
async def rollouts_get_all(request: Request) -> dict[str, int | list[dict]]:
    query = Rollout.all().prefetch_related("firmware")

    def search_filter(search_value):
        return Q(name__icontains=search_value) | Q(feed__icontains=search_value) | Q(flavor__icontains=search_value)

    async def parse(rollout: Rollout) -> dict:
        return {
            "id": rollout.id,
            "created_at": int(rollout.created_at.timestamp() * 1000),
            "name": rollout.name,
            "feed": rollout.feed,
            "flavor": rollout.flavor,
            "fw_file": rollout.firmware.path.name,
            "fw_version": rollout.firmware.version,
            "paused": rollout.paused,
            "success_count": rollout.success_count,
            "failure_count": rollout.failure_count,
        }

    total_records = await Rollout.all().count()
    return await filter_data(request, query, search_filter, parse, total_records)


class CreateRolloutsModel(BaseModel):
    name: str
    feed: str
    flavor: str
    firmware_id: int


@router.post(
    "/",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.WRITE])],
)
async def rollouts_create(_: Request, rollout: CreateRolloutsModel) -> dict:
    rollout = await Rollout.create(
        name=rollout.name,
        feed=rollout.feed,
        flavor=rollout.flavor,
        firmware_id=rollout.firmware_id,
    )
    return {"success": True, "id": rollout.id}


class UpdateRolloutsModel(BaseModel):
    ids: list[int]
    paused: bool


@router.post(
    "/update",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.WRITE])],
)
async def rollouts_update(_: Request, rollouts: UpdateRolloutsModel) -> dict:
    await Rollout.filter(id__in=rollouts.ids).update(paused=rollouts.paused)
    return {"success": True}


class DeleteRolloutsModel(BaseModel):
    ids: list[int]


@router.post(
    "/delete",
    dependencies=[Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.DELETE])],
)
async def rollouts_delete(_: Request, rollouts: DeleteRolloutsModel) -> dict:
    await Rollout.filter(id__in=rollouts.ids).delete()
    return {"success": True}
