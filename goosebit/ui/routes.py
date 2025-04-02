from fastapi import APIRouter, Depends, Security
from fastapi.requests import Request
from fastapi.responses import RedirectResponse

from goosebit.auth import redirect_if_unauthenticated, validate_user_permissions
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.ui.nav import nav

from . import bff
from .templates import templates

router = APIRouter(prefix="/ui", include_in_schema=False)
router.include_router(bff.router)


@router.get("", dependencies=[Depends(redirect_if_unauthenticated)])
async def ui_root(request: Request):
    return RedirectResponse(request.url_for("devices_ui"))


@router.get(
    "/devices",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["read"]()]),
    ],
)
@nav.route("Devices", permissions=[GOOSEBIT_PERMISSIONS["device"]["read"]()])
async def devices_ui(request: Request):
    return templates.TemplateResponse(request, "devices.html.jinja", context={"title": "Devices"})


@router.get(
    "/software",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["software"]["read"]()]),
    ],
)
@nav.route("Software", permissions=[GOOSEBIT_PERMISSIONS["software"]["read"]()])
async def software_ui(request: Request):
    return templates.TemplateResponse(request, "software.html.jinja", context={"title": "Software"})


@router.get(
    "/rollouts",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions, scopes=GOOSEBIT_PERMISSIONS["rollout"]["read"]()),
    ],
)
@nav.route("Rollouts", permissions=GOOSEBIT_PERMISSIONS["rollout"]["read"]())
async def rollouts_ui(request: Request):
    return templates.TemplateResponse(request, "rollouts.html.jinja", context={"title": "Rollouts"})


@router.get(
    "/logs/{dev_id}",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["device"]["read"]()]),
    ],
)
async def logs_ui(request: Request, dev_id: str):
    return templates.TemplateResponse(request, "logs.html.jinja", context={"title": "Log", "device": dev_id})


@router.get(
    "/settings",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions, scopes=[GOOSEBIT_PERMISSIONS["settings"]()]),
    ],
)
async def settings_ui(request: Request):
    return templates.TemplateResponse(request, "settings.html.jinja", context={"title": "Settings"})
