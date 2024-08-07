from importlib.metadata import entry_points

plugins = entry_points(group="goosebit.plugins")

api_routers = []
ui_templates = []
ui_routers = []

for plugin in plugins:
    if plugin.name.endswith("-api"):
        api_routers.append(plugin)

for plugin in plugins:
    if plugin.name.endswith("-templates"):
        ui_templates.append(plugin)

for plugin in plugins:
    if plugin.name.endswith("-ui"):
        ui_routers.append(plugin)

API = api_routers
TEMPLATES = ui_templates
UI = ui_routers
