import hashlib
import logging
from pathlib import Path
from typing import Any

import aiofiles
import httpx
import libconf
import semver
from aiofiles import os

logger = logging.getLogger(__name__)


def _append_compatibility(boardname, value, compatibility):
    if "hardware-compatibility" in value:
        for revision in value["hardware-compatibility"]:
            compatibility.append({"hw_model": boardname, "hw_revision": revision})


def parse_descriptor(swdesc: libconf.AttrDict[Any, Any | None]):
    swdesc_attrs = {}
    try:
        swdesc_attrs["version"] = semver.Version.parse(swdesc["software"]["version"])
        compatibility = []
        _append_compatibility("default", swdesc["software"], compatibility)

        for key in swdesc["software"]:
            element = swdesc["software"][key]
            _append_compatibility(key, element, compatibility)

            if isinstance(element, dict):
                for key2 in element:
                    _append_compatibility(key, element[key2], compatibility)

        swdesc_attrs["compatibility"] = compatibility
    except KeyError as e:
        logging.warning(f"Parsing swu descriptor failed, error={e}")
        raise ValueError("Parsing swu descriptor failed", e)

    return swdesc_attrs


async def parse_file(file: Path):
    async with aiofiles.open(file, "r+b") as f:
        # get file size
        size = int((await f.read(110))[54:62], 16)
        filename = b""
        next_byte = await f.read(1)
        while not next_byte == b"\x00":
            filename += next_byte
            next_byte = await f.read(1)
        # 4 null bytes
        await f.read(3)

        # should always be the first file
        if not filename == b"sw-description":
            return None

        swdesc = libconf.loads((await f.read(size)).decode("utf-8"))

        swdesc_attrs = parse_descriptor(swdesc)
        stat = await os.stat(file)
        swdesc_attrs["size"] = stat.st_size
        swdesc_attrs["hash"] = await _sha1_hash_file(file)
        return swdesc_attrs


async def parse_remote(url: str):
    async with httpx.AsyncClient() as c:
        file = await c.get(url)
        async with aiofiles.tempfile.NamedTemporaryFile("w+b") as f:
            await f.write(file.content)
            return await parse_file(Path(f.name))


async def _sha1_hash_file(file_path: Path):
    sha1_hash = hashlib.sha1()

    async with aiofiles.open(file_path, "rb") as f:
        while True:
            chunk = await f.read(5 * 1024 * 1024)  # Read in 5MB chunks
            if not chunk:
                break
            sha1_hash.update(chunk)

    return sha1_hash.hexdigest()
