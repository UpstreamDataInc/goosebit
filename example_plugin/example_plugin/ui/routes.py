from fastapi import APIRouter, Depends, Security
from fastapi.requests import Request

from goosebit import nav
from goosebit.auth import redirect_if_unauthenticated, validate_user_permissions
from goosebit.ui.templates import templates

from . import bff

router = APIRouter(prefix="/ui", include_in_schema=False)

router.include_router(bff.router)


@router.get(
    "/example",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions, scopes=["example.read"]),
    ],
)
@nav.route("Example", permissions="example.read")
async def example_ui(request: Request):
    return templates.TemplateResponse(request, "example.html.jinja", context={"title": "Example"})
