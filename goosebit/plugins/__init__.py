from importlib.metadata import entry_points

plugins = entry_points(group="goosebit.plugins")

print(plugins)
