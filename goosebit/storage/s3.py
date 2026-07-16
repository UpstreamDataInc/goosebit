import asyncio
from functools import partial
from typing import AsyncIterable
from urllib.parse import urlparse

from anyio import Path
from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from .base import StorageProtocol

DOWNLOAD_CHUNK_SIZE = 64 * 1024
# bytes fetched per ranged GetObject; request count and per-stream memory both scale with this
RANGE_REQUEST_SIZE = 1024 * 1024
# retries per range for transient read failures; botocore only retries get_object, not body.read()
RANGE_READ_ATTEMPTS = 3


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
        loop = asyncio.get_running_loop()

        offset = 0
        total_size: int | None = None
        etag: str | None = None

        try:
            while total_size is None or offset < total_size:
                request = {
                    "Bucket": self.bucket,
                    "Key": key,
                    "Range": f"bytes={offset}-{offset + RANGE_REQUEST_SIZE - 1}",
                }
                if etag is not None:
                    # fail with 412 instead of splicing two versions if the artifact is replaced mid-download
                    request["IfMatch"] = etag

                # retry the whole range fetch on transient failures; ClientErrors are terminal
                data = None
                for attempt in range(RANGE_READ_ATTEMPTS):
                    try:
                        response = await loop.run_in_executor(None, partial(self.s3_client.get_object, **request))

                        if total_size is None:
                            etag = response.get("ETag")
                            # ContentRange is "bytes 0-1048575/104857600"; fall back to
                            # ContentLength if a backend ignored Range (200) or reports "*" total
                            content_range = response.get("ContentRange")
                            if content_range and content_range.rsplit("/", 1)[1] != "*":
                                total_size = int(content_range.rsplit("/", 1)[1])
                            else:
                                total_size = response["ContentLength"]
                            if etag is not None:
                                request["IfMatch"] = etag  # pin version across ranges and retries

                        body = response["Body"]
                        try:
                            data = await loop.run_in_executor(None, body.read)
                        finally:
                            await loop.run_in_executor(None, body.close)
                        break
                    except ClientError as e:
                        if offset == 0 and e.response["Error"]["Code"] == "InvalidRange":
                            return  # zero-byte object: any range request returns 416
                        raise
                    except BotoCoreError:
                        if attempt + 1 == RANGE_READ_ATTEMPTS:
                            raise
                        await asyncio.sleep(0.5 * (attempt + 1))  # back off, then re-fetch this range

                if not data:
                    raise ValueError(f"S3 returned empty range at offset {offset} for {uri}")
                offset += len(data)

                # device-paced waits happen here, with no S3 request in flight to time out
                for i in range(0, len(data), DOWNLOAD_CHUNK_SIZE):
                    yield data[i : i + DOWNLOAD_CHUNK_SIZE]

        # BotoCoreError covers mid-transfer failures (e.g. ResponseStreamingError
        # when the connection drops), which are not ClientError subclasses.
        except (BotoCoreError, ClientError) as e:
            raise ValueError(f"S3 download failed: {e}")

    async def get_download_url(self, uri: str) -> str:
        parsed = urlparse(uri)
        if parsed.scheme in ("http", "https"):
            return uri
        else:
            raise ValueError(f"Fallback to streaming as S3 service might not be exposed externally: {uri}")

    async def get_temp_dir(self) -> Path:
        import tempfile

        temp_dir = Path(tempfile.gettempdir()).joinpath("goosebit-s3-temp")
        await temp_dir.mkdir(parents=True, exist_ok=True)
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
