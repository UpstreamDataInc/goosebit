from logging import getLogger

from tortoise import Tortoise
from tortoise.exceptions import OperationalError

from goosebit.db.config import TORTOISE_CONF
from goosebit.db.models import Device

logger = getLogger(__name__)


async def init() -> bool:
    await Tortoise.init(config=TORTOISE_CONF)
    try:
        await Device.first()
    except OperationalError:
        return False
    return True


async def close():
    await Tortoise.close_connections()
