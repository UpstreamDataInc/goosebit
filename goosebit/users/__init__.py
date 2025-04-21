from aiocache import caches

from goosebit.api.telemetry.metrics import users_count
from goosebit.db.models import User
from goosebit.settings import PWD_CXT


async def create_user(username: str, password: str, permissions: list[str]) -> User:
    return await UserManager.setup_user(username=username, hashed_pwd=PWD_CXT.hash(password), permissions=permissions)


async def create_initial_user(username: str, hashed_pwd: str) -> User:
    return await UserManager.setup_user(username=username, hashed_pwd=hashed_pwd, permissions=["*"])


class UserManager:
    @staticmethod
    async def save_user(user: User, update_fields: list[str]) -> None:
        await user.save(update_fields=update_fields)

        # only update cache after a successful database save
        result = await caches.get("default").set(user.username, user, ttl=600)
        assert result, "user being cached"

    @staticmethod
    async def update_enabled(user: User, enabled: bool) -> None:
        user.enabled = enabled
        await UserManager.save_user(user, update_fields=["enabled"])

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
        users_count.set(await User.all().count())
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

    @staticmethod
    async def delete_users(usernames: list[str]):
        await User.filter(username__in=usernames).delete()
        for username in usernames:
            await caches.get("default").delete(username)
        users_count.set(await User.all().count())
