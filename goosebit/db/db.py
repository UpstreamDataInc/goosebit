from tortoise import Tortoise, run_async

from goosebit.db.config import TORTOISE_CONF


async def init():
    await Tortoise.init(config=TORTOISE_CONF)


async def close():
    await Tortoise.close_connections()


if __name__ == "__main__":
    run_async(init())
