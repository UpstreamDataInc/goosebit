import hashlib
import logging
import random
import string
from typing import Any

import httpx
import libconf
from anyio import AsyncFile, Path, open_file

from goosebit.storage import storage
from goosebit.util.version import Version

logger = logging.getLogger(__name__)


def _append_compatibility(boardname, value, compatibility):
    if not isinstance(value, dict):
        return
    if "hardware-compatibility" in value:
        for revision in value["hardware-compatibility"]:
            compatibility.append({"hw_model": boardname, "hw_revision": revision})


def parse_descriptor(swdesc: libconf.AttrDict[Any, Any | None]):
    swdesc_attrs = {}
    try:
        swdesc_attrs["version"] = Version.parse(swdesc["software"]["version"])
        compatibility: list[dict[str, str]] = []
        _append_compatibility("default", swdesc["software"], compatibility)

        for key in swdesc["software"]:
            element = swdesc["software"][key]
            _append_compatibility(key, element, compatibility)

            if isinstance(element, dict):
                for key2 in element:
                    _append_compatibility(key, element[key2], compatibility)

        if len(compatibility) == 0:
            # if nothing is specified, assume compatibility with default / default boards
            compatibility.append({"hw_model": "default", "hw_revision": "default"})

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
        temp_dir = Path(storage.get_temp_dir())
        tmp_file_path = temp_dir.joinpath("".join(random.choices(string.ascii_lowercase, k=12)) + ".tmp")
        try:
            async with await open_file(tmp_file_path, "w+b") as f:
                await f.write(file.content)
            file_data = await parse_file(tmp_file_path)  # Use anyio.Path for parse_file
        except Exception:
            raise
        finally:
            await tmp_file_path.unlink(missing_ok=True)
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
