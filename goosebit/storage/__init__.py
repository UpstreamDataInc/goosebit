from pathlib import Path
from typing import AsyncIterable

from goosebit.settings import config
from goosebit.settings.schema import GooseBitSettings, StorageType
from goosebit.storage.base import StorageProtocol

from .filesystem import FilesystemStorageBackend
from .s3 import S3StorageBackend


class GoosebitStorage:
    def __init__(self, config: GooseBitSettings):
        self.config = config
        self._backend: StorageProtocol = self._create_backend()

    def _create_backend(self) -> StorageProtocol:

        if self.config.storage.backend == StorageType.FILESYSTEM:
            return FilesystemStorageBackend(base_path=self.config.artifacts_dir)

        elif self.config.storage.backend == StorageType.S3:
            if self.config.storage.s3 is None:
                return FilesystemStorageBackend(base_path=self.config.artifacts_dir)

            s3_config = self.config.storage.s3
            return S3StorageBackend(
                bucket=s3_config.bucket,
                region=s3_config.region,
                endpoint_url=s3_config.endpoint_url,
                access_key_id=s3_config.access_key_id,
                secret_access_key=s3_config.secret_access_key,
            )

        else:
            raise ValueError(f"Unknown storage backend type: {self.config.storage.backend}")

    @property
    def backend(self) -> StorageProtocol:
        if self._backend is None:
            raise RuntimeError("Storage backend not initialized. Use async context manager.")
        return self._backend

    async def store_file(self, source_path: Path, dest_path: Path) -> str:
        return await self.backend.store_file(source_path, dest_path)

    async def get_file_stream(self, uri: str) -> AsyncIterable[bytes]:
        async for chunk in self.backend.get_file_stream(uri):  # type: ignore[attr-defined]
            yield chunk

    async def get_download_url(self, uri: str) -> str:
        return await self.backend.get_download_url(uri)

    def get_temp_dir(self) -> Path:
        return self.backend.get_temp_dir()

    async def delete_file(self, uri: str) -> bool:
        return await self.backend.delete_file(uri)


# Init the module-level storage instance
storage = GoosebitStorage(config)
