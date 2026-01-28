from fastapi import APIRouter, Security

from goosebit.auth import validate_user_permissions
from goosebit_simple_stats.api.v1.stats import routes

router = APIRouter(prefix="/stats")


router.add_api_route(
    "",
    routes.stats_get,
    methods=["GET"],
    dependencies=[Security(validate_user_permissions, scopes=["stats.read"])],
    name="bff_stats_get",
)
