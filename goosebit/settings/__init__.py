import logging.config

from .const import PWD_CXT  # noqa: F401
from .schema import GooseBitSettings, secret_key_was_generated

config = GooseBitSettings()


logging.config.dictConfig(config.logging)

logger = logging.getLogger(__name__)

if config.config_file is not None:
    logger.info(f"Loading settings from: {config.config_file}")

if secret_key_was_generated():
    logger.warning(
        "No secret_key configured, generated a random one. User sessions will not survive restarts "
        "and logins will fail intermittently when running multiple workers. Set GOOSEBIT_SECRET_KEY."
    )
