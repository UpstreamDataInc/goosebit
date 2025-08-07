import shutil
from pathlib import Path
from typing import AsyncGenerator
from urllib.parse import urlparse

import httpx
from anyio import open_file

from . import Storage


class FilesystemStorage(Storage):
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def store_file(self, source_path: Path, key: str) -> str:
        dest_path = self._validate_key(key)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, dest_path)

        return dest_path.resolve().as_uri()

    async def get_file_stream(self, uri: str) -> AsyncGenerator[bytes, None]:
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

    def _extract_path_from_uri(self, uri: str) -> Path:
        parsed = urlparse(uri)

        if parsed.scheme != "file":
            raise ValueError(f"Expected file:// URI, got: {uri}")

        return Path(parsed.path)

    def _validate_key(self, key: str) -> Path:
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")

        key_path = Path(key.strip())

        if key_path.is_absolute():
            raise ValueError("Key cannot be an absolute path")

        dest_path = self.base_path / key_path

        resolved_dest = dest_path.resolve()
        resolved_base = self.base_path.resolve()

        try:
            resolved_dest.relative_to(resolved_base)
        except ValueError:
            raise ValueError("Key contains invalid path traversal components")

        return dest_path
