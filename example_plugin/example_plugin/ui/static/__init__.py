from pathlib import Path

from fastapi.staticfiles import StaticFiles

static = StaticFiles(directory=Path(__file__).resolve().parent)
