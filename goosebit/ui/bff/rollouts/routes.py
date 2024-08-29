from fastapi import APIRouter, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.api.v1.rollouts import routes
from goosebit.auth import validate_user_permissions
from goosebit.db.models import Rollout

from .responses import BFFRolloutsResponse

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
