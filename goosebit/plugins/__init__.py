import logging
from importlib.metadata import entry_points

from goosebit.schema.plugins import PluginSchema
from goosebit.settings import config

logger = logging.getLogger(__name__)


def load() -> list:
    plugin_configs = []
    logger.info("Checking for plugins to be loaded...")
    if len(config.plugins) == 0:
        logger.info("No plugins found.")
        return []
    logger.info(f"Found plugins enabled in config: {config.plugins}")

    entries = entry_points(group="goosebit.plugins")

    for plugin in config.plugins:
        modules = entries.select(name=plugin)
        for module in modules:  # should be 1 or 0
            logger.info(f"Loading plugin: {plugin}")
            loaded_plugin = module.load()
            if not hasattr(loaded_plugin, "config"):
                logger.error(f"Failed to load plugin: {plugin}, plugin has not defined config")
                continue
            if not isinstance(loaded_plugin.config, PluginSchema):
                logger.error(f"Failed to load plugin: {plugin}, config is not an instance of PluginSchema")
                continue
            plugin_configs.append(loaded_plugin.config)
    return plugin_configs
