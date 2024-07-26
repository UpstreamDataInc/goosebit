from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import semver

from goosebit.models import Device, Firmware, Hardware, UpdateModeEnum


def sha1_hash_file(file_path: Path):
    with file_path.open("rb") as f:
        sha1_hash = hashlib.file_digest(f, "sha1")
    return sha1_hash.hexdigest()


async def get_newest_fw(hw_model: str, hw_revision: str) -> Optional[str]:
    compatibility = await Hardware.get_or_create(
        hw_model=hw_model, hw_revision=hw_revision
    )
    firmware = await Firmware.filter(compatibility=compatibility).all()
    if len(firmware) == 0:
        return None

    return str(
        sorted(firmware, key=lambda x: semver.Version.parse(x.version), reverse=True)[
            0
        ].path
    )


def validate_filename(filename: str) -> bool:
    return filename.endswith(".swu")
