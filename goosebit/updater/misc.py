from __future__ import annotations

import datetime
import hashlib
from pathlib import Path

from goosebit.models import Device
from goosebit.settings import UPDATES_DIR


def sha1_hash_file(file_path: Path):
    with file_path.open("rb") as f:
        sha1_hash = hashlib.file_digest(f, "sha1")
    return sha1_hash.hexdigest()


def get_newest_fw() -> str:
    fw_files = [f for f in UPDATES_DIR.iterdir() if f.suffix == ".swu"]
    if len(fw_files) == 0:
        return ""

    return str(sorted(fw_files, key=lambda x: fw_sort_key(x), reverse=True)[0].name)


def fw_sort_key(filename: Path) -> datetime.datetime:
    image_data = filename.stem.split("_")
    if len(image_data) == 3:
        tenant, date, time = image_data
    elif len(image_data) == 4:
        tenant, hw_version, date, time = image_data
    else:
        return datetime.datetime.now()

    return datetime.datetime.strptime(f"{date}_{time}", "%Y%m%d_%H%M%S")


def get_fw_components(filename: Path) -> dict:
    image_data = filename.stem.split("_")
    if len(image_data) == 3:
        tenant, date, time = image_data
        return {
            "date": datetime.datetime.strptime(f"{date}_{time}", "%Y%m%d_%H%M%S"),
            "day": date,
            "time": time,
            "tenant": tenant,
            "hw_version": 0,
        }
    elif len(image_data) == 4:
        tenant, hw_version, date, time = image_data
        return {
            "date": datetime.datetime.strptime(f"{date}_{time}", "%Y%m%d_%H%M%S"),
            "day": date,
            "time": time,
            "tenant": tenant,
            "hw_version": int(hw_version.upper().replace("V", "")),
        }


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
