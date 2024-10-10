import asyncio
from logging import getLogger

from tortoise import Tortoise
from tortoise.exceptions import OperationalError

from goosebit.db.config import TORTOISE_CONF
from goosebit.db.models import Device

logger = getLogger(__name__)


async def init():
    await Tortoise.init(config=TORTOISE_CONF)
    try:
        await Device.first()
    except OperationalError:
        logger.exception("DB does not exist, try running `poetry run aerich upgrade`.")
        loop = asyncio.get_running_loop()
        loop.stop()


async def close():
    await Tortoise.close_connections()
