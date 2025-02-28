from fastapi import APIRouter, Security

from example_plugin.api.v1.example import routes
from goosebit.auth import validate_user_permissions

router = APIRouter(prefix="/example")


router.add_api_route(
    "",
    routes.example_get,
    methods=["GET"],
    dependencies=[Security(validate_user_permissions, scopes=["example.read"])],
    name="bff_example_get",
)
