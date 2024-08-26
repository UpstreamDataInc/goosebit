from fastapi import APIRouter, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.auth import validate_user_permissions
from goosebit.models import Rollout

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
