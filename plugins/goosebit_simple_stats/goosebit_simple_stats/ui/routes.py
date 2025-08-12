from fastapi import APIRouter, Depends, Security
from fastapi.requests import Request

from goosebit import nav
from goosebit.auth import redirect_if_unauthenticated, validate_user_permissions
from goosebit.ui.templates import templates

from . import bff

router = APIRouter(prefix="/ui", include_in_schema=False)

router.include_router(bff.router)


@router.get(
    "/stats",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions, scopes=["stats.read"]),
    ],
)
@nav.route("Stats", permissions=["stats.read"])
async def stats_ui(request: Request):
    return templates.TemplateResponse(request, "stats.html.jinja", context={"title": "Simple Stats"})
