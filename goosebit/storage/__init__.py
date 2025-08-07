from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncGenerator

from goosebit.settings.schema import GooseBitSettings, StorageType


class Storage(ABC):
    @abstractmethod
    async def store_file(self, source_path: Path, key: str) -> str:
        pass

    @abstractmethod
    async def get_file_stream(self, uri: str) -> AsyncGenerator[bytes, None]:
        pass

    @abstractmethod
    async def get_download_url(self, uri: str) -> str:
        pass


_storage: Storage | None = None


def init_storage(config: GooseBitSettings) -> None:
    global _storage
    _storage = create_storage(config)


def create_storage(config: GooseBitSettings) -> Storage:
    from .filesystem import FilesystemStorage
    from .s3 import S3Storage

    if config.storage.backend == StorageType.FILESYSTEM:
        return FilesystemStorage(base_path=config.artifacts_dir)

    elif config.storage.backend == StorageType.S3:
        if config.storage.s3 is None:
            return FilesystemStorage(base_path=config.artifacts_dir)

        config = config.storage.s3
        return S3Storage(
            bucket=config.bucket,
            region=config.region,
            endpoint_url=config.endpoint_url,
            access_key_id=config.access_key_id,
            secret_access_key=config.secret_access_key,
        )

    else:
        raise ValueError(f"Unknown storage backend type: {config.storage.backend}")


def get_storage() -> Storage:
    if _storage is None:
        raise RuntimeError("Storage backend not initialized. Call init_storage() first.")

    return _storage


def close_storage() -> None:
    global _storage
    _storage = None
