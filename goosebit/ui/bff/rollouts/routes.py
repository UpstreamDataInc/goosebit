from typing import Annotated

from fastapi import APIRouter, Depends, Security
from tortoise.expressions import Q

from goosebit.api.v1.rollouts import routes
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db.models import Rollout
from goosebit.ui.bff.common.requests import DataTableRequest
from goosebit.ui.bff.common.util import parse_datatables_query

from ..common.columns import RolloutColumns
from ..common.responses import DTColumns
from .responses import BFFRolloutsResponse

router = APIRouter(prefix="/rollouts")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["rollout"]["read"]()])],
)
async def rollouts_get(dt_query: Annotated[DataTableRequest, Depends(parse_datatables_query)]) -> BFFRolloutsResponse:
    def search_filter(search_value):
        return Q(name__icontains=search_value) | Q(feed__icontains=search_value)

    query = Rollout.all().prefetch_related("software", "software__compatibility")

    return await BFFRolloutsResponse.convert(dt_query, query, search_filter)


router.add_api_route(
    "",
    routes.rollouts_put,
    methods=["POST"],
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["rollout"]["write"]()])],
    name="bff_rollouts_post",
)


router.add_api_route(
    "",
    routes.rollouts_patch,
    methods=["PATCH"],
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["rollout"]["write"]()])],
    name="bff_rollouts_patch",
)


router.add_api_route(
    "",
    routes.rollouts_delete,
    methods=["DELETE"],
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["rollout"]["delete"]()])],
    name="bff_rollouts_delete",
)


@router.get(
    "/columns",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["rollout"]["read"]()])],
    response_model_exclude_none=True,
)
async def devices_get_columns() -> DTColumns:
    columns = list(
        filter(
            None,
            [
                RolloutColumns.id,
                RolloutColumns.created_at,
                RolloutColumns.name,
                RolloutColumns.feed,
                RolloutColumns.sw_file,
                RolloutColumns.sw_version,
                RolloutColumns.paused,
                RolloutColumns.success_count,
                RolloutColumns.failure_count,
            ],
        )
    )
    return DTColumns(columns=columns)
