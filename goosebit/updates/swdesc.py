import hashlib
import logging
import random
import string
from typing import Any

import httpx
import libconf
import semver
from anyio import AsyncFile, Path, open_file

from goosebit.settings import config

logger = logging.getLogger(__name__)


def _append_compatibility(boardname, value, compatibility):
    if "hardware-compatibility" in value:
        for revision in value["hardware-compatibility"]:
            compatibility.append({"hw_model": boardname, "hw_revision": revision})


def parse_descriptor(swdesc: libconf.AttrDict[Any, Any | None]):
    swdesc_attrs = {}
    try:
        swdesc_attrs["version"] = semver.Version.parse(swdesc["software"]["version"])
        compatibility: list[dict[str, str]] = []
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
    async with await open_file(file, "r+b") as f:
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
        stat = await file.stat()
        swdesc_attrs["size"] = stat.st_size
        swdesc_attrs["hash"] = await _sha1_hash_file(f)
        return swdesc_attrs


async def parse_remote(url: str):
    async with httpx.AsyncClient() as c:
        file = await c.get(url)
        artifacts_dir = Path(config.artifacts_dir)
        tmp_file_path = artifacts_dir.joinpath("tmp", ("".join(random.choices(string.ascii_lowercase, k=12)) + ".tmp"))
        await tmp_file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            async with await open_file(tmp_file_path, "w+b") as f:
                await f.write(file.content)
            file_data = await parse_file(Path(str(f.name)))
        finally:
            await tmp_file_path.unlink()
        return file_data


async def _sha1_hash_file(fileobj: AsyncFile):
    last = await fileobj.tell()
    await fileobj.seek(0)
    sha1_hash = hashlib.sha1()
    buf = bytearray(2**18)
    view = memoryview(buf)
    while True:
        size = await fileobj.readinto(buf)
        if size == 0:
            break
        sha1_hash.update(view[:size])

    await fileobj.seek(last)
    return sha1_hash.hexdigest()
