from pathlib import Path

from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from goosebit.auth import compare_permissions


def attach_permissions_comparison(_: Request):
    return {"compare_permissions": compare_permissions}


templates = Jinja2Templates(str(Path(__file__).resolve().parent), context_processors=[attach_permissions_comparison])
