from fastapi import APIRouter, Security

from goosebit.api.v1.settings import routes
from goosebit.auth import validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS

from . import users

router = APIRouter(prefix="/settings")

router.include_router(users.router)

router.add_api_route(
    "/permissions",
    routes.settings_permissions_get,
    methods=["GET"],
    dependencies=[Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["settings"]["users"]["read"]()])],
    name="bff_settings_permissions_get",
    response_model_exclude_none=True,
)
