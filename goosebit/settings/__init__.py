import logging.config

from .const import PWD_CXT  # noqa: F401
from .schema import GooseBitSettings

config = GooseBitSettings()


logging.config.dictConfig(config.logging)

logger = logging.getLogger(__name__)

if config.config_file is not None:
    logger.info(f"Loading settings from: {config.config_file}")


USERS = {u.username: u for u in config.users}
