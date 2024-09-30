from logging import getLogger

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from goosebit.db.config import SQLMODEL_CONFIG

logger = getLogger(__name__)

engine = create_async_engine(**SQLMODEL_CONFIG)


async def init() -> bool:
    try:
        async with AsyncSession(engine) as session:
            # Try to create session to check if DB is awake
            await session.exec(select(1))
        return True
    except Exception as e:
        logger.error(e)
        return False


async def close():
    pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(init())
