from __future__ import annotations

import hashlib
from pathlib import Path


def sha1_hash_file(file_path: Path):
    with file_path.open("rb") as f:
        sha1_hash = hashlib.file_digest(f, "sha1")
    return sha1_hash.hexdigest()


def validate_filename(filename: str) -> bool:
    return filename.endswith(".swu")
