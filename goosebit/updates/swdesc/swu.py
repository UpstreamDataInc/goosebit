import logging
from typing import Any

import libconf
from anyio import Path, open_file

from goosebit.util.version import Version

from .func import sha1_hash_file

logger = logging.getLogger(__name__)

MAGIC = b"0707"


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
        logger.warning(f"Parsing swu descriptor failed, error={e}")
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
        swdesc_attrs["hash"] = await sha1_hash_file(f)

        return swdesc_attrs
