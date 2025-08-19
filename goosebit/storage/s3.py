import asyncio
from pathlib import Path
from typing import AsyncIterable
from urllib.parse import urlparse

from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import ClientError

from .base import StorageProtocol


class S3StorageBackend(StorageProtocol):
    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ):
        self.bucket = bucket

        config = Config(
            region_name=region,
            connect_timeout=10,
            read_timeout=60,
            retries={"max_attempts": 5, "mode": "adaptive"},
            signature_version="s3v4",
        )

        session_config = {}
        if access_key_id is not None:
            session_config["aws_access_key_id"] = access_key_id
        if secret_access_key is not None:
            session_config["aws_secret_access_key"] = secret_access_key

        session = Session(**session_config)

        self.s3_client = session.client("s3", config=config, endpoint_url=endpoint_url)

    async def store_file(self, source_path: Path, dest_path: Path) -> str:
        key = str(dest_path).replace("\\", "/").lstrip("/")  # Convert path to S3 key

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.s3_client.upload_file, str(source_path), self.bucket, key)
            return f"s3://{self.bucket}/{key}"
        except ClientError as e:
            raise ValueError(f"S3 upload failed: {e}")

    async def get_file_stream(self, uri: str) -> AsyncIterable[bytes]:  # type: ignore[override]
        key = self._extract_key_from_uri(uri)

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: self.s3_client.get_object(Bucket=self.bucket, Key=key))

            body = response["Body"]
            try:
                while True:
                    chunk = await loop.run_in_executor(None, body.read, 8192)
                    if not chunk:
                        break
                    yield chunk
            finally:
                await loop.run_in_executor(None, body.close)

        except ClientError as e:
            raise ValueError(f"S3 download failed: {e}")

    async def get_download_url(self, uri: str) -> str:
        parsed = urlparse(uri)
        if parsed.scheme in ("http", "https"):
            return uri
        else:
            raise ValueError(f"Fallback to streaming as S3 service might not be exposed externally: {uri}")

    def get_temp_dir(self) -> Path:
        import tempfile

        temp_dir = Path(tempfile.gettempdir()).joinpath("goosebit-s3-temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    async def delete_file(self, uri: str) -> bool:
        parsed = urlparse(uri)
        if parsed.scheme != "s3":
            raise ValueError(f"Cannot delete remote file: {uri}")

        key = self._extract_key_from_uri(uri)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.s3_client.delete_object(Bucket=self.bucket, Key=key))
            return True
        except ClientError as e:
            raise ValueError(f"S3 delete failed: {e}")

    def _extract_key_from_uri(self, uri: str) -> str:
        if not uri.startswith(f"s3://{self.bucket}/"):
            raise ValueError(f"Invalid S3 URI for bucket {self.bucket}: {uri}")

        return uri.replace(f"s3://{self.bucket}/", "")
