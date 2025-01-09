from os import PathLike
from pathlib import Path

import jinja2
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from goosebit.auth import check_permissions


def attach_permissions_comparison(_: Request):
    return {"compare_permissions": check_permissions}


env = jinja2.Environment(loader=jinja2.ChoiceLoader([jinja2.FileSystemLoader(str(Path(__file__).resolve().parent))]))
templates = Jinja2Templates(context_processors=[attach_permissions_comparison], env=env)


def add_dir(directory: PathLike):
    templates.env.loader.loaders.append(jinja2.FileSystemLoader(directory))


templates.add_dir = add_dir
