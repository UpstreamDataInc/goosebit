from pathlib import Path

import jinja2
from fastapi.templating import Jinja2Templates

from goosebit.plugins import TEMPLATES

template_dir = str(Path(__file__).resolve().parent)

template_loaders = [jinja2.FileSystemLoader(template_dir)]

for t in TEMPLATES:
    template_loaders.append(t.load())

loader = jinja2.ChoiceLoader(template_loaders)

templates = Jinja2Templates(directory=template_dir, loader=loader)
