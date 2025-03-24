from aiocache import caches

from goosebit.api.telemetry.metrics import users_count
from goosebit.db.models import User
from goosebit.settings import PWD_CXT, config


async def init():
    await create_initial_user(username=config.initial_user.username, hashed_pwd=config.initial_user.hashed_pwd)
    users_count.set(await User.all().count())


async def create_user(username: str, password: str, permissions: list[str]) -> User:
    return await UserManager.setup_user(username=username, hashed_pwd=PWD_CXT.hash(password), permissions=permissions)


async def create_initial_user(username: str, hashed_pwd: str) -> User:
    return await UserManager.setup_user(username=username, hashed_pwd=hashed_pwd, permissions=["*"])


class UserManager:
    @classmethod
    async def setup_user(cls, username: str, hashed_pwd: str, permissions: list[str]) -> User:
        user = (
            await User.get_or_create(
                username=username,
                defaults={
                    "hashed_pwd": hashed_pwd,
                    "permissions": permissions,
                },
            )
        )[0]
        return user

    @staticmethod
    async def get_user(username: str) -> User:
        cache = caches.get("default")
        user = await cache.get(username)
        if user:
            return user

        user = await User.get_or_none(username=username)
        if user is not None:
            result = await cache.set(user.username, user, ttl=600)
            assert result, "user being cached"

        return user
