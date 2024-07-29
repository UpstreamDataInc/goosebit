from fastapi import APIRouter, Security
from fastapi.requests import Request
from pydantic import BaseModel

from goosebit.auth import validate_user_permissions
from goosebit.models import Rollout
from goosebit.permissions import Permissions

router = APIRouter(prefix="/rollouts")


@router.get(
    "/all",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.READ])
    ],
)
async def rollouts_get_all() -> list[dict]:
    def parse(rollout: Rollout) -> dict:
        return {
            "id": rollout.id,
            "created_at": rollout.created_at,
            "name": rollout.name,
            "feed": rollout.feed,
            "flavor": rollout.flavor,
            "fw_file": rollout.firmware.path.name,
            "paused": rollout.paused,
            "success_count": rollout.success_count,
            "failure_count": rollout.failure_count,
        }

    rollouts = await Rollout.all().prefetch_related("firmware")
    return list([parse(r) for r in rollouts])


class CreateRolloutsModel(BaseModel):
    name: str
    feed: str
    flavor: str
    firmware_id: int


@router.post(
    "/",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.WRITE])
    ],
)
async def rollouts_create(_: Request, rollout: CreateRolloutsModel) -> dict:
    await Rollout.create(
        name=rollout.name,
        feed=rollout.feed,
        flavor=rollout.flavor,
        firmware_id=rollout.firmware_id,
    )
    return {"success": True}


class UpdateRolloutsModel(BaseModel):
    ids: list[int]
    paused: bool


@router.post(
    "/update",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.WRITE])
    ],
)
async def rollouts_update(_: Request, rollouts: UpdateRolloutsModel) -> dict:
    await Rollout.filter(id__in=rollouts.ids).update(paused=rollouts.paused)
    return {"success": True}


class DeleteRolloutsModel(BaseModel):
    ids: list[int]


@router.post(
    "/delete",
    dependencies=[
        Security(validate_user_permissions, scopes=[Permissions.ROLLOUT.DELETE])
    ],
)
async def rollouts_delete(_: Request, rollouts: DeleteRolloutsModel) -> dict:
    await Rollout.filter(id__in=rollouts.ids).delete()
    return {"success": True}
