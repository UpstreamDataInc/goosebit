from pathlib import Path

import jinja2

from goosebit.ui.templates import TEMPLATES

template_dir = str(Path(__file__).resolve().parent)

loader = jinja2.FileSystemLoader(template_dir)

TEMPLATES.register_handler(loader)
