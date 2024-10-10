from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.security import OAuth2PasswordRequestForm

from . import azure
from .templates import templates
from .util import login_user, redirect_if_authenticated

router = APIRouter(prefix="/login")

router.include_router(azure.router)


@router.get("", include_in_schema=False, dependencies=[Depends(redirect_if_authenticated)])
async def login_get(request: Request):
    return templates.TemplateResponse(request, "login.html.jinja")


@router.post("", tags=["login"])
async def login_post(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return {"access_token": login_user(form_data.username, form_data.password), "token_type": "bearer"}
