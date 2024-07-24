import hashlib
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

import semver
from fastapi.requests import Request
from tortoise import Model, fields


def sha1_hash_file(file_path: Path):
    with file_path.open("rb") as f:
        sha1_hash = hashlib.file_digest(f, "sha1")
    return sha1_hash.hexdigest()


class Tag(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)


class Device(Model):
    uuid = fields.CharField(max_length=255, primary_key=True)
    name = fields.CharField(max_length=255, null=True)
    fw_file = fields.CharField(max_length=255, default="latest")
    fw_version = fields.CharField(max_length=255, null=True)
    hw_model = fields.CharField(max_length=255, null=True, default="default")
    hw_revision = fields.CharField(max_length=255, null=True, default="default")
    feed = fields.CharField(max_length=255, default="default")
    flavor = fields.CharField(max_length=255, default="default")
    last_state = fields.CharField(max_length=255, null=True, default="unknown")
    progress = fields.IntField(null=True)
    last_log = fields.TextField(null=True)
    last_seen = fields.BigIntField(null=True)
    last_ip = fields.CharField(max_length=15, null=True)
    last_ipv6 = fields.CharField(max_length=40, null=True)
    tags = fields.ManyToManyField(
        "models.Tag", related_name="devices", through="device_tags"
    )


class Rollout(Model):
    id = fields.IntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    name = fields.CharField(max_length=255, null=True)
    hw_model = fields.CharField(max_length=255, default="default")
    hw_revision = fields.CharField(max_length=255, default="default")
    feed = fields.CharField(max_length=255, default="default")
    flavor = fields.CharField(max_length=255, default="default")
    fw_file = fields.CharField(max_length=255)
    paused = fields.BooleanField(default=False)
    success_count = fields.IntField(default=0)
    failure_count = fields.IntField(default=0)


class FirmwareCompatibility(Model):
    id = fields.IntField(primary_key=True)
    hw_model = fields.CharField(max_length=255)
    hw_revision = fields.CharField(max_length=255)


class FirmwareUpdate(Model):
    id = fields.IntField(primary_key=True)
    uri = fields.CharField(max_length=255)
    version = fields.CharField(max_length=255)
    compatibility = fields.ManyToManyField(
        "models.FirmwareCompatibility",
        related_name="updates",
        through="update_compatibility",
    )

    @classmethod
    async def latest(cls):
        updates = await cls.all()
        return sorted(
            updates,
            key=lambda x: semver.Version.parse(x.version),
            reverse=True,
        )[0]

    @property
    def path(self):
        return Path(url2pathname(unquote(urlparse(self.uri).path)))

    def generate_chunk(self, request: Request, tenant: str, dev_id: str) -> list:
        path = Path(self.uri)
        return [
            {
                "part": "os",
                "version": "1",
                "name": path.name,
                "artifacts": [
                    {
                        "filename": path.name,
                        "hashes": {"sha1": sha1_hash_file(path)},
                        "size": path.stat().st_size,
                        "_links": {
                            "download": {
                                "href": str(
                                    request.url_for(
                                        "download_firmware",
                                        tenant=tenant,
                                        dev_id=dev_id,
                                        file=path,
                                    )
                                )
                            }
                        },
                    }
                ],
            }
        ]
