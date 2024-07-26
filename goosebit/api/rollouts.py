from __future__ import annotations

from fastapi import APIRouter, Security

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
            "fw_file": rollout.firmware.uri,
            "paused": rollout.paused,
            "success_count": rollout.success_count,
            "failure_count": rollout.failure_count,
        }

    rollouts = await Rollout.all().prefetch_related("firmware")
    return list([parse(r) for r in rollouts])
