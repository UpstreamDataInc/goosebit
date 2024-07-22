from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from goosebit.models import Device
from goosebit.settings import UPDATE_VERSION_PARSER, UPDATES_DIR


def sha1_hash_file(file_path: Path):
    with file_path.open("rb") as f:
        sha1_hash = hashlib.file_digest(f, "sha1")
    return sha1_hash.hexdigest()


def get_newest_fw(hw_model: str, hw_revision: str) -> Optional[str]:
    def filter_filename(filename, hw_model, hw_revision) -> bool:
        image_data = filename.split("_")
        assert len(image_data) == 3
        model, revision, _ = image_data
        return model == hw_model and revision == hw_revision

    fw_files = [
        f
        for f in UPDATES_DIR.iterdir()
        if f.suffix == ".swu" and filter_filename(f.name, hw_model, hw_revision)
    ]
    if len(fw_files) == 0:
        return None

    return str(sorted(fw_files, key=lambda x: fw_sort_key(x), reverse=True)[0].name)


def validate_filename(filename: str) -> bool:
    try:
        fw_sort_key(Path(filename))
        return True
    except ValueError:
        return False


def fw_sort_key(filename: Path):
    return UPDATE_VERSION_PARSER.parse(filename)


async def get_device_by_uuid(dev_id: str) -> Device:
    if dev_id == "unknown":
        return Device(
            uuid="unknown",
            name="Unknown",
            fw_file="latest",
            fw_version=None,
            last_state=None,
            last_log=None,
        )
    return (await Device.get_or_create(uuid=dev_id))[0]
