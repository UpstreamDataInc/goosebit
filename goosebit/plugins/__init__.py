from importlib.metadata import entry_points

from goosebit.settings import PLUGINS

entries = entry_points(group="goosebit.plugins")

plugins = []

for p in PLUGINS:
    plugins.extend(entries.select(name=p))
