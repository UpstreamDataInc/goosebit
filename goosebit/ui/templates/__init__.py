from pathlib import Path

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(str(Path(__file__).resolve().parent))
