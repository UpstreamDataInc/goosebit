from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Security
from tortoise.expressions import Q

from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.db.models import User
from goosebit.ui.bff.common.columns import SettingsUsersColumns
from goosebit.ui.bff.common.requests import DataTableRequest
from goosebit.ui.bff.common.responses import DTColumns
from goosebit.ui.bff.common.util import parse_datatables_query
from goosebit.ui.bff.settings.users.responses import BFFSettingsUsersResponse

router = APIRouter(prefix="/users")


@router.get(
    "",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["settings"]["users"]["read"]()])],
)
async def settings_users_get(
    dt_query: Annotated[DataTableRequest, Depends(parse_datatables_query)],
) -> BFFSettingsUsersResponse:
    filters: list[Q] = []

    def search_filter(search_value):
        base_filter = Q(Q(username__icontains=search_value), join_type="OR")
        return Q(base_filter, *filters, join_type="AND")

    query = User.all()

    return await BFFSettingsUsersResponse.convert(dt_query, query, search_filter)


@router.get(
    "/columns",
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["settings"]["users"]["read"]()])],
    response_model_exclude_none=True,
)
async def settings_users_get_columns() -> DTColumns:
    columns = list(
        filter(
            None,
            [
                SettingsUsersColumns.username,
                SettingsUsersColumns.enabled,
                SettingsUsersColumns.permissions,
            ],
        )
    )
    return DTColumns(columns=columns)
