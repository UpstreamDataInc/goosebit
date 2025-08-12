from fastapi import APIRouter, Security
from goosebit_simple_stats.api.v1.stats import routes

from goosebit.auth import validate_user_permissions

router = APIRouter(prefix="/stats")


router.add_api_route(
    "",
    routes.stats_get,
    methods=["GET"],
    dependencies=[Security(validate_user_permissions, scopes=["stats.read"])],
    name="bff_stats_get",
)
