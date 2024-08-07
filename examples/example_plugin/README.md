# gooseBit Example Plugin

This is a basic example plugin to provide a framework for creating custom plugins for gooseBit.

## Plugin Requirements

Plugins are identified automatically with entry points. This means that you must define the relevant section in your `pyproject.toml` file.

### `poetry`

```toml
[tool.poetry.plugins.'goosebit.plugins']
example_plugin = "example_plugin"
```

### Other systems

```toml
[proejct.entry-points.'goosebit.plugins']
example_plugin = "example_plugin"
```

## Plugin Functionality

Make sure all plugin files are imported into the root of your project, this will ensure they get put into the main app.

### Adding API endpoints:

```python
from goosebit.api.routes import router as api_router

from fastapi import APIRouter

# not required to have a prefix, but good convention
# this will prevent any overlaps from other plugins
router = APIRouter(prefix="/my_custom_plugin")

@router.get("/test")
async def test_endpoint():
    return {"value": True, "message": "Hello world!"}

api_router.include_router(router)
```

### Adding UI endpoints:

```python
from goosebit.ui.routes import router as ui_router
from goosebit.ui.templates import TEMPLATES
from goosebit.ui.nav import NAVIGATION


from fastapi.requests import Request

from fastapi import APIRouter

# not required to have a prefix, but good convention
# this will prevent any overlaps from other plugins
router = APIRouter(prefix="/my_custom_plugin")

@router.get("/test")
# add the page to the navigation header
@NAVIGATION.add("Custom")
async def test_endpoint(request: Request):
    return TEMPLATES.handler.TemplateResponse(request, "my_custom_page.html", {"title": "Custom"})

ui_router.include_router(router)
```

### Adding templates:

```python
import jinja2

from goosebit.ui.templates import TEMPLATES

loader = jinja2.FileSystemLoader("custom_templates")

TEMPLATES.register_handler(loader)
```

### Adding static files:

```python
from fastapi.staticfiles import StaticFiles

from goosebit.ui.static import router as static_router

static = StaticFiles(directory="custom_static")

static_router.mount(path="/example_plugin", name="example_plugin_static", app=static)
```
