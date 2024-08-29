from tortoise import Tortoise

from goosebit.db.config import TORTOISE_CONF


async def init():
    await Tortoise.init(config=TORTOISE_CONF)


async def close():
    await Tortoise.close_connections()
