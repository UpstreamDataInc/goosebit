from pathlib import Path

from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from goosebit.settings import config


def attach_saml_status(_: Request):
    return {"azure": config.auth.azure is not None}


templates = Jinja2Templates(str(Path(__file__).resolve().parent), context_processors=[attach_saml_status])
