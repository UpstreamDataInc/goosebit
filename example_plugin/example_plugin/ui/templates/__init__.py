from pathlib import Path

from starlette.templating import Jinja2Templates

templates = Jinja2Templates(Path(__file__).resolve().parent)
