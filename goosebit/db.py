from aerich import Command
from tortoise import Tortoise, run_async

from goosebit.settings import DB_MIGRATIONS_LOC, DB_URI

TORTOISE_CONF = {
    "connections": {"default": DB_URI},
    "apps": {
        "models": {
            "models": ["goosebit.models", "aerich.models"],
        },
    },
}


async def init():
    command = Command(tortoise_config=TORTOISE_CONF, location=DB_MIGRATIONS_LOC)
    await Tortoise.init(config=TORTOISE_CONF)
    if not DB_MIGRATIONS_LOC.exists():
        await command.init_db(safe=True)
    await command.init()
    await command.migrate()
    await command.upgrade(run_in_transaction=True)
    await Tortoise.generate_schemas(safe=True)


async def close():
    await Tortoise.close_connections()


if __name__ == "__main__":
    run_async(init())
