from typing import Any

from aiocache import SimpleMemoryCache
from aiocache.serializers import PickleSerializer

from goosebit.settings import config

CACHE_TTL = 600


class Cache:
    """Object cache honoring the `cache.enabled` setting.

    With caching disabled every lookup is a miss and writes are dropped, leaving the
    database as the only source of truth. This is required when running multiple
    workers, see https://github.com/UpstreamDataInc/goosebit/issues/125.
    """

    def __init__(self, enabled: bool):
        self.enabled = enabled
        self._backend = SimpleMemoryCache(serializer=PickleSerializer())

    async def get(self, key: str) -> Any:
        if not self.enabled:
            return None
        return await self._backend.get(key)

    async def set(self, key: str, value: Any) -> None:
        if not self.enabled:
            return
        await self._backend.set(key, value, ttl=CACHE_TTL)

    async def delete(self, key: str) -> None:
        if not self.enabled:
            return
        # missing keys are fine, the entry may have expired or was never cached by this worker
        await self._backend.delete(key)

    async def clear(self) -> None:
        if not self.enabled:
            return
        await self._backend.clear()


cache = Cache(enabled=config.cache.enabled)
