import logging
from importlib.metadata import entry_points

from goosebit.settings import config

logger = logging.getLogger(__name__)


def load():
    logger.info("Checking for plugins to be loaded...")
    if len(config.plugins) == 0:
        logger.info("No plugins found.")
        return

    entries = entry_points(group="goosebit.plugins")

    for plugin in config.plugins:
        modules = entries.select(name=plugin)
        for module in modules:  # should be 1 or 0
            logger.info(f"Loading plugin: {plugin}")
            module.load()
