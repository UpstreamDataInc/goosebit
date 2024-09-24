from typing import Annotated

from fastapi import APIRouter, Depends, Security
from tortoise.expressions import Q

from goosebit.api.v1.rollouts import routes
from goosebit.auth import validate_user_permissions
from goosebit.db.models import Rollout
from goosebit.ui.bff.common.requests import DataTableRequest
from goosebit.ui.bff.common.util import parse_datatables_query

from .responses import BFFRolloutsResponse

router = APIRouter(prefix="/rollouts")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["rollout.read"])],
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
    dependencies=[Security(validate_user_permissions, scopes=["rollout.write"])],
    name="bff_rollouts_post",
)


router.add_api_route(
    "",
    routes.rollouts_patch,
    methods=["PATCH"],
    dependencies=[Security(validate_user_permissions, scopes=["rollout.write"])],
    name="bff_rollouts_patch",
)


router.add_api_route(
    "",
    routes.rollouts_delete,
    methods=["DELETE"],
    dependencies=[Security(validate_user_permissions, scopes=["rollout.delete"])],
    name="bff_rollouts_delete",
)
