from __future__ import annotations

from fastapi import APIRouter, Security
from fastapi.requests import Request
from tortoise.expressions import Q

from goosebit.auth import validate_user_permissions
from goosebit.db.models import Software
from goosebit.ui.bff.software.responses import BFFSoftwareResponse

router = APIRouter(prefix="/software")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=["software.read"])],
)
async def software_get(request: Request) -> BFFSoftwareResponse:
    def search_filter(search_value):
        return Q(uri__icontains=search_value) | Q(version__icontains=search_value)

    query = Software.all().prefetch_related("compatibility")
    total_records = await Software.all().count()

    return await BFFSoftwareResponse.convert(request, query, search_filter, total_records)
