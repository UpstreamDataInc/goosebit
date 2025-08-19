import shutil
from pathlib import Path
from typing import AsyncIterable
from urllib.parse import urlparse

import httpx
from anyio import Path as AnyioPath
from anyio import open_file

from .base import StorageProtocol


class FilesystemStorageBackend(StorageProtocol):
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def store_file(self, source_path: Path, dest_path: Path) -> str:
        final_dest_path = self._validate_dest_path(dest_path)
        final_dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, final_dest_path)

        return final_dest_path.resolve().as_uri()

    async def get_file_stream(self, uri: str) -> AsyncIterable[bytes]:  # type: ignore[override]
        parsed = urlparse(uri)

        if parsed.scheme in ("http", "https"):
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", uri) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes(8192):
                        yield chunk

        elif parsed.scheme == "file":
            file_path = self._extract_path_from_uri(uri)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            async with await open_file(file_path, "rb") as f:
                while True:
                    chunk = await f.read(8192)
                    if not chunk:
                        break
                    yield chunk
        else:
            raise ValueError(f"Unsupported URI scheme '{parsed.scheme}' for filesystem backend: {uri}")

    async def get_download_url(self, uri: str) -> str:
        parsed = urlparse(uri)

        if parsed.scheme in ("http", "https"):
            return uri

        elif parsed.scheme == "file":
            file_path = self._extract_path_from_uri(uri)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            return file_path.resolve().as_uri()

        else:
            raise ValueError(f"Unsupported URI scheme '{parsed.scheme}' for filesystem backend: {uri}")

    def get_temp_dir(self) -> Path:
        temp_dir = self.base_path / "tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    async def delete_file(self, uri: str) -> bool:
        parsed = urlparse(uri)

        if parsed.scheme == "file":
            file_path = self._extract_path_from_uri(uri)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        else:
            raise ValueError(f"Cannot delete remote file: {uri}")

    def _extract_path_from_uri(self, uri: str) -> Path:
        parsed = urlparse(uri)

        if parsed.scheme != "file":
            raise ValueError(f"Expected file:// URI, got: {uri}")

        return Path(parsed.path)

    def _validate_dest_path(self, dest_path: Path) -> Path:
        if not isinstance(dest_path, (Path, AnyioPath)):
            raise ValueError("Destination path must be a Path object")

        if isinstance(dest_path, AnyioPath):
            dest_path = Path(str(dest_path))

        if dest_path.is_absolute():
            raise ValueError("Destination path cannot be absolute")

        final_dest_path = self.base_path / dest_path

        resolved_dest = final_dest_path.resolve()
        resolved_base = self.base_path.resolve()

        try:
            resolved_dest.relative_to(resolved_base)
        except ValueError:
            raise ValueError("Destination path contains invalid path traversal components")

        return final_dest_path
