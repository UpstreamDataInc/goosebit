from logging import getLogger

from tortoise import Tortoise
from tortoise.exceptions import OperationalError

from goosebit.db import config
from goosebit.db.models import Device

logger = getLogger(__name__)


async def init() -> bool:
    await Tortoise.init(config=config.TORTOISE_CONF)
    try:
        await Device.first()
    except OperationalError:
        return False
    return True


async def close() -> None:
    await Tortoise.close_connections()
