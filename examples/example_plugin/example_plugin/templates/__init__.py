from pathlib import Path

import jinja2

template_dir = str(Path(__file__).resolve().parent)

loader = jinja2.FileSystemLoader(template_dir)
