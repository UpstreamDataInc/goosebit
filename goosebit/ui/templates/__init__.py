from pathlib import Path

import jinja2
from fastapi.templating import Jinja2Templates

TEMPLATE_DIR = str(Path(__file__).resolve().parent)


class Templates:
    def __init__(self):
        self.loader = jinja2.ChoiceLoader([jinja2.FileSystemLoader(TEMPLATE_DIR)])
        self._handler = None

    @property
    def handler(self):
        if self._handler is None:
            self._handler = Jinja2Templates(directory=TEMPLATE_DIR, loader=self.loader)
        return self._handler

    def register_handler(self, handler):
        self.loader.loaders = [*self.loader.loaders, handler]


TEMPLATES = Templates()
