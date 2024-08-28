from tortoise import Tortoise, run_async

from goosebit.db.config import TORTOISE_CONF
from goosebit.db.models import Software


async def init():
    await Tortoise.init(config=TORTOISE_CONF)

    for software in await Software.all():
        if software.local and not software.path.exists():
            # delete it
            await software.delete()


async def close():
    await Tortoise.close_connections()


if __name__ == "__main__":
    run_async(init())
