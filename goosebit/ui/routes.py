from fastapi import APIRouter, Depends, Security
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer

from goosebit.auth import redirect_if_unauthenticated, validate_user_permissions
from goosebit.ui.nav import nav

from . import bff
from .templates import templates

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter(prefix="/ui", dependencies=[Depends(redirect_if_unauthenticated)], include_in_schema=False)
router.include_router(bff.router)


@router.get("")
async def ui_root(request: Request):
    return RedirectResponse(request.url_for("home_ui"))


@router.get(
    "/home",
    dependencies=[Security(validate_user_permissions, scopes=["home.read"])],
)
@nav.route("Home", permissions=["home.read"])
async def home_ui(request: Request):
    return templates.TemplateResponse(request, "index.html.jinja", context={"title": "Home"})


@router.get(
    "/devices",
    dependencies=[Security(validate_user_permissions, scopes=["device.read"])],
)
@nav.route("Devices", permissions=["device.read"])
async def devices_ui(request: Request):
    return templates.TemplateResponse(request, "devices.html.jinja", context={"title": "Devices"})


@router.get(
    "/software",
    dependencies=[Security(validate_user_permissions, scopes=["software.read"])],
)
@nav.route("Software", permissions=["software.read"])
async def software_ui(request: Request):
    return templates.TemplateResponse(request, "software.html.jinja", context={"title": "Software"})


@router.get(
    "/rollouts",
    dependencies=[Security(validate_user_permissions, scopes=["rollout.read"])],
)
@nav.route("Rollouts", permissions=["rollout.read"])
async def rollouts_ui(request: Request):
    return templates.TemplateResponse(request, "rollouts.html.jinja", context={"title": "Rollouts"})


@router.get(
    "/logs/{dev_id}",
    dependencies=[Security(validate_user_permissions, scopes=["device.read"])],
)
async def logs_ui(request: Request, dev_id: str):
    return templates.TemplateResponse(request, "logs.html.jinja", context={"title": "Log", "device": dev_id})
