import logging

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.requests import HTTPConnection, Request
from fastapi.responses import RedirectResponse
from fastapi.security import SecurityScopes

from goosebit.auth import (
    check_permissions,
    get_current_user,
    redirect_if_unauthenticated,
)
from goosebit.auth.permissions import GOOSEBIT_PERMISSIONS
from goosebit.ui.nav import nav

from ..db.models import User
from . import bff
from .templates import templates

router = APIRouter(prefix="/ui", include_in_schema=False)
router.include_router(bff.router)

logger = logging.getLogger(__name__)


def validate_user_permissions_with_nav_redirect(
    connection: HTTPConnection,
    security: SecurityScopes,
    user: User = Depends(get_current_user),
):
    if not check_permissions(security.scopes, user.permissions):
        logger.warning(f"{user.username} does not have sufficient permissions")
        for item in nav.items:
            if check_permissions(item.permissions, user.permissions):
                raise HTTPException(
                    status_code=302,
                    headers={"location": str(connection.url_for(item.function))},
                )
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return connection


@router.get("", dependencies=[Depends(redirect_if_unauthenticated)])
async def ui_root(request: Request):
    return RedirectResponse(request.url_for("devices_ui"))


@router.get(
    "/devices",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions_with_nav_redirect, scopes=[GOOSEBIT_PERMISSIONS["device"]["read"]()]),
    ],
)
@nav.route("Devices", permissions=[GOOSEBIT_PERMISSIONS["device"]["read"]()])
async def devices_ui(request: Request):
    return templates.TemplateResponse(request, "devices.html.jinja", context={"title": "Devices"})


@router.get(
    "/software",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions_with_nav_redirect, scopes=[GOOSEBIT_PERMISSIONS["software"]["read"]()]),
    ],
)
@nav.route("Software", permissions=[GOOSEBIT_PERMISSIONS["software"]["read"]()])
async def software_ui(request: Request):
    return templates.TemplateResponse(request, "software.html.jinja", context={"title": "Software"})


@router.get(
    "/rollouts",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions_with_nav_redirect, scopes=[GOOSEBIT_PERMISSIONS["rollout"]["read"]()]),
    ],
)
@nav.route("Rollouts", permissions=[GOOSEBIT_PERMISSIONS["rollout"]["read"]()])
async def rollouts_ui(request: Request):
    return templates.TemplateResponse(request, "rollouts.html.jinja", context={"title": "Rollouts"})


@router.get(
    "/logs/{dev_id}",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions_with_nav_redirect, scopes=[GOOSEBIT_PERMISSIONS["device"]["read"]()]),
    ],
)
async def logs_ui(request: Request, dev_id: str):
    return templates.TemplateResponse(request, "logs.html.jinja", context={"title": "Log", "device": dev_id})


@router.get(
    "/settings",
    dependencies=[
        Depends(redirect_if_unauthenticated),
        Security(validate_user_permissions_with_nav_redirect, scopes=[GOOSEBIT_PERMISSIONS["settings"]()]),
    ],
)
@nav.route("Settings", permissions=[GOOSEBIT_PERMISSIONS["settings"]()], show=False)
async def settings_ui(request: Request):
    return templates.TemplateResponse(request, "settings.html.jinja", context={"title": "Settings"})
